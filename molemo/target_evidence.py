"""Bounded Open Targets evidence review for researcher-approved target comparison."""

from __future__ import annotations

import csv
import json
import re
import shutil
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .bio_clients import ExternalDataError, post_json
from .workspace_utils import WORKSPACE_ROOT


GRAPHQL_URL = "https://api.platform.opentargets.org/api/v4/graphql"
PLATFORM_URL = "https://platform.opentargets.org"
MAX_TARGETS = 8
ENTITY_ID = re.compile(r"^[A-Za-z][A-Za-z0-9]*_\d+$")
TARGET_TERM = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")

DATA_TYPE_LABELS = {
    "genetic_association": "Genetics",
    "clinical": "Clinical",
    "literature": "Literature",
    "rna_expression": "RNA expression",
    "animal_model": "Animal models",
    "somatic_mutation": "Somatic mutation",
    "affected_pathway": "Affected pathways",
    "known_drug": "Known drugs",
}

DISEASE_ALIASES = {
    "哮喘": "asthma",
    "乳腺癌": "breast cancer",
    "肺癌": "lung cancer",
    "阿尔茨海默病": "Alzheimer disease",
    "类风湿关节炎": "rheumatoid arthritis",
    "克罗恩病": "Crohn disease",
    "溃疡性结肠炎": "ulcerative colitis",
    "2型糖尿病": "type 2 diabetes mellitus",
    "二型糖尿病": "type 2 diabetes mellitus",
}

RESOLVE_TARGETS_QUERY = """
query ResolveTargets($terms: [String!]!) {
  mapIds(queryTerms: $terms, entityNames: ["target"]) {
    mappings { term hits { id name entity } }
  }
}
"""

SEARCH_DISEASE_QUERY = """
query SearchDisease($query: String!) {
  search(queryString: $query, entityNames: ["disease"], page: {index: 0, size: 5}) {
    total
    hits { id name entity description }
  }
}
"""

GET_DISEASE_QUERY = """
query GetDisease($id: String!) {
  disease(efoId: $id) { id name description }
}
"""

REVIEW_QUERY = """
query ReviewTargets($disease: String!, $targets: [String!]!, $indirect: Boolean!) {
  disease(efoId: $disease) {
    id
    name
    description
    associatedTargets(Bs: $targets, enableIndirect: $indirect, page: {index: 0, size: 20}) {
      count
      rows {
        score
        novelty
        target { id approvedSymbol approvedName biotype }
        datatypeScores { id score }
        datasourceScores { id score }
      }
    }
    clinical: evidences(
      ensemblIds: $targets
      enableIndirect: $indirect
      datasourceIds: ["clinical_precedence"]
      size: 100
    ) {
      count
      rows {
        id
        target { id approvedSymbol }
        datasourceId
        datatypeId
        score
        literature
        publicationYear
        drug { id name maximumClinicalStage drugType }
        directionOnTarget
        directionOnTrait
      }
    }
    literature: evidences(
      ensemblIds: $targets
      enableIndirect: $indirect
      datasourceIds: ["europepmc"]
      size: 32
    ) {
      count
      rows {
        id
        target { id approvedSymbol }
        datasourceId
        datatypeId
        score
        literature
        publicationYear
      }
    }
  }
  targets(ensemblIds: $targets) {
    id
    approvedSymbol
    approvedName
    biotype
    tractability { label modality value }
    pathways { pathwayId pathway }
    safetyLiabilities { event datasource url literature }
  }
}
"""


class TargetEvidenceError(ValueError):
    """Raised when target evidence inputs or Open Targets results are invalid."""


