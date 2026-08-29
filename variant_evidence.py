"""Researcher-approved human variant evidence review across public sources."""

from __future__ import annotations

import csv
import json
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from bio_clients import ExternalDataError, get_json, get_json_array, post_json
from workspace_utils import WORKSPACE_ROOT


CLINVAR_SEARCH = "https://clinicaltables.nlm.nih.gov/api/variants/v4/search"
CLINVAR_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
CLINVAR_SITE = "https://www.ncbi.nlm.nih.gov/clinvar/variation"
ENSEMBL_VEP = "https://rest.ensembl.org/vep/human/hgvs"
GNOMAD_API = "https://gnomad.broadinstitute.org/api"
GNOMAD_SITE = "https://gnomad.broadinstitute.org/variant"
MAX_QUERY_CHARS = 160
MAX_TRANSCRIPTS = 12
MAX_TRAITS = 24

CLINVAR_FIELD_KEYS = {
    "VariationID": "variation_id",
    "Name": "name",
    "GeneSymbol": "gene_symbol",
    "HGVS_c": "hgvs_c",
    "HGVS_p": "hgvs_p",
    "HGVS_exprs": "hgvs_exprs",
    "dbSNP": "db_snp",
    "Chromosome": "chromosome",
    "Start": "start",
    "Stop": "stop",
    "Type": "type",
}

GNOMAD_QUERY = """
query Variant($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id
    rsid
    ref
    alt
    joint {
      ac
      an
      homozygote_count
      filters
      populations { id ac an homozygote_count }
    }
  }
}
"""

POPULATION_LABELS = {
    "afr": "African/African American",
    "ami": "Amish",
    "amr": "Admixed American",
    "asj": "Ashkenazi Jewish",
    "eas": "East Asian",
    "fin": "Finnish",
    "mid": "Middle Eastern",
    "nfe": "Non-Finnish European",
    "remaining": "Remaining individuals",
    "sas": "South Asian",
}


class VariantEvidenceError(ValueError):
    """Raised when a variant cannot be resolved or reviewed safely."""


def normalize_variant_query(query: str) -> str:
    cleaned = re.sub(r"\s+", "", str(query or "")).strip()
    if not cleaned or len(cleaned) > MAX_QUERY_CHARS:
        raise VariantEvidenceError(
            f"Variant identifier must contain between 1 and {MAX_QUERY_CHARS} characters."
        )
    if any(ord(char) < 32 for char in cleaned):
        raise VariantEvidenceError("Variant identifier contains unsupported control characters.")
    if re.fullmatch(r"rs\d{1,12}", cleaned, re.I):
        return cleaned.lower()
    if re.fullmatch(r"VCV\d{1,12}(?:\.\d+)?", cleaned, re.I):
        return cleaned.upper()
    if re.fullmatch(r"\d{1,12}", cleaned):
        return cleaned
    if re.fullmatch(
        r"N[CMPRG]_[0-9]+(?:\.[0-9]+)?(?:\([A-Za-z0-9_.-]+\))?:[cgmnpr]\.\S{1,100}",
        cleaned,
        re.I,
    ):
        return cleaned
    raise VariantEvidenceError(
        "Use an exact RefSeq HGVS expression, rsID, ClinVar Variation ID, or VCV accession."
    )


def preflight_variant_evidence(query: str) -> dict[str, Any]:
    variant = resolve_variant(query)
    return {
        "ready": True,
        "query": variant["query"],
        "source": "ClinVar",
        "source_url": variant["clinvar_url"],
        "variant": variant,
        "warnings": [
            "Review the normalized allele, transcript, and assembly before approval.",
            "ClinVar assertions are submitted interpretations and are not a diagnosis or a new ACMG/AMP classification.",
        ],
        "summary": (
            f"Resolved {variant['query']} to ClinVar {variant['accession']} "
            f"({variant['title']})."
        ),
    }


