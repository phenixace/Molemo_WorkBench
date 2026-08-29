"""ClinicalTrials.gov landscape and exact posted-results handlers."""

from __future__ import annotations

from typing import Any

from molemo.clinical_trial_results import (
    preflight_clinical_trial_results,
    review_clinical_trial_results,
)
from molemo.clinical_trials import collect_clinical_trial_landscape, search_clinical_trials_preview


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


def results_preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_clinical_trial_results(str(arguments.get("nct_id") or ""))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["source"],
                "url": result["source_url"],
                "nct_id": result["nct_id"],
            }
        ],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-clinical-results-preflight",
                "type": "clinical-trial-results-preflight",
                "title": f"Posted results preflight · {result['nct_id']}",
                "data": result,
            }
        ],
    }


def results_review(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = review_clinical_trial_results(str(arguments.get("nct_id") or ""))
    evidence = [
        {
            "source": result["source"],
            "url": result["source_url"],
            "nct_id": result["nct_id"],
            "retrieved_at": result["retrieved_at"],
        }
    ]
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": evidence,
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "clinical-trial-results",
                "title": f"Posted results · {result['nct_id']}",
                "data": result,
            }
        ],
    }


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
