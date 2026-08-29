"""Shared single-cell input loading for isolated Scanpy processes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anndata
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse
from scipy.io import mmread


def read_single_cell(config: dict[str, Any]) -> tuple[anndata.AnnData, dict[str, Any]]:
    path = Path(config["count_matrix"])
    input_format = str(config["input_format"])
    count_layer = str(config.get("count_layer") or "").strip()
    if input_format in {"csv", "tsv"}:
        frame = pd.read_csv(path, sep=config["count_delimiter"], index_col=0)
        frame.index = frame.index.astype(str)
        frame.columns = frame.columns.astype(str)
        adata = anndata.AnnData(
            X=sparse.csr_matrix(frame.to_numpy()),
            obs=pd.DataFrame(index=frame.index.copy()),
            var=pd.DataFrame(index=frame.columns.copy()),
        )
        source_layers: list[str] = []
        selected_layer = "X"
    elif input_format == "h5ad":
        source = sc.read_h5ad(path)
        source_layers = sorted(
            str(layer)
            for layer in source.layers.keys()
            if layer is not None and str(layer).strip()
        )
        if count_layer:
            if count_layer not in source.layers:
                raise ValueError(
                    f"AnnData count layer {count_layer!r} was not found; available layers: "
                    + (", ".join(source_layers) or "none")
                    + "."
                )
            counts = source.layers[count_layer]
            selected_layer = count_layer
        else:
            counts = source.X
            selected_layer = "X"
        adata = anndata.AnnData(
            X=counts.copy(),
            obs=source.obs.copy(),
            var=source.var.copy(),
        )
    elif input_format == "10x_h5":
        if count_layer:
            raise ValueError("count_layer applies only to AnnData .h5ad input.")
        source = sc.read_10x_h5(path, gex_only=True)
        source.var_names_make_unique()
        adata = anndata.AnnData(X=source.X.copy(), obs=source.obs.copy(), var=source.var.copy())
        source_layers = []
        selected_layer = "X"
    elif input_format == "10x_mtx_gz":
        if count_layer:
            raise ValueError("count_layer applies only to AnnData .h5ad input.")
        source = sc.read_10x_mtx(
            path.parent,
            var_names="gene_symbols",
            make_unique=True,
            cache=False,
            gex_only=True,
        )
        adata = anndata.AnnData(X=source.X.copy(), obs=source.obs.copy(), var=source.var.copy())
        source_layers = []
        selected_layer = "X"
    elif input_format == "10x_mtx":
        if count_layer:
            raise ValueError("count_layer applies only to AnnData .h5ad input.")
        adata = _read_uncompressed_10x_mtx(path)
        source_layers = []
        selected_layer = "X"
    else:
        raise ValueError(f"Unsupported single-cell input format: {input_format}")

    adata.obs_names = adata.obs_names.astype(str)
    adata.var_names = adata.var_names.astype(str)
    _validate_identifiers(adata)
    _validate_raw_counts(adata.X)
    _merge_external_metadata(adata, config)
    return adata, {
        "input_format": input_format,
        "count_layer": selected_layer,
        "available_layers": source_layers,
    }


def count_metrics(matrix: Any) -> dict[str, Any]:
    if sparse.issparse(matrix):
        values = np.asarray(matrix.data)
        nonzero = int(matrix.nnz)
        library_sizes = np.asarray(matrix.sum(axis=1)).ravel()
        detected_genes = np.asarray((matrix > 0).sum(axis=1)).ravel()
        detected_cells = np.asarray((matrix > 0).sum(axis=0)).ravel()
    else:
        array = np.asarray(matrix)
        values = array.ravel()
        nonzero = int(np.count_nonzero(array))
        library_sizes = array.sum(axis=1)
        detected_genes = (array > 0).sum(axis=1)
        detected_cells = (array > 0).sum(axis=0)
    return {
        "values": values,
        "nonzero": nonzero,
        "library_sizes": np.asarray(library_sizes),
        "detected_genes": np.asarray(detected_genes),
        "detected_cells": np.asarray(detected_cells),
    }


def mitochondrial_mask(adata: anndata.AnnData) -> np.ndarray:
    names = pd.Index(adata.var_names.astype(str)).str.upper()
    mask = np.asarray(names.str.startswith("MT-"), dtype=bool)
    for column in ("gene_symbols", "gene_symbol", "symbol", "feature_name"):
        if column in adata.var:
            symbols = adata.var[column].fillna("").astype(str).str.upper()
            mask |= np.asarray(symbols.str.startswith("MT-"), dtype=bool)
    return mask


def categorical_metadata(obs: pd.DataFrame) -> list[dict[str, Any]]:
    fields = []
    for column in obs.columns:
        values = obs[column].astype(object)
        values = values.where(pd.notna(values), "").astype(str)
        counts = values[values != ""].value_counts()
        if 1 < len(counts) <= 30:
            fields.append(
                {
                    "column": str(column),
                    "levels": int(len(counts)),
                    "missing": int((values == "").sum()),
                    "counts": {str(key): int(value) for key, value in sorted(counts.items())},
                }
            )
    return fields


def _validate_identifiers(adata: anndata.AnnData) -> None:
    if adata.n_obs == 0 or adata.n_vars == 0:
        raise ValueError("Single-cell input contains no cells or genes.")
    if adata.obs_names.has_duplicates:
        duplicate = adata.obs_names[adata.obs_names.duplicated()][0]
        raise ValueError(f"Cell IDs must be unique; duplicate: {duplicate}")
    if adata.var_names.has_duplicates:
        duplicate = adata.var_names[adata.var_names.duplicated()][0]
        raise ValueError(f"Gene identifiers must be unique; duplicate: {duplicate}")
    if any(not str(value).strip() for value in adata.obs_names):
        raise ValueError("Cell IDs cannot be empty.")
    if any(not str(value).strip() for value in adata.var_names):
        raise ValueError("Gene identifiers cannot be empty.")


def _read_uncompressed_10x_mtx(path: Path) -> anndata.AnnData:
    features_path = path.parent / "features.tsv"
    if not features_path.is_file():
        features_path = path.parent / "genes.tsv"
    barcodes = pd.read_csv(
        path.parent / "barcodes.tsv", sep="\t", header=None, dtype=str
    )
    features = pd.read_csv(features_path, sep="\t", header=None, dtype=str)
    matrix = mmread(path)
    matrix = sparse.csr_matrix(matrix).T
    if matrix.shape != (len(barcodes), len(features)):
        raise ValueError(
            "10x matrix dimensions do not match barcodes.tsv and features.tsv/genes.tsv."
        )
    names = features.iloc[:, 1] if features.shape[1] > 1 else features.iloc[:, 0]
    var_names = anndata.utils.make_index_unique(pd.Index(names.astype(str).to_numpy()))
    var_names.name = None
    obs_names = pd.Index(barcodes.iloc[:, 0].astype(str).to_numpy())
    obs_names.name = None
    var = pd.DataFrame(index=var_names)
    var["gene_ids"] = features.iloc[:, 0].astype(str).to_numpy()
    if features.shape[1] > 2:
        var["feature_types"] = features.iloc[:, 2].astype(str).to_numpy()
        keep = var["feature_types"] == "Gene Expression"
        matrix = matrix[:, keep.to_numpy()]
        var = var.loc[keep].copy()
    return anndata.AnnData(
        X=matrix,
        obs=pd.DataFrame(index=obs_names),
        var=var,
    )


def _validate_raw_counts(matrix: Any) -> None:
    metrics = count_metrics(matrix)
    values = metrics["values"]
    if values.size and not np.isfinite(values).all():
        raise ValueError("Raw-count matrix contains non-finite values.")
    if values.size and float(values.min()) < 0:
        raise ValueError("Raw-count matrix contains negative values.")
    if values.size and float(values.max()) > 2_147_483_647:
        raise ValueError("Raw-count matrix contains values above the supported count limit.")
    if values.size and not np.allclose(values, np.rint(values), rtol=0, atol=1e-8):
        raise ValueError(
            "Selected expression matrix is not non-negative integer raw counts; choose a raw-count AnnData layer."
        )
    if sparse.issparse(matrix):
        matrix.data = np.rint(matrix.data).astype(np.int64)
    else:
        matrix[:] = np.rint(np.asarray(matrix)).astype(np.int64)


def _merge_external_metadata(adata: anndata.AnnData, config: dict[str, Any]) -> None:
    metadata_path = config.get("metadata")
    if not metadata_path:
        return
    cell_id_column = str(config["cell_id_column"])
    metadata = pd.read_csv(
        metadata_path,
        sep=config["metadata_delimiter"],
        dtype=str,
    )
    if cell_id_column not in metadata.columns:
        raise ValueError(f"Cell metadata is missing the {cell_id_column!r} column.")
    if len(metadata.columns) > 21:
        raise ValueError("Cell metadata may contain at most 20 annotation columns plus the cell ID.")
    if metadata[cell_id_column].isna().any() or (metadata[cell_id_column].str.strip() == "").any():
        raise ValueError("Cell metadata contains an empty cell ID.")
    metadata[cell_id_column] = metadata[cell_id_column].astype(str)
    if metadata[cell_id_column].duplicated().any():
        duplicate = metadata.loc[metadata[cell_id_column].duplicated(), cell_id_column].iloc[0]
        raise ValueError(f"Cell metadata IDs must be unique; duplicate: {duplicate}")
    metadata = metadata.set_index(cell_id_column)
    expected = set(adata.obs_names)
    observed = set(metadata.index)
    missing = expected - observed
    extra = observed - expected
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {len(missing)} expression-matrix cells")
        if extra:
            details.append(f"contains {len(extra)} extra cells")
        raise ValueError("Expression matrix and cell metadata must match exactly: " + "; ".join(details) + ".")
    metadata = metadata.loc[adata.obs_names]
    for column in metadata.columns:
        target = str(column)
        if target in adata.obs.columns:
            target = f"{target}_external"
            if target in adata.obs.columns:
                raise ValueError(f"External metadata column conflicts with AnnData obs: {column}")
        adata.obs[target] = metadata[column].fillna("").astype(str).to_numpy()
