"""Reactome and STRING functional-analysis handlers."""

from __future__ import annotations

from typing import Any

from functional_analysis import preflight_functional_analysis, run_functional_analysis


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "genes": str(arguments.get("genes") or ""),
        "required_score": arguments.get("required_score", 400),
        "fdr_threshold": arguments.get("fdr_threshold", 0.05),
        "max_terms": arguments.get("max_terms", 20),
        "include_disease_pathways": arguments.get("include_disease_pathways", False),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_functional_analysis(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": result["sources"],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-functional-analysis-preflight",
                "type": "functional-analysis-preflight",
                "title": "Gene-set analysis preflight",
                "data": result,
            }
        ],
    }


def run(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_functional_analysis(**_arguments(arguments))
    evidence = [
        {
            "source": source["name"],
            "url": source["url"],
            "retrieved_at": result["retrieved_at"],
            "manifest": result["outputs"]["manifest"],
        }
        for source in result["sources"]
    ]
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": evidence,
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "functional-analysis",
                "title": "Human gene-set functional analysis",
                "data": result,
            }
        ],
    }
