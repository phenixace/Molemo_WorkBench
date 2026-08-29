"""Experimental protein variant context with strict residue and contact provenance."""

from __future__ import annotations

import csv
import json
import math
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bio_clients import (
    ExternalDataError,
    fetch_rcsb_pdb_text,
    lookup_rcsb_entry,
    normalize_pdb_id,
)
from structure_io import (
    AA3_TO1,
    StructureError,
    build_structure_from_atoms,
    build_structure_sample,
    parse_structure_atoms,
)
from workspace_utils import WORKSPACE_ROOT


AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
MAX_CONTACTS = 200


class VariantStructureError(ValueError):
    """Raised when a variant cannot be located or interpreted in a structure."""


def normalize_variant_structure_inputs(
    pdb_id: str,
    chain: str,
    variant: str,
    contact_cutoff: Any = 4.5,
) -> dict[str, Any]:
    try:
        normalized_pdb = normalize_pdb_id(pdb_id)
    except ExternalDataError as exc:
        raise VariantStructureError(str(exc)) from exc
    author_chain = str(chain or "").strip()
    if len(author_chain) != 1:
        raise VariantStructureError("Author chain is required and must contain exactly one PDB chain character.")
    normalized_variant = str(variant or "").strip().upper().replace("P.", "")
    if len(normalized_variant) < 3:
        raise VariantStructureError("Variant must use one-letter protein notation such as G12C.")
    reference = normalized_variant[0]
    alternate = normalized_variant[-1]
    position_text = normalized_variant[1:-1]
    if reference not in AMINO_ACIDS or alternate not in AMINO_ACIDS or not position_text.isdigit():
        raise VariantStructureError("Variant must use one-letter protein notation such as G12C.")
    if reference == alternate:
        raise VariantStructureError("Variant reference and alternate amino acids must differ.")
    position = int(position_text)
    if position < 1:
        raise VariantStructureError("Variant residue position must be positive.")
    try:
        cutoff = float(contact_cutoff)
    except (TypeError, ValueError) as exc:
        raise VariantStructureError("Contact cutoff must be numeric.") from exc
    if not math.isfinite(cutoff) or not 3.0 <= cutoff <= 8.0:
        raise VariantStructureError("Contact cutoff must be between 3 and 8 Å.")
    return {
        "pdb_id": normalized_pdb,
        "chain": author_chain,
        "variant": f"{reference}{position}{alternate}",
        "reference_aa": reference,
        "alternate_aa": alternate,
        "author_residue_number": str(position),
        "contact_cutoff_angstrom": round(cutoff, 2),
    }


