"""ClinicalTrials.gov preview and approved landscape handlers."""

from __future__ import annotations

from typing import Any

from clinical_trials import collect_clinical_trial_landscape, search_clinical_trials_preview


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "condition": str(arguments.get("condition") or ""),
        "intervention": str(arguments.get("intervention") or ""),
        "status_scope": str(arguments.get("status_scope") or "all"),
        "study_scope": str(arguments.get("study_scope") or "interventional"),
        "max_results": arguments.get("max_results", 8),
    }


def preview(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    values = _arguments(arguments)
    values["max_results"] = min(int(values["max_results"]), 10)
    return _result(search_clinical_trials_preview(**values), "Clinical trial preview")


def collect(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    return _result(collect_clinical_trial_landscape(**_arguments(arguments)), "Clinical trial landscape")


def _result(result: dict[str, Any], title: str) -> dict[str, Any]:
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["source"],
                "url": result["search_url"],
                "query_parameters": result["query_parameters"],
                "retrieved_at": result["retrieved_at"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "clinical-trial-landscape",
                "title": title,
                "data": result,
            }
        ],
    }
