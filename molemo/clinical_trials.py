"""Bounded ClinicalTrials.gov landscapes for researcher-approved reviews."""

from __future__ import annotations

import csv
import json
import re
import shutil
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from .bio_clients import ExternalDataError, get_json
from .workspace_utils import WORKSPACE_ROOT


CLINICAL_TRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
CLINICAL_TRIALS_SITE = "https://clinicaltrials.gov"
MAX_TERM_CHARS = 160
MAX_RESULTS = 30
ACTIVE_STATUSES = (
    "RECRUITING",
    "NOT_YET_RECRUITING",
    "ACTIVE_NOT_RECRUITING",
    "ENROLLING_BY_INVITATION",
)
STATUS_SCOPES = {"active", "completed", "all"}
STUDY_SCOPES = {"interventional", "all"}
FIELDS = ",".join(
    [
        "NCTId",
        "BriefTitle",
        "OfficialTitle",
        "BriefSummary",
        "OverallStatus",
        "Phase",
        "StudyType",
        "EnrollmentCount",
        "EnrollmentType",
        "LeadSponsorName",
        "LeadSponsorClass",
        "Condition",
        "Keyword",
        "InterventionType",
        "InterventionName",
        "PrimaryOutcomeMeasure",
        "PrimaryOutcomeTimeFrame",
        "SecondaryOutcomeMeasure",
        "Sex",
        "MinimumAge",
        "MaximumAge",
        "HealthyVolunteers",
        "LocationCountry",
        "StartDate",
        "PrimaryCompletionDate",
        "CompletionDate",
        "StudyFirstPostDate",
        "LastUpdatePostDate",
        "HasResults",
        "DesignAllocation",
        "DesignInterventionModel",
        "DesignMasking",
        "DesignPrimaryPurpose",
        "ReferencePMID",
        "ReferenceType",
        "ReferenceCitation",
    ]
)


class ClinicalTrialsError(ValueError):
    """Raised when a trial landscape query or response is invalid."""


def normalize_clinical_trial_inputs(
    condition: str,
    intervention: str = "",
    status_scope: str = "all",
    study_scope: str = "interventional",
    max_results: int | str = 20,
) -> dict[str, Any]:
    cleaned_condition = _term(condition, "Condition", required=True)
    cleaned_intervention = _term(intervention, "Intervention", required=False)
    cleaned_status = str(status_scope or "all").strip().casefold()
    if cleaned_status not in STATUS_SCOPES:
        raise ClinicalTrialsError("status_scope must be active, completed, or all.")
    cleaned_study = str(study_scope or "interventional").strip().casefold()
    if cleaned_study not in STUDY_SCOPES:
        raise ClinicalTrialsError("study_scope must be interventional or all.")
    try:
        bounded_results = int(max_results)
    except (TypeError, ValueError) as exc:
        raise ClinicalTrialsError("max_results must be an integer.") from exc
    if not 1 <= bounded_results <= MAX_RESULTS:
        raise ClinicalTrialsError(f"max_results must be between 1 and {MAX_RESULTS}.")

    parameters: dict[str, str] = {"query.cond": cleaned_condition}
    if cleaned_intervention:
        parameters["query.intr"] = cleaned_intervention
    if cleaned_study == "interventional":
        parameters["query.term"] = "AREA[StudyType]INTERVENTIONAL"
    if cleaned_status == "active":
        parameters["filter.overallStatus"] = "|".join(ACTIVE_STATUSES)
    elif cleaned_status == "completed":
        parameters["filter.overallStatus"] = "COMPLETED"

    search_parameters = {"cond": cleaned_condition}
    if cleaned_intervention:
        search_parameters["intr"] = cleaned_intervention
    return {
        "condition": cleaned_condition,
        "intervention": cleaned_intervention,
        "status_scope": cleaned_status,
        "study_scope": cleaned_study,
        "max_results": bounded_results,
        "source_order": "ClinicalTrials.gov source order",
        "query_parameters": parameters,
        "search_url": f"{CLINICAL_TRIALS_SITE}/search?{urlencode(search_parameters)}",
    }


