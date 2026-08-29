"""Open Targets preflight and approved evidence-review handlers."""

from __future__ import annotations

from typing import Any

from target_evidence import resolve_target_review_inputs, review_target_evidence


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "disease": str(arguments.get("disease") or ""),
        "candidates": str(arguments.get("candidates") or ""),
        "include_indirect": bool(arguments.get("include_indirect", False)),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = resolve_target_review_inputs(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [{"source": result["source"], "url": result["source_url"]}],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-target-evidence-preflight",
                "type": "target-evidence-preflight",
                "title": "Target evidence preflight",
                "data": result,
            }
        ],
    }


def compare(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = review_target_evidence(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["source"],
                "url": result["source_url"],
                "disease": result["disease"]["id"],
                "retrieved_at": result["retrieved_at"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "target-evidence-review",
                "title": f"Target evidence · {result['disease']['name']}",
                "data": result,
            }
        ],
    }
