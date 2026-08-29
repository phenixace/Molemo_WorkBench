"""Sequence-derived protein analysis skill."""

from __future__ import annotations

from typing import Any

from pipeline import parse_protein


def analyze_protein(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    sample = parse_protein(str(arguments.get("sequence") or ""))
    properties = sample["properties"]
    return {
        "summary": (
            f"Analyzed {properties['Length']}; pI {properties['pI']}, "
            f"GRAVY {properties['GRAVY']}, aggregation flag {properties['Risk']}."
        ),
        "data": sample,
        "evidence": [
            {"source": "Molemo local sequence pipeline", "method": "sequence-derived heuristics"}
        ],
        "artifacts": [
            {
                "id": "active-protein-sequence",
                "type": "protein-sequence",
                "title": f"Protein sequence ({properties['Length']})",
                "data": sample,
            }
        ],
    }
