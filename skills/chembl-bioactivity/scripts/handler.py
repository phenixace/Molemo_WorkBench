"""ChEMBL bioactivity preflight and approved collection handlers."""

from __future__ import annotations

from typing import Any

from molemo.chembl_bioactivity import collect_chembl_bioactivity, preflight_chembl_bioactivity


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "accession": str(arguments.get("accession") or ""),
        "assay_scope": str(arguments.get("assay_scope") or "binding_functional"),
        "min_pchembl": arguments.get("min_pchembl", 5.0),
        "max_activities": arguments.get("max_activities", 50),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_chembl_bioactivity(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": f"ChEMBL {result['database']['version']}",
                "url": result["source_url"],
                "retrieved_at": result["retrieved_at"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": "latest-chembl-bioactivity-preflight",
                "type": "chembl-bioactivity-preflight",
                "title": f"ChEMBL preflight · {result['target']['pref_name']}",
                "data": result,
            }
        ],
    }


def collect(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = collect_chembl_bioactivity(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": f"ChEMBL {result['database']['version']}",
                "url": result["source_url"],
                "retrieved_at": result["retrieved_at"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "chembl-bioactivity-review",
                "title": f"ChEMBL bioactivity · {result['target']['pref_name']}",
                "data": result,
            }
        ],
    }
