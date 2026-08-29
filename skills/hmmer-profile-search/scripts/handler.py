"""HMMER profile-search preflight and approved execution handlers."""

from __future__ import annotations

from typing import Any

from hmmer_search import preflight_hmmer_profile_search, run_hmmer_profile_search


def _arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "hmm_path": str(arguments.get("hmm_path") or ""),
        "database_path": str(arguments.get("database_path") or ""),
        "evalue": arguments.get("evalue", 1e-5),
        "domain_evalue": arguments.get("domain_evalue", 1e-5),
        "max_hits": arguments.get("max_hits", 25),
        "threads": arguments.get("threads", 1),
    }


def preflight(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = preflight_hmmer_profile_search(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {"source": "Local HMMER3 profile", "path": result["hmm_path"]},
            {"source": "Local protein FASTA", "path": result["database_path"]},
        ],
        "caveats": result["warnings"],
        "artifacts": [
            {
                "id": "latest-hmmer-profile-preflight",
                "type": "hmmer-profile-preflight",
                "title": "HMMER profile preflight",
                "data": result,
            }
        ],
    }


def search(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = run_hmmer_profile_search(**_arguments(arguments))
    return {
        "summary": result["summary"],
        "data": result,
        "evidence": [
            {
                "source": result["engine"],
                "version": result["version"],
                "profile_path": result["inputs"]["hmm_path"],
                "database_path": result["inputs"]["database_path"],
                "retrieved_at": result["retrieved_at"],
                "manifest": result["outputs"]["manifest"],
            }
        ],
        "caveats": result["caveats"],
        "artifacts": [
            {
                "id": result["analysis_id"],
                "type": "hmmer-profile-search",
                "title": "HMMER profile search",
                "data": result,
            }
        ],
    }
