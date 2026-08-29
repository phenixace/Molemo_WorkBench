"""GEO Series Matrix preflight and approved import handlers."""

from __future__ import annotations

from typing import Any

from geo_series_matrix import import_geo_series_matrix, preflight_geo_series_matrix


def _arguments(arguments: dict[str, Any]) -> dict[str, str]:
    return {
        "accession": str(arguments.get("accession") or ""),
        "matrix_file": str(arguments.get("matrix_file") or ""),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_geo_series_matrix(**_arguments(arguments))
    return _result(result, "GEO Series Matrix preflight", "geo-series-matrix-preflight")


def run_import(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = import_geo_series_matrix(**_arguments(arguments))
    return _result(result, f"{result['accession']} · Series Matrix", "geo-series-matrix-import")


def _result(result: dict[str, Any], title: str, artifact_type: str) -> dict[str, Any]:
    evidence = {
        "source": result["source"],
        "url": result.get("source_url") or result.get("download_url"),
        "accession": result["accession"],
        "matrix_file": result.get("matrix_file", ""),
    }
    if result.get("retrieved_at"):
        evidence["retrieved_at"] = result["retrieved_at"]
    if result.get("source_sha256"):
        evidence["source_sha256"] = result["source_sha256"]
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [evidence],
        "caveats": result.get("caveats") or result.get("warnings") or [],
        "artifacts": [
            {
                "id": result.get("analysis_id") or f"geo-series-matrix-preflight-{result['accession']}",
                "type": artifact_type,
                "title": title,
                "data": result,
            }
        ],
    }
