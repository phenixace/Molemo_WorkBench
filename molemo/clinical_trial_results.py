"""Exact ClinicalTrials.gov posted-results reviews with auditable persistence."""

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
from urllib.parse import quote

from .bio_clients import ExternalDataError, get_json
from .workspace_utils import WORKSPACE_ROOT


CLINICAL_TRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
CLINICAL_TRIALS_SITE = "https://clinicaltrials.gov"
CLINICAL_TRIALS_DOCS = "https://cdn.clinicaltrials.gov/large-docs"
NCT_ID = re.compile(r"^NCT\d{8}$", re.I)
MAX_OUTCOMES = 100
MAX_ROWS_PER_MEASURE = 80
MAX_BASELINE_MEASURES = 60
MAX_EVENTS = 300
MAX_PUBLICATIONS = 80
MAX_TEXT_CHARS = 4000


class ClinicalTrialResultsError(ValueError):
    """Raised when an exact posted-results review cannot be completed."""


def normalize_nct_id(value: str) -> str:
    cleaned = str(value or "").strip().upper()
    if not NCT_ID.fullmatch(cleaned):
        raise ClinicalTrialResultsError("NCT ID must match NCT followed by eight digits.")
    return cleaned


def preflight_clinical_trial_results(nct_id: str) -> dict[str, Any]:
    normalized = normalize_nct_id(nct_id)
    payload, api_url = _fetch_study(normalized)
    if not payload.get("hasResults") or not isinstance(payload.get("resultsSection"), dict):
        raise ClinicalTrialResultsError(
            f"{normalized} does not have posted tabular results in ClinicalTrials.gov."
        )
    protocol = payload.get("protocolSection") or {}
    results = payload.get("resultsSection") or {}
    study = _study_identity(protocol, normalized)
    outcomes = ((results.get("outcomeMeasuresModule") or {}).get("outcomeMeasures")) or []
    serious_events = ((results.get("adverseEventsModule") or {}).get("seriousEvents")) or []
    other_events = ((results.get("adverseEventsModule") or {}).get("otherEvents")) or []
    publications = _normalize_publications(protocol)
    documents = _normalize_documents(payload.get("documentSection") or {}, normalized)
    primary_count = sum(
        1 for item in outcomes if isinstance(item, dict) and item.get("type") == "PRIMARY"
    )
    secondary_count = sum(
        1 for item in outcomes if isinstance(item, dict) and item.get("type") == "SECONDARY"
    )
    warnings = [
        "Posted tables are submitted registry results, not an independent efficacy, safety, or risk-of-bias conclusion.",
        "Outcome values must be interpreted with their group definitions, units, denominators, time frames, analysis population, and statistical method.",
        "Adverse-event counts are descriptive registry data; comparisons require exposure, ascertainment, denominators, and the prespecified analysis context.",
    ]
    return {
        "ready": True,
        "source": "ClinicalTrials.gov",
        "source_url": f"{CLINICAL_TRIALS_SITE}/study/{normalized}?format=json",
        "api_url": api_url,
        "nct_id": normalized,
        "study": study,
        "has_results": True,
        "outcome_count": len(outcomes),
        "primary_outcome_count": primary_count,
        "secondary_outcome_count": secondary_count,
        "serious_event_term_count": len(serious_events),
        "other_event_term_count": len(other_events),
        "publication_count": len(publications),
        "document_count": len(documents),
        "warnings": warnings,
        "summary": (
            f"Resolved {normalized} with posted results: {primary_count} primary and "
            f"{secondary_count} secondary outcome measures, {len(serious_events)} serious adverse-event "
            f"terms, and {len(publications)} linked publications."
        ),
    }


def review_clinical_trial_results(nct_id: str) -> dict[str, Any]:
    normalized = normalize_nct_id(nct_id)
    payload, api_url = _fetch_study(normalized)
    if not payload.get("hasResults") or not isinstance(payload.get("resultsSection"), dict):
        raise ClinicalTrialResultsError(
            f"{normalized} does not have posted tabular results in ClinicalTrials.gov."
        )
    result = parse_clinical_trial_results(payload, normalized, api_url)
    _persist_review(result)
    return result