def review_variant_evidence(query: str) -> dict[str, Any]:
    variant = resolve_variant(query)
    vep = fetch_vep_evidence(variant)
    gnomad = fetch_gnomad_evidence(variant)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    sources = [
        {"name": "ClinVar", "url": variant["clinvar_url"]},
        {"name": "Ensembl VEP", "url": vep["source_url"]},
    ]
    if gnomad.get("source_url"):
        sources.append({"name": "gnomAD v4", "url": gnomad["source_url"]})
    result = {
        "analysis_id": f"variant-review-{uuid.uuid4().hex[:12]}",
        "method": "ClinVar, Ensembl VEP, and gnomAD evidence review",
        "retrieved_at": retrieved_at,
        "query": variant["query"],
        "sources": sources,
        "variant": variant,
        "vep": vep,
        "gnomad": gnomad,
        "outputs": {},
        "caveats": [
            "This report organizes public evidence; it is not a diagnosis, clinical recommendation, or de novo ACMG/AMP classification.",
            "ClinVar classifications are submitted assertions that may conflict or change; review status, condition scope, and current source records matter.",
            "Ensembl VEP consequence terms and SIFT/PolyPhen outputs are computational annotations, not independent proof of pathogenicity.",
            "gnomAD frequencies depend on ancestry, coverage, representation, and quality filters; rarity or absence alone does not establish pathogenicity.",
            "Interpretation is allele-, transcript-, assembly-, phenotype-, and inheritance-specific; confirm all five before clinical or experimental use.",
        ],
    }
    classification = variant.get("germline_classification") or {}
    consequence = vep.get("most_severe_consequence") or "unresolved consequence"
    frequency = gnomad.get("allele_frequency")
    frequency_text = f"{frequency:.6g}" if isinstance(frequency, (int, float)) else "not returned"
    result["summary"] = (
        f"ClinVar reports {classification.get('description') or 'no germline aggregate classification'} "
        f"with review status '{classification.get('review_status') or 'not provided'}'; "
        f"VEP reports {consequence}; gnomAD v4 joint AF is {frequency_text}."
    )
    _persist_review(result)
    return result


def resolve_variant(query: str) -> dict[str, Any]:
    normalized = normalize_variant_query(query)
    variation_id: str
    candidate: dict[str, Any] = {}
    if re.fullmatch(r"\d{1,12}", normalized):
        variation_id = normalized.lstrip("0") or "0"
    elif normalized.upper().startswith("VCV"):
        variation_id = str(int(re.match(r"VCV(\d+)", normalized, re.I).group(1)))
    else:
        candidates = _search_clinvar(normalized)
        exact = [item for item in candidates if _candidate_matches(normalized, item)]
        if not exact:
            raise VariantEvidenceError(
                "ClinVar did not return an exact simple-variant match. Use a versioned RefSeq HGVS expression or ClinVar Variation ID."
            )
        unique = {str(item["variation_id"]): item for item in exact}
        if len(unique) > 1:
            suggestions = [
                str(item.get("hgvs_c") or item.get("hgvs_p") or item.get("name") or item["variation_id"])
                for item in list(unique.values())[:5]
            ]
            raise VariantEvidenceError(
                "Variant identifier is allele-ambiguous in ClinVar; use one exact HGVS expression: "
                + ", ".join(suggestions)
            )
        candidate = next(iter(unique.values()))
        variation_id = str(candidate["variation_id"])
    payload = _clinvar_summary(variation_id)
    return parse_clinvar_summary(payload, normalized, variation_id, candidate)


