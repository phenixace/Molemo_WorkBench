import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.agent_runtime import extract_clinical_results_plan, local_workflow_plan
from molemo.clinical_trial_results import (
    ClinicalTrialResultsError,
    normalize_nct_id,
    parse_clinical_trial_results,
    preflight_clinical_trial_results,
    review_clinical_trial_results,
)
from molemo.skill_runtime import SkillRegistry
from molemo.workflow_runtime import WorkflowManager


GROUPS = [
    {"id": "OG000", "title": "Placebo"},
    {"id": "OG001", "title": "Dupilumab"},
]

CLINICAL_RESULTS_PAYLOAD = {
    "hasResults": True,
    "protocolSection": {
        "identificationModule": {
            "nctId": "NCT02414854",
            "briefTitle": "Dupilumab in uncontrolled asthma",
            "officialTitle": "A randomized study of dupilumab in uncontrolled asthma",
        },
        "statusModule": {
            "overallStatus": "COMPLETED",
            "startDateStruct": {"date": "2015-05-01"},
            "primaryCompletionDateStruct": {"date": "2017-03-01"},
            "completionDateStruct": {"date": "2017-06-01"},
            "resultsFirstPostDateStruct": {"date": "2018-05-01"},
            "lastUpdatePostDateStruct": {"date": "2024-06-01"},
        },
        "sponsorCollaboratorsModule": {
            "leadSponsor": {"name": "Example Sponsor", "class": "INDUSTRY"}
        },
        "conditionsModule": {"conditions": ["Asthma"]},
        "designModule": {
            "studyType": "INTERVENTIONAL",
            "phases": ["PHASE3"],
            "designInfo": {
                "allocation": "RANDOMIZED",
                "interventionModel": "PARALLEL",
                "primaryPurpose": "TREATMENT",
                "maskingInfo": {"masking": "QUADRUPLE"},
            },
            "enrollmentInfo": {"count": 631, "type": "ACTUAL"},
        },
        "armsInterventionsModule": {
            "armGroups": [
                {"label": "Placebo", "type": "PLACEBO_COMPARATOR"},
                {"label": "Dupilumab", "type": "EXPERIMENTAL"},
            ],
            "interventions": [
                {"type": "DRUG", "name": "Placebo", "armGroupLabels": ["Placebo"]},
                {"type": "BIOLOGICAL", "name": "Dupilumab", "armGroupLabels": ["Dupilumab"]},
            ],
        },
        "referencesModule": {
            "references": [
                {"pmid": "29782217", "type": "RESULT", "citation": "Example result paper."}
            ]
        },
    },
    "resultsSection": {
        "participantFlowModule": {
            "groups": [
                {"id": "FG000", "title": "Placebo"},
                {"id": "FG001", "title": "Dupilumab"},
            ],
            "periods": [
                {
                    "title": "Overall Study",
                    "milestones": [
                        {
                            "type": "STARTED",
                            "achievements": [
                                {"groupId": "FG000", "numSubjects": 317},
                                {"groupId": "FG001", "numSubjects": 314},
                            ],
                        },
                        {
                            "type": "COMPLETED",
                            "achievements": [
                                {"groupId": "FG000", "numSubjects": 282},
                                {"groupId": "FG001", "numSubjects": 288},
                            ],
                        },
                    ],
                }
            ],
        },
        "baselineCharacteristicsModule": {
            "groups": [
                {"id": "BG000", "title": "Placebo"},
                {"id": "BG001", "title": "Dupilumab"},
            ],
            "measures": [
                {
                    "title": "Age",
                    "paramType": "MEAN",
                    "dispersionType": "STANDARD_DEVIATION",
                    "unitOfMeasure": "years",
                    "classes": [
                        {
                            "categories": [
                                {
                                    "measurements": [
                                        {"groupId": "BG000", "value": "48.2", "spread": "15.6"},
                                        {"groupId": "BG001", "value": "47.9", "spread": "14.8"},
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ],
        },
        "outcomeMeasuresModule": {
            "outcomeMeasures": [
                {
                    "type": "PRIMARY",
                    "title": "Annualized severe exacerbation rate",
                    "timeFrame": "52 weeks",
                    "paramType": "RATE_RATIO",
                    "unitOfMeasure": "events per patient-year",
                    "groups": GROUPS,
                    "classes": [
                        {
                            "categories": [
                                {
                                    "measurements": [
                                        {"groupId": "OG000", "value": "0.871", "lowerLimit": "0.724", "upperLimit": "1.048"},
                                        {"groupId": "OG001", "value": "0.459", "lowerLimit": "0.365", "upperLimit": "0.577"},
                                    ]
                                }
                            ]
                        }
                    ],
                    "analyses": [
                        {
                            "groupIds": ["OG000", "OG001"],
                            "statisticalMethod": "Negative binomial regression",
                            "pValue": "<0.0001",
                            "paramType": "RATE_RATIO",
                            "paramValue": "0.526",
                            "ciPctValue": "95",
                            "ciLowerLimit": "0.401",
                            "ciUpperLimit": "0.689",
                        }
                    ],
                },
                {
                    "type": "SECONDARY",
                    "title": "Change from baseline in FEV1",
                    "timeFrame": "Week 12",
                    "paramType": "MEAN",
                    "unitOfMeasure": "liters",
                    "groups": GROUPS,
                    "classes": [],
                },
            ]
        },
        "adverseEventsModule": {
            "timeFrame": "Up to 64 weeks",
            "eventGroups": [
                {
                    "id": "EG000",
                    "title": "Placebo",
                    "deathsNumAffected": 1,
                    "deathsNumAtRisk": 317,
                    "seriousNumAffected": 25,
                    "seriousNumAtRisk": 317,
                    "otherNumAffected": 220,
                    "otherNumAtRisk": 317,
                },
                {
                    "id": "EG001",
                    "title": "Dupilumab",
                    "deathsNumAffected": 0,
                    "deathsNumAtRisk": 314,
                    "seriousNumAffected": 18,
                    "seriousNumAtRisk": 314,
                    "otherNumAffected": 215,
                    "otherNumAtRisk": 314,
                },
            ],
            "seriousEvents": [
                {
                    "term": "Pneumonia",
                    "organSystem": "Respiratory disorders",
                    "assessmentType": "SYSTEMATIC_ASSESSMENT",
                    "stats": [
                        {"groupId": "EG000", "numAffected": 3, "numAtRisk": 317, "numEvents": 3},
                        {"groupId": "EG001", "numAffected": 1, "numAtRisk": 314, "numEvents": 1},
                    ],
                }
            ],
            "otherEvents": [
                {
                    "term": "Injection site reaction",
                    "organSystem": "General disorders",
                    "stats": [
                        {"groupId": "EG000", "numAffected": 12, "numAtRisk": 317},
                        {"groupId": "EG001", "numAffected": 35, "numAtRisk": 314},
                    ],
                }
            ],
        },
        "moreInfoModule": {"limitationsAndCaveats": "Registry-submitted summary."},
    },
    "documentSection": {
        "largeDocumentModule": {
            "largeDocs": [
                {
                    "label": "Study Protocol and Statistical Analysis Plan",
                    "filename": "Prot_SAP_000.pdf",
                    "hasProtocol": True,
                    "hasSap": True,
                }
            ]
        }
    },
}


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "clinical-trial-landscape",
            "summary": "Posted results captured.",
            "artifacts": [{"id": "results", "type": "clinical-trial-results", "data": {}}],
        }


class ClinicalTrialResultsTests(unittest.TestCase):
    def test_exact_identifier_and_posted_results_are_required(self):
        self.assertEqual(normalize_nct_id("nct02414854"), "NCT02414854")
        with self.assertRaises(ClinicalTrialResultsError):
            normalize_nct_id("NCT123")
        with patch("molemo.clinical_trial_results.get_json", return_value={"protocolSection": {}, "hasResults": False}):
            with self.assertRaises(ClinicalTrialResultsError):
                preflight_clinical_trial_results("NCT02414854")

    def test_parser_preserves_submitted_values_group_context_and_sources(self):
        result = parse_clinical_trial_results(
            CLINICAL_RESULTS_PAYLOAD,
            "NCT02414854",
            "https://clinicaltrials.gov/api/v2/studies/NCT02414854?format=json",
        )

        self.assertEqual(result["participant_flow"]["periods"][0]["milestones"][0]["values"][0]["subjects"], 317)
        self.assertEqual(result["baseline"]["measures"][0]["rows"][0]["values"][0]["group"], "Placebo")
        self.assertEqual(result["outcomes"][0]["rows"][0]["values"][0]["value"], "0.871")
        self.assertEqual(result["outcomes"][0]["analyses"][0]["p_value"], "<0.0001")
        self.assertEqual(result["outcomes"][0]["analyses"][0]["ci_lower"], "0.401")
        self.assertEqual(result["adverse_events"]["groups"][0]["serious_at_risk"], 317)
        self.assertTrue(result["documents"][0]["url"].endswith("/54/NCT02414854/Prot_SAP_000.pdf"))
        self.assertIn("No effect conclusion was generated.", result["summary"])

    def test_approved_review_atomically_persists_all_audit_files(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.clinical_trial_results.get_json", return_value=CLINICAL_RESULTS_PAYLOAD
        ), patch("molemo.clinical_trial_results.WORKSPACE_ROOT", Path(temporary)):
            result = review_clinical_trial_results("NCT02414854")
            outputs = [Path(temporary) / path for path in result["outputs"].values()]
            files_exist = all(path.is_file() for path in outputs)
            manifest = json.loads(
                (Path(temporary) / result["outputs"]["manifest"]).read_text(encoding="utf-8")
            )

        self.assertEqual(len(outputs), 8)
        self.assertTrue(files_exist)
        self.assertEqual(manifest["nct_id"], "NCT02414854")
        self.assertEqual(manifest["files"], [path.name for path in outputs])

    def test_agent_routes_exact_results_and_hides_full_review_tool(self):
        question = "请审阅 NCT02414854 的 posted results、主要结局和不良事件"
        template, inputs = local_workflow_plan(question, {})
        exposed = {item["function"]["name"] for item in SkillRegistry().openai_tools()}

        self.assertEqual(extract_clinical_results_plan(question), {"nct_id": "NCT02414854"})
        self.assertEqual(template, "clinical-trial-results-review")
        self.assertEqual(inputs, {"nct_id": "NCT02414854"})
        self.assertIn("clinical_trial_results_preflight", exposed)
        self.assertNotIn("clinical_trial_results_review", exposed)

    def test_workflow_preflights_but_reviews_only_after_approval(self):
        preflight = {
            "ready": True,
            "summary": "Resolved NCT02414854 with posted results.",
            "nct_id": "NCT02414854",
            "study": {"nct_id": "NCT02414854"},
        }
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.workflow_runtime.preflight_clinical_trial_results", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "clinical-trial-results-review", {"nct_id": "nct02414854"}
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(run["inputs"]["nct_id"], "NCT02414854")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(
            registry.calls,
            [("clinical_trial_results_review", {"nct_id": "NCT02414854"})],
        )


if __name__ == "__main__":
    unittest.main()