def parse_clinical_trial_results(
    payload: dict[str, Any], nct_id: str, api_url: str
) -> dict[str, Any]:
    protocol = payload.get("protocolSection") or {}
    results = payload.get("resultsSection") or {}
    study = _study_identity(protocol, nct_id)
    flow = _normalize_participant_flow(results.get("participantFlowModule") or {})
    baseline = _normalize_baseline(results.get("baselineCharacteristicsModule") or {})
    outcomes_module = results.get("outcomeMeasuresModule") or {}
    raw_outcomes = outcomes_module.get("outcomeMeasures") or []
    outcomes = [
        _normalize_measure(item)
        for item in raw_outcomes[:MAX_OUTCOMES]
        if isinstance(item, dict)
    ]
    outcomes = [item for item in outcomes if item.get("title")]
    adverse_events = _normalize_adverse_events(results.get("adverseEventsModule") or {})
    publications = _normalize_publications(protocol)
    documents = _normalize_documents(payload.get("documentSection") or {}, nct_id)
    more_info = _normalize_more_info(results.get("moreInfoModule") or {})
    primary_count = sum(item["type"] == "PRIMARY" for item in outcomes)
    secondary_count = sum(item["type"] == "SECONDARY" for item in outcomes)
    analysis_count = sum(len(item["analyses"]) for item in outcomes)
    result = {
        "analysis_id": f"clinical-results-{nct_id.lower()}-{uuid.uuid4().hex[:8]}",
        "method": "ClinicalTrials.gov posted tabular results review",
        "source": "ClinicalTrials.gov",
        "source_url": f"{CLINICAL_TRIALS_SITE}/study/{nct_id}?format=json",
        "api_url": api_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "nct_id": nct_id,
        "study": study,
        "participant_flow": flow,
        "baseline": baseline,
        "outcomes": outcomes,
        "outcome_count": len(raw_outcomes),
        "returned_outcome_count": len(outcomes),
        "outcomes_truncated": len(raw_outcomes) > len(outcomes),
        "primary_outcome_count": primary_count,
        "secondary_outcome_count": secondary_count,
        "analysis_count": analysis_count,
        "adverse_events": adverse_events,
        "publications": publications,
        "documents": documents,
        "more_info": more_info,
        "outputs": {},
        "caveats": [
            "The review reproduces sponsor- or investigator-submitted ClinicalTrials.gov tables and does not independently verify, pool, or reanalyze participant-level data.",
            "No custom efficacy, safety, benefit-risk, certainty, or study-quality score is calculated.",
            "Outcome measures must be read with the registered endpoint definition, time frame, unit, denominator, analysis population, group mapping, and submitted statistical analysis.",
            "P-values and confidence intervals are shown as submitted and are not corrected or reinterpreted for multiplicity, missing data, estimand choice, protocol deviations, or post-hoc analyses.",
            "Adverse-event tables are descriptive and may use different assessment methods, reporting thresholds, exposure periods, and analysis populations across groups or studies.",
            "Linked publications, protocol, statistical analysis plan, amendments, and regulatory assessments remain necessary for critical appraisal.",
        ],
    }
    result["summary"] = (
        f"Captured posted results for {nct_id}: {primary_count} primary and {secondary_count} "
        f"secondary outcomes, {analysis_count} submitted statistical analyses, "
        f"{adverse_events['serious_event_term_count']} serious adverse-event terms, and "
        f"{len(publications)} linked publications. No effect conclusion was generated."
    )
    return result


def _fetch_study(nct_id: str) -> tuple[dict[str, Any], str]:
    api_url = f"{CLINICAL_TRIALS_API}/{quote(nct_id, safe='')}?format=json"
    try:
        payload = get_json(api_url)
    except ExternalDataError as exc:
        raise ClinicalTrialResultsError(str(exc)) from exc
    if not isinstance(payload.get("protocolSection"), dict):
        raise ClinicalTrialResultsError("ClinicalTrials.gov returned an unexpected study record.")
    return payload, api_url


