"""NCBI GEO Series preview and approved collection handlers."""

from __future__ import annotations

from typing import Any

from geo_dataset_discovery import collect_geo_datasets, search_geo_dataset_preview


def _arguments(arguments: dict[str, Any], *, default_max_results: int) -> dict[str, Any]:
    return {
        "query": str(arguments.get("query") or ""),
        "organism": (
            "Homo sapiens"
            if "organism" not in arguments
            else str(arguments.get("organism") or "")
        ),
        "assay_scope": str(arguments.get("assay_scope") or "all"),
        "min_samples": arguments.get("min_samples", 4),
        "max_results": arguments.get("max_results", default_max_results),
    }


def preview(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    values = _arguments(arguments, default_max_results=8)
    values["max_results"] = min(int(values["max_results"]), 8)
    return _result(search_geo_dataset_preview(**values), "GEO dataset preview", "geo-dataset-preview")


def collect(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    values = _arguments(arguments, default_max_results=12)
    return _result(collect_geo_datasets(**values), "GEO dataset landscape", "geo-dataset-landscape")


def _result(result: dict[str, Any], title: str, artifact_type: str) -> dict[str, Any]:
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["source"],
                "url": result["search_url"],
                "query": result["exact_query"],
                "retrieved_at": result["retrieved_at"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": artifact_type,
                "title": title,
                "data": result,
            }
        ],
    }
