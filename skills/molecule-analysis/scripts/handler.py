"""RDKit-backed molecule analysis skill."""

from __future__ import annotations

from typing import Any

from pipeline import parse_molecule


def analyze_molecule(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    sample = parse_molecule(str(arguments.get("smiles") or ""))
    properties = sample["properties"]
    return {
        "summary": (
            f"Parsed {sample['formula']} with {len(sample['atoms'])} atoms and "
            f"{len(sample['bonds'])} bonds; MW {properties['MW']}, logP {properties['logP']}."
        ),
        "data": sample,
        "evidence": [{"source": "RDKit", "method": "SMILES parsing and descriptors"}],
        "artifacts": [
            {
                "id": "active-molecule",
                "type": "molecule",
                "title": f"{sample['formula']} molecular structure",
                "data": sample,
            }
        ],
    }