def _study_identity(protocol: dict[str, Any], nct_id: str) -> dict[str, Any]:
    identification = protocol.get("identificationModule") or {}
    status = protocol.get("statusModule") or {}
    sponsor = (protocol.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}
    conditions = protocol.get("conditionsModule") or {}
    design = protocol.get("designModule") or {}
    design_info = design.get("designInfo") or {}
    masking = design_info.get("maskingInfo") or {}
    enrollment = design.get("enrollmentInfo") or {}
    arms_module = protocol.get("armsInterventionsModule") or {}
    arms = [
        {
            "label": str(item.get("label") or "").strip(),
            "type": str(item.get("type") or "").strip(),
            "description": _text(item.get("description")),
            "interventions": [str(value) for value in item.get("interventionNames") or []],
        }
        for item in arms_module.get("armGroups") or []
        if isinstance(item, dict) and item.get("label")
    ]
    interventions = [
        {
            "type": str(item.get("type") or "").strip(),
            "name": str(item.get("name") or "").strip(),
            "description": _text(item.get("description")),
            "arm_group_labels": [str(value) for value in item.get("armGroupLabels") or []],
        }
        for item in arms_module.get("interventions") or []
        if isinstance(item, dict) and item.get("name")
    ]
    return {
        "nct_id": str(identification.get("nctId") or nct_id).upper(),
        "title": str(identification.get("briefTitle") or identification.get("officialTitle") or nct_id),
        "official_title": str(identification.get("officialTitle") or ""),
        "status": str(status.get("overallStatus") or "UNKNOWN"),
        "sponsor": str(sponsor.get("name") or ""),
        "sponsor_class": str(sponsor.get("class") or ""),
        "conditions": [str(item) for item in conditions.get("conditions") or []],
        "study_type": str(design.get("studyType") or "UNKNOWN"),
        "phases": [str(item) for item in design.get("phases") or []],
        "enrollment": _integer(enrollment.get("count")),
        "enrollment_type": str(enrollment.get("type") or ""),
        "design": {
            "allocation": str(design_info.get("allocation") or ""),
            "intervention_model": str(design_info.get("interventionModel") or ""),
            "masking": str(masking.get("masking") or ""),
            "who_masked": [str(item) for item in masking.get("whoMasked") or []],
            "primary_purpose": str(design_info.get("primaryPurpose") or ""),
        },
        "arms": arms,
        "interventions": interventions,
        "dates": {
            "start": _date(status.get("startDateStruct")),
            "primary_completion": _date(status.get("primaryCompletionDateStruct")),
            "completion": _date(status.get("completionDateStruct")),
            "results_first_posted": _date(status.get("resultsFirstPostDateStruct")),
            "last_updated": _date(status.get("lastUpdatePostDateStruct")),
        },
        "url": f"{CLINICAL_TRIALS_SITE}/study/{nct_id}?format=json",
    }


def _normalize_participant_flow(module: dict[str, Any]) -> dict[str, Any]:
    groups = _groups(module.get("groups") or [])
    group_map = {item["id"]: item["title"] for item in groups}
    periods = []
    for raw_period in (module.get("periods") or [])[:12]:
        if not isinstance(raw_period, dict):
            continue
        milestones = []
        for raw_milestone in raw_period.get("milestones") or []:
            if not isinstance(raw_milestone, dict):
                continue
            milestones.append(
                {
                    "type": str(raw_milestone.get("type") or ""),
                    "comment": _text(raw_milestone.get("comment")),
                    "values": _subject_values(raw_milestone.get("achievements") or [], group_map),
                }
            )
        withdrawals = []
        for raw_reason in (raw_period.get("dropWithdraws") or [])[:80]:
            if not isinstance(raw_reason, dict):
                continue
            withdrawals.append(
                {
                    "reason": str(raw_reason.get("type") or ""),
                    "values": _subject_values(raw_reason.get("reasons") or [], group_map),
                }
            )
        periods.append(
            {
                "title": str(raw_period.get("title") or "Study period"),
                "milestones": milestones,
                "withdrawals": withdrawals,
            }
        )
    return {
        "groups": groups,
        "periods": periods,
        "pre_assignment_details": _text(module.get("preAssignmentDetails")),
        "recruitment_details": _text(module.get("recruitmentDetails")),
    }


def _normalize_baseline(module: dict[str, Any]) -> dict[str, Any]:
    groups = _groups(module.get("groups") or [])
    raw_measures = module.get("measures") or []
    measures = []
    for item in raw_measures[:MAX_BASELINE_MEASURES]:
        if not isinstance(item, dict):
            continue
        inherited = dict(item)
        inherited.setdefault("groups", module.get("groups") or [])
        measures.append(_normalize_measure(inherited))
    return {
        "groups": groups,
        "population_description": _text(module.get("populationDescription")),
        "measures": [item for item in measures if item.get("title")],
        "measure_count": len(raw_measures),
        "measures_truncated": len(raw_measures) > MAX_BASELINE_MEASURES,
    }


