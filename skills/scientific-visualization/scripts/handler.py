"""Declarative scientific visualization artifacts rendered by the frontend."""

from __future__ import annotations

import math
import re
from typing import Any

from pipeline import HYDROPATHY, VALID_AA


def property_chart(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    title = str(arguments.get("title") or "Property chart")
    properties = dict(arguments.get("properties") or {})
    if not properties:
        raise ValueError("properties must contain at least one numeric value")
    labels, values = [], []
    for label, value in list(properties.items())[:16]:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"Non-finite value for {label}")
        labels.append(str(label))
        values.append(number)
    artifact = {
        "id": "latest-property-chart",
        "type": "bar-chart",
        "title": title,
        "data": {"labels": labels, "values": values, "unit": str(arguments.get("unit") or "")},
    }
    return {"summary": f"Created a bar chart with {len(labels)} properties.", "artifacts": [artifact]}


def sequence_track(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    raw = str(arguments.get("sequence") or "")
    lines = [line.strip() for line in raw.splitlines() if not line.strip().startswith(">")]
    sequence = re.sub(r"[^A-Za-z]", "", "".join(lines)).upper()
    invalid = sorted(set(sequence) - VALID_AA)
    if not sequence or invalid:
        raise ValueError("A valid standard amino-acid sequence is required")
    values = [HYDROPATHY[aa] for aa in sequence]
    artifact = {
        "id": "latest-sequence-track",
        "type": "sequence-track",
        "title": str(arguments.get("title") or "Protein hydropathy track"),
        "data": {"sequence": sequence, "values": values, "scale": [-4.5, 4.5]},
    }
    return {
        "summary": f"Created a hydropathy track for {len(sequence)} residues.",
        "artifacts": [artifact],
    }
