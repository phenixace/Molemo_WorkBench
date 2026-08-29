"""Multi-sample VCF preflight and approved review handlers."""

from __future__ import annotations

from typing import Any

from vcf_cohort import preflight_vcf_cohort, review_vcf_cohort


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "vcf_path": str(arguments.get("vcf_path") or ""),
        "metadata_path": str(arguments.get("metadata_path") or ""),
        "sample_column": str(arguments.get("sample_column") or "sample"),
        "subject_column": str(arguments.get("subject_column") or "subject"),
        "timepoint_column": str(arguments.get("timepoint_column") or "timepoint"),
        "time_order_column": str(arguments.get("time_order_column") or "time_order"),
        "min_vaf": arguments.get("min_vaf", 0.01),
        "min_depth": arguments.get("min_depth", 10),
        "include_filtered": arguments.get("include_filtered", False),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_vcf_cohort(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [{"source": "Local workspace VCF", "path": result["vcf_path"]}],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-vcf-cohort-preflight",
                "type": "vcf-cohort-preflight",
                "title": "VCF cohort preflight",
                "data": result,
            }
        ],
    }


def review(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = review_vcf_cohort(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["source"],
                "path": result["inputs"]["vcf_path"],
                "retrieved_at": result["retrieved_at"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "vcf-cohort-review",
                "title": "Multi-sample VCF review",
                "data": result,
            }
        ],
    }