def preflight_variant_structure(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_variant_structure_inputs(**arguments)
    result = _review(normalized, persist=False)
    result.update({"ready": True, "preview": True})
    result["summary"] = _summary(result, "Located")
    return result


def collect_variant_structure(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_variant_structure_inputs(**arguments)
    result = _review(normalized, persist=True)
    result["summary"] = _summary(result, "Reviewed")
    return result


def analyze_variant_contacts(
    atoms: list[dict[str, Any]],
    *,
    chain: str,
    author_residue_number: str,
    reference_aa: str,
    alternate_aa: str,
    variant: str,
    contact_cutoff_angstrom: float,
) -> dict[str, Any]:
    protein_groups = _group_atoms(atoms, hetero=False)
    hetero_groups = _group_atoms(atoms, hetero=True)
    matches = [
        (key, group)
        for key, group in protein_groups.items()
        if key[0] == chain and key[1] == author_residue_number
    ]
    if not matches:
        available = sorted({key[0] for key in protein_groups})
        raise VariantStructureError(
            f"Author residue {chain}:{author_residue_number} was not found; available chains: "
            f"{', '.join(available) or 'none'}."
        )
    residue_names = {key[2] for key, _group in matches}
    if len(matches) != 1 or len(residue_names) != 1:
        raise VariantStructureError(
            f"Author residue {chain}:{author_residue_number} is ambiguous in the first coordinate model."
        )
    focus_key, focus_atoms = matches[0]
    observed_aa = AA3_TO1.get(focus_key[2])
    if not observed_aa:
        raise VariantStructureError(
            f"Observed residue {focus_key[2]} at {chain}:{author_residue_number} is not a supported amino acid."
        )
    if observed_aa == reference_aa:
        structure_allele = "reference"
    elif observed_aa == alternate_aa:
        structure_allele = "alternate"
    else:
        raise VariantStructureError(
            f"Structure contains {observed_aa} at {chain}:{author_residue_number}; "
            f"variant {variant} expects {reference_aa} or {alternate_aa}."
        )

    contacts = []
    for key, group in protein_groups.items():
        if key == focus_key:
            continue
        closest = _closest_heavy_atom_pair(focus_atoms, group)
        if closest and closest[0] <= contact_cutoff_angstrom:
            row = _contact_row("protein", key, closest)
            row["sequence_relation"] = _sequence_relation(
                focus_key,
                key,
                int(author_residue_number),
            )
            contacts.append(row)
    ligand_instances = []
    for key, group in hetero_groups.items():
        closest = _closest_heavy_atom_pair(focus_atoms, group)
        if not closest:
            continue
        row = _contact_row("hetero", key, closest)
        row["within_cutoff"] = closest[0] <= contact_cutoff_angstrom
        ligand_instances.append(row)
        if row["within_cutoff"]:
            contacts.append(dict(row))
    contacts.sort(key=_contact_sort_key)
    ligand_instances.sort(key=_contact_sort_key)
    truncated = len(contacts) > MAX_CONTACTS
    contacts = contacts[:MAX_CONTACTS]
    protein_contacts = [item for item in contacts if item["kind"] == "protein"]
    hetero_contacts = [item for item in contacts if item["kind"] == "hetero"]
    sequence_adjacent_count = sum(
        item.get("sequence_relation") == "sequence-adjacent" for item in protein_contacts
    )
    return {
        "variant": variant,
        "chain": chain,
        "author_residue_number": author_residue_number,
        "reference_aa": reference_aa,
        "alternate_aa": alternate_aa,
        "observed_residue": focus_key[2],
        "observed_aa": observed_aa,
        "structure_allele": structure_allele,
        "contact_cutoff_angstrom": contact_cutoff_angstrom,
        "focus_atom_count": len(focus_atoms),
        "contact_count": len(contacts),
        "protein_contact_count": len(protein_contacts),
        "sequence_adjacent_count": sequence_adjacent_count,
        "nonlocal_protein_contact_count": len(protein_contacts) - sequence_adjacent_count,
        "hetero_contact_count": len(hetero_contacts),
        "contacts_truncated": truncated,
        "contacts": contacts,
        "protein_contacts": protein_contacts,
        "hetero_contacts": hetero_contacts,
        "ligand_instances": ligand_instances,
    }


def _review(normalized: dict[str, Any], persist: bool) -> dict[str, Any]:
    try:
        metadata = lookup_rcsb_entry(normalized["pdb_id"])
        raw = fetch_rcsb_pdb_text(normalized["pdb_id"])
        atoms, source_format = parse_structure_atoms(raw, "pdb")
    except (ExternalDataError, StructureError) as exc:
        raise VariantStructureError(str(exc)) from exc
    site = analyze_variant_contacts(atoms, **{key: normalized[key] for key in (
        "chain",
        "author_residue_number",
        "reference_aa",
        "alternate_aa",
        "variant",
        "contact_cutoff_angstrom",
    )})
    priority_residues = {
        (site["chain"], site["author_residue_number"], site["observed_residue"], False),
        *{
            (item["chain"], item["resSeq"], item["residue"], item["kind"] == "hetero")
            for item in site["contacts"]
        },
    }
    structure = build_structure_from_atoms(
        atoms,
        normalized["pdb_id"],
        source_format,
        priority_residues=priority_residues,
    )
    structure["focus"] = site
    metadata = {**metadata, "coordinate_type": "experimental"}
    sample = build_structure_sample(structure, str(metadata.get("title") or normalized["pdb_id"]), metadata)
    _annotate_sample(sample, site)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    result = {
        "analysis_id": f"variant-structure-{uuid.uuid4().hex[:12]}",
        "method": "RCSB author-residue heavy-atom contact review",
        "source": "RCSB PDB",
        "source_url": metadata["source_url"],
        "retrieved_at": retrieved_at,
        "inputs": dict(normalized),
        "entry": metadata,
        "structure": {
            "format": structure["format"],
            "atom_count": structure["atom_count"],
            "viewer_atom_count": structure["viewer_atom_count"],
            "chains": structure["chains"],
            "ligand_types": structure["ligands"],
        },
        "site": site,
        "sample": sample,
        "caveats": [
            "Distances are geometric heavy-atom proximity in one deposited coordinate model; they do not establish energetic effects, affinity, causality, pathogenicity, or functional impact.",
            "Sequence-adjacent residues can show peptide-bond distances and are labeled separately from nonlocal structural neighbors.",
            "Author chain and residue numbering are used exactly; construct mutations, missing residues, alternate conformations, occupancy, and crystallization conditions require entry-level review.",
            "HETATM groups can be inhibitors, nucleotides, cofactors, ions, or crystallization components; the workflow does not assign biological role from residue name or distance alone.",
            "A short contact does not by itself prove a covalent bond; inspect deposited chemical connectivity and primary evidence before making that claim.",
        ],
        "outputs": {},
    }
    result["summary"] = _summary(result, "Reviewed")
    if persist:
        _persist_review(result)
    return result


def _group_atoms(
    atoms: list[dict[str, Any]], *, hetero: bool
) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for atom in atoms:
        if bool(atom.get("hetero")) != hetero:
            continue
        key = (str(atom.get("chain") or "_"), str(atom.get("resSeq") or ""), str(atom.get("residue") or ""))
        grouped.setdefault(key, []).append(atom)
    return grouped


def _closest_heavy_atom_pair(
    focus_atoms: list[dict[str, Any]],
    other_atoms: list[dict[str, Any]],
) -> tuple[float, dict[str, Any], dict[str, Any]] | None:
    focus_heavy = [atom for atom in focus_atoms if str(atom.get("e") or "").upper() not in {"H", "D"}]
    other_heavy = [atom for atom in other_atoms if str(atom.get("e") or "").upper() not in {"H", "D"}]
    closest = None
    for focus in focus_heavy:
        for other in other_heavy:
            distance = math.dist(
                (float(focus["x"]), float(focus["y"]), float(focus["z"])),
                (float(other["x"]), float(other["y"]), float(other["z"])),
            )
            if closest is None or distance < closest[0]:
                closest = (distance, focus, other)
    return closest


def _contact_row(
    kind: str,
    key: tuple[str, str, str],
    closest: tuple[float, dict[str, Any], dict[str, Any]],
) -> dict[str, Any]:
    distance, focus, other = closest
    residue_aa = AA3_TO1.get(key[2]) if kind == "protein" else None
    return {
        "kind": kind,
        "chain": key[0],
        "resSeq": key[1],
        "residue": key[2],
        "aa": residue_aa,
        "instance_id": f"{key[2]}:{key[0]}:{key[1]}",
        "min_distance_angstrom": round(distance, 3),
        "focus_atom": str(focus.get("name") or ""),
        "contact_atom": str(other.get("name") or ""),
        "focus_xyz": [round(float(focus[axis]), 3) for axis in ("x", "y", "z")],
        "contact_xyz": [round(float(other[axis]), 3) for axis in ("x", "y", "z")],
        "short_contact_below_2_1_angstrom": distance < 2.1,
    }


def _contact_sort_key(item: dict[str, Any]) -> tuple[float, str, str, str]:
    return (
        float(item["min_distance_angstrom"]),
        str(item["kind"]),
        str(item["chain"]),
        str(item["resSeq"]),
    )


def _sequence_relation(
    focus_key: tuple[str, str, str],
    contact_key: tuple[str, str, str],
    focus_position: int,
) -> str:
    if contact_key[0] != focus_key[0] or not contact_key[1].isdigit():
        return "nonlocal"
    return "sequence-adjacent" if abs(int(contact_key[1]) - focus_position) == 1 else "nonlocal"


def _annotate_sample(sample: dict[str, Any], site: dict[str, Any]) -> None:
    variant = site["variant"]
    observed = f"{site['observed_residue']} {site['chain']}:{site['author_residue_number']}"
    nearby_ligands = [item["instance_id"] for item in site["hetero_contacts"]]
    sample.update(
        {
            "id": f"variant-structure-{sample['pdbId'].lower()}-{site['chain'].lower()}-{variant.lower()}",
            "shortName": f"{sample['pdbId']} {variant}",
            "selection": f"{sample['pdbId']} · {observed} · {site['structure_allele']} allele",
            "notes": (
                f"Variant {variant} is represented by the {site['structure_allele']} residue at author position "
                f"{site['chain']}:{site['author_residue_number']}. The site view shows heavy-atom contacts within "
                f"{site['contact_cutoff_angstrom']:.2f} Å; proximity is not a functional or energetic conclusion."
            ),
            "confidence": "RCSB experimental coordinates · author numbering",
            "prompts": [
                f"总结 {variant} 位点附近的蛋白与配体接触",
                "区分结构观察、机制假设与需要实验验证的结论",
                "提出下一步保守的结构比较方案",
            ],
        }
    )
    sample["properties"].update(
        {
            "Variant": variant,
            "Observed": observed,
            "Allele": site["structure_allele"],
            "Contacts": str(site["contact_count"]),
            "Nearby ligands": str(len(nearby_ligands)),
            "Cutoff": f"{site['contact_cutoff_angstrom']:.2f} Å",
        }
    )
    sample["metadata"].update(
        {
            "variantReview": True,
            "variant": variant,
            "source_url": sample["metadata"].get("source_url"),
        }
    )


def _summary(result: dict[str, Any], verb: str) -> str:
    site = result["site"]
    return (
        f"{verb} {site['variant']} at {result['entry']['pdb_id']} author chain "
        f"{site['chain']}:{site['author_residue_number']} as the {site['structure_allele']} allele, with "
        f"{site['protein_contact_count']} protein and {site['hetero_contact_count']} hetero-group contacts "
        f"within {site['contact_cutoff_angstrom']:.2f} Å."
    )


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="variant-structure-", dir=temp_root))
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "contacts": f"{relative_root}/contacts.tsv",
        "ligands": f"{relative_root}/ligands.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    try:
        contact_fields = [
            "kind", "chain", "resSeq", "residue", "aa", "instance_id",
            "min_distance_angstrom", "focus_atom", "contact_atom",
            "short_contact_below_2_1_angstrom", "sequence_relation",
        ]
        _write_tsv(temporary / "contacts.tsv", result["site"]["contacts"], contact_fields)
        _write_tsv(
            temporary / "ligands.tsv",
            result["site"]["ligand_instances"],
            [*contact_fields, "within_cutoff"],
        )
        report = {key: value for key, value in result.items() if key != "sample"}
        (temporary / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "retrieved_at": result["retrieved_at"],
            "entry": result["entry"],
            "inputs": result["inputs"],
            "outputs": result["outputs"],
        }
        (temporary / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (temporary / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise VariantStructureError("Variant structure analysis output already exists.")
        shutil.move(str(temporary), str(final_output))
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _summary_markdown(result: dict[str, Any]) -> str:
    site = result["site"]
    lines = [
        f"# Variant structure review: {site['variant']} in {result['entry']['pdb_id']}",
        "",
        f"- Author residue: {site['chain']}:{site['author_residue_number']} ({site['observed_residue']})",
        f"- Structure allele: {site['structure_allele']}",
        f"- Heavy-atom contact cutoff: {site['contact_cutoff_angstrom']:.2f} Å",
        f"- Protein contacts: {site['protein_contact_count']}",
        f"- Nonlocal protein contacts: {site['nonlocal_protein_contact_count']}",
        f"- Hetero-group contacts: {site['hetero_contact_count']}",
        "",
        "## Interpretation boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in result["caveats"])
    return "\n".join(lines) + "\n"
