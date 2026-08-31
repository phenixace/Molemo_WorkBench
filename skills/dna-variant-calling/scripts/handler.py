"""Researcher-approved paired-end DNA variant-calling skill handlers."""

from __future__ import annotations

from typing import Any

from molemo.dna_variant_calling import preflight_dna_variant_calling, run_dna_variant_calling


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_dna_variant_calling(**arguments)
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "Molemo local NGS toolchain",
                "method": result["method"],
                "tools": result["toolchain"]["tools"],
            }
        ],
        "artifacts": [
            {
                "id": "dna-variant-calling-preflight",
                "type": "dna-variant-calling-preflight",
                "title": "Paired-end DNA variant calling preflight",
                "data": result,
            }
        ],
    }


def run(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_dna_variant_calling(**arguments)
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": "Molemo local NGS toolchain",
                "method": result["method"],
                "input_sha256": result["input_sha256"],
                "toolchain": result["toolchain"],
            }
        ],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "dna-variant-calling",
                "title": f"DNA variant calling · {result['inputs']['sample_id']}",
                "data": result,
            }
        ],
    }
