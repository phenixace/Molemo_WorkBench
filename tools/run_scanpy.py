"""Isolated Scanpy runner invoked by the approved Molemo workflow."""

from __future__ import annotations

import importlib.metadata
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import anndata
import leidenalg
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse

from single_cell_io import mitochondrial_mask, read_single_cell


RANDOM_SEED = 0
MAX_EMBEDDING_POINTS = 5_000
MAX_QC_POINTS = 2_000
SCANPY_VERSION = importlib.metadata.version("scanpy")
ANNDATA_VERSION = importlib.metadata.version("anndata")
LEIDENALG_VERSION = importlib.metadata.version("leidenalg")
try:
    SCIKIT_IMAGE_VERSION = importlib.metadata.version("scikit-image")
except importlib.metadata.PackageNotFoundError:
    SCIKIT_IMAGE_VERSION = None


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_scanpy.py CONFIG_JSON OUTPUT_DIR")
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=False)

    adata, source_info = read_single_cell(config)
    adata.obs_names.name = config["cell_id_column"]
    input_counts = adata.X.copy()
    input_var_names = adata.var_names.copy()
    metadata_fields = [str(column) for column in adata.obs.columns]
    adata.var["mt"] = mitochondrial_mask(adata)
    qc_vars = ["mt"] if bool(adata.var["mt"].any()) else []
    sc.pp.calculate_qc_metrics(adata, qc_vars=qc_vars, percent_top=None, log1p=True, inplace=True)
    if "pct_counts_mt" not in adata.obs:
        adata.obs["pct_counts_mt"] = 0.0
    initial_obs = adata.obs.copy()
    initial_var = adata.var.copy()

    parameters = config["parameters"]
    cell_mask = (
        (adata.obs["n_genes_by_counts"] >= int(parameters["min_genes"]))
        & (adata.obs["pct_counts_mt"] <= float(parameters["max_mito_percent"]))
    )
    adata = adata[cell_mask].copy()
    detected_after_cell_filter = np.asarray((adata.X > 0).sum(axis=0)).ravel()
    gene_mask = detected_after_cell_filter >= int(parameters["min_cells"])
    adata = adata[:, gene_mask].copy()
    qc_retained = set(adata.obs_names)
    captured_warnings: list[str] = []
    doublet = {
        "enabled": False,
        "predicted": 0,
        "excluded": 0,
        "expected_rate": None,
        "batch_key": None,
        "threshold": None,
        "batch_thresholds": {},
    }
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        if bool(parameters.get("run_scrublet")):
            batch_key = str(parameters.get("doublet_batch_key") or "").strip() or None
            effective_cells = adata.n_obs
            if batch_key:
                effective_cells = int(adata.obs[batch_key].value_counts().min())
            n_prin_comps = min(
                30,
                max(2, int(math.sqrt(effective_cells))),
                effective_cells - 1,
                adata.n_vars - 1,
            )
            if n_prin_comps < 2:
                raise ValueError("Scrublet requires at least two principal components after QC filtering.")
            sc.pp.scrublet(
                adata,
                batch_key=batch_key,
                expected_doublet_rate=float(parameters["expected_doublet_rate"]),
                n_prin_comps=n_prin_comps,
                random_state=RANDOM_SEED,
                verbose=False,
            )
            initial_obs["doublet_score"] = np.nan
            initial_obs["predicted_doublet"] = pd.Series(
                pd.NA, index=initial_obs.index, dtype="boolean"
            )
            initial_obs.loc[adata.obs_names, "doublet_score"] = adata.obs[
                "doublet_score"
            ].astype(float)
            initial_obs.loc[adata.obs_names, "predicted_doublet"] = adata.obs[
                "predicted_doublet"
            ].astype(bool)
            predicted = int(adata.obs["predicted_doublet"].sum())
            doublet = _doublet_summary(
                adata,
                expected_rate=float(parameters["expected_doublet_rate"]),
                batch_key=batch_key,
                predicted=predicted,
                excluded=predicted if bool(parameters.get("exclude_predicted_doublets")) else 0,
            )
            doublet["n_prin_comps"] = n_prin_comps
            if bool(parameters.get("exclude_predicted_doublets")):
                adata = adata[~adata.obs["predicted_doublet"].astype(bool)].copy()
                if adata.n_obs < 10:
                    raise ValueError(
                        "Excluding predicted doublets leaves fewer than 10 cells; keep them and review scores."
                    )
        adata.layers["counts"] = adata.X.copy()
        sc.pp.normalize_total(adata, target_sum=10_000)
        sc.pp.log1p(adata)
        adata.raw = adata
        n_top = min(int(parameters["n_top_genes"]), adata.n_vars)
        if n_top < adata.n_vars:
            sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat")
        else:
            adata.var["highly_variable"] = True
        hvg_count = int(adata.var["highly_variable"].sum())
        n_comps = min(30, adata.n_obs - 1, hvg_count - 1)
        if n_comps < 2:
            raise ValueError("At least two PCA components are required after filtering.")
        sc.pp.pca(
            adata,
            n_comps=n_comps,
            mask_var="highly_variable",
            svd_solver="arpack",
            random_state=RANDOM_SEED,
        )
        n_neighbors = min(int(parameters["n_neighbors"]), adata.n_obs - 1)
        sc.pp.neighbors(
            adata,
            n_neighbors=n_neighbors,
            n_pcs=n_comps,
            random_state=RANDOM_SEED,
        )
        sc.tl.umap(adata, random_state=RANDOM_SEED)
        sc.tl.leiden(
            adata,
            key_added="leiden",
            resolution=float(parameters["leiden_resolution"]),
            random_state=RANDOM_SEED,
            flavor="igraph",
            n_iterations=2,
            directed=False,
        )
        if adata.obs["leiden"].nunique() > 1:
            sc.tl.rank_genes_groups(
                adata,
                groupby="leiden",
                reference="rest",
                method="wilcoxon",
                use_raw=True,
                n_genes=min(int(parameters["marker_genes"]), adata.n_vars),
                corr_method="benjamini-hochberg",
            )
        for item in warning_records:
            message = " ".join(str(item.message).split())
            if message and message not in captured_warnings:
                captured_warnings.append(message[:500])

    cell_qc = _cell_qc(initial_obs, adata, qc_retained)
    embedding = _embedding_frame(adata)
    markers = _marker_frame(adata, int(parameters["marker_genes"]))
    gene_qc = _gene_qc(initial_var, adata, input_counts, input_var_names)
    cluster_summary = _cluster_summary(adata, markers)
    marker_dotplot = _marker_dotplot(adata, markers)
    embedding_points = _sample_embedding(embedding, MAX_EMBEDDING_POINTS)
    qc_points = _sample_qc(cell_qc, MAX_QC_POINTS)

    cell_qc.to_csv(output_dir / "cell_qc.tsv", sep="\t", index=False, float_format="%.6g")
    embedding.to_csv(output_dir / "embedding.tsv", sep="\t", index=False, float_format="%.6g")
    markers.to_csv(output_dir / "markers.tsv", sep="\t", index=False, float_format="%.6g")
    gene_qc.to_csv(output_dir / "gene_qc.tsv", sep="\t", index=False, float_format="%.6g")
    cluster_summary.to_csv(output_dir / "cluster_summary.tsv", sep="\t", index=False)
    adata.write_h5ad(output_dir / "analysis.h5ad", compression="gzip")

    clusters = int(adata.obs["leiden"].nunique())
    caveats = [
        "Leiden clusters and UMAP coordinates are exploratory representations, not discovered cell types.",
        "Marker ranking compares cells within this dataset and does not account for donor-level replication; use sample-aware pseudobulk methods for inferential differential expression.",
        "This workflow does not perform ambient-RNA correction, batch integration, automated cell-type annotation, or trajectory inference.",
        "QC thresholds are dataset-specific; mitochondrial percentage and detected-gene cutoffs should be reviewed per sample when batches are present.",
    ]
    if doublet["enabled"]:
        caveats.append(
            "Scrublet scores and automatic thresholds are model-based QC signals, not confirmed doublet labels; review their distribution and sample context."
        )
    else:
        caveats.append("Doublet detection was not requested for this run.")
    if clusters == 1:
        caveats.append("Only one Leiden cluster was found, so cluster marker ranking was not performed.")
    summary = {
        "method": "Scanpy",
        "method_version": SCANPY_VERSION,
        "random_seed": RANDOM_SEED,
        "input_mode": "cell_by_gene_raw_counts",
        "input_format": source_info["input_format"],
        "count_layer": source_info["count_layer"],
        "available_layers": source_info["available_layers"],
        "cells_input": int(initial_obs.shape[0]),
        "genes_input": int(len(input_var_names)),
        "cells_retained": int(adata.n_obs),
        "genes_retained": int(adata.n_vars),
        "highly_variable_genes": int(adata.var["highly_variable"].sum()),
        "clusters": clusters,
        "parameters": parameters,
        "metadata_fields": metadata_fields,
        "doublet": doublet,
        "embedding": {
            "points": embedding_points,
            "shown": len(embedding_points),
            "total": int(embedding.shape[0]),
            "variance_explained": [
                round(float(value) * 100.0, 2) for value in adata.uns["pca"]["variance_ratio"][:2]
            ],
        },
        "qc": {
            "points": qc_points,
            "shown": len(qc_points),
            "total": int(cell_qc.shape[0]),
        },
        "cluster_summary": cluster_summary.to_dict(orient="records"),
        "markers": _records(markers.head(200)),
        "marker_dotplot": marker_dotplot,
        "warnings": captured_warnings,
        "caveats": caveats,
        "package_versions": {
            "scanpy": SCANPY_VERSION,
            "anndata": ANNDATA_VERSION,
            "leidenalg": LEIDENALG_VERSION,
            "scikit-image": SCIKIT_IMAGE_VERSION,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    manifest = {
        "method": summary["method"],
        "method_version": summary["method_version"],
        "random_seed": RANDOM_SEED,
        "input_mode": summary["input_mode"],
        "input_format": summary["input_format"],
        "count_layer": summary["count_layer"],
        "source_paths": config["source_paths"],
        "input_sha256": config["input_sha256"],
        "parameters": parameters,
        "preflight_counts": config["preflight_counts"],
        "result_counts": {
            "cells_retained": summary["cells_retained"],
            "genes_retained": summary["genes_retained"],
            "highly_variable_genes": summary["highly_variable_genes"],
            "clusters": summary["clusters"],
            "predicted_doublets": doublet["predicted"],
            "excluded_doublets": doublet["excluded"],
        },
        "package_versions": summary["package_versions"],
        "outputs": [
            "cell_qc.tsv",
            "embedding.tsv",
            "markers.tsv",
            "gene_qc.tsv",
            "cluster_summary.tsv",
            "analysis.h5ad",
            "run_manifest.json",
            "summary.json",
            "artifact_index.json",
            "summary.md",
        ],
    }
    artifact_index = {
        "artifacts": [
            {"type": "table", "path": "cell_qc.tsv"},
            {"type": "embedding", "path": "embedding.tsv"},
            {"type": "table", "path": "markers.tsv"},
            {"type": "table", "path": "gene_qc.tsv"},
            {"type": "table", "path": "cluster_summary.tsv"},
            {"type": "anndata", "path": "analysis.h5ad"},
            {"type": "manifest", "path": "run_manifest.json"},
            {"type": "analysis-summary", "path": "summary.json"},
            {"type": "summary", "path": "summary.md"},
        ]
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "run_manifest.json", manifest)
    _write_json(output_dir / "artifact_index.json", artifact_index)
    (output_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")


def _doublet_summary(
    adata: anndata.AnnData,
    *,
    expected_rate: float,
    batch_key: str | None,
    predicted: int,
    excluded: int,
) -> dict[str, Any]:
    scrublet = dict(adata.uns.get("scrublet") or {})
    batches = dict(scrublet.get("batches") or {})
    batch_thresholds = {
        str(batch): _finite(details.get("threshold"))
        for batch, details in batches.items()
        if isinstance(details, dict)
    }
    return {
        "enabled": True,
        "predicted": predicted,
        "excluded": excluded,
        "expected_rate": expected_rate,
        "batch_key": batch_key,
        "threshold": _finite(scrublet.get("threshold")),
        "batch_thresholds": batch_thresholds,
    }


def _cell_qc(
    initial_obs: pd.DataFrame,
    adata: anndata.AnnData,
    qc_retained: set[str],
) -> pd.DataFrame:
    retained = set(adata.obs_names)
    frame = pd.DataFrame(
        {
            "cell_id": initial_obs.index.astype(str),
            "total_counts": initial_obs["total_counts"].astype(float).to_numpy(),
            "n_genes_by_counts": initial_obs["n_genes_by_counts"].astype(int).to_numpy(),
            "pct_counts_mt": initial_obs["pct_counts_mt"].astype(float).to_numpy(),
        }
    )
    frame["qc_retained"] = frame["cell_id"].isin(qc_retained)
    frame["retained"] = frame["cell_id"].isin(retained)
    clusters = adata.obs["leiden"].astype(str).to_dict()
    frame["cluster"] = frame["cell_id"].map(clusters)
    if "doublet_score" in initial_obs:
        frame["doublet_score"] = initial_obs["doublet_score"].astype(float).to_numpy()
        frame["predicted_doublet"] = initial_obs["predicted_doublet"].to_numpy()
    for column in initial_obs.columns:
        if column not in frame.columns and column not in {
            "doublet_score",
            "predicted_doublet",
        }:
            values = initial_obs[column]
            if values.dtype.name in {"category", "object", "string"}:
                text = values.astype(object).where(pd.notna(values), "").astype(str)
                frame[str(column)] = text.to_numpy()
    return frame


def _embedding_frame(adata: anndata.AnnData) -> pd.DataFrame:
    umap = np.asarray(adata.obsm["X_umap"])
    pca = np.asarray(adata.obsm["X_pca"])
    frame = pd.DataFrame(
        {
            "cell_id": adata.obs_names.astype(str),
            "cluster": adata.obs["leiden"].astype(str).to_numpy(),
            "umap_1": umap[:, 0],
            "umap_2": umap[:, 1],
            "pc_1": pca[:, 0],
            "pc_2": pca[:, 1],
            "total_counts": adata.obs["total_counts"].astype(float).to_numpy(),
            "n_genes_by_counts": adata.obs["n_genes_by_counts"].astype(int).to_numpy(),
            "pct_counts_mt": adata.obs["pct_counts_mt"].astype(float).to_numpy(),
        }
    )
    if "doublet_score" in adata.obs:
        frame["doublet_score"] = adata.obs["doublet_score"].astype(float).to_numpy()
        frame["predicted_doublet"] = adata.obs["predicted_doublet"].astype(bool).to_numpy()
    for column in adata.obs.columns:
        if column not in frame.columns and column not in {"leiden"}:
            values = adata.obs[column]
            if values.dtype.name in {"category", "object", "string"}:
                frame[str(column)] = values.astype(str).to_numpy()
    return frame


def _marker_frame(adata: anndata.AnnData, marker_genes: int) -> pd.DataFrame:
    columns = ["cluster", "rank", "gene", "score", "logfoldchange", "pvalue", "pvalue_adj", "pct_cluster", "pct_rest"]
    if adata.obs["leiden"].nunique() <= 1:
        return pd.DataFrame(columns=columns)
    groups = sorted(adata.obs["leiden"].astype(str).unique(), key=lambda value: int(value))
    records = []
    raw = adata.raw
    assert raw is not None
    for group in groups:
        frame = sc.get.rank_genes_groups_df(adata, group=group).head(marker_genes)
        group_mask = adata.obs["leiden"].astype(str).to_numpy() == group
        rest_mask = ~group_mask
        for rank, row in enumerate(frame.itertuples(index=False), start=1):
            gene = str(row.names)
            gene_index = raw.var_names.get_loc(gene)
            expression = raw.X[:, gene_index]
            values = expression.toarray().ravel() if sparse.issparse(expression) else np.asarray(expression).ravel()
            records.append(
                {
                    "cluster": group,
                    "rank": rank,
                    "gene": gene,
                    "score": _finite(row.scores),
                    "logfoldchange": _finite(row.logfoldchanges),
                    "pvalue": _finite(row.pvals),
                    "pvalue_adj": _finite(row.pvals_adj),
                    "pct_cluster": round(float((values[group_mask] > 0).mean()), 4),
                    "pct_rest": round(float((values[rest_mask] > 0).mean()), 4),
                }
            )
    return pd.DataFrame.from_records(records, columns=columns)


def _gene_qc(
    initial_var: pd.DataFrame,
    adata: anndata.AnnData,
    counts: Any,
    gene_names: pd.Index,
) -> pd.DataFrame:
    retained = set(adata.var_names)
    highly_variable = set(adata.var_names[adata.var["highly_variable"]])
    if sparse.issparse(counts):
        total_counts = np.asarray(counts.sum(axis=0)).ravel()
        cells_by_counts = np.asarray((counts > 0).sum(axis=0)).ravel()
    else:
        array = np.asarray(counts)
        total_counts = array.sum(axis=0)
        cells_by_counts = (array > 0).sum(axis=0)
    return pd.DataFrame(
        {
            "gene": gene_names.astype(str),
            "total_counts": np.asarray(total_counts, dtype=np.int64),
            "cells_by_counts": np.asarray(cells_by_counts, dtype=np.int64),
            "mitochondrial": initial_var["mt"].astype(bool).to_numpy(),
            "retained": [gene in retained for gene in gene_names],
            "highly_variable": [gene in highly_variable for gene in gene_names],
        }
    )


def _cluster_summary(adata: anndata.AnnData, markers: pd.DataFrame) -> pd.DataFrame:
    counts = adata.obs["leiden"].astype(str).value_counts().sort_index(key=lambda values: values.astype(int))
    rows = []
    for cluster, count in counts.items():
        genes = markers.loc[markers["cluster"] == cluster, "gene"].head(5).tolist()
        rows.append(
            {
                "cluster": cluster,
                "cells": int(count),
                "percent": round(float(count / adata.n_obs * 100.0), 2),
                "top_markers": ", ".join(genes),
            }
        )
    return pd.DataFrame(rows)


def _marker_dotplot(adata: anndata.AnnData, markers: pd.DataFrame) -> dict[str, Any]:
    if markers.empty:
        return {"genes": [], "clusters": [], "values": []}
    genes = []
    for gene in markers.groupby("cluster", sort=False).head(3)["gene"]:
        if gene not in genes:
            genes.append(str(gene))
        if len(genes) >= 24:
            break
    clusters = sorted(adata.obs["leiden"].astype(str).unique(), key=lambda value: int(value))
    raw = adata.raw
    assert raw is not None
    values = []
    for cluster in clusters:
        mask = adata.obs["leiden"].astype(str).to_numpy() == cluster
        for gene in genes:
            gene_index = raw.var_names.get_loc(gene)
            expression = raw.X[:, gene_index]
            vector = expression.toarray().ravel() if sparse.issparse(expression) else np.asarray(expression).ravel()
            cluster_values = vector[mask]
            values.append(
                {
                    "cluster": cluster,
                    "gene": gene,
                    "mean": round(float(cluster_values.mean()), 4),
                    "fraction": round(float((cluster_values > 0).mean()), 4),
                }
            )
    return {"genes": genes, "clusters": clusters, "values": values, "scale": "mean log1p CP10k"}


def _sample_embedding(frame: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    if len(frame) <= limit:
        return _records(frame)
    selected = []
    grouped = list(frame.groupby("cluster", sort=True))
    per_group = max(1, limit // len(grouped))
    for _, group in grouped:
        indexes = np.linspace(0, len(group) - 1, min(per_group, len(group)), dtype=int)
        selected.append(group.iloc[indexes])
    sampled = pd.concat(selected).head(limit)
    return _records(sampled)


def _sample_qc(frame: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    if len(frame) <= limit:
        return _records(frame)
    indexes = np.linspace(0, len(frame) - 1, limit, dtype=int)
    return _records(frame.iloc[indexes])


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for row in frame.to_dict(orient="records"):
        records.append({key: _json_value(value) for key, value in row.items()})
    return records


def _json_value(value: Any) -> Any:
    if value is None or (isinstance(value, float) and not math.isfinite(value)) or pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _summary_markdown(summary: dict[str, Any]) -> str:
    doublet = summary["doublet"]
    doublet_line = (
        f"- Scrublet: {doublet['predicted']:,} predicted, {doublet['excluded']:,} excluded\n"
        if doublet["enabled"]
        else "- Scrublet: not run\n"
    )
    return (
        "# Single-cell exploratory analysis\n\n"
        f"- Method: Scanpy {summary['method_version']}\n"
        f"- Source: {summary['input_format']} · counts from {summary['count_layer']}\n"
        f"- Input: {summary['cells_input']:,} cells by {summary['genes_input']:,} genes\n"
        f"- Retained: {summary['cells_retained']:,} cells and {summary['genes_retained']:,} genes\n"
        f"- Highly variable genes: {summary['highly_variable_genes']:,}\n"
        f"- Leiden clusters: {summary['clusters']}\n"
        f"{doublet_line}"
        f"- Random seed: {summary['random_seed']}\n\n"
        "Clusters, UMAP coordinates, and cell-level marker rankings are exploratory. "
        "Review QC per biological sample and use sample-aware inference before making biological claims.\n"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
