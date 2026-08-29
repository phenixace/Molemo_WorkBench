"""Single-cell preflight and approved Scanpy analysis handlers."""

from __future__ import annotations

from typing import Any

from single_cell import preflight_single_cell, run_single_cell_analysis


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "count_matrix_path": str(arguments.get("count_matrix_path") or ""),
        "metadata_path": str(arguments.get("metadata_path") or ""),
        "cell_id_column": str(arguments.get("cell_id_column") or "cell_id"),
        "min_genes": arguments.get("min_genes", 20),
        "min_cells": arguments.get("min_cells", 3),
        "max_mito_percent": arguments.get("max_mito_percent", 20),
        "n_top_genes": arguments.get("n_top_genes", 2000),
        "n_neighbors": arguments.get("n_neighbors", 15),
        "leiden_resolution": arguments.get("leiden_resolution", 1),
        "marker_genes": arguments.get("marker_genes", 10),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_single_cell(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "Molemo single-cell preflight",
                "count_matrix": result["count_matrix_path"],
                "metadata": result["metadata_path"],
                "input_mode": result["input_mode"],
                "scanpy_version": result["toolchain"]["scanpy_version"],
            }
        ],
        "artifacts": [
            {
                "id": "latest-single-cell-preflight",
                "type": "single-cell-preflight",
                "title": "Single-cell preflight",
                "data": result,
            }
        ],
    }


def run_analysis(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_single_cell_analysis(**_arguments(arguments))
    return {
        "summary": (
            f"Scanpy retained {result['cells_retained']:,} cells and {result['genes_retained']:,} genes, "
            f"then produced {result['clusters']} exploratory Leiden clusters."
        ),
        "data": result,
        "evidence": [
            {
                "source": "Scanpy",
                "version": result["method_version"],
                "random_seed": result["random_seed"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": f"single-cell-analysis-{result['analysis_id']}",
                "type": "single-cell-analysis",
                "title": "Single-cell exploratory analysis",
                "data": result,
            }
        ],
    }
