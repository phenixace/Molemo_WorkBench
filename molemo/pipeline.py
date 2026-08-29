"""Real data pipeline for Molemo WorkBench.

Run this module with the conda base Python that has RDKit installed:
    /opt/miniconda3/bin/python server.py
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

try:
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, Lipinski, rdDepictor, rdMolDescriptors
except ImportError as exc:  # pragma: no cover - exercised only in wrong runtime.
    Chem = None
    Crippen = None
    Descriptors = None
    Lipinski = None
    rdDepictor = None
    rdMolDescriptors = None
    RDKIT_IMPORT_ERROR = exc
else:
    RDKIT_IMPORT_ERROR = None


AA_MASS = {
    "A": 89.094,
    "R": 174.203,
    "N": 132.119,
    "D": 133.104,
    "C": 121.154,
    "E": 147.131,
    "Q": 146.146,
    "G": 75.067,
    "H": 155.156,
    "I": 131.175,
    "L": 131.175,
    "K": 146.189,
    "M": 149.208,
    "F": 165.192,
    "P": 115.132,
    "S": 105.093,
    "T": 119.12,
    "W": 204.228,
    "Y": 181.191,
    "V": 117.148,
}

AA_RESIDUE_MASS = {aa: mass - 18.015 for aa, mass in AA_MASS.items()}
HYDROPATHY = {
    "I": 4.5,
    "V": 4.2,
    "L": 3.8,
    "F": 2.8,
    "C": 2.5,
    "M": 1.9,
    "A": 1.8,
    "G": -0.4,
    "T": -0.7,
    "S": -0.8,
    "W": -0.9,
    "Y": -1.3,
    "P": -1.6,
    "H": -3.2,
    "E": -3.5,
    "Q": -3.5,
    "D": -3.5,
    "N": -3.5,
    "K": -3.9,
    "R": -4.5,
}

PKA_POSITIVE = {"N_TERM": 9.69, "K": 10.5, "R": 12.4, "H": 6.0}
PKA_NEGATIVE = {"C_TERM": 2.34, "D": 3.86, "E": 4.25, "C": 8.33, "Y": 10.07}
VALID_AA = set(AA_MASS)


@dataclass(frozen=True)
class PipelineError(Exception):
    message: str
    code: str = "pipeline_error"

    def to_dict(self) -> dict[str, str]:
        return {"error": self.message, "code": self.code}


def parse_molecule(smiles: str) -> dict[str, Any]:
    """Parse a SMILES string with RDKit and return a viewer-ready sample."""
    if Chem is None:
        raise PipelineError(
            "RDKit is not available in this Python runtime. Run server.py with conda base.",
            "rdkit_missing",
        ) from RDKIT_IMPORT_ERROR

    cleaned = smiles.strip()
    if not cleaned:
        raise PipelineError("SMILES input is empty.", "empty_smiles")

    mol = Chem.MolFromSmiles(cleaned)
    if mol is None:
        raise PipelineError("RDKit could not parse this SMILES.", "invalid_smiles")

    mol = Chem.Mol(mol)
    rdDepictor.Compute2DCoords(mol)
    conformer = mol.GetConformer()
    atoms = []
    for atom in mol.GetAtoms():
        position = conformer.GetAtomPosition(atom.GetIdx())
        atoms.append(
            {
                "e": atom.GetSymbol(),
                "x": round(float(position.x), 4),
                "y": round(float(-position.y), 4),
                "z": 0,
                "charge": atom.GetFormalCharge(),
                "aromatic": atom.GetIsAromatic(),
                "hybridization": str(atom.GetHybridization()),
            }
        )

    bonds = []
    for bond in mol.GetBonds():
        order = 1.5 if bond.GetIsAromatic() else float(bond.GetBondTypeAsDouble())
        bonds.append([bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), order])

    rings = [list(ring) for ring in Chem.GetSymmSSSR(mol)]
    formula = rdMolDescriptors.CalcMolFormula(mol)
    canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
    name = "Custom molecule"

    properties = {
        "Formula": formula,
        "MW": f"{Descriptors.MolWt(mol):.2f}",
        "logP": f"{Crippen.MolLogP(mol):.2f}",
        "HBA": str(Lipinski.NumHAcceptors(mol)),
        "HBD": str(Lipinski.NumHDonors(mol)),
        "TPSA": f"{rdMolDescriptors.CalcTPSA(mol):.1f}",
        "RotB": str(Lipinski.NumRotatableBonds(mol)),
        "Rings": str(rdMolDescriptors.CalcNumRings(mol)),
    }

    notes = (
        "RDKit parsed this SMILES, generated 2D coordinates, assigned bond orders, "
        "detected ring systems, and calculated core drug-like descriptors."
    )

    return {
        "id": "custom-molecule",
        "type": "molecule",
        "name": name,
        "shortName": "Custom",
        "subtitle": f"{formula} · {mol.GetNumHeavyAtoms()} heavy atoms · RDKit",
        "formula": formula,
        "smiles": canonical,
        "input": cleaned,
        "notes": notes,
        "selection": f"{formula} · RDKit molecular graph",
        "confidence": "RDKit parsed",
        "properties": properties,
        "atoms": atoms,
        "bonds": bonds,
        "rings": rings,
        "metadata": {
            "source": "rdkit",
            "canonicalSmiles": canonical,
            "heavyAtoms": mol.GetNumHeavyAtoms(),
            "aromaticAtoms": sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic()),
            "chiralCenters": Chem.FindMolChiralCenters(mol, includeUnassigned=True),
        },
        "prompts": [
            "解释这个分子的关键官能团",
            "优化这个分子的水溶性并解释风险",
            "生成 3 个下一轮设计方向",
        ],
    }


def parse_protein(raw_sequence: str) -> dict[str, Any]:
    """Parse FASTA/plain protein sequence and return a viewer-ready sample."""
    sequence = clean_fasta(raw_sequence)
    if not sequence:
        raise PipelineError("Protein sequence input is empty.", "empty_sequence")

    invalid = sorted(set(sequence) - VALID_AA)
    if invalid:
        raise PipelineError(f"Unsupported amino acid code(s): {', '.join(invalid)}.", "invalid_sequence")

    counts = Counter(sequence)
    length = len(sequence)
    mw = sum(AA_RESIDUE_MASS[aa] for aa in sequence) + 18.015
    gravy = sum(HYDROPATHY[aa] for aa in sequence) / length
    charge7 = protein_charge(sequence, 7.0)
    pi = estimate_pi(sequence)
    helix = sum(counts[aa] for aa in "AEKLQRMH") / length
    hydrophobic = sum(counts[aa] for aa in "AILMFWYV") / length
    acidic = counts["D"] + counts["E"]
    basic = counts["K"] + counts["R"] + counts["H"]
    aggregation_risk = "Medium" if hydrophobic > 0.42 and abs(charge7) < 2 else "Low"

    properties = {
        "Length": f"{length} aa",
        "MW": f"{mw / 1000:.2f} kDa",
        "pI": f"{pi:.2f}",
        "Charge": format_charge(charge7),
        "GRAVY": f"{gravy:.2f}",
        "Helix": f"{round(helix * 100)}%",
        "Hydrophobic": f"{round(hydrophobic * 100)}%",
        "Risk": aggregation_risk,
    }

    notes = (
        "The local sequence pipeline cleaned FASTA input and calculated composition, "
        "molecular weight, charge, pI, GRAVY, helix propensity, and aggregation flags."
    )

    return {
        "id": "custom-protein",
        "type": "protein",
        "name": "Custom protein",
        "shortName": "Custom protein",
        "subtitle": f"{length} aa · sequence pipeline",
        "formula": sequence,
        "sequence": sequence,
        "notes": notes,
        "selection": f"Custom protein · {length} aa",
        "confidence": "sequence-derived",
        "properties": properties,
        "metadata": {
            "source": "local_sequence_pipeline",
            "composition": dict(sorted(counts.items())),
            "acidicResidues": acidic,
            "basicResidues": basic,
        },
        "prompts": [
            "找出这个蛋白的稳定性热点",
            "建议 3 个突变并说明实验验证",
            "降低聚集风险并保留功能界面",
        ],
    }


def clean_fasta(raw_sequence: str) -> str:
    lines = []
    for line in raw_sequence.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(">"):
            continue
        lines.append(stripped)
    return re.sub(r"[^A-Za-z]", "", "".join(lines)).upper()


def protein_charge(sequence: str, ph: float) -> float:
    counts = Counter(sequence)
    positive = 1 / (1 + 10 ** (ph - PKA_POSITIVE["N_TERM"]))
    positive += counts["K"] / (1 + 10 ** (ph - PKA_POSITIVE["K"]))
    positive += counts["R"] / (1 + 10 ** (ph - PKA_POSITIVE["R"]))
    positive += counts["H"] / (1 + 10 ** (ph - PKA_POSITIVE["H"]))

    negative = 1 / (1 + 10 ** (PKA_NEGATIVE["C_TERM"] - ph))
    negative += counts["D"] / (1 + 10 ** (PKA_NEGATIVE["D"] - ph))
    negative += counts["E"] / (1 + 10 ** (PKA_NEGATIVE["E"] - ph))
    negative += counts["C"] / (1 + 10 ** (PKA_NEGATIVE["C"] - ph))
    negative += counts["Y"] / (1 + 10 ** (PKA_NEGATIVE["Y"] - ph))
    return positive - negative


def estimate_pi(sequence: str) -> float:
    low = 0.0
    high = 14.0
    for _ in range(48):
        mid = (low + high) / 2
        if protein_charge(sequence, mid) > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def format_charge(charge: float) -> str:
    rounded = round(charge, 1)
    if math.isclose(rounded, 0.0, abs_tol=0.05):
        return "0.0"
    return f"{rounded:+.1f}"
