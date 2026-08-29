"""Small, allow-listed clients for public life-science databases."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import quote, urlencode, urlparse


ALLOWED_HOSTS = {
    "alphafold.ebi.ac.uk",
    "api.platform.opentargets.org",
    "clinicaltrials.gov",
    "clinicaltables.nlm.nih.gov",
    "eutils.ncbi.nlm.nih.gov",
    "gnomad.broadinstitute.org",
    "pubchem.ncbi.nlm.nih.gov",
    "rest.ensembl.org",
    "rest.uniprot.org",
    "reactome.org",
    "version-12-0.string-db.org",
    "data.rcsb.org",
    "files.rcsb.org",
    "www.ebi.ac.uk",
}
MAX_JSON_BYTES = 6 * 1024 * 1024
MAX_JSON_REQUEST_BYTES = 256 * 1024
MAX_STRUCTURE_BYTES = 24 * 1024 * 1024
USER_AGENT = "Molemo-WorkBench/0.17 (public scientific database client)"
MAX_STRING_QUERY_BYTES = 16 * 1024
_STRING_REQUEST_LOCK = threading.Lock()
_STRING_LAST_REQUEST = 0.0


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
    raw = _request(
        url,
        "application/json",
        MAX_JSON_BYTES,
        method="POST",
        body=body,
        content_type="application/json",
    )
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def post_text_json(url: str, text: str) -> dict[str, Any]:
    """POST bounded plain text and require a JSON object response."""
    body = str(text or "").encode("utf-8")
    if not body or len(body) > MAX_JSON_REQUEST_BYTES:
        raise ExternalDataError("Public database text request must be non-empty and within the local size limit.")
    raw = _request(
        url,
        "application/json",
        MAX_JSON_BYTES,
        method="POST",
        body=body,
        content_type="text/plain; charset=utf-8",
    )
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def post_form_json_array(url: str, fields: dict[str, Any]) -> list[Any]:
    """POST bounded form data and require a JSON array response."""
    body = urlencode({key: str(value) for key, value in fields.items()}).encode("utf-8")
    if len(body) > MAX_JSON_REQUEST_BYTES:
        raise ExternalDataError("Public database form request exceeded the local size limit.")
    parsed = urlparse(url)
    if parsed.hostname == "version-12-0.string-db.org" and shutil.which("curl"):
        global _STRING_LAST_REQUEST
        with _STRING_REQUEST_LOCK:
            delay = 1.05 - (time.monotonic() - _STRING_LAST_REQUEST)
            if delay > 0:
                time.sleep(delay)
            try:
                raw = _curl_form_request(url, body, MAX_JSON_BYTES)
            finally:
                _STRING_LAST_REQUEST = time.monotonic()
    else:
        raw = _request(
            url,
            "application/json",
            MAX_JSON_BYTES,
            method="POST",
            body=body,
            content_type="application/x-www-form-urlencoded; charset=utf-8",
        )
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExternalDataError("The public database returned invalid JSON.") from exc
    if not isinstance(data, list):
        raise ExternalDataError("The public database returned an unexpected response shape.")
    return data


def _curl_form_request(url: str, body: bytes, max_bytes: int) -> bytes:
    """Use a bounded curl GET for STRING endpoints challenged by its CDN."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "version-12-0.string-db.org":
        raise ExternalDataError("External requests are restricted to approved scientific databases.")
    curl = shutil.which("curl")
    if not curl:
        raise ExternalDataError("The STRING API requires a local curl executable in this environment.")
    if len(body) > MAX_STRING_QUERY_BYTES:
        raise ExternalDataError("STRING API query exceeded the local URL size limit.")
    command = [
        curl,
        "--silent",
        "--show-error",
        "--max-time",
        "30",
        "--max-filesize",
        str(max_bytes),
        "--header",
        "Accept: application/json",
        "--header",
        f"User-Agent: {USER_AGENT}",
        "--get",
        "--data-binary",
        "@-",
        "--write-out",
        "\n%{http_code}",
        url,
    ]
    try:
        completed = subprocess.run(
            command,
            input=body,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=35,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExternalDataError(f"Could not reach the public database: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ExternalDataError(f"Could not reach the public database: {detail or 'curl failed'}")
    try:
        raw, status_text = completed.stdout.rsplit(b"\n", 1)
        status = int(status_text)
    except (ValueError, TypeError) as exc:
        raise ExternalDataError("The public database returned an unexpected transport response.") from exc
    if status == 404:
        raise ExternalDataError("No matching public database record was found.")
    if not 200 <= status < 300:
        raise ExternalDataError(f"Public database request failed with HTTP {status}.")
    if len(raw) > max_bytes:
        raise ExternalDataError("Public database response exceeded the local size limit.")
    return raw


def _get(url: str, accept: str, max_bytes: int) -> bytes:
    return _request(url, accept, max_bytes, method="GET")


def _request(
    url: str,
    accept: str,
    max_bytes: int,
    *,
    method: str,
    body: bytes | None = None,
    content_type: str | None = None,
) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ExternalDataError("External requests are restricted to approved scientific databases.")
    headers = {"Accept": accept, "User-Agent": USER_AGENT}
    if body is not None and content_type:
        headers["Content-Type"] = content_type
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
    cleaned = normalize_uniprot_accession(accession)
    payload = get_json(f"https://rest.uniprot.org/uniprotkb/{quote(cleaned, safe='-')}.json")
    return parse_uniprot_payload(payload, cleaned)


def lookup_alphafold_prediction(accession: str) -> dict[str, Any]:
    """Return the exact AlphaFold DB record for a UniProt accession."""
    cleaned = normalize_uniprot_accession(accession)
    payload = get_json_array(f"https://alphafold.ebi.ac.uk/api/prediction/{quote(cleaned, safe='-')}")
    return parse_alphafold_predictions(payload, cleaned)


def parse_alphafold_predictions(payload: list[Any], accession: str) -> dict[str, Any]:
    cleaned = normalize_uniprot_accession(accession)
    record = next(
        (
            item
            for item in payload
            if isinstance(item, dict)
            and str(item.get("uniprotAccession") or "").strip().upper() == cleaned
        ),
        None,
    )
    if record is None:
        raise ExternalDataError(f"AlphaFold DB did not return an exact model for {cleaned}.")
    entry_id = str(record.get("entryId") or record.get("modelEntityId") or "").strip()
    model_url = str(record.get("pdbUrl") or "").strip()
    if not entry_id or not model_url:
        raise ExternalDataError("AlphaFold DB returned a record without a downloadable PDB model.")
    return {
        "source": "AlphaFold Protein Structure Database",
        "source_url": f"https://alphafold.ebi.ac.uk/entry/{quote(cleaned, safe='-')}",
        "coordinate_type": "predicted",
        "accession": cleaned,
        "entry_id": entry_id,
        "gene": record.get("gene"),
        "organism": record.get("organismScientificName"),
        "taxon_id": record.get("taxId"),
        "sequence": record.get("uniprotSequence") or "",
        "length": record.get("uniprotEnd"),
        "reviewed": bool(record.get("isReviewed")),
        "tool": record.get("toolUsed"),
        "mean_plddt": record.get("globalMetricValue"),
        "fraction_very_high": record.get("fractionPlddtVeryHigh"),
        "fraction_confident": record.get("fractionPlddtConfident"),
        "fraction_low": record.get("fractionPlddtLow"),
        "fraction_very_low": record.get("fractionPlddtVeryLow"),
        "latest_version": record.get("latestVersion"),
        "all_versions": record.get("allVersions") or [],
        "model_created_date": record.get("modelCreatedDate"),
        "model_url": model_url,
        "confidence_url": record.get("plddtDocUrl"),
        "pae_url": record.get("paeDocUrl"),
        "pae_image_url": record.get("paeImageUrl"),
    }


def fetch_alphafold_pdb_text(model_url: str) -> str:
    """Fetch an AlphaFold PDB URL only when it matches the official file layout."""
    parsed = urlparse(str(model_url or ""))
    if (
        parsed.scheme != "https"
        or parsed.hostname != "alphafold.ebi.ac.uk"
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(r"/files/AF-[A-Z0-9-]+-F1-model_v\d+\.pdb", parsed.path, re.I)
    ):
        raise ExternalDataError("AlphaFold model URL did not match the approved official file path.")
    return get_text(parsed.geturl())


def fetch_alphafold_pae_payload(pae_url: str) -> list[Any]:
    """Fetch AlphaFold PAE JSON only from an official versioned file path."""
    parsed = urlparse(str(pae_url or ""))
    if (
        parsed.scheme != "https"
        or parsed.hostname != "alphafold.ebi.ac.uk"
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(
            r"/files/AF-[A-Z0-9-]+-F1-predicted_aligned_error_v\d+\.json",
            parsed.path,
            re.I,
        )
    ):
        raise ExternalDataError("AlphaFold PAE URL did not match the approved official file path.")
    return get_json_array(parsed.geturl())


def normalize_uniprot_accession(accession: str) -> str:
    cleaned = str(accession or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{6,10}(?:-\d+)?", cleaned):
        raise ExternalDataError("UniProt accession must be a 6-10 character accession, optionally with an isoform suffix.")
    return cleaned


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
