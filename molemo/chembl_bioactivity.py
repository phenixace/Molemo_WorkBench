"""Researcher-approved ChEMBL target-to-small-molecule bioactivity review."""

from __future__ import annotations

import csv
import json
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .bio_clients import ExternalDataError, get_json, normalize_uniprot_accession
from .workspace_utils import WORKSPACE_ROOT


CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
CHEMBL_WEB = "https://www.ebi.ac.uk/chembl/explore"
MAX_ACTIVITIES = 100
MAX_FETCHED_ACTIVITIES = 200
ASSAY_SCOPES = {
    "binding": ("B",),
    "functional": ("F",),
    "binding_functional": ("B", "F"),
}
ASSAY_LABELS = {"B": "Binding", "F": "Functional"}


class ChemblBioactivityError(ValueError):
    """Raised when a ChEMBL bioactivity review cannot be normalized safely."""


def normalize_chembl_inputs(
    accession: str,
    assay_scope: str = "binding_functional",
    min_pchembl: Any = 5.0,
    max_activities: Any = 50,
) -> dict[str, Any]:
    try:
        normalized_accession = normalize_uniprot_accession(accession)
    except ExternalDataError as exc:
        raise ChemblBioactivityError(str(exc)) from exc
    scope = str(assay_scope or "binding_functional").strip().lower()
    if scope not in ASSAY_SCOPES:
        raise ChemblBioactivityError(
            "assay_scope must be binding, functional, or binding_functional."
        )
    try:
        threshold = float(min_pchembl)
    except (TypeError, ValueError) as exc:
        raise ChemblBioactivityError("min_pchembl must be numeric.") from exc
    if not 4.0 <= threshold <= 12.0:
        raise ChemblBioactivityError("min_pchembl must be between 4 and 12.")
    try:
        limit = int(max_activities)
    except (TypeError, ValueError) as exc:
        raise ChemblBioactivityError("max_activities must be an integer.") from exc
    if not 10 <= limit <= MAX_ACTIVITIES:
        raise ChemblBioactivityError(f"max_activities must be between 10 and {MAX_ACTIVITIES}.")
    return {
        "accession": normalized_accession,
        "assay_scope": scope,
        "assay_types": list(ASSAY_SCOPES[scope]),
        "min_pchembl": round(threshold, 2),
        "max_activities": limit,
    }