def _normalize_measure(raw: dict[str, Any]) -> dict[str, Any]:
    groups = _groups(raw.get("groups") or [])
    group_map = {item["id"]: item["title"] for item in groups}
    denoms = _normalize_denoms(raw.get("denoms") or [], group_map)
    rows = []
    for class_index, raw_class in enumerate(raw.get("classes") or []):
        if not isinstance(raw_class, dict):
            continue
        class_title = str(raw_class.get("title") or "").strip()
        class_denoms = _normalize_denoms(raw_class.get("denoms") or [], group_map)
        for category_index, category in enumerate(raw_class.get("categories") or []):
            if not isinstance(category, dict):
                continue
            category_title = str(category.get("title") or "").strip()
            label = " · ".join(value for value in (class_title, category_title) if value) or "Result"
            values = []
            for measurement in category.get("measurements") or []:
                if not isinstance(measurement, dict):
                    continue
                group_id = str(measurement.get("groupId") or "")
                values.append(
                    {
                        "group_id": group_id,
                        "group": group_map.get(group_id, group_id),
                        "value": str(measurement.get("value") or ""),
                        "spread": str(measurement.get("spread") or ""),
                        "lower_limit": str(measurement.get("lowerLimit") or ""),
                        "upper_limit": str(measurement.get("upperLimit") or ""),
                        "comment": _text(measurement.get("comment")),
                    }
                )
            rows.append(
                {
                    "label": label,
                    "class_index": class_index,
                    "category_index": category_index,
                    "denominators": class_denoms,
                    "values": values,
                }
            )
            if len(rows) >= MAX_ROWS_PER_MEASURE:
                break
        if len(rows) >= MAX_ROWS_PER_MEASURE:
            break
    analyses = [_normalize_analysis(item, group_map) for item in raw.get("analyses") or [] if isinstance(item, dict)]
    return {
        "type": str(raw.get("type") or "BASELINE"),
        "title": str(raw.get("title") or "").strip(),
        "description": _text(raw.get("description")),
        "population_description": _text(raw.get("populationDescription")),
        "reporting_status": str(raw.get("reportingStatus") or ""),
        "param_type": str(raw.get("paramType") or ""),
        "dispersion_type": str(raw.get("dispersionType") or ""),
        "unit": str(raw.get("unitOfMeasure") or ""),
        "time_frame": str(raw.get("timeFrame") or ""),
        "groups": groups,
        "denominators": denoms,
        "rows": rows,
        "rows_truncated": sum(
            len(item.get("categories") or [])
            for item in raw.get("classes") or []
            if isinstance(item, dict)
        ) > len(rows),
        "analyses": analyses,
    }


def _normalize_analysis(raw: dict[str, Any], group_map: dict[str, str]) -> dict[str, Any]:
    group_ids = [str(item) for item in raw.get("groupIds") or []]
    return {
        "groups": [group_map.get(item, item) for item in group_ids],
        "group_ids": group_ids,
        "group_description": _text(raw.get("groupDescription")),
        "method": str(raw.get("statisticalMethod") or ""),
        "p_value": str(raw.get("pValue") or ""),
        "p_value_comment": _text(raw.get("pValueComment")),
        "parameter": str(raw.get("paramType") or ""),
        "parameter_value": str(raw.get("paramValue") or ""),
        "ci_percent": str(raw.get("ciPctValue") or ""),
        "ci_sides": str(raw.get("ciNumSides") or ""),
        "ci_lower": str(raw.get("ciLowerLimit") or ""),
        "ci_upper": str(raw.get("ciUpperLimit") or ""),
        "estimate_comment": _text(raw.get("estimateComment")),
        "non_inferiority_type": str(raw.get("nonInferiorityType") or ""),
        "non_inferiority_comment": _text(raw.get("nonInferiorityComment")),
        "statistical_comment": _text(raw.get("statisticalComment")),
        "other_analysis": _text(raw.get("otherAnalysisDescription")),
    }