def preflight_clinical_trial_landscape(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_clinical_trial_inputs(**arguments)
    payload, api_url = _search(normalized, page_size=1)
    hit_count = _integer(payload.get("totalCount"))
    if hit_count == 0:
        raise ClinicalTrialsError("ClinicalTrials.gov returned no studies for the approved query and filters.")
    warnings = [
        "Registry records describe study plans and status; they do not by themselves establish efficacy or safety.",
        "Recruitment status, dates, enrollment, and results availability can change after retrieval.",
    ]
    return {
        "ready": True,
        "source": "ClinicalTrials.gov",
        "source_url": CLINICAL_TRIALS_SITE,
        **normalized,
        "api_url": api_url,
        "hit_count": hit_count,
        "warnings": warnings,
        "summary": (
            f"ClinicalTrials.gov found {hit_count:,} matching studies; the approved run will collect "
            f"the first {normalized['max_results']} in source order."
        ),
    }


def search_clinical_trials_preview(**arguments: Any) -> dict[str, Any]:
    normalized = normalize_clinical_trial_inputs(**arguments)
    normalized["max_results"] = min(normalized["max_results"], 10)
    payload, api_url = _search(normalized, page_size=normalized["max_results"])
    return parse_clinical_trials_payload(payload, normalized, api_url=api_url, persisted=False)


def collect_clinical_trial_landscape(**arguments: Any) -> dict[str, Any]:
    preflight = preflight_clinical_trial_landscape(**arguments)
    normalized = {
        key: preflight[key]
        for key in (
            "condition",
            "intervention",
            "status_scope",
            "study_scope",
            "max_results",
            "source_order",
            "query_parameters",
            "search_url",
        )
    }
    payload, api_url = _search(normalized, page_size=normalized["max_results"])
    result = parse_clinical_trials_payload(payload, normalized, api_url=api_url, persisted=True)
    _persist_landscape(result)
    return result


def parse_clinical_trials_payload(
    payload: dict[str, Any],
    normalized: dict[str, Any],
    *,
    api_url: str,
    persisted: bool,
) -> dict[str, Any]:
    raw_studies = payload.get("studies") or []
    if not isinstance(raw_studies, list):
        raise ClinicalTrialsError("ClinicalTrials.gov returned an unexpected studies list.")
    studies = []
    for rank, raw in enumerate(raw_studies[: int(normalized["max_results"])], 1):
        study = _normalize_study(raw, rank) if isinstance(raw, dict) else None
        if study:
            studies.append(study)
    if not studies:
        raise ClinicalTrialsError("ClinicalTrials.gov returned no usable study records.")

    status_counts = Counter(study["status"] for study in studies)
    phase_counts = Counter(phase for study in studies for phase in (study["phases"] or ["NOT_APPLICABLE"]))
    intervention_counts = Counter(
        intervention["type"] for study in studies for intervention in study["interventions"]
    )
    sponsor_counts = Counter(study["sponsor_class"] for study in studies if study["sponsor_class"])
    country_counts = Counter(country for study in studies for country in study["countries"])
    result = {
        "analysis_id": f"clinical-trials-{uuid.uuid4().hex[:12]}" if persisted else "clinical-trials-preview",
        "method": "ClinicalTrials.gov registry evidence landscape",
        "source": "ClinicalTrials.gov",
        "source_url": CLINICAL_TRIALS_SITE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        **normalized,
        "api_url": api_url,
        "hit_count": _integer(payload.get("totalCount")),
        "returned_count": len(studies),
        "results_available_count": sum(1 for study in studies if study["has_results"]),
        "country_count": len(country_counts),
        "status_counts": _counts(status_counts),
        "phase_counts": _counts(phase_counts),
        "intervention_type_counts": _counts(intervention_counts),
        "sponsor_class_counts": _counts(sponsor_counts),
        "country_counts": _counts(country_counts)[:12],
        "studies": studies,
        "outputs": {},
        "caveats": [
            "ClinicalTrials.gov records are sponsor- or investigator-submitted registry metadata; a registration is not evidence that an intervention is effective or safe.",
            "Overall status applies to the study record and may not describe recruitment at every site; verify the live record before acting on recruitment information.",
            "Primary outcomes shown here are registered endpoints, not outcome values. A record marked as having results still requires review of the results tables, protocol, statistical analysis, and linked publications.",
            "Missing posted results or publications must not be interpreted as study failure, negative efficacy, or poor quality.",
            "The bounded set preserves source order and is not a risk-of-bias assessment, meta-analysis, or comprehensive regulatory review.",
        ],
    }
    intervention_clause = f" with {normalized['intervention']}" if normalized["intervention"] else ""
    result["summary"] = (
        f"Mapped {len(studies)} of {result['hit_count']:,} ClinicalTrials.gov studies for "
        f"'{normalized['condition']}'{intervention_clause}; "
        f"{result['results_available_count']} mapped records have posted results."
    )
    return result


def _normalize_study(raw: dict[str, Any], rank: int) -> dict[str, Any] | None:
    protocol = raw.get("protocolSection") or {}
    identification = protocol.get("identificationModule") or {}
    nct_id = str(identification.get("nctId") or "").upper()
    title = str(identification.get("briefTitle") or identification.get("officialTitle") or "").strip()
    if not nct_id or not title:
        return None
    status = protocol.get("statusModule") or {}
    sponsor = (protocol.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}
    conditions = protocol.get("conditionsModule") or {}
    design = protocol.get("designModule") or {}
    design_info = design.get("designInfo") or {}
    masking = design_info.get("maskingInfo") or {}
    enrollment = design.get("enrollmentInfo") or {}
    arms = protocol.get("armsInterventionsModule") or {}
    outcomes = protocol.get("outcomesModule") or {}
    eligibility = protocol.get("eligibilityModule") or {}
    locations = (protocol.get("contactsLocationsModule") or {}).get("locations") or []
    references = (protocol.get("referencesModule") or {}).get("references") or []

    interventions = [
        {"type": str(item.get("type") or "OTHER"), "name": str(item.get("name") or "").strip()}
        for item in arms.get("interventions") or []
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    ]
    primary_outcomes = [
        {
            "measure": str(item.get("measure") or "").strip(),
            "time_frame": str(item.get("timeFrame") or "").strip(),
        }
        for item in outcomes.get("primaryOutcomes") or []
        if isinstance(item, dict) and str(item.get("measure") or "").strip()
    ]
    publications = [
        {
            "pmid": str(item.get("pmid") or "").strip() or None,
            "type": str(item.get("type") or "").strip(),
            "citation": str(item.get("citation") or "").strip(),
        }
        for item in references
        if isinstance(item, dict) and (item.get("pmid") or item.get("citation"))
    ]
    countries = sorted(
        {
            str(item.get("country") or "").strip()
            for item in locations
            if isinstance(item, dict) and str(item.get("country") or "").strip()
        }
    )
    return {
        "rank": rank,
        "nct_id": nct_id,
        "title": title,
        "official_title": str(identification.get("officialTitle") or "").strip(),
        "brief_summary": str((protocol.get("descriptionModule") or {}).get("briefSummary") or "").strip(),
        "status": str(status.get("overallStatus") or "UNKNOWN"),
        "study_type": str(design.get("studyType") or "UNKNOWN"),
        "phases": [str(item) for item in design.get("phases") or []],
        "enrollment": _integer(enrollment.get("count")),
        "enrollment_type": str(enrollment.get("type") or ""),
        "sponsor": str(sponsor.get("name") or "").strip(),
        "sponsor_class": str(sponsor.get("class") or "").strip(),
        "conditions": [str(item) for item in conditions.get("conditions") or []],
        "interventions": interventions,
        "primary_outcomes": primary_outcomes,
        "secondary_outcome_count": len(outcomes.get("secondaryOutcomes") or []),
        "eligibility": {
            "sex": str(eligibility.get("sex") or ""),
            "minimum_age": str(eligibility.get("minimumAge") or ""),
            "maximum_age": str(eligibility.get("maximumAge") or ""),
            "healthy_volunteers": bool(eligibility.get("healthyVolunteers")),
        },
        "design": {
            "allocation": str(design_info.get("allocation") or ""),
            "intervention_model": str(design_info.get("interventionModel") or ""),
            "masking": str(masking.get("masking") or ""),
            "primary_purpose": str(design_info.get("primaryPurpose") or ""),
        },
        "dates": {
            "start": _date(status.get("startDateStruct")),
            "primary_completion": _date(status.get("primaryCompletionDateStruct")),
            "completion": _date(status.get("completionDateStruct")),
            "first_posted": _date(status.get("studyFirstPostDateStruct")),
            "last_updated": _date(status.get("lastUpdatePostDateStruct")),
        },
        "countries": countries,
        "has_results": bool(raw.get("hasResults")),
        "publications": publications,
        "url": f"{CLINICAL_TRIALS_SITE}/study/{nct_id}",
        "selection_basis": "Matched the approved ClinicalTrials.gov query and filters; retained in source order.",
    }


def _search(normalized: dict[str, Any], page_size: int) -> tuple[dict[str, Any], str]:
    parameters = {
        **normalized["query_parameters"],
        "format": "json",
        "pageSize": str(max(1, min(int(page_size), MAX_RESULTS))),
        "countTotal": "true",
        "fields": FIELDS,
    }
    api_url = f"{CLINICAL_TRIALS_API}?{urlencode(parameters)}"
    try:
        payload = get_json(api_url)
    except ExternalDataError as exc:
        raise ClinicalTrialsError(str(exc)) from exc
    if "studies" not in payload or "totalCount" not in payload:
        raise ClinicalTrialsError("ClinicalTrials.gov returned an unexpected response shape.")
    return payload, api_url


def _persist_landscape(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "trials": f"{relative_root}/trials.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="clinical-trials-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_trials(output / "trials.tsv", result["studies"])
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "source": result["source"],
            "source_url": result["source_url"],
            "retrieved_at": result["retrieved_at"],
            "condition": result["condition"],
            "intervention": result["intervention"],
            "filters": {
                "status_scope": result["status_scope"],
                "study_scope": result["study_scope"],
                "max_results": result["max_results"],
            },
            "query_parameters": result["query_parameters"],
            "api_url": result["api_url"],
            "files": ["trials.tsv", "report.json", "run_manifest.json", "summary.md"],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise ClinicalTrialsError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_trials(path: Path, studies: list[dict[str, Any]]) -> None:
    fields = [
        "rank",
        "nct_id",
        "title",
        "status",
        "study_type",
        "phases",
        "enrollment",
        "enrollment_type",
        "sponsor",
        "sponsor_class",
        "conditions",
        "interventions",
        "primary_outcomes",
        "countries",
        "has_results",
        "publication_pmids",
        "start_date",
        "primary_completion_date",
        "completion_date",
        "last_updated",
        "url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for study in studies:
            writer.writerow(
                {
                    "rank": study["rank"],
                    "nct_id": study["nct_id"],
                    "title": study["title"],
                    "status": study["status"],
                    "study_type": study["study_type"],
                    "phases": "; ".join(study["phases"]),
                    "enrollment": study["enrollment"],
                    "enrollment_type": study["enrollment_type"],
                    "sponsor": study["sponsor"],
                    "sponsor_class": study["sponsor_class"],
                    "conditions": "; ".join(study["conditions"]),
                    "interventions": "; ".join(
                        f"{item['type']}: {item['name']}" for item in study["interventions"]
                    ),
                    "primary_outcomes": "; ".join(
                        item["measure"] for item in study["primary_outcomes"]
                    ),
                    "countries": "; ".join(study["countries"]),
                    "has_results": study["has_results"],
                    "publication_pmids": "; ".join(
                        item["pmid"] for item in study["publications"] if item["pmid"]
                    ),
                    "start_date": study["dates"]["start"],
                    "primary_completion_date": study["dates"]["primary_completion"],
                    "completion_date": study["dates"]["completion"],
                    "last_updated": study["dates"]["last_updated"],
                    "url": study["url"],
                }
            )


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Clinical trial evidence landscape",
        "",
        f"Condition: **{result['condition']}**",
        f"Intervention: **{result['intervention'] or 'Any'}**",
        f"Filters: `{result['status_scope']}` status; `{result['study_scope']}` study scope",
        "",
        result["summary"],
        "",
        "| Rank | Status | Phase | Study | Sponsor |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for study in result["studies"]:
        title = study["title"].replace("|", "\\|")
        sponsor = study["sponsor"].replace("|", "\\|")
        lines.append(
            f"| {study['rank']} | {study['status']} | {', '.join(study['phases']) or 'n/a'} | "
            f"[{title}]({study['url']}) ({study['nct_id']}) | {sponsor} |"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _term(value: Any, label: str, *, required: bool) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    if required and not cleaned:
        raise ClinicalTrialsError(f"{label} is required.")
    if len(cleaned) > MAX_TERM_CHARS:
        raise ClinicalTrialsError(f"{label} must contain at most {MAX_TERM_CHARS} characters.")
    if any(ord(char) < 32 for char in cleaned):
        raise ClinicalTrialsError(f"{label} contains unsupported control characters.")
    return cleaned


def _counts(counter: Counter[str]) -> list[dict[str, Any]]:
    return [
        {"label": label, "count": count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _date(value: Any) -> str:
    return str((value or {}).get("date") or "") if isinstance(value, dict) else ""


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