def parse_target_terms(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        raw_terms = [str(item).strip() for item in value]
    else:
        text = str(value or "").strip()
        raw_terms = re.split(r"[,;，、\n\r\t]+", text)
        if len(raw_terms) == 1 and " " in text:
            raw_terms = text.split()
    terms = [term.strip() for term in raw_terms if term.strip()]
    if not terms:
        raise TargetEvidenceError("At least one candidate target is required.")
    if len(terms) > MAX_TARGETS:
        raise TargetEvidenceError(f"Target reviews are limited to {MAX_TARGETS} candidates.")
    for term in terms:
        if not TARGET_TERM.fullmatch(term):
            raise TargetEvidenceError(f"Unsupported target identifier: {term}")
    lowered = [term.casefold() for term in terms]
    if len(lowered) != len(set(lowered)):
        raise TargetEvidenceError("Candidate target terms must be unique.")
    return terms


def resolve_target_review_inputs(
    disease: str,
    candidates: str | list[str],
    include_indirect: bool = False,
) -> dict[str, Any]:
    disease_query = str(disease or "").strip()
    if not disease_query or len(disease_query) > 120:
        raise TargetEvidenceError("Disease must contain between 1 and 120 characters.")
    terms = parse_target_terms(candidates)
    resolved_disease = _resolve_disease(disease_query)
    resolved_targets = _resolve_targets(terms)
    warnings = [
        "Open Targets association scores rank evidence strength; they are not probabilities, confidence values, or proof of causality."
    ]
    if include_indirect:
        warnings.append("Indirect mode includes ontology descendants and can broaden the disease evidence context.")
    return {
        "ready": True,
        "source": "Open Targets Platform",
        "source_url": "https://platform.opentargets.org/",
        "disease": resolved_disease,
        "targets": resolved_targets,
        "include_indirect": bool(include_indirect),
        "warnings": warnings,
        "summary": (
            f"Resolved {resolved_disease['name']} ({resolved_disease['id']}) and "
            f"{len(resolved_targets)} candidate target{'s' if len(resolved_targets) != 1 else ''}."
        ),
    }


def review_target_evidence(
    disease: str,
    candidates: str | list[str],
    include_indirect: bool = False,
) -> dict[str, Any]:
    resolved = resolve_target_review_inputs(disease, candidates, include_indirect)
    target_ids = [item["id"] for item in resolved["targets"]]
    payload = _graphql(
        REVIEW_QUERY,
        {
            "disease": resolved["disease"]["id"],
            "targets": target_ids,
            "indirect": bool(include_indirect),
        },
    )
    result = parse_target_review_payload(payload, resolved)
    _persist_review(result)
    return result


def parse_target_review_payload(payload: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    disease_payload = payload.get("disease")
    if not isinstance(disease_payload, dict):
        raise TargetEvidenceError("Open Targets returned no disease evidence record.")

    annotations = {
        str(item.get("id")): item
        for item in payload.get("targets") or []
        if isinstance(item, dict) and item.get("id")
    }
    association_rows = (((disease_payload.get("associatedTargets") or {}).get("rows")) or [])
    associations = {
        str((row.get("target") or {}).get("id")): row
        for row in association_rows
        if isinstance(row, dict) and (row.get("target") or {}).get("id")
    }
    clinical_by_target = _group_evidence(((disease_payload.get("clinical") or {}).get("rows")) or [])
    literature_by_target = _group_evidence(((disease_payload.get("literature") or {}).get("rows")) or [])

    candidates = []
    all_data_types: set[str] = set()
    for resolved_target in resolved.get("targets") or []:
        target_id = str(resolved_target["id"])
        annotation = annotations.get(target_id) or {}
        association = associations.get(target_id) or {}
        data_types = _score_rows(association.get("datatypeScores") or [], DATA_TYPE_LABELS)
        data_sources = _score_rows(association.get("datasourceScores") or [], {})
        all_data_types.update(item["id"] for item in data_types)
        clinical_rows = clinical_by_target.get(target_id, [])
        literature_rows = literature_by_target.get(target_id, [])
        drugs = _clinical_drugs(clinical_rows)
        publications = _publication_ids([*clinical_rows, *literature_rows])
        tractability = _tractability(annotation.get("tractability") or [])
        pathways = _pathways(annotation.get("pathways") or [])
        safety = _safety_liabilities(annotation.get("safetyLiabilities") or [])
        candidates.append(
            {
                "rank": 0,
                "id": target_id,
                "query": resolved_target.get("query"),
                "symbol": annotation.get("approvedSymbol") or resolved_target.get("symbol") or target_id,
                "name": annotation.get("approvedName") or resolved_target.get("name") or target_id,
                "biotype": annotation.get("biotype"),
                "association_score": _number(association.get("score")),
                "novelty_score": _number(association.get("novelty")),
                "datatype_scores": data_types,
                "datatype_score_map": {item["id"]: item["score"] for item in data_types},
                "datasource_scores": data_sources[:12],
                "tractability": tractability,
                "pathways": pathways,
                "safety_liabilities": safety,
                "drugs": drugs,
                "publications": publications,
                "target_url": f"{PLATFORM_URL}/target/{target_id}",
            }
        )

    candidates.sort(key=lambda item: (-item["association_score"], str(item["symbol"])))
    for index, candidate in enumerate(candidates, 1):
        candidate["rank"] = index
    evidence_lanes = [
        {"id": lane, "label": DATA_TYPE_LABELS.get(lane, _humanize(lane))}
        for lane in DATA_TYPE_LABELS
        if lane in all_data_types
    ]
    remaining_lanes = sorted(all_data_types - set(DATA_TYPE_LABELS))
    evidence_lanes.extend({"id": lane, "label": _humanize(lane)} for lane in remaining_lanes)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    disease = dict(resolved["disease"])
    disease.update(
        {
            "name": disease_payload.get("name") or disease["name"],
            "description": disease_payload.get("description") or disease.get("description"),
        }
    )
    result = {
        "analysis_id": f"target-review-{uuid.uuid4().hex[:12]}",
        "method": "Open Targets Platform association evidence",
        "source": "Open Targets Platform",
        "source_url": "https://platform.opentargets.org/",
        "retrieved_at": retrieved_at,
        "disease": disease,
        "include_indirect": bool(resolved.get("include_indirect")),
        "evidence_lanes": evidence_lanes,
        "candidates": candidates,
        "caveats": [
            "Association score is a ranking signal, not a probability, confidence estimate, or proof of causality.",
            "Scores depend on available public evidence and can disadvantage under-studied targets or diseases.",
            "Clinical and tractability annotations describe existing evidence; they do not establish efficacy or safety for a new program.",
            "Displayed publication and clinical-evidence rows are bounded samples; use the source links for exhaustive review.",
        ],
        "outputs": {},
    }
    result["summary"] = (
        f"Reviewed {len(candidates)} targets for {disease['name']}; "
        f"{candidates[0]['symbol']} has the highest Open Targets association score "
        f"({candidates[0]['association_score']:.3f})."
        if candidates
        else f"No candidate targets were returned for {disease['name']}."
    )
    return result


def _resolve_disease(query: str) -> dict[str, Any]:
    if ENTITY_ID.fullmatch(query):
        data = _graphql(GET_DISEASE_QUERY, {"id": query.upper()})
        record = data.get("disease")
        if not isinstance(record, dict):
            raise TargetEvidenceError(f"Disease identifier was not found: {query}")
    else:
        search_query = DISEASE_ALIASES.get(query, query)
        data = _graphql(SEARCH_DISEASE_QUERY, {"query": search_query})
        hits = ((data.get("search") or {}).get("hits")) or []
        hits = [hit for hit in hits if isinstance(hit, dict) and hit.get("id") and hit.get("name")]
        if not hits:
            raise TargetEvidenceError(f"Disease could not be resolved: {query}")
        record = next(
            (hit for hit in hits if str(hit["name"]).casefold() == search_query.casefold()),
            hits[0],
        )
    disease_id = str(record["id"])
    return {
        "query": query,
        "id": disease_id,
        "name": str(record.get("name") or disease_id),
        "description": str(record.get("description") or ""),
        "url": f"{PLATFORM_URL}/disease/{disease_id}/associations",
    }


def _resolve_targets(terms: list[str]) -> list[dict[str, Any]]:
    data = _graphql(RESOLVE_TARGETS_QUERY, {"terms": terms})
    mappings = ((data.get("mapIds") or {}).get("mappings")) or []
    by_term = {str(item.get("term") or "").casefold(): item for item in mappings if isinstance(item, dict)}
    resolved = []
    seen = set()
    for term in terms:
        mapping = by_term.get(term.casefold()) or {}
        hits = [hit for hit in mapping.get("hits") or [] if isinstance(hit, dict) and hit.get("id")]
        if not hits:
            raise TargetEvidenceError(f"Target could not be resolved: {term}")
        hit = next(
            (
                candidate
                for candidate in hits
                if str(candidate.get("id") or "").casefold() == term.casefold()
                or str(candidate.get("name") or "").casefold() == term.casefold()
            ),
            hits[0],
        )
        target_id = str(hit["id"])
        if target_id in seen:
            raise TargetEvidenceError(f"Multiple candidate terms resolve to {target_id}.")
        seen.add(target_id)
        symbol = str(hit.get("name") or target_id)
        resolved.append(
            {
                "query": term,
                "id": target_id,
                "symbol": symbol,
                "name": symbol,
                "url": f"{PLATFORM_URL}/target/{target_id}",
            }
        )
    return resolved


def _graphql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = post_json(GRAPHQL_URL, {"query": query, "variables": variables})
    except ExternalDataError as exc:
        raise TargetEvidenceError(str(exc)) from exc
    errors = payload.get("errors") or []
    if errors:
        message = str((errors[0] or {}).get("message") or "Open Targets GraphQL request failed.")
        raise TargetEvidenceError(message[:240])
    data = payload.get("data")
    if not isinstance(data, dict):
        raise TargetEvidenceError("Open Targets returned an unexpected response shape.")
    return data


def _group_evidence(rows: list[Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        target_id = str((row.get("target") or {}).get("id") or "")
        if target_id:
            grouped[target_id].append(row)
    return grouped


def _score_rows(rows: list[Any], labels: dict[str, str]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        identifier = str(row["id"])
        result.append(
            {
                "id": identifier,
                "label": labels.get(identifier, _humanize(identifier)),
                "score": _number(row.get("score")),
            }
        )
    return sorted(result, key=lambda item: (-item["score"], item["id"]))


def _tractability(rows: list[Any]) -> dict[str, Any]:
    available = []
    approved = []
    for row in rows:
        if not isinstance(row, dict) or row.get("value") is not True:
            continue
        item = {"label": str(row.get("label") or ""), "modality": str(row.get("modality") or "")}
        if item not in available:
            available.append(item)
        if "approved" in item["label"].casefold() and item["modality"] not in approved:
            approved.append(item["modality"])
    return {"approved_modalities": approved, "available": available[:12]}


def _pathways(rows: list[Any]) -> list[dict[str, str]]:
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("pathway") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result.append({"id": str(row.get("pathwayId") or ""), "name": name})
    return result[:5]


def _safety_liabilities(rows: list[Any]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        event = str(row.get("event") or "").strip()
        if not event or event in seen:
            continue
        seen.add(event)
        result.append(
            {
                "event": event,
                "source": str(row.get("datasource") or ""),
                "url": str(row.get("url") or ""),
                "literature": [str(item) for item in row.get("literature") or []][:5],
            }
        )
    return result[:5]


def _clinical_drugs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drugs = []
    seen = set()
    for row in sorted(rows, key=lambda item: -_number(item.get("score"))):
        drug = row.get("drug") or {}
        drug_id = str(drug.get("id") or "")
        if not drug_id or drug_id in seen:
            continue
        seen.add(drug_id)
        drugs.append(
            {
                "id": drug_id,
                "name": str(drug.get("name") or drug_id),
                "stage": str(drug.get("maximumClinicalStage") or ""),
                "type": str(drug.get("drugType") or ""),
                "direction_on_target": str(row.get("directionOnTarget") or ""),
                "direction_on_trait": str(row.get("directionOnTrait") or ""),
                "url": f"{PLATFORM_URL}/drug/{drug_id}",
            }
        )
    return drugs[:5]


def _publication_ids(rows: list[dict[str, Any]]) -> list[str]:
    result = []
    for row in rows:
        for identifier in row.get("literature") or []:
            value = str(identifier).strip()
            if value and value not in result:
                result.append(value)
    return result[:8]


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "evidence_table": f"{relative_root}/target_evidence.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="target-review-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_evidence_table(output / "target_evidence.tsv", result)
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "source": result["source"],
            "source_url": result["source_url"],
            "retrieved_at": result["retrieved_at"],
            "disease": result["disease"],
            "target_ids": [item["id"] for item in result["candidates"]],
            "include_indirect": result["include_indirect"],
            "files": ["target_evidence.tsv", "report.json", "run_manifest.json", "summary.md"],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise TargetEvidenceError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_evidence_table(path: Path, result: dict[str, Any]) -> None:
    lane_ids = [item["id"] for item in result["evidence_lanes"]]
    fieldnames = [
        "rank",
        "target_id",
        "symbol",
        "name",
        "association_score",
        *lane_ids,
        "approved_modalities",
        "clinical_drugs",
        "pathways",
        "safety_liability_count",
        "publication_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for candidate in result["candidates"]:
            row = {
                "rank": candidate["rank"],
                "target_id": candidate["id"],
                "symbol": candidate["symbol"],
                "name": candidate["name"],
                "association_score": candidate["association_score"],
                "approved_modalities": "; ".join(candidate["tractability"]["approved_modalities"]),
                "clinical_drugs": "; ".join(item["name"] for item in candidate["drugs"]),
                "pathways": "; ".join(item["name"] for item in candidate["pathways"]),
                "safety_liability_count": len(candidate["safety_liabilities"]),
                "publication_ids": "; ".join(candidate["publications"]),
            }
            row.update({lane: candidate["datatype_score_map"].get(lane, 0.0) for lane in lane_ids})
            writer.writerow(row)


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# Target evidence review: {result['disease']['name']}",
        "",
        result["summary"],
        "",
        "| Rank | Target | Association score | Clinical drugs |",
        "| ---: | --- | ---: | --- |",
    ]
    for candidate in result["candidates"]:
        drugs = ", ".join(item["name"] for item in candidate["drugs"]) or "None returned"
        lines.append(
            f"| {candidate['rank']} | {candidate['symbol']} | {candidate['association_score']:.3f} | {drugs} |"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {caveat}" for caveat in result["caveats"])
    lines.extend(["", f"Source: {result['source_url']}", ""])
    return "\n".join(lines)


def _number(value: Any) -> float:
    try:
        return round(float(value or 0.0), 6)
    except (TypeError, ValueError):
        return 0.0


def _humanize(value: str) -> str:
    return str(value).replace("_", " ").strip().title()
