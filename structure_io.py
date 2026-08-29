"""PDB/mmCIF parsing and viewer-ready protein structure samples."""

from __future__ import annotations

import math
import shlex
from collections import defaultdict
from typing import Any

from pipeline import PipelineError, parse_protein


AA3_TO1 = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLU": "E", "GLN": "Q", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
    "MSE": "M", "SEC": "C", "PYL": "K",
}
MAX_VIEWER_ATOMS = 12000
MAX_PAE_BINS = 384
MAX_PAE_CELLS = 2_000_000


class StructureError(ValueError):
    """Raised when coordinate data cannot be parsed safely."""


def parse_structure_text(raw: str, source_id: str = "local", fmt: str = "") -> dict[str, Any]:
    text = str(raw or "")
    if not text.strip():
        raise StructureError("Structure text is empty.")
    selected = str(fmt or "").strip().lower()
    if selected in {"cif", "mmcif"} or "_atom_site.Cartn_x" in text:
        atoms = _parse_mmcif_atoms(text)
        source_format = "mmCIF"
    else:
        atoms = _parse_pdb_atoms(text)
        source_format = "PDB"
    if not atoms:
        raise StructureError("No ATOM/HETATM coordinates were found in the structure.")
    return _build_structure(atoms, source_id, source_format)


def _parse_pdb_atoms(text: str) -> list[dict[str, Any]]:
    atoms = []
    first_model = None
    for line in text.splitlines():
        record = line[:6].strip().upper()
        if record == "MODEL":
            model = line[10:14].strip() or "1"
            if first_model is None:
                first_model = model
            elif model != first_model:
                break
            continue
        if record == "ENDMDL" and atoms:
            break
        if record not in {"ATOM", "HETATM"} or len(line) < 54:
            continue
        alt = line[16:17]
        if alt not in {" ", "", "A", "1"}:
            continue
        residue = line[17:20].strip().upper()
        if residue in {"HOH", "WAT", "DOD"}:
            continue
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
        except ValueError:
            continue
        try:
            bfactor = float(line[60:66]) if len(line) >= 66 and line[60:66].strip() else None
        except ValueError:
            bfactor = None
        name = line[12:16].strip()
        element = line[76:78].strip().title() if len(line) >= 78 else ""
        if not element:
            element = "".join(char for char in name if char.isalpha())[:2].title() or "X"
            if len(element) == 2 and element.upper() not in {"CL", "BR", "NA", "MG", "CA", "FE", "ZN"}:
                element = element[0]
        atoms.append(
            {
                "e": element,
                "x": x,
                "y": y,
                "z": z,
                "name": name,
                "residue": residue,
                "chain": line[21:22].strip() or "_",
                "resSeq": line[22:27].strip(),
                "hetero": record == "HETATM",
                "bfactor": bfactor,
            }
        )
    return atoms


