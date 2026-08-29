"""Europe PMC preview and approved evidence-map handlers."""

from __future__ import annotations

from typing import Any

from molemo.literature_review import collect_literature_review, search_literature_preview


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": str(arguments.get("query") or ""),
        "start_year": arguments.get("start_year"),
        "end_year": arguments.get("end_year"),
        "max_results": arguments.get("max_results", 8),
        "include_preprints": arguments.get("include_preprints", False),
        "require_abstract": arguments.get("require_abstract", True),
    }


def preview(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    values = _arguments(arguments)
    values["max_results"] = min(int(values["max_results"]), 10)
    result = search_literature_preview(**values)
    return _result(result, "Literature preview")


def collect(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = collect_literature_review(**_arguments(arguments))
    return _result(result, "Literature evidence map")


def _result(result: dict[str, Any], title: str) -> dict[str, Any]:
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
                "type": "literature-evidence-map",
                "title": title,
                "data": result,
            }
        ],
    }
