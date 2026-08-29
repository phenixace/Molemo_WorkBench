"""Protein conservation preflight and approved MAFFT handlers."""

from __future__ import annotations

from typing import Any

from multiple_alignment import preflight_multiple_alignment, run_multiple_alignment


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "fasta_path": str(arguments.get("fasta_path") or ""),
        "reference_id": str(arguments.get("reference_id") or ""),
        "site": str(arguments.get("site") or ""),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_multiple_alignment(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {"source": "Local protein FASTA", "path": result["inputs"]["fasta_path"]},
            {"source": "MAFFT", "version": result["version"]},
        ],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-protein-conservation-preflight",
                "type": "protein-conservation-preflight",
                "title": f"Alignment preflight · {result['reference']['site']}",
                "data": result,
            }
        ],
    }


def run(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_multiple_alignment(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "MAFFT",
                "version": result["version"],
                "input_path": result["inputs"]["fasta_path"],
                "created_at": result["created_at"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "protein-conservation-review",
                "title": f"{result['site']['reference_id']} · {result['site']['label']} conservation",
                "data": result,
            }
        ],
    }