def preflight_chembl_bioactivity(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_chembl_inputs(**arguments)
    preview_limit = min(20, normalized["max_activities"])
    result = _review(normalized, output_limit=preview_limit, persist=False)
    result["ready"] = True
    result["preview"] = True
    result["requested_max_activities"] = normalized["max_activities"]
    result["summary"] = (
        f"Resolved {result['target']['pref_name']} ({result['target']['target_chembl_id']}) and previewed "
        f"{len(result['activities'])} confidence-9 activities across {len(result['compounds'])} compounds."
    )
    return result


def collect_chembl_bioactivity(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_chembl_inputs(**arguments)
    result = _review(normalized, output_limit=normalized["max_activities"], persist=True)
    result["summary"] = (
        f"Collected {len(result['activities'])} confidence-9 ChEMBL activities across "
        f"{len(result['compounds'])} compounds for {result['target']['pref_name']}."
    )
    return result


def _review(normalized: dict[str, Any], output_limit: int, persist: bool) -> dict[str, Any]:
    status = _request("status", {})
    target_payload = _request(
        "target",
        {
            "target_components__accession": normalized["accession"],
            "limit": 20,
            "only": "target_chembl_id,pref_name,target_type,organism,tax_id",
        },
    )
    target = parse_chembl_target(target_payload, normalized["accession"])
    fetch_limit = min(MAX_FETCHED_ACTIVITIES, max(20, int(output_limit) * 2))
    activity_payload = _request(
        "activity",
        {
            "target_chembl_id": target["target_chembl_id"],
            "assay_type__in": ",".join(normalized["assay_types"]),
            "pchembl_value__gte": normalized["min_pchembl"],
            "pchembl_value__isnull": "false",
            "data_validity_comment__isnull": "true",
            "potential_duplicate": 0,
            "standard_flag": 1,
            "limit": fetch_limit,
            "order_by": "-pchembl_value",
        },
    )
    raw_activities = [
        item for item in activity_payload.get("activities") or [] if isinstance(item, dict)
    ]
    assay_ids = list(
        dict.fromkeys(
            str(item.get("assay_chembl_id") or "")
            for item in raw_activities
            if item.get("assay_chembl_id")
        )
    )
    assay_payload = (
        _request(
            "assay",
            {
                "assay_chembl_id__in": ",".join(assay_ids),
                "limit": max(1, len(assay_ids)),
                "only": (
                    "assay_chembl_id,assay_type,confidence_score,relationship_type,"
                    "bao_format,description"
                ),
            },
        )
        if assay_ids
        else {"assays": [], "page_meta": {"total_count": 0}}
    )
    parsed = parse_chembl_activities(
        activity_payload,
        assay_payload,
        min_pchembl=normalized["min_pchembl"],
        limit=output_limit,
    )
    compounds = summarize_chembl_compounds(parsed["activities"])
    page_meta = activity_payload.get("page_meta") or {}
    retrieved_at = datetime.now(timezone.utc).isoformat()
    result = {
        "analysis_id": f"chembl-bioactivity-{uuid.uuid4().hex[:12]}",
        "method": "ChEMBL confidence-9 target bioactivity review",
        "source": "ChEMBL",
        "source_url": target["url"],
        "retrieved_at": retrieved_at,
        "database": {
            "version": str(status.get("chembl_db_version") or "ChEMBL"),
            "release_date": status.get("chembl_release_date"),
            "status": status.get("status"),
        },
        "inputs": dict(normalized),
        "target": target,
        "retrieval": {
            "source_total_count": int(page_meta.get("total_count") or 0),
            "source_rows_retrieved": len(raw_activities),
            "confidence_9_rows": parsed["confidence_9_rows"],
            "reported_activities": len(parsed["activities"]),
            "reported_compounds": len(compounds),
            "query_limit": fetch_limit,
            "truncated": int(page_meta.get("total_count") or 0) > fetch_limit,
            "excluded": parsed["excluded"],
        },
        "activities": parsed["activities"],
        "compounds": compounds,
        "distributions": _distributions(parsed["activities"]),
        "caveats": [
            "pChEMBL is a standardized negative log molar activity value, not a probability or lead-quality score.",
            "IC50, Ki, Kd, EC50 and other endpoints or assay contexts are not directly interchangeable.",
            "Confidence score 9 supports a direct single-protein target assignment; it does not prove direct physical binding or assay quality.",
            "ChEMBL binding-class assays can use cell-based or other formats; review BAO format and assay description.",
            "The bounded, potency-ordered sample does not establish selectivity, mechanism, ADME, safety, or clinical efficacy.",
        ],
        "outputs": {},
    }
    result["summary"] = (
        f"Reviewed {len(result['activities'])} activities for {target['pref_name']} "
        f"from {result['database']['version']}."
    )
    if persist:
        _persist_review(result)
    return result


def parse_chembl_target(payload: dict[str, Any], accession: str) -> dict[str, Any]:
    targets = [item for item in payload.get("targets") or [] if isinstance(item, dict)]
    single_proteins = [
        item
        for item in targets
        if str(item.get("target_type") or "").upper() == "SINGLE PROTEIN"
        and item.get("target_chembl_id")
    ]
    if not single_proteins:
        raise ChemblBioactivityError(
            f"ChEMBL returned no exact single-protein target for UniProt {accession}."
        )
    if len(single_proteins) > 1:
        identifiers = ", ".join(str(item["target_chembl_id"]) for item in single_proteins[:5])
        raise ChemblBioactivityError(
            f"UniProt {accession} maps to multiple ChEMBL single-protein targets: {identifiers}."
        )
    target = single_proteins[0]
    target_id = str(target["target_chembl_id"])
    return {
        "accession": accession,
        "target_chembl_id": target_id,
        "pref_name": str(target.get("pref_name") or target_id),
        "target_type": "SINGLE PROTEIN",
        "organism": str(target.get("organism") or ""),
        "tax_id": target.get("tax_id"),
        "url": f"{CHEMBL_WEB}/target/{target_id}",
    }


def parse_chembl_activities(
    activity_payload: dict[str, Any],
    assay_payload: dict[str, Any],
    *,
    min_pchembl: float,
    limit: int,
) -> dict[str, Any]:
    assays = {
        str(item.get("assay_chembl_id")): item
        for item in assay_payload.get("assays") or []
        if isinstance(item, dict) and item.get("assay_chembl_id")
    }
    excluded = Counter()
    normalized = []
    confidence_9_rows = 0
    for raw in activity_payload.get("activities") or []:
        if not isinstance(raw, dict):
            excluded["invalid_record"] += 1
            continue
        assay_id = str(raw.get("assay_chembl_id") or "")
        assay = assays.get(assay_id) or {}
        if int(assay.get("confidence_score") or 0) != 9:
            excluded["confidence_below_9"] += 1
            continue
        confidence_9_rows += 1
        if str(assay.get("relationship_type") or "") != "D":
            excluded["non_direct_relationship"] += 1
            continue
        molecule_id = str(raw.get("molecule_chembl_id") or "")
        smiles = str(raw.get("canonical_smiles") or "").strip()
        try:
            pchembl = float(raw.get("pchembl_value"))
        except (TypeError, ValueError):
            excluded["invalid_pchembl"] += 1
            continue
        if pchembl < float(min_pchembl):
            excluded["below_threshold"] += 1
            continue
        if not molecule_id or not smiles or len(smiles) > 1000:
            excluded["missing_small_molecule_structure"] += 1
            continue
        standard_value = str(raw.get("standard_value") or "").strip()
        normalized.append(
            {
                "rank": 0,
                "activity_id": str(raw.get("activity_id") or ""),
                "molecule_chembl_id": molecule_id,
                "molecule_name": str(raw.get("molecule_pref_name") or molecule_id),
                "canonical_smiles": smiles,
                "pchembl_value": round(pchembl, 2),
                "standard_type": str(raw.get("standard_type") or ""),
                "standard_relation": str(raw.get("standard_relation") or raw.get("relation") or ""),
                "standard_value": standard_value,
                "standard_units": str(raw.get("standard_units") or ""),
                "assay_chembl_id": assay_id,
                "assay_type": str(raw.get("assay_type") or assay.get("assay_type") or ""),
                "assay_type_label": ASSAY_LABELS.get(
                    str(raw.get("assay_type") or assay.get("assay_type") or ""),
                    "Other",
                ),
                "assay_description": str(
                    raw.get("assay_description") or assay.get("description") or ""
                )[:1000],
                "bao_label": str(raw.get("bao_label") or ""),
                "bao_format": str(assay.get("bao_format") or ""),
                "confidence_score": 9,
                "relationship_type": "D",
                "document_chembl_id": str(raw.get("document_chembl_id") or ""),
                "document_journal": str(raw.get("document_journal") or ""),
                "document_year": raw.get("document_year"),
                "molecule_url": f"{CHEMBL_WEB}/compound/{molecule_id}",
                "assay_url": f"{CHEMBL_WEB}/assay/{assay_id}",
            }
        )
    normalized.sort(
        key=lambda item: (
            -float(item["pchembl_value"]),
            str(item["molecule_chembl_id"]),
            str(item["assay_chembl_id"]),
        )
    )
    normalized = normalized[: int(limit)]
    for index, item in enumerate(normalized, 1):
        item["rank"] = index
    return {
        "activities": normalized,
        "confidence_9_rows": confidence_9_rows,
        "excluded": dict(sorted(excluded.items())),
    }


def summarize_chembl_compounds(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for activity in activities:
        grouped.setdefault(str(activity["molecule_chembl_id"]), []).append(activity)
    compounds = []
    for molecule_id, rows in grouped.items():
        strongest = rows[0]
        compounds.append(
            {
                "rank": 0,
                "molecule_chembl_id": molecule_id,
                "name": strongest["molecule_name"],
                "canonical_smiles": strongest["canonical_smiles"],
                "max_pchembl": max(float(row["pchembl_value"]) for row in rows),
                "min_pchembl": min(float(row["pchembl_value"]) for row in rows),
                "retrieved_activity_count": len(rows),
                "assay_count": len({row["assay_chembl_id"] for row in rows}),
                "endpoint_types": sorted({row["standard_type"] for row in rows if row["standard_type"]}),
                "assay_types": sorted({row["assay_type"] for row in rows if row["assay_type"]}),
                "url": strongest["molecule_url"],
            }
        )
    compounds.sort(key=lambda item: (-float(item["max_pchembl"]), item["molecule_chembl_id"]))
    for index, item in enumerate(compounds, 1):
        item["rank"] = index
    return compounds


def _distributions(activities: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    def count(field: str) -> list[dict[str, Any]]:
        values = Counter(str(item.get(field) or "Unknown") for item in activities)
        return [
            {"label": label, "count": value}
            for label, value in sorted(values.items(), key=lambda item: (-item[1], item[0]))
        ]

    return {
        "assay_types": count("assay_type_label"),
        "endpoint_types": count("standard_type"),
        "bao_formats": count("bao_label"),
    }


def _request(resource: str, parameters: dict[str, Any]) -> dict[str, Any]:
    url = f"{CHEMBL_API}/{resource}.json"
    if parameters:
        url += "?" + urlencode(parameters)
    try:
        return get_json(url)
    except ExternalDataError as exc:
        raise ChemblBioactivityError(str(exc)) from exc


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="chembl-bioactivity-", dir=temp_root))
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "activities": f"{relative_root}/activities.tsv",
        "compounds": f"{relative_root}/compounds.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    try:
        _write_tsv(
            temporary / "activities.tsv",
            result["activities"],
            [
                "rank",
                "molecule_chembl_id",
                "molecule_name",
                "pchembl_value",
                "standard_type",
                "standard_relation",
                "standard_value",
                "standard_units",
                "assay_chembl_id",
                "assay_type",
                "bao_label",
                "confidence_score",
                "document_chembl_id",
                "document_year",
                "canonical_smiles",
            ],
        )
        compound_rows = [
            {
                **item,
                "endpoint_types": ",".join(item["endpoint_types"]),
                "assay_types": ",".join(item["assay_types"]),
            }
            for item in result["compounds"]
        ]
        _write_tsv(
            temporary / "compounds.tsv",
            compound_rows,
            [
                "rank",
                "molecule_chembl_id",
                "name",
                "max_pchembl",
                "min_pchembl",
                "retrieved_activity_count",
                "assay_count",
                "endpoint_types",
                "assay_types",
                "canonical_smiles",
                "url",
            ],
        )
        (temporary / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "retrieved_at": result["retrieved_at"],
            "database": result["database"],
            "target": result["target"],
            "inputs": result["inputs"],
            "outputs": result["outputs"],
        }
        (temporary / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (temporary / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise ChemblBioactivityError("ChEMBL analysis output already exists.")
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
    target = result["target"]
    retrieval = result["retrieval"]
    lines = [
        f"# ChEMBL bioactivity review: {target['pref_name']}",
        "",
        f"- UniProt: {target['accession']}",
        f"- ChEMBL target: {target['target_chembl_id']}",
        f"- Database: {result['database']['version']} ({result['database'].get('release_date') or 'date unavailable'})",
        f"- Reported activities: {retrieval['reported_activities']}",
        f"- Reported compounds: {retrieval['reported_compounds']}",
        f"- Minimum pChEMBL: {result['inputs']['min_pchembl']}",
        "",
        "## Interpretation boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in result["caveats"])
    return "\n".join(lines) + "\n"
