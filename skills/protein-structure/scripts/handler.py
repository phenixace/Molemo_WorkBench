"""Experimental and predicted protein coordinate handlers."""

from __future__ import annotations

from typing import Any

from molemo.bio_clients import (
    ExternalDataError,
    fetch_alphafold_pae_payload,
    fetch_alphafold_pdb_text,
    fetch_rcsb_pdb_text,
    lookup_alphafold_prediction,
    lookup_rcsb_entry,
    normalize_pdb_id,
)
from molemo.structure_io import (
    StructureError,
    build_structure_sample,
    parse_alphafold_pae,
    parse_structure_text,
    summarize_plddt,
)
from molemo.workspace_utils import resolve_workspace_path


MAX_LOCAL_STRUCTURE_BYTES = 24 * 1024 * 1024


def fetch_structure(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    pdb_id = normalize_pdb_id(str(arguments.get("pdb_id") or ""))
    metadata = lookup_rcsb_entry(pdb_id)
    metadata["coordinate_type"] = "experimental"
    structure = parse_structure_text(fetch_rcsb_pdb_text(pdb_id), pdb_id, "pdb")
    sample = build_structure_sample(structure, str(metadata.get("title") or pdb_id), metadata)
    return _result(sample, metadata, "RCSB PDB Data API and coordinate archive")


def fetch_alphafold_structure(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    metadata = lookup_alphafold_prediction(str(arguments.get("accession") or ""))
    structure = parse_structure_text(
        fetch_alphafold_pdb_text(str(metadata["model_url"])),
        str(metadata["entry_id"]),
        "pdb",
    )
    structure["confidence"] = summarize_plddt(structure, metadata.get("mean_plddt"))
    pae_warning = ""
    pae_url = str(metadata.get("pae_url") or "")
    if pae_url:
        try:
            structure["pae"] = parse_alphafold_pae(
                fetch_alphafold_pae_payload(pae_url),
                expected_residues=len(structure.get("sequence") or ""),
            )
        except (ExternalDataError, StructureError) as exc:
            pae_warning = f"PAE matrix could not be loaded: {exc}"
    else:
        pae_warning = "AlphaFold DB did not provide a PAE matrix URL for this model."
    accession = str(metadata["accession"])
    gene = str(metadata.get("gene") or "").strip()
    title = f"{gene} ({accession}) predicted structure" if gene else f"{accession} predicted structure"
    sample = build_structure_sample(structure, title, metadata)
    confidence = structure["confidence"]
    summary = (
        f"Loaded AlphaFold DB model {structure['source_id']} for {accession}: "
        f"{confidence['residue_count']} residues with mean pLDDT {confidence['mean_plddt']:.2f}."
    )
    if structure.get("pae"):
        pae = structure["pae"]
        summary += f" PAE covers {pae['residue_count']} residues up to {pae['max_error']:.2f} Å."
    caveats = [
        "pLDDT is local confidence; use PAE to review relative domain placement.",
        "A predicted structure does not by itself establish binding, dynamics, or mechanism.",
    ]
    if pae_warning:
        caveats.append(pae_warning)
    return {
        "summary": summary,
        "data": {"structure": structure, "metadata": metadata, "confidence": confidence},
        "evidence": [
            {
                "source": "AlphaFold Protein Structure Database",
                "url": metadata["source_url"],
            }
        ],
        "caveats": caveats,
        "artifacts": [
            {
                "id": f"protein-structure-{structure['source_id'].lower()}",
                "type": "protein-structure",
                "title": f"{structure['source_id'].upper()} predicted structure",
                "data": sample,
            }
        ],
    }


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
    metadata = {"source": "local workspace", "path": relative, "coordinate_type": "local"}
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
