import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from molemo.agent_runtime import extract_clinical_trial_plan, local_workflow_plan
from molemo.clinical_trials import (
    ClinicalTrialsError,
    collect_clinical_trial_landscape,
    normalize_clinical_trial_inputs,
    search_clinical_trials_preview,
)
from molemo.skill_runtime import SkillRegistry, compact_tool_result
from molemo.workflow_runtime import WorkflowManager


CLINICAL_TRIALS_PAYLOAD = {
    "totalCount": 59,
    "studies": [
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                    "briefTitle": "Dupilumab in adults with asthma",
                    "officialTitle": "A randomized study of dupilumab in adults with asthma",
                },
                "statusModule": {
                    "overallStatus": "COMPLETED",
                    "startDateStruct": {"date": "2021-01-15"},
                    "primaryCompletionDateStruct": {"date": "2023-06-01"},
                    "completionDateStruct": {"date": "2023-08-01"},
                    "studyFirstPostDateStruct": {"date": "2020-12-01"},
                    "lastUpdatePostDateStruct": {"date": "2024-02-10"},
                },
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Example Biopharma", "class": "INDUSTRY"}
                },
                "descriptionModule": {"briefSummary": "Registry-provided study summary."},
                "conditionsModule": {"conditions": ["Asthma"], "keywords": ["eosinophilic asthma"]},
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "phases": ["PHASE3"],
                    "designInfo": {
                        "allocation": "RANDOMIZED",
                        "interventionModel": "PARALLEL",
                        "primaryPurpose": "TREATMENT",
                        "maskingInfo": {"masking": "QUADRUPLE"},
                    },
                    "enrollmentInfo": {"count": 420, "type": "ACTUAL"},
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"type": "DRUG", "name": "Dupilumab"},
                        {"type": "DRUG", "name": "Placebo"},
                    ]
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {"measure": "Annualized severe exacerbation rate", "timeFrame": "52 weeks"}
                    ],
                    "secondaryOutcomes": [{"measure": "Change in FEV1"}],
                },
                "eligibilityModule": {
                    "sex": "ALL",
                    "minimumAge": "18 Years",
                    "maximumAge": "75 Years",
                    "healthyVolunteers": False,
                },
                "contactsLocationsModule": {
                    "locations": [
                        {"country": "United States"},
                        {"country": "France"},
                        {"country": "United States"},
                    ]
                },
                "referencesModule": {
                    "references": [
                        {"pmid": "12345678", "type": "RESULT", "citation": "Example result paper."}
                    ]
                },
            },
            "hasResults": True,
        },
        {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000002",
                    "briefTitle": "Active asthma biomarker study",
                },
                "statusModule": {"overallStatus": "RECRUITING"},
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Example University", "class": "OTHER"}
                },
                "conditionsModule": {"conditions": ["Asthma"]},
                "designModule": {
                    "studyType": "INTERVENTIONAL",
                    "phases": ["PHASE2"],
                    "enrollmentInfo": {"count": 80, "type": "ESTIMATED"},
                },
                "armsInterventionsModule": {
                    "interventions": [{"type": "BIOLOGICAL", "name": "Dupilumab"}]
                },
                "outcomesModule": {
                    "primaryOutcomes": [{"measure": "Biomarker change", "timeFrame": "24 weeks"}]
                },
                "eligibilityModule": {"sex": "ALL", "healthyVolunteers": False},
                "contactsLocationsModule": {"locations": [{"country": "United Kingdom"}]},
            },
            "hasResults": False,
        },
    ],
}


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "clinical-trial-landscape",
            "summary": "Trial landscape collected.",
            "artifacts": [{"id": "trial-landscape", "type": "clinical-trial-landscape", "data": {}}],
        }