def _normalize_adverse_events(module: dict[str, Any]) -> dict[str, Any]:
    groups = []
    for item in module.get("eventGroups") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        groups.append(
            {
                "id": str(item.get("id")),
                "title": str(item.get("title") or item.get("id")),
                "deaths_affected": _integer(item.get("deathsNumAffected")),
                "deaths_at_risk": _integer(item.get("deathsNumAtRisk")),
                "serious_affected": _integer(item.get("seriousNumAffected")),
                "serious_at_risk": _integer(item.get("seriousNumAtRisk")),
                "other_affected": _integer(item.get("otherNumAffected")),
                "other_at_risk": _integer(item.get("otherNumAtRisk")),
            }
        )
    group_map = {item["id"]: item["title"] for item in groups}
    raw_serious = module.get("seriousEvents") or []
    raw_other = module.get("otherEvents") or []
    serious = [_normalize_event(item, group_map) for item in raw_serious[:MAX_EVENTS] if isinstance(item, dict)]
    other = [_normalize_event(item, group_map) for item in raw_other[:MAX_EVENTS] if isinstance(item, dict)]
    return {
        "time_frame": _text(module.get("timeFrame")),
        "description": _text(module.get("description")),
        "frequency_threshold_percent": str(module.get("frequencyThreshold") or ""),
        "groups": groups,
        "serious_events": serious,
        "other_events": other,
        "serious_event_term_count": len(raw_serious),
        "other_event_term_count": len(raw_other),
        "serious_events_truncated": len(raw_serious) > len(serious),
        "other_events_truncated": len(raw_other) > len(other),
    }


def _normalize_event(raw: dict[str, Any], group_map: dict[str, str]) -> dict[str, Any]:
    stats = []
    for item in raw.get("stats") or []:
        if not isinstance(item, dict):
            continue
        group_id = str(item.get("groupId") or "")
        stats.append(
            {
                "group_id": group_id,
                "group": group_map.get(group_id, group_id),
                "affected": _integer(item.get("numAffected")),
                "at_risk": _integer(item.get("numAtRisk")),
                "events": _integer(item.get("numEvents")),
            }
        )
    return {
        "term": str(raw.get("term") or ""),
        "organ_system": str(raw.get("organSystem") or ""),
        "source_vocabulary": str(raw.get("sourceVocabulary") or ""),
        "assessment_type": str(raw.get("assessmentType") or ""),
        "notes": _text(raw.get("notes")),
        "stats": stats,
    }


