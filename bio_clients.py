"""Small, allow-listed clients for public life-science databases."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote, urlparse


ALLOWED_HOSTS = {
    "api.platform.opentargets.org",
    "clinicaltrials.gov",
    "clinicaltables.nlm.nih.gov",
    "eutils.ncbi.nlm.nih.gov",
    "gnomad.broadinstitute.org",
    "pubchem.ncbi.nlm.nih.gov",
    "rest.ensembl.org",
    "rest.uniprot.org",
    "data.rcsb.org",
    "files.rcsb.org",
    "www.ebi.ac.uk",
}
MAX_JSON_BYTES = 6 * 1024 * 1024
MAX_JSON_REQUEST_BYTES = 256 * 1024
MAX_STRUCTURE_BYTES = 24 * 1024 * 1024
USER_AGENT = "Molemo-WorkBench/0.11 (public scientific database client)"


class ExternalDataError(RuntimeError):
    """Raised when an allow-listed public data source cannot be queried."""


def get_json(url: str) -> dict[str, Any]:
    raw = _get(url, "application/json", MAX_JSON_BYTES)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def get_json_array(url: str) -> list[Any]:
    """GET a bounded JSON array from an allow-listed scientific database."""
    raw = _get(url, "application/json", MAX_JSON_BYTES)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, list):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def get_text(url: str) -> str:
    raw = _get(url, "text/plain", MAX_STRUCTURE_BYTES)
    return raw.decode("utf-8", errors="replace")


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST a bounded JSON request to an allow-listed scientific database."""
    try:
        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExternalDataError("The public database request could not be encoded as JSON.") from exc
    if len(body) > MAX_JSON_REQUEST_BYTES:
        raise ExternalDataError("Public database request exceeded the local size limit.")
    raw = _request(url, "application/json", MAX_JSON_BYTES, method="POST", body=body)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def _get(url: str, accept: str, max_bytes: int) -> bytes:
    return _request(url, accept, max_bytes, method="GET")


def _request(
    url: str,
    accept: str,
    max_bytes: int,
    *,
    method: str,
    body: bytes | None = None,
) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ExternalDataError("External requests are restricted to approved scientific databases.")
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read(max_bytes + 1)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ExternalDataError("No matching public database record was found.") from exc
        raise ExternalDataError(f"Public database request failed with HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ExternalDataError(f"Could not reach the public database: {exc}") from exc
    if len(raw) > max_bytes:
        raise ExternalDataError("Public database response exceeded the local size limit.")
    return raw


def lookup_pubchem(query: str) -> dict[str, Any]:
    cleaned = str(query or "").strip()
    if not cleaned or len(cleaned) > 200:
        raise ExternalDataError("PubChem query must contain between 1 and 200 characters.")
    fields = ",".join(
        [
            "Title",
            "IUPACName",
            "MolecularFormula",
            "MolecularWeight",
            "XLogP",
            "HBondDonorCount",
            "HBondAcceptorCount",
            "RotatableBondCount",
            "TPSA",
            "SMILES",
            "ConnectivitySMILES",
            "InChIKey",
        ]
    )
    url = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
        f"{quote(cleaned, safe='')}/property/{fields}/JSON"
    )
    payload = get_json(url)
    return parse_pubchem_payload(payload, cleaned)


def parse_pubchem_payload(payload: dict[str, Any], query: str = "") -> dict[str, Any]:
    records = ((payload.get("PropertyTable") or {}).get("Properties") or [])
    if not records or not isinstance(records[0], dict):
        raise ExternalDataError("PubChem returned no compound properties.")
    record = records[0]
    cid = record.get("CID")
    smiles = (
        record.get("SMILES")
        or record.get("ConnectivitySMILES")
        or ""
    )
    return {
        "source": "PubChem",
        "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}" if cid else "https://pubchem.ncbi.nlm.nih.gov/",
        "query": query,
        "cid": cid,
        "title": record.get("Title") or record.get("IUPACName") or query,
        "iupac_name": record.get("IUPACName"),
        "formula": record.get("MolecularFormula"),
        "molecular_weight": record.get("MolecularWeight"),
        "xlogp": record.get("XLogP"),
        "hbd": record.get("HBondDonorCount"),
        "hba": record.get("HBondAcceptorCount"),
        "rotatable_bonds": record.get("RotatableBondCount"),
        "tpsa": record.get("TPSA"),
        "smiles": smiles,
        "inchikey": record.get("InChIKey"),
    }