class ClinicalTrialsTests(unittest.TestCase):
    def test_normalization_builds_bounded_official_filters(self):
        result = normalize_clinical_trial_inputs(
            " asthma ",
            " dupilumab ",
            status_scope="active",
            study_scope="interventional",
            max_results=20,
        )

        self.assertEqual(result["condition"], "asthma")
        self.assertEqual(result["query_parameters"]["query.intr"], "dupilumab")
        self.assertEqual(result["query_parameters"]["query.term"], "AREA[StudyType]INTERVENTIONAL")
        self.assertIn("RECRUITING", result["query_parameters"]["filter.overallStatus"])
        with self.assertRaises(ClinicalTrialsError):
            normalize_clinical_trial_inputs("asthma", max_results=31)
        with self.assertRaises(ClinicalTrialsError):
            normalize_clinical_trial_inputs("asthma", status_scope="unknown")

    def test_preview_preserves_source_order_and_registry_evidence_lanes(self):
        with patch("molemo.clinical_trials.get_json", return_value=CLINICAL_TRIALS_PAYLOAD) as request:
            result = search_clinical_trials_preview(
                condition="asthma", intervention="dupilumab", max_results=2
            )

        query = parse_qs(urlparse(request.call_args.args[0]).query)
        self.assertEqual(query["query.cond"], ["asthma"])
        self.assertEqual(query["query.intr"], ["dupilumab"])
        self.assertIn("NCTId", query["fields"][0])
        self.assertEqual([study["nct_id"] for study in result["studies"]], ["NCT00000001", "NCT00000002"])
        self.assertEqual(result["status_counts"][0], {"label": "COMPLETED", "count": 1})
        self.assertEqual(result["results_available_count"], 1)
        self.assertEqual(result["studies"][0]["countries"], ["France", "United States"])
        self.assertEqual(result["studies"][0]["publications"][0]["pmid"], "12345678")
        self.assertIn("not evidence", " ".join(result["caveats"]))

    def test_approved_collection_persists_manifest_report_summary_and_table(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.clinical_trials.get_json", return_value=CLINICAL_TRIALS_PAYLOAD
        ), patch("molemo.clinical_trials.WORKSPACE_ROOT", Path(temporary)):
            result = collect_clinical_trial_landscape(
                condition="asthma", intervention="dupilumab", max_results=2
            )
            files_exist = all((Path(temporary) / path).is_file() for path in result["outputs"].values())
            manifest = json.loads(
                (Path(temporary) / result["outputs"]["manifest"]).read_text(encoding="utf-8")
            )

        self.assertTrue(files_exist)
        self.assertEqual(manifest["condition"], "asthma")
        self.assertEqual(manifest["intervention"], "dupilumab")
        self.assertEqual(manifest["filters"]["max_results"], 2)

    def test_agent_routes_approved_landscape_and_exposes_only_preview(self):
        question = "请梳理 dupilumab 在哮喘中的临床试验版图，关注正在招募"
        plan = extract_clinical_trial_plan(question)
        template, inputs = local_workflow_plan(question, {})
        registry = SkillRegistry()
        exposed = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(plan["condition"], "asthma")
        self.assertEqual(plan["intervention"], "dupilumab")
        self.assertEqual(plan["status_scope"], "active")
        self.assertEqual(template, "clinical-trial-landscape-review")
        self.assertEqual(inputs, plan)
        self.assertIn("clinical_trials_preview", exposed)
        self.assertNotIn("clinical_trials_collect", exposed)

    def test_workflow_preflights_but_collects_only_after_approval(self):
        preflight = {
            "ready": True,
            "summary": "ClinicalTrials.gov found 59 matching studies.",
            "condition": "asthma",
            "intervention": "dupilumab",
            "hit_count": 59,
        }
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.workflow_runtime.preflight_clinical_trial_landscape", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "clinical-trial-landscape-review",
                {
                    "condition": "asthma",
                    "intervention": "dupilumab",
                    "status_scope": "all",
                    "study_scope": "interventional",
                    "max_results": 20,
                },
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(registry.calls, [])

            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "clinical_trials_collect")

    def test_model_compaction_keeps_citable_trial_fields(self):
        study = {
            "rank": 1,
            "nct_id": "NCT00000001",
            "title": "Dupilumab in adults with asthma",
            "brief_summary": "registry text " * 4000,
            "status": "COMPLETED",
            "study_type": "INTERVENTIONAL",
            "phases": ["PHASE3"],
            "enrollment": 420,
            "sponsor": "Example Biopharma",
            "interventions": [{"type": "DRUG", "name": "Dupilumab"}],
            "primary_outcomes": [{"measure": "Exacerbation rate", "time_frame": "52 weeks"}],
            "publications": [{"pmid": "12345678", "type": "RESULT"}],
            "url": "https://clinicaltrials.gov/study/NCT00000001",
        }
        result = {
            "ok": True,
            "tool": "clinical_trials_preview",
            "skill": "clinical-trial-landscape",
            "summary": "Mapped trials.",
            "data": {"condition": "asthma", "studies": [study] * 8},
            "artifacts": [{"data": {"studies": [study] * 8}}] * 4,
        }

        compact = json.loads(compact_tool_result(result))

        self.assertEqual(compact["data"]["studies"][0]["nct_id"], "NCT00000001")
        self.assertEqual(compact["data"]["studies"][0]["publications"][0]["pmid"], "12345678")
        self.assertNotIn("brief_summary", compact["data"]["studies"][0])


if __name__ == "__main__":
    unittest.main()
