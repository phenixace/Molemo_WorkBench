"""Bulk RNA-seq preflight and approved differential-expression handlers."""

from __future__ import annotations

from typing import Any

from transcriptomics import preflight_bulk_rnaseq, run_bulk_rnaseq_de


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "count_matrix_path": str(arguments.get("count_matrix_path") or ""),
        "metadata_path": str(arguments.get("metadata_path") or ""),
        "sample_column": str(arguments.get("sample_column") or "sample"),
        "condition_column": str(arguments.get("condition_column") or "condition"),
        "test_level": str(arguments.get("test_level") or ""),
        "reference_level": str(arguments.get("reference_level") or ""),
        "batch_column": str(arguments.get("batch_column") or ""),
        "min_total_count": arguments.get("min_total_count", 10),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_bulk_rnaseq(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "Molemo bulk RNA-seq preflight",
                "count_matrix": result["count_matrix_path"],
                "metadata": result["metadata_path"],
                "design": result["design_formula"],
            }
        ],
        "artifacts": [
            {
                "id": "latest-rnaseq-preflight",
                "type": "rnaseq-preflight",
                "title": "Bulk RNA-seq preflight",
                "data": result,
            }
        ],
    }


def run_differential_expression(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_bulk_rnaseq_de(
        **_arguments(arguments),
        fdr_threshold=arguments.get("fdr_threshold", 0.05),
        lfc_threshold=arguments.get("lfc_threshold", 1.0),
    )
    contrast = result["contrast"]
    return {
        "summary": (
            f"PyDESeq2 tested {result['genes_tested']} genes for {contrast['test']} vs "
            f"{contrast['reference']}; {result['significant_genes']} passed the configured "
            f"FDR and effect-size thresholds ({result['upregulated']} up, {result['downregulated']} down)."
        ),
        "data": result,
        "evidence": [
            {
                "source": "PyDESeq2",
                "version": result["method_version"],
                "design": result["design_formula"],
                "contrast": result["contrast"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": f"transcriptomics-de-{result['analysis_id']}",
                "type": "transcriptomics-de",
                "title": f"Bulk RNA-seq · {contrast['test']} vs {contrast['reference']}",
                "data": result,
            }
        ],
    }