def _normalize_publications(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    publications = []
    for item in ((protocol.get("referencesModule") or {}).get("references") or [])[:MAX_PUBLICATIONS]:
        if not isinstance(item, dict) or not (item.get("pmid") or item.get("citation")):
            continue
        pmid = str(item.get("pmid") or "").strip()
        publications.append(
            {
                "pmid": pmid or None,
                "type": str(item.get("type") or ""),
                "citation": _text(item.get("citation")),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
            }
        )
    return publications


def _normalize_documents(document_section: dict[str, Any], nct_id: str) -> list[dict[str, Any]]:
    documents = []
    raw_docs = ((document_section.get("largeDocumentModule") or {}).get("largeDocs")) or []
    for item in raw_docs:
        if not isinstance(item, dict) or not item.get("filename"):
            continue
        filename = str(item["filename"])
        documents.append(
            {
                "label": str(item.get("label") or filename),
                "date": str(item.get("date") or ""),
                "upload_date": str(item.get("uploadDate") or ""),
                "filename": filename,
                "size": _integer(item.get("size")),
                "has_protocol": bool(item.get("hasProtocol")),
                "has_sap": bool(item.get("hasSap")),
                "url": f"{CLINICAL_TRIALS_DOCS}/{nct_id[-2:]}/{nct_id}/{quote(filename, safe='._-')}",
            }
        )
    return documents


def _normalize_more_info(module: dict[str, Any]) -> dict[str, Any]:
    agreement = module.get("certainAgreement") or {}
    return {
        "limitations_and_caveats": _text(module.get("limitationsAndCaveats")),
        "restrictive_agreement": bool(agreement.get("restrictiveAgreement")),
        "agreement_restriction_type": str(agreement.get("restrictionType") or ""),
        "agreement_details": _text(agreement.get("otherDetails")),
    }


def _groups(raw_groups: list[Any]) -> list[dict[str, str]]:
    return [
        {
            "id": str(item.get("id")),
            "title": str(item.get("title") or item.get("id")),
            "description": _text(item.get("description")),
        }
        for item in raw_groups
        if isinstance(item, dict) and item.get("id")
    ]


def _subject_values(raw_values: list[Any], group_map: dict[str, str]) -> list[dict[str, Any]]:
    values = []
    for item in raw_values:
        if not isinstance(item, dict):
            continue
        group_id = str(item.get("groupId") or "")
        values.append(
            {
                "group_id": group_id,
                "group": group_map.get(group_id, group_id),
                "subjects": _integer(item.get("numSubjects")),
                "comment": _text(item.get("comment")),
            }
        )
    return values


def _normalize_denoms(raw_denoms: list[Any], group_map: dict[str, str]) -> list[dict[str, Any]]:
    denoms = []
    for item in raw_denoms:
        if not isinstance(item, dict):
            continue
        counts = []
        for count in item.get("counts") or []:
            if not isinstance(count, dict):
                continue
            group_id = str(count.get("groupId") or "")
            counts.append(
                {
                    "group_id": group_id,
                    "group": group_map.get(group_id, group_id),
                    "value": str(count.get("value") or ""),
                }
            )
        denoms.append({"units": str(item.get("units") or ""), "counts": counts})
    return denoms


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "participant_flow": f"{relative_root}/participant_flow.tsv",
        "baseline": f"{relative_root}/baseline.tsv",
        "outcomes": f"{relative_root}/outcomes.tsv",
        "analyses": f"{relative_root}/statistical_analyses.tsv",
        "adverse_events": f"{relative_root}/adverse_events.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="clinical-results-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_flow(output / "participant_flow.tsv", result["participant_flow"])
        _write_measure_rows(output / "baseline.tsv", result["baseline"]["measures"])
        _write_measure_rows(output / "outcomes.tsv", result["outcomes"])
        _write_analyses(output / "statistical_analyses.tsv", result["outcomes"])
        _write_adverse_events(output / "adverse_events.tsv", result["adverse_events"])
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "source": result["source"],
            "source_url": result["source_url"],
            "api_url": result["api_url"],
            "retrieved_at": result["retrieved_at"],
            "nct_id": result["nct_id"],
            "bounds": {
                "max_outcomes": MAX_OUTCOMES,
                "max_rows_per_measure": MAX_ROWS_PER_MEASURE,
                "max_baseline_measures": MAX_BASELINE_MEASURES,
                "max_events_per_class": MAX_EVENTS,
                "max_publications": MAX_PUBLICATIONS,
            },
            "truncation": {
                "outcomes": result["outcomes_truncated"],
                "baseline": result["baseline"]["measures_truncated"],
                "serious_events": result["adverse_events"]["serious_events_truncated"],
                "other_events": result["adverse_events"]["other_events_truncated"],
            },
            "files": [path.rsplit("/", 1)[-1] for path in result["outputs"].values()],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise ClinicalTrialResultsError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_flow(path: Path, flow: dict[str, Any]) -> None:
    fields = ["period", "record_type", "label", "group_id", "group", "subjects", "comment"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for period in flow["periods"]:
            for milestone in period["milestones"]:
                for value in milestone["values"]:
                    writer.writerow(
                        {
                            "period": period["title"],
                            "record_type": "milestone",
                            "label": milestone["type"],
                            "group_id": value["group_id"],
                            "group": value["group"],
                            "subjects": value["subjects"],
                            "comment": value["comment"] or milestone["comment"],
                        }
                    )
            for reason in period["withdrawals"]:
                for value in reason["values"]:
                    writer.writerow(
                        {
                            "period": period["title"],
                            "record_type": "withdrawal",
                            "label": reason["reason"],
                            "group_id": value["group_id"],
                            "group": value["group"],
                            "subjects": value["subjects"],
                            "comment": value["comment"],
                        }
                    )


def _write_measure_rows(path: Path, measures: list[dict[str, Any]]) -> None:
    fields = [
        "measure_index",
        "measure_type",
        "title",
        "time_frame",
        "param_type",
        "dispersion_type",
        "unit",
        "row",
        "group_id",
        "group",
        "value",
        "spread",
        "lower_limit",
        "upper_limit",
        "comment",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for measure_index, measure in enumerate(measures, 1):
            for row in measure["rows"]:
                for value in row["values"]:
                    writer.writerow(
                        {
                            "measure_index": measure_index,
                            "measure_type": measure["type"],
                            "title": measure["title"],
                            "time_frame": measure["time_frame"],
                            "param_type": measure["param_type"],
                            "dispersion_type": measure["dispersion_type"],
                            "unit": measure["unit"],
                            "row": row["label"],
                            **{key: value.get(key, "") for key in fields if key in value},
                        }
                    )


def _write_analyses(path: Path, measures: list[dict[str, Any]]) -> None:
    fields = [
        "measure_index",
        "measure_type",
        "title",
        "analysis_index",
        "groups",
        "method",
        "p_value",
        "parameter",
        "parameter_value",
        "ci_percent",
        "ci_lower",
        "ci_upper",
        "estimate_comment",
        "non_inferiority_type",
        "group_description",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for measure_index, measure in enumerate(measures, 1):
            for analysis_index, analysis in enumerate(measure["analyses"], 1):
                writer.writerow(
                    {
                        "measure_index": measure_index,
                        "measure_type": measure["type"],
                        "title": measure["title"],
                        "analysis_index": analysis_index,
                        "groups": "; ".join(analysis["groups"]),
                        **{key: analysis.get(key, "") for key in fields if key in analysis},
                    }
                )


def _write_adverse_events(path: Path, adverse: dict[str, Any]) -> None:
    fields = [
        "event_class",
        "term",
        "organ_system",
        "assessment_type",
        "group_id",
        "group",
        "affected",
        "at_risk",
        "events",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for event_class, events in (
            ("serious", adverse["serious_events"]),
            ("other", adverse["other_events"]),
        ):
            for event in events:
                for stat in event["stats"]:
                    writer.writerow(
                        {
                            "event_class": event_class,
                            "term": event["term"],
                            "organ_system": event["organ_system"],
                            "assessment_type": event["assessment_type"],
                            **{key: stat.get(key, "") for key in fields if key in stat},
                        }
                    )


def _summary_markdown(result: dict[str, Any]) -> str:
    study = result["study"]
    lines = [
        f"# Posted results review: {result['nct_id']}",
        "",
        f"**{study['title']}**",
        "",
        result["summary"],
        "",
        "## Study design",
        "",
        f"- Status: {study['status']}",
        f"- Phase: {', '.join(study['phases']) or 'n/a'}",
        f"- Enrollment: {study['enrollment']} {study['enrollment_type']}",
        f"- Sponsor: {study['sponsor']} ({study['sponsor_class']})",
        "",
        "## Submitted primary outcomes",
        "",
    ]
    for measure in [item for item in result["outcomes"] if item["type"] == "PRIMARY"]:
        lines.append(f"### {measure['title']}")
        lines.append("")
        lines.append(f"Time frame: {measure['time_frame']}; unit: {measure['unit'] or 'n/a'}")
        lines.append("")
        for row in measure["rows"][:8]:
            values = "; ".join(
                f"{item['group']}: {item['value']}"
                + (f" ({item['lower_limit']} to {item['upper_limit']})" if item["lower_limit"] or item["upper_limit"] else "")
                for item in row["values"]
            )
            lines.append(f"- {row['label']}: {values}")
        for analysis in measure["analyses"]:
            estimate = " ".join(
                value
                for value in (
                    analysis["parameter"],
                    analysis["parameter_value"],
                    f"{analysis['ci_percent']}% CI {analysis['ci_lower']} to {analysis['ci_upper']}"
                    if analysis["ci_lower"] or analysis["ci_upper"]
                    else "",
                    f"p={analysis['p_value']}" if analysis["p_value"] else "",
                )
                if value
            )
            lines.append(f"- Submitted analysis: {estimate or analysis['method']}")
        lines.append("")
    lines.extend(["## Adverse-event group totals", ""])
    for group in result["adverse_events"]["groups"]:
        lines.append(
            f"- {group['title']}: deaths {group['deaths_affected']}/{group['deaths_at_risk']}; "
            f"serious events {group['serious_affected']}/{group['serious_at_risk']}"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _text(value: Any) -> str:
    cleaned = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(cleaned) <= MAX_TEXT_CHARS:
        return cleaned
    return cleaned[:MAX_TEXT_CHARS].rsplit(" ", 1)[0] + "..."


def _date(value: Any) -> str:
    return str((value or {}).get("date") or "") if isinstance(value, dict) else ""


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
