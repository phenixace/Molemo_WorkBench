"""Handlers for allow-listed public biological databases."""

from __future__ import annotations

from typing import Any

from molemo.bio_clients import lookup_pubchem, lookup_uniprot
from molemo.pipeline import parse_molecule, parse_protein


def lookup_compound(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    record = lookup_pubchem(str(arguments.get("query") or ""))
    artifacts = [
        {
            "id": f"pubchem-record-{record.get('cid') or 'query'}",
            "type": "database-record",
            "title": f"PubChem · {record.get('title') or record.get('query')}",
            "data": record,
        }
    ]
    smiles = str(record.get("smiles") or "")
    if smiles:
        sample = parse_molecule(smiles)
        sample.update(
            {
                "id": f"pubchem-{record.get('cid') or 'compound'}",
                "name": str(record.get("title") or "PubChem compound"),
                "shortName": str(record.get("title") or "PubChem")[:28],
                "subtitle": f"PubChem CID {record.get('cid')} · RDKit structure",
                "selection": f"PubChem CID {record.get('cid')} · {sample['formula']}",
                "confidence": "PubChem record + RDKit parsed",
            }
        )
        sample["metadata"].update({"source": "PubChem + RDKit", "sourceUrl": record["source_url"], "cid": record.get("cid")})
        artifacts.append(
            {
                "id": f"pubchem-structure-{record.get('cid') or 'compound'}",
                "type": "molecule",
                "title": f"{record.get('title') or 'PubChem compound'} structure",
                "data": sample,
            }
        )
    return {
        "summary": (
            f"PubChem CID {record.get('cid')} identifies {record.get('title')}; "
            f"formula {record.get('formula')}, molecular weight {record.get('molecular_weight')}."
        ),
        "data": record,
        "evidence": [{"source": "PubChem PUG REST", "url": record["source_url"]}],
        "artifacts": artifacts,
    }


def lookup_protein(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    record = lookup_uniprot(str(arguments.get("accession") or ""))
    artifacts = [
        {
            "id": f"uniprot-record-{record['accession']}",
            "type": "database-record",
            "title": f"UniProtKB · {record['accession']}",
            "data": record,
        }
    ]
    sequence = str(record.get("sequence") or "")
    if sequence:
        sample = parse_protein(sequence)
        sample.update(
            {
                "id": f"uniprot-{record['accession'].lower()}",
                "name": str(record.get("protein_name") or record["accession"]),
                "shortName": record["accession"],
                "subtitle": f"{record.get('organism') or 'unknown organism'} · UniProtKB",
                "selection": f"UniProtKB {record['accession']} · {record.get('protein_name')}",
                "confidence": "reviewed UniProtKB" if record.get("reviewed") else "UniProtKB annotation",
            }
        )
        sample["metadata"].update(
            {
                "source": "UniProtKB + local sequence pipeline",
                "sourceUrl": record["source_url"],
                "accession": record["accession"],
                "pdbIds": record.get("pdb_ids") or [],
            }
        )
        artifacts.append(
            {
                "id": f"uniprot-sequence-{record['accession']}",
                "type": "protein-sequence",
                "title": f"{record['accession']} protein sequence",
                "data": sample,
            }
        )
    return {
        "summary": (
            f"UniProtKB {record['accession']} is {record.get('protein_name')} from "
            f"{record.get('organism')}; {record.get('length')} aa with {len(record.get('pdb_ids') or [])} PDB cross-references."
        ),
        "data": record,
        "evidence": [{"source": "UniProtKB REST API", "url": record["source_url"]}],
        "artifacts": artifacts,
    }
