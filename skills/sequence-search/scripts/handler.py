"""Researcher-approved local BLAST+ sequence-search skill."""

from __future__ import annotations

from typing import Any

from sequence_search import run_local_blast


def search_sequence(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_local_blast(
        query=str(arguments.get("query") or ""),
        database_path=str(arguments.get("database_path") or ""),
        program=str(arguments.get("program") or "blastp"),
        evalue=arguments.get("evalue", 1e-5),
        max_hits=arguments.get("max_hits", 10),
        threads=arguments.get("threads", 1),
    )
    hit_count = result["hit_count"]
    top = result["hits"][0] if hit_count else None
    summary = (
        f"{result['program'].upper()} found {hit_count} hit(s) in {result['database_path']}."
        if top is None
        else (
            f"{result['program'].upper()} found {hit_count} hit(s); top hit {top['title']} "
            f"has {top['identity_percent']}% identity, {top['query_coverage_percent']}% query coverage, "
            f"and E-value {top['evalue']:.3g}."
        )
    )
    return {
        "summary": summary,
        "data": result,
        "evidence": [
            {
                "source": "NCBI BLAST+",
                "version": result["version"],
                "program": result["program"],
                "task": result["task"],
                "database_path": result["database_path"],
            }
        ],
        "caveat": "Sequence similarity is evidence for relatedness, not proof of shared function or biological activity.",
        "artifacts": [
            {
                "id": "latest-sequence-search",
                "type": "sequence-search",
                "title": f"Local {result['program'].upper()} search",
                "data": result,
            }
        ],
    }