def parse_clinvar_summary(
    payload: dict[str, Any],
    query: str,
    variation_id: str,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = payload.get("result")
    if not isinstance(result, dict):
        raise VariantEvidenceError("ClinVar returned an unexpected summary response.")
    record = result.get(str(variation_id))
    if not isinstance(record, dict):
        raise VariantEvidenceError(f"ClinVar Variation ID was not found: {variation_id}")
    if str(record.get("obj_type") or "").casefold() == "haplotype":
        raise VariantEvidenceError("Haplotype records are not supported by this single-variant workflow.")
    variation_set = [item for item in record.get("variation_set") or [] if isinstance(item, dict)]
    if len(variation_set) != 1:
        raise VariantEvidenceError("ClinVar record does not resolve to one simple allele.")
    allele = variation_set[0]
    candidate = dict(candidate or {})
    title = str(record.get("title") or allele.get("variation_name") or "")
    hgvs_c = str(candidate.get("hgvs_c") or _extract_hgvs(title, "c") or "")
    hgvs_p = str(candidate.get("hgvs_p") or _extract_hgvs(title, "p") or "")
    locations = _locations(allele.get("variation_loc") or [])
    genes = _genes(record.get("genes") or [])
    germline = _classification(record.get("germline_classification") or {})
    clinical_impact = _classification(record.get("clinical_impact_classification") or {})
    oncogenicity = _classification(record.get("oncogenicity_classification") or {})
    accession = str(record.get("accession_version") or record.get("accession") or f"VCV{int(variation_id):09d}")
    canonical_spdi = str(allele.get("canonical_spdi") or "")
    gnomad_variant_id = _gnomad_variant_id(canonical_spdi, locations)
    dbsnp_ids = []
    cross_references = []
    for item in allele.get("variation_xrefs") or []:
        if not isinstance(item, dict):
            continue
        source = str(item.get("db_source") or "")
        identifier = str(item.get("db_id") or "")
        if not source or not identifier:
            continue
        cross_references.append({"source": source, "id": identifier})
        if source == "dbSNP":
            dbsnp_ids.append(f"rs{identifier}")
    supporting = record.get("supporting_submissions") or {}
    clinvar_url = f"{CLINVAR_SITE}/{variation_id}/"
    return {
        "query": query,
        "variation_id": variation_id,
        "accession": accession,
        "title": title,
        "object_type": str(record.get("obj_type") or allele.get("variant_type") or ""),
        "variant_type": str(allele.get("variant_type") or record.get("obj_type") or ""),
        "genes": genes,
        "gene_symbols": [item["symbol"] for item in genes],
        "hgvs_c": hgvs_c or None,
        "hgvs_p": hgvs_p or None,
        "protein_change": str(record.get("protein_change") or "") or None,
        "aliases": [str(item) for item in allele.get("aliases") or []][:12],
        "dbsnp_ids": list(dict.fromkeys(dbsnp_ids)),
        "molecular_consequences": [
            str(item) for item in record.get("molecular_consequence_list") or [] if str(item)
        ],
        "locations": locations,
        "canonical_spdi": canonical_spdi or None,
        "gnomad_variant_id": gnomad_variant_id,
        "germline_classification": germline,
        "clinical_impact_classification": clinical_impact,
        "oncogenicity_classification": oncogenicity,
        "supporting_submission_counts": {
            "scv": len(supporting.get("scv") or []),
            "rcv": len(supporting.get("rcv") or []),
        },
        "frequency_context": _frequency_context(allele.get("allele_freq_set") or []),
        "cross_references": cross_references[:40],
        "clinvar_url": clinvar_url,
    }


def fetch_vep_evidence(variant: dict[str, Any]) -> dict[str, Any]:
    hgvs = str(variant.get("hgvs_c") or "")
    if not hgvs:
        raise VariantEvidenceError("ClinVar record has no exact RefSeq coding HGVS expression for VEP.")
    parameters = {
        "canonical": 1,
        "mane": 1,
        "hgvs": 1,
        "variant_class": 1,
    }
    url = f"{ENSEMBL_VEP}/{quote(hgvs, safe='')}?{urlencode(parameters)}"
    try:
        payload = get_json_array(url)
    except ExternalDataError as exc:
        raise VariantEvidenceError(str(exc)) from exc
    if not payload or not isinstance(payload[0], dict):
        raise VariantEvidenceError("Ensembl VEP returned no consequence annotation.")
    record = payload[0]
    transcripts = _transcript_consequences(record.get("transcript_consequences") or [])
    colocated = [item for item in record.get("colocated_variants") or [] if isinstance(item, dict)]
    colocated_ids = [str(item.get("id")) for item in colocated if item.get("id")]
    return {
        "source": "Ensembl VEP",
        "source_url": url,
        "input": str(record.get("input") or hgvs),
        "assembly": str(record.get("assembly_name") or ""),
        "location": {
            "chromosome": str(record.get("seq_region_name") or ""),
            "start": _integer(record.get("start")),
            "end": _integer(record.get("end")),
            "allele_string": str(record.get("allele_string") or ""),
            "strand": _integer(record.get("strand")),
        },
        "variant_class": str(record.get("variant_class") or ""),
        "most_severe_consequence": str(record.get("most_severe_consequence") or ""),
        "transcript_count": len(record.get("transcript_consequences") or []),
        "transcripts": transcripts,
        "colocated_ids": list(dict.fromkeys(colocated_ids))[:20],
    }


def fetch_gnomad_evidence(variant: dict[str, Any]) -> dict[str, Any]:
    variant_id = str(variant.get("gnomad_variant_id") or "")
    if not variant_id:
        return {
            "available": False,
            "dataset": "gnomAD v4",
            "reason": "The ClinVar record could not be mapped to a simple GRCh38 gnomAD variant ID.",
        }
    try:
        payload = post_json(
            GNOMAD_API,
            {"query": GNOMAD_QUERY, "variables": {"variantId": variant_id, "dataset": "gnomad_r4"}},
        )
    except ExternalDataError as exc:
        return {"available": False, "dataset": "gnomAD v4", "reason": str(exc)}
    errors = payload.get("errors") or []
    if errors:
        message = str((errors[0] or {}).get("message") or "gnomAD GraphQL query failed.")
        return {"available": False, "dataset": "gnomAD v4", "reason": message[:240]}
    raw = ((payload.get("data") or {}).get("variant"))
    if not isinstance(raw, dict):
        return {
            "available": False,
            "dataset": "gnomAD v4",
            "variant_id": variant_id,
            "source_url": f"{GNOMAD_SITE}/{quote(variant_id, safe='-')}?dataset=gnomad_r4",
            "reason": "Variant was not returned by the gnomAD v4 browser API.",
        }
    joint = raw.get("joint") or {}
    ac = _integer(joint.get("ac"))
    an = _integer(joint.get("an"))
    populations = []
    for item in joint.get("populations") or []:
        if not isinstance(item, dict):
            continue
        identifier = str(item.get("id") or "")
        if identifier not in POPULATION_LABELS:
            continue
        population_an = _integer(item.get("an"))
        population_ac = _integer(item.get("ac"))
        populations.append(
            {
                "id": identifier,
                "label": POPULATION_LABELS[identifier],
                "ac": population_ac,
                "an": population_an,
                "allele_frequency": _frequency(population_ac, population_an),
                "homozygote_count": _integer(item.get("homozygote_count")),
            }
        )
    populations.sort(key=lambda item: (-item["allele_frequency"], item["id"]))
    source_url = f"{GNOMAD_SITE}/{quote(str(raw.get('variant_id') or variant_id), safe='-')}?dataset=gnomad_r4"
    return {
        "available": True,
        "source": "gnomAD",
        "source_url": source_url,
        "dataset": "gnomAD v4 joint",
        "variant_id": str(raw.get("variant_id") or variant_id),
        "rsid": str(raw.get("rsid") or "") or None,
        "ref": str(raw.get("ref") or ""),
        "alt": str(raw.get("alt") or ""),
        "ac": ac,
        "an": an,
        "allele_frequency": _frequency(ac, an),
        "homozygote_count": _integer(joint.get("homozygote_count")),
        "filters": [str(item) for item in joint.get("filters") or []],
        "populations": populations,
    }


def _search_clinvar(query: str) -> list[dict[str, Any]]:
    fields = [
        "VariationID",
        "Name",
        "GeneSymbol",
        "HGVS_c",
        "HGVS_p",
        "HGVS_exprs",
        "dbSNP",
        "Chromosome",
        "Start",
        "Stop",
        "Type",
    ]
    url = f"{CLINVAR_SEARCH}?{urlencode({'terms': query, 'count': 20, 'ef': ','.join(fields)})}"
    try:
        payload = get_json_array(url)
    except ExternalDataError as exc:
        raise VariantEvidenceError(str(exc)) from exc
    if len(payload) < 4 or not isinstance(payload[1], list) or not isinstance(payload[2], dict):
        raise VariantEvidenceError("ClinVar search returned an unexpected response shape.")
    codes = payload[1]
    extras = payload[2]
    candidates = []
    for index, code in enumerate(codes):
        candidate = {"variation_id": str(code)}
        for field in fields:
            values = extras.get(field) or []
            candidate[CLINVAR_FIELD_KEYS[field]] = values[index] if index < len(values) else None
        candidates.append(candidate)
    return candidates


def _candidate_matches(query: str, candidate: dict[str, Any]) -> bool:
    normalized = _canonical_hgvs(query).casefold()
    if query.lower().startswith("rs"):
        return str(candidate.get("db_snp") or "").casefold() == query.casefold()
    expressions = [candidate.get("hgvs_c"), candidate.get("hgvs_p")]
    raw_expressions = candidate.get("hgvs_exprs")
    if isinstance(raw_expressions, list):
        expressions.extend(raw_expressions)
    elif raw_expressions:
        expressions.extend(re.split(r"[|~]", str(raw_expressions)))
    return any(_canonical_hgvs(str(value or "")).casefold() == normalized for value in expressions)


def _clinvar_summary(variation_id: str) -> dict[str, Any]:
    url = f"{CLINVAR_SUMMARY}?{urlencode({'db': 'clinvar', 'id': variation_id, 'retmode': 'json'})}"
    try:
        return get_json(url)
    except ExternalDataError as exc:
        raise VariantEvidenceError(str(exc)) from exc


def _classification(raw: dict[str, Any]) -> dict[str, Any]:
    description = str(raw.get("description") or "").strip()
    if not description:
        return {}
    traits = []
    seen = set()
    for item in raw.get("trait_set") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("trait_name") or "").strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        traits.append(
            {
                "name": name,
                "cross_references": [
                    {"source": str(xref.get("db_source") or ""), "id": str(xref.get("db_id") or "")}
                    for xref in item.get("trait_xrefs") or []
                    if isinstance(xref, dict) and xref.get("db_source") and xref.get("db_id")
                ],
            }
        )
        if len(traits) >= MAX_TRAITS:
            break
    return {
        "description": description,
        "review_status": str(raw.get("review_status") or ""),
        "last_evaluated": _clean_date(raw.get("last_evaluated")),
        "traits": traits,
    }


