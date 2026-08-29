"""Experimental coordinate retrieval and parsing handlers."""

from __future__ import annotations

from typing import Any

from bio_clients import fetch_rcsb_pdb_text, lookup_rcsb_entry, normalize_pdb_id
from structure_io import build_structure_sample, parse_structure_text
from workspace_utils import resolve_workspace_path


MAX_LOCAL_STRUCTURE_BYTES = 24 * 1024 * 1024


def fetch_structure(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    pdb_id = normalize_pdb_id(str(arguments.get("pdb_id") or ""))
    metadata = lookup_rcsb_entry(pdb_id)
    structure = parse_structure_text(fetch_rcsb_pdb_text(pdb_id), pdb_id, "pdb")
    sample = build_structure_sample(structure, str(metadata.get("title") or pdb_id), metadata)
    return _result(sample, metadata, "RCSB PDB Data API and coordinate archive")


def parse_workspace_structure(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    relative = str(arguments.get("path") or "")
    target = resolve_workspace_path(relative)
    if not target.is_file():
        raise ValueError(f"Workspace file not found: {relative}")
    if target.suffix.lower() not in {".pdb", ".cif", ".mmcif"}:
        raise ValueError("Structure parser accepts .pdb, .cif, or .mmcif files.")
    if target.stat().st_size > MAX_LOCAL_STRUCTURE_BYTES:
        raise ValueError("Structure file exceeds the 24 MB parser limit.")
    structure = parse_structure_text(
        target.read_text(encoding="utf-8", errors="replace"),
        target.stem,
        target.suffix.lstrip("."),
    )
    metadata = {"source": "local workspace", "path": relative}
    sample = build_structure_sample(structure, target.stem, metadata)
    return _result(sample, metadata, "local PDB/mmCIF coordinate parser")


def _result(sample: dict[str, Any], metadata: dict[str, Any], evidence_source: str) -> dict[str, Any]:
    structure = sample["structure"]
    summary = (
        f"Parsed {structure['source_id']} with {structure['atom_count']} atoms, "
        f"{len(structure['chains'])} protein chains, and {len(structure['ligands'])} ligand types."
    )
    evidence = {"source": evidence_source}
    if metadata.get("source_url"):
        evidence["url"] = metadata["source_url"]
    return {
        "summary": summary,
        "data": {"structure": structure, "metadata": metadata},
        "evidence": [evidence],
        "artifacts": [
            {
                "id": f"protein-structure-{structure['source_id'].lower()}",
                "type": "protein-structure",
                "title": f"{structure['source_id'].upper()} atom-level structure",
                "data": sample,
            }
        ],
    }