def _parse_mmcif_atoms(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    atoms: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        if lines[index].strip() != "loop_":
            index += 1
            continue
        index += 1
        headers = []
        while index < len(lines) and lines[index].strip().startswith("_"):
            headers.append(lines[index].strip())
            index += 1
        if not headers or not any(header.startswith("_atom_site.") for header in headers):
            continue
        field = {header.split(".", 1)[1]: position for position, header in enumerate(headers)}
        required = {"Cartn_x", "Cartn_y", "Cartn_z"}
        if not required.issubset(field):
            raise StructureError("mmCIF atom_site loop is missing Cartesian coordinates.")
        while index < len(lines):
            stripped = lines[index].strip()
            if not stripped or stripped.startswith("#"):
                index += 1
                if stripped.startswith("#"):
                    break
                continue
            if stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
                break
            try:
                values = shlex.split(stripped, posix=True)
            except ValueError:
                index += 1
                continue
            index += 1
            if len(values) < len(headers):
                continue
            group = _cif_value(values, field, "group_PDB", "ATOM").upper()
            if group not in {"ATOM", "HETATM"}:
                continue
            model = _cif_value(values, field, "pdbx_PDB_model_num", "1")
            if model not in {"1", ".", "?"}:
                continue
            alt = _cif_value(values, field, "label_alt_id", ".")
            if alt not in {".", "?", "A", "1"}:
                continue
            residue = _cif_first(values, field, "auth_comp_id", "label_comp_id").upper()
            if residue in {"HOH", "WAT", "DOD"}:
                continue
            try:
                x = float(values[field["Cartn_x"]])
                y = float(values[field["Cartn_y"]])
                z = float(values[field["Cartn_z"]])
            except (ValueError, IndexError):
                continue
            try:
                raw_bfactor = _cif_value(values, field, "B_iso_or_equiv")
                bfactor = float(raw_bfactor) if raw_bfactor not in {"", ".", "?"} else None
            except ValueError:
                bfactor = None
            atoms.append(
                {
                    "e": _cif_value(values, field, "type_symbol", "X").title(),
                    "x": x,
                    "y": y,
                    "z": z,
                    "name": _cif_first(values, field, "auth_atom_id", "label_atom_id"),
                    "residue": residue,
                    "chain": _cif_first(values, field, "auth_asym_id", "label_asym_id") or "_",
                    "resSeq": _cif_first(values, field, "auth_seq_id", "label_seq_id"),
                    "hetero": group == "HETATM",
                    "bfactor": bfactor,
                }
            )
        break
    return atoms


def _cif_value(values: list[str], field: dict[str, int], name: str, default: str = "") -> str:
    position = field.get(name)
    return values[position] if position is not None and position < len(values) else default


def _cif_first(values: list[str], field: dict[str, int], *names: str) -> str:
    for name in names:
        value = _cif_value(values, field, name)
        if value not in {"", ".", "?"}:
            return value
    return ""


def _build_structure(atoms: list[dict[str, Any]], source_id: str, source_format: str) -> dict[str, Any]:
    raw_count = len(atoms)
    visual_atoms = _select_viewer_atoms(atoms, MAX_VIEWER_ATOMS)
    chain_points: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_residues: set[tuple[str, str]] = set()
    chain_sequences: dict[str, list[str]] = defaultdict(list)
    ligands: set[str] = set()
    for atom in atoms:
        if atom["hetero"]:
            ligands.add(atom["residue"])
            continue
        if atom["name"].upper() != "CA":
            continue
        key = (atom["chain"], atom["resSeq"])
        if key in seen_residues:
            continue
        seen_residues.add(key)
        amino_acid = AA3_TO1.get(atom["residue"])
        if not amino_acid:
            continue
        chain_sequences[atom["chain"]].append(amino_acid)
        chain_points[atom["chain"]].append(
            {
                "x": round(atom["x"], 3),
                "y": round(atom["y"], 3),
                "z": round(atom["z"], 3),
                "aa": amino_acid,
                "residue": atom["residue"],
                "resSeq": atom["resSeq"],
                "bfactor": atom.get("bfactor"),
            }
        )
    sequence = "".join("".join(chain_sequences[chain]) for chain in sorted(chain_sequences))
    chains = [
        {"id": chain, "sequence": "".join(chain_sequences[chain]), "residues": len(chain_sequences[chain])}
        for chain in sorted(chain_sequences)
    ]
    return {
        "source_id": str(source_id or "local"),
        "format": source_format,
        "atom_count": raw_count,
        "viewer_atom_count": len(visual_atoms),
        "atoms_truncated": len(visual_atoms) < raw_count,
        "atoms": visual_atoms,
        "backbone": [{"chain": chain, "points": points} for chain, points in sorted(chain_points.items())],
        "chains": chains,
        "sequence": sequence,
        "ligands": sorted(ligands),
    }


def _select_viewer_atoms(atoms: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(atoms) <= limit:
        selected = atoms
    else:
        backbone = [atom for atom in atoms if atom["name"].upper() in {"N", "CA", "C", "O"}]
        remaining = max(0, limit - len(backbone))
        sidechain = [atom for atom in atoms if atom["name"].upper() not in {"N", "CA", "C", "O"}]
        stride = max(1, len(sidechain) // max(1, remaining))
        selected = (backbone + sidechain[::stride][:remaining])[:limit]
    return [
        {
            "e": atom["e"],
            "x": round(atom["x"], 3),
            "y": round(atom["y"], 3),
            "z": round(atom["z"], 3),
            "name": atom["name"],
            "residue": atom["residue"],
            "chain": atom["chain"],
            "resSeq": atom["resSeq"],
            "hetero": atom["hetero"],
            "bfactor": atom.get("bfactor"),
        }
        for atom in selected
    ]


def summarize_plddt(structure: dict[str, Any], reported_mean: Any = None) -> dict[str, Any]:
    """Summarize AlphaFold pLDDT from CA B-factors without reinterpreting generic structures."""
    residues = []
    for chain in structure.get("backbone") or []:
        for point in chain.get("points") or []:
            value = point.get("bfactor")
            if value is None:
                continue
            score = max(0.0, min(100.0, float(value)))
            residues.append(
                {
                    "chain": chain.get("chain") or "_",
                    "resSeq": point.get("resSeq"),
                    "aa": point.get("aa"),
                    "plddt": round(score, 2),
                    "category": _plddt_category(score),
                }
            )
    if not residues:
        raise StructureError("AlphaFold coordinates did not contain per-residue pLDDT values.")
    counts = {name: 0 for name in ("very_high", "confident", "low", "very_low")}
    for residue in residues:
        counts[residue["category"]] += 1
    total = len(residues)
    calculated_mean = sum(item["plddt"] for item in residues) / total
    try:
        mean_plddt = float(reported_mean)
    except (TypeError, ValueError):
        mean_plddt = calculated_mean
    return {
        "metric": "pLDDT",
        "mean_plddt": round(mean_plddt, 2),
        "calculated_mean_plddt": round(calculated_mean, 2),
        "residue_count": total,
        "counts": counts,
        "fractions": {name: round(count / total, 4) for name, count in counts.items()},
        "residues": residues,
    }


def _plddt_category(score: float) -> str:
    if score >= 90:
        return "very_high"
    if score >= 70:
        return "confident"
    if score >= 50:
        return "low"
    return "very_low"


def parse_alphafold_pae(
    payload: list[Any],
    expected_residues: int | None = None,
    max_bins: int = MAX_PAE_BINS,
) -> dict[str, Any]:
    """Validate and downsample an AlphaFold predicted-aligned-error matrix."""
    if len(payload) != 1 or not isinstance(payload[0], dict):
        raise StructureError("AlphaFold PAE response must contain exactly one matrix record.")
    matrix = payload[0].get("predicted_aligned_error")
    if not isinstance(matrix, list) or not matrix:
        raise StructureError("AlphaFold PAE response did not contain a matrix.")
    residue_count = len(matrix)
    if expected_residues and residue_count != int(expected_residues):
        raise StructureError(
            f"AlphaFold PAE matrix has {residue_count} residues; expected {int(expected_residues)}."
        )
    if residue_count * residue_count > MAX_PAE_CELLS:
        raise StructureError("AlphaFold PAE matrix exceeds the local analysis cell limit.")
    if not 32 <= int(max_bins) <= MAX_PAE_BINS:
        raise StructureError(f"PAE max_bins must be between 32 and {MAX_PAE_BINS}.")

    normalized: list[list[float]] = []
    observed_max = 0.0
    for row in matrix:
        if not isinstance(row, list) or len(row) != residue_count:
            raise StructureError("AlphaFold PAE matrix must be square.")
        normalized_row = []
        for value in row:
            if isinstance(value, bool):
                raise StructureError("AlphaFold PAE matrix contains a non-numeric value.")
            try:
                score = float(value)
            except (TypeError, ValueError) as exc:
                raise StructureError("AlphaFold PAE matrix contains a non-numeric value.") from exc
            if not math.isfinite(score) or score < 0 or score > 100:
                raise StructureError("AlphaFold PAE values must be finite and between 0 and 100 Å.")
            observed_max = max(observed_max, score)
            normalized_row.append(score)
        normalized.append(normalized_row)

    bin_size = max(1, math.ceil(residue_count / int(max_bins)))
    display_size = math.ceil(residue_count / bin_size)
    display_matrix: list[list[float]] = []
    for row_start in range(0, residue_count, bin_size):
        row_end = min(residue_count, row_start + bin_size)
        display_row = []
        for column_start in range(0, residue_count, bin_size):
            column_end = min(residue_count, column_start + bin_size)
            total = 0.0
            count = 0
            for row_index in range(row_start, row_end):
                values = normalized[row_index][column_start:column_end]
                total += sum(values)
                count += len(values)
            display_row.append(round(total / max(1, count), 2))
        display_matrix.append(display_row)

    reported_max = payload[0].get("max_predicted_aligned_error")
    try:
        max_error = float(reported_max)
    except (TypeError, ValueError):
        max_error = observed_max
    if not math.isfinite(max_error) or max_error <= 0 or max_error > 100:
        max_error = observed_max or 1.0
    else:
        max_error = max(max_error, observed_max)
    return {
        "metric": "predicted aligned error",
        "unit": "Å",
        "residue_count": residue_count,
        "matrix_size": display_size,
        "bin_size": bin_size,
        "downsampled": bin_size > 1,
        "max_error": round(max_error, 2),
        "matrix": display_matrix,
        "orientation": {
            "rows": "scored residue",
            "columns": "aligned residue",
        },
    }


def build_structure_sample(
    structure: dict[str, Any],
    title: str = "Protein structure",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sequence = str(structure.get("sequence") or "")
    try:
        base = parse_protein(sequence) if sequence else None
    except PipelineError:
        base = None
    source_id = str(structure.get("source_id") or "local")
    chain_count = len(structure.get("chains") or [])
    metadata_payload = dict(metadata or {})
    coordinate_type = str(metadata_payload.get("coordinate_type") or ("experimental" if source_id != "local" else "local"))
    confidence = structure.get("confidence") or {}
    properties = dict((base or {}).get("properties") or {})
    properties.update(
        {
            "Atoms": str(structure.get("atom_count") or 0),
            "Chains": str(chain_count),
            "Format": str(structure.get("format") or "structure"),
            "Ligands": str(len(structure.get("ligands") or [])),
        }
    )
    if coordinate_type == "predicted":
        fractions = confidence.get("fractions") or {}
        pae = structure.get("pae") or {}
        properties.update(
            {
                "Mean pLDDT": f"{float(confidence.get('mean_plddt') or 0):.2f}",
                "Very high": f"{float(fractions.get('very_high') or 0) * 100:.1f}%",
                "Low / very low": f"{(float(fractions.get('low') or 0) + float(fractions.get('very_low') or 0)) * 100:.1f}%",
                "Model": str(metadata_payload.get("entry_id") or source_id),
            }
        )
        if pae:
            properties["PAE"] = f"{int(pae.get('residue_count') or 0)} × {int(pae.get('residue_count') or 0)}"
        notes = (
            "AlphaFold DB predicted model colored by per-residue pLDDT. pLDDT describes local confidence; "
            "review the PAE matrix before interpreting relative domain placement. Prediction does not establish ligand binding, dynamics, or mechanism."
        )
        selection = f"{source_id.upper()} · predicted monomer structure"
        confidence_label = f"AlphaFold prediction · mean pLDDT {float(confidence.get('mean_plddt') or 0):.2f}"
    else:
        notes = (
            "Coordinates were parsed locally from the first structural model. Viewer atoms may be sampled for large entries; "
            "reported atom counts retain the full parsed total."
        )
        selection = f"{source_id.upper()} · atom-level protein structure"
        confidence_label = "experimental coordinates" if coordinate_type == "experimental" else "parsed coordinates"
    return {
        "id": f"structure-{source_id.lower()}",
        "type": "protein",
        "name": title,
        "shortName": source_id.upper() if source_id != "local" else "Structure",
        "subtitle": f"{structure.get('atom_count', 0)} atoms · {chain_count} chains · {structure.get('format')}",
        "formula": sequence,
        "sequence": sequence,
        "pdbId": source_id.upper() if len(source_id) == 4 else "",
        "notes": notes,
        "selection": selection,
        "confidence": confidence_label,
        "properties": properties,
        "structure": structure,
        "metadata": {
            "source": "coordinate_parser",
            **metadata_payload,
            "coordinateType": coordinate_type,
            "paeAvailable": bool(structure.get("pae")),
        },
        "prompts": [
            "总结这个结构的链组成和配体",
            "结合序列与结构提出需要验证的功能位点",
            "设计下一步结构比较或突变实验",
        ],
    }