def _locations(rows: list[Any]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("assembly_name"):
            continue
        result.append(
            {
                "assembly": str(row.get("assembly_name") or ""),
                "chromosome": str(row.get("chr") or ""),
                "start": _integer(row.get("start")),
                "stop": _integer(row.get("stop")),
                "cytoband": str(row.get("band") or ""),
                "status": str(row.get("status") or ""),
                "assembly_accession": str(row.get("assembly_acc_ver") or ""),
            }
        )
    return result


def _genes(rows: list[Any]) -> list[dict[str, str]]:
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip()
        gene_id = str(row.get("geneid") or "").strip()
        key = (symbol, gene_id)
        if not symbol or key in seen:
            continue
        seen.add(key)
        result.append({"symbol": symbol, "gene_id": gene_id})
    return result[:12]


def _frequency_context(rows: list[Any]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("source"):
            continue
        try:
            value = float(row.get("value"))
        except (TypeError, ValueError):
            continue
        result.append(
            {
                "source": str(row.get("source")),
                "value": value,
                "minor_allele": str(row.get("minor_allele") or "") or None,
            }
        )
    return result[:12]


def _transcript_consequences(rows: list[Any]) -> list[dict[str, Any]]:
    normalized = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("transcript_id"):
            continue
        normalized.append(
            {
                "transcript_id": str(row.get("transcript_id") or ""),
                "gene_symbol": str(row.get("gene_symbol") or ""),
                "gene_id": str(row.get("gene_id") or ""),
                "biotype": str(row.get("biotype") or ""),
                "consequences": [str(item) for item in row.get("consequence_terms") or []],
                "impact": str(row.get("impact") or ""),
                "canonical": bool(row.get("canonical")),
                "mane_select": str(row.get("mane_select") or "") or None,
                "hgvsc": str(row.get("hgvsc") or "") or None,
                "hgvsp": str(row.get("hgvsp") or "") or None,
                "protein_position": _integer(row.get("protein_start")) or None,
                "amino_acids": str(row.get("amino_acids") or "") or None,
                "codons": str(row.get("codons") or "") or None,
                "sift": _prediction(row, "sift"),
                "polyphen": _prediction(row, "polyphen"),
            }
        )
    impact_rank = {"HIGH": 0, "MODERATE": 1, "LOW": 2, "MODIFIER": 3}
    normalized.sort(
        key=lambda item: (
            0 if item["mane_select"] else 1,
            impact_rank.get(item["impact"], 4),
            0 if item["canonical"] else 1,
            0 if item["gene_symbol"] else 1,
            item["transcript_id"],
        )
    )
    return normalized[:MAX_TRANSCRIPTS]


def _prediction(row: dict[str, Any], prefix: str) -> dict[str, Any] | None:
    label = str(row.get(f"{prefix}_prediction") or "").strip()
    score = row.get(f"{prefix}_score")
    if not label and score is None:
        return None
    return {"prediction": label or None, "score": _number_or_none(score)}


def _gnomad_variant_id(spdi: str, locations: list[dict[str, Any]]) -> str | None:
    match = re.fullmatch(r"[^:]+:(\d+):([ACGT]+):([ACGT]+)", spdi, re.I)
    current = next((item for item in locations if item.get("assembly") == "GRCh38"), None)
    if not match or not current or not current.get("chromosome"):
        return None
    position = int(match.group(1)) + 1
    if position != int(current.get("start") or 0):
        return None
    return f"{current['chromosome']}-{position}-{match.group(2).upper()}-{match.group(3).upper()}"


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "evidence_table": f"{relative_root}/variant_evidence.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="variant-review-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_evidence_table(output / "variant_evidence.tsv", result)
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "retrieved_at": result["retrieved_at"],
            "query": result["query"],
            "clinvar_variation_id": result["variant"]["variation_id"],
            "clinvar_accession": result["variant"]["accession"],
            "gnomad_variant_id": result["variant"].get("gnomad_variant_id"),
            "sources": result["sources"],
            "files": ["variant_evidence.tsv", "report.json", "run_manifest.json", "summary.md"],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise VariantEvidenceError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_evidence_table(path: Path, result: dict[str, Any]) -> None:
    rows = []
    variant = result["variant"]
    germline = variant.get("germline_classification") or {}
    rows.extend(
        [
            {
                "source": "ClinVar",
                "evidence_type": "aggregate classification",
                "label": germline.get("description") or "not provided",
                "value": germline.get("review_status") or "not provided",
                "context": "; ".join(item["name"] for item in germline.get("traits") or []),
                "url": variant["clinvar_url"],
            },
            {
                "source": "ClinVar",
                "evidence_type": "allele identity",
                "label": variant.get("hgvs_c") or variant["accession"],
                "value": variant.get("hgvs_p") or "",
                "context": variant.get("canonical_spdi") or "",
                "url": variant["clinvar_url"],
            },
        ]
    )
    for transcript in result["vep"].get("transcripts") or []:
        rows.append(
            {
                "source": "Ensembl VEP",
                "evidence_type": "transcript consequence",
                "label": transcript["transcript_id"],
                "value": "; ".join(transcript["consequences"]),
                "context": "; ".join(
                    value
                    for value in [transcript.get("hgvsc"), transcript.get("hgvsp"), transcript.get("impact")]
                    if value
                ),
                "url": result["vep"]["source_url"],
            }
        )
    gnomad = result.get("gnomad") or {}
    if gnomad.get("available"):
        rows.append(
            {
                "source": "gnomAD",
                "evidence_type": "joint allele frequency",
                "label": gnomad["variant_id"],
                "value": gnomad["allele_frequency"],
                "context": f"AC {gnomad['ac']}; AN {gnomad['an']}; homozygotes {gnomad['homozygote_count']}",
                "url": gnomad["source_url"],
            }
        )
        for population in gnomad.get("populations") or []:
            rows.append(
                {
                    "source": "gnomAD",
                    "evidence_type": "population allele frequency",
                    "label": population["label"],
                    "value": population["allele_frequency"],
                    "context": f"AC {population['ac']}; AN {population['an']}; homozygotes {population['homozygote_count']}",
                    "url": gnomad["source_url"],
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source", "evidence_type", "label", "value", "context", "url"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)


def _summary_markdown(result: dict[str, Any]) -> str:
    variant = result["variant"]
    classification = variant.get("germline_classification") or {}
    lines = [
        "# Variant evidence review",
        "",
        f"Query: `{result['query']}`",
        "",
        f"ClinVar: [{variant['accession']}]({variant['clinvar_url']})",
        f"Normalized allele: `{variant.get('hgvs_c') or variant.get('canonical_spdi') or 'not available'}`",
        f"Aggregate germline classification: **{classification.get('description') or 'not provided'}**",
        f"Review status: {classification.get('review_status') or 'not provided'}",
        f"Most severe VEP consequence: {result['vep'].get('most_severe_consequence') or 'not returned'}",
        "",
        "## Population frequency",
        "",
    ]
    gnomad = result.get("gnomad") or {}
    if gnomad.get("available"):
        lines.append(
            f"gnomAD v4 joint AF: {gnomad['allele_frequency']:.6g} "
            f"(AC {gnomad['ac']}, AN {gnomad['an']}, homozygotes {gnomad['homozygote_count']})."
        )
    else:
        lines.append(f"gnomAD v4: {gnomad.get('reason') or 'not available'}")
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _extract_hgvs(title: str, kind: str) -> str:
    match = re.search(
        rf"(N[CMPRG]_[0-9]+(?:\.[0-9]+)?)(?:\([^)]+\))?:({kind}\.[^ )]+)",
        title,
        re.I,
    )
    return f"{match.group(1)}:{match.group(2)}" if match else ""


def _canonical_hgvs(value: str) -> str:
    return re.sub(r"(N[CMPRG]_[0-9]+(?:\.[0-9]+)?)\([^)]+\):", r"\1:", value, flags=re.I)


def _clean_date(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text or text.startswith("1/01/01"):
        return None
    return text.split(" ", 1)[0]


def _frequency(ac: int, an: int) -> float:
    return ac / an if an > 0 else 0.0


def _number_or_none(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
