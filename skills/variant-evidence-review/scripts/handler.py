"""ClinVar preflight and approved multi-source variant review handlers."""

from __future__ import annotations

from typing import Any

from molemo.variant_evidence import preflight_variant_evidence, review_variant_evidence


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_variant_evidence(str(arguments.get("variant") or ""))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [{"source": result["source"], "url": result["source_url"]}],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-variant-evidence-preflight",
                "type": "variant-evidence-preflight",
                "title": "Variant evidence preflight",
                "data": result,
            }
        ],
    }


def review(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = review_variant_evidence(str(arguments.get("variant") or ""))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": source["name"],
                "url": source["url"],
                "retrieved_at": result["retrieved_at"],
                "manifest": result["outputs"]["manifest"],
            }
            for source in result["sources"]
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "variant-evidence-review",
                "title": f"Variant evidence · {result['variant']['accession']}",
                "data": result,
            }
        ],
    }