def lookup_uniprot(accession: str) -> dict[str, Any]:
    cleaned = str(accession or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,10}(?:-\d+)?", cleaned):
        raise ExternalDataError("UniProt accession must be a 6-10 character accession, optionally with an isoform suffix.")
    payload = get_json(f"https://rest.uniprot.org/uniprotkb/{quote(cleaned, safe='-')}.json")
    return parse_uniprot_payload(payload, cleaned)


def parse_uniprot_payload(payload: dict[str, Any], accession: str = "") -> dict[str, Any]:
    description = payload.get("proteinDescription") or {}
    recommended = ((description.get("recommendedName") or {}).get("fullName") or {}).get("value")
    submitted = description.get("submissionNames") or []
    submitted_name = (((submitted[0] or {}).get("fullName") or {}).get("value")) if submitted else None
    genes = []
    for gene in payload.get("genes") or []:
        name = ((gene.get("geneName") or {}).get("value"))
        if name:
            genes.append(name)
    functions = []
    for comment in payload.get("comments") or []:
        if comment.get("commentType") != "FUNCTION":
            continue
        for text in comment.get("texts") or []:
            value = text.get("value")
            if value:
                functions.append(value)
    pdb_ids = []
    for reference in payload.get("uniProtKBCrossReferences") or []:
        if reference.get("database") == "PDB" and reference.get("id"):
            pdb_ids.append(reference["id"])
    sequence = payload.get("sequence") or {}
    primary = payload.get("primaryAccession") or accession
    return {
        "source": "UniProtKB",
        "source_url": f"https://www.uniprot.org/uniprotkb/{primary}/entry",
        "accession": primary,
        "entry_name": payload.get("uniProtkbId"),
        "reviewed": payload.get("entryType") == "UniProtKB reviewed (Swiss-Prot)",
        "protein_name": recommended or submitted_name or primary,
        "genes": genes,
        "organism": (payload.get("organism") or {}).get("scientificName"),
        "taxon_id": (payload.get("organism") or {}).get("taxonId"),
        "sequence": sequence.get("value") or "",
        "length": sequence.get("length"),
        "molecular_weight": sequence.get("molWeight"),
        "functions": functions[:3],
        "pdb_ids": list(dict.fromkeys(pdb_ids))[:24],
        "feature_count": len(payload.get("features") or []),
    }


def lookup_rcsb_entry(pdb_id: str) -> dict[str, Any]:
    cleaned = normalize_pdb_id(pdb_id)
    payload = get_json(f"https://data.rcsb.org/rest/v1/core/entry/{cleaned}")
    return parse_rcsb_payload(payload, cleaned)


def parse_rcsb_payload(payload: dict[str, Any], pdb_id: str = "") -> dict[str, Any]:
    entry_id = str(((payload.get("rcsb_entry_container_identifiers") or {}).get("entry_id")) or pdb_id).upper()
    info = payload.get("rcsb_entry_info") or {}
    resolutions = info.get("resolution_combined") or []
    methods = [item.get("method") for item in payload.get("exptl") or [] if item.get("method")]
    return {
        "source": "RCSB PDB",
        "source_url": f"https://www.rcsb.org/structure/{entry_id}",
        "pdb_id": entry_id,
        "title": (payload.get("struct") or {}).get("title") or entry_id,
        "methods": methods,
        "resolution_angstrom": resolutions[0] if resolutions else None,
        "polymer_entity_count": info.get("polymer_entity_count"),
        "deposited_atom_count": info.get("deposited_atom_count"),
        "release_date": (payload.get("rcsb_accession_info") or {}).get("initial_release_date"),
    }


def fetch_rcsb_pdb_text(pdb_id: str) -> str:
    cleaned = normalize_pdb_id(pdb_id)
    return get_text(f"https://files.rcsb.org/download/{cleaned}.pdb")


def normalize_pdb_id(pdb_id: str) -> str:
    cleaned = str(pdb_id or "").strip().upper()
    if not re.fullmatch(r"[0-9][A-Z0-9]{3}", cleaned):
        raise ExternalDataError("PDB identifier must contain four alphanumeric characters and start with a digit.")
    return cleaned
