"""Protein variant structure preflight and approved review handlers."""

from __future__ import annotations

from typing import Any

from molemo.variant_structure import collect_variant_structure, preflight_variant_structure


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "pdb_id": str(arguments.get("pdb_id") or ""),
        "chain": str(arguments.get("chain") or ""),
        "variant": str(arguments.get("variant") or ""),
        "contact_cutoff": arguments.get("contact_cutoff", 4.5),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_variant_structure(**_arguments(arguments))
    return _result(result, "variant-structure-preflight")


def collect(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = collect_variant_structure(**_arguments(arguments))
    return _result(result, "variant-structure-review")


def _result(result: dict[str, Any], artifact_type: str) -> dict[str, Any]:
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "RCSB Protein Data Bank",
                "url": result["source_url"],
                "retrieved_at": result["retrieved_at"],
                **({"manifest": result["outputs"]["manifest"]} if result["outputs"] else {}),
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": artifact_type,
                "title": f"{result['entry']['pdb_id']} · {result['site']['variant']} structural context",
                "data": result,
            }
        ],
    }
