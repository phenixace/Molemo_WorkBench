"""Inspect a single-cell input inside the project Scanpy runtime."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from single_cell_io import categorical_metadata, count_metrics, mitochondrial_mask, read_single_cell


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: inspect_single_cell.py CONFIG_JSON OUTPUT_JSON")
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output_path = Path(sys.argv[2])
    adata, source = read_single_cell(config)
    metrics = count_metrics(adata.X)
    mito_mask = mitochondrial_mask(adata)
    if mito_mask.any():
        mito_counts = np.asarray(adata.X[:, mito_mask].sum(axis=1)).ravel()
    else:
        mito_counts = np.zeros(adata.n_obs, dtype=float)
    library_sizes = metrics["library_sizes"].astype(float)
    mito_percent = np.divide(
        mito_counts * 100.0,
        library_sizes,
        out=np.zeros_like(library_sizes, dtype=float),
        where=library_sizes > 0,
    )
    parameters = config["parameters"]
    cell_mask = (
        (metrics["detected_genes"] >= int(parameters["min_genes"]))
        & (mito_percent <= float(parameters["max_mito_percent"]))
    )
    if cell_mask.any():
        retained = adata.X[cell_mask]
        if hasattr(retained, "getnnz"):
            detected_after_cells = np.asarray(retained.getnnz(axis=0)).ravel()
        else:
            detected_after_cells = np.asarray((retained > 0).sum(axis=0)).ravel()
    else:
        detected_after_cells = np.zeros(adata.n_vars, dtype=int)
    genes_after_filter = int((detected_after_cells >= int(parameters["min_cells"])).sum())
    entries = int(adata.n_obs * adata.n_vars)
    warnings = []
    if not mito_mask.any():
        warnings.append("No MT- prefixed gene symbols were found; mitochondrial-percentage filtering is inactive.")
    if int(cell_mask.sum()) < adata.n_obs * 0.5:
        warnings.append("Configured cell QC excludes at least half of the input cells; inspect the thresholds.")
    if genes_after_filter < adata.n_vars * 0.25:
        warnings.append("Configured gene filtering excludes at least three quarters of the input genes.")
    payload = {
        **source,
        "cells": int(adata.n_obs),
        "genes": int(adata.n_vars),
        "entries": entries,
        "nonzero_entries": int(metrics["nonzero"]),
        "sparsity_percent": round((1.0 - metrics["nonzero"] / entries) * 100.0, 2),
        "mitochondrial_genes": int(mito_mask.sum()),
        "cells_after_filter": int(cell_mask.sum()),
        "genes_after_filter": genes_after_filter,
        "qc_summary": {
            "library_size": _distribution(library_sizes),
            "detected_genes": _distribution(metrics["detected_genes"]),
            "mitochondrial_percent": _distribution(mito_percent),
        },
        "metadata": {
            "provided": bool(config.get("metadata")) or len(adata.obs.columns) > 0,
            "columns": [str(column) for column in adata.obs.columns],
            "categorical_columns": categorical_metadata(adata.obs),
        },
        "warnings": warnings,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def _distribution(values: Any) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "min": round(float(np.min(array)), 3),
        "median": round(float(np.median(array)), 3),
        "max": round(float(np.max(array)), 3),
    }


if __name__ == "__main__":
    main()
