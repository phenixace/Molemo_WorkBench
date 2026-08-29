import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_runtime import local_workflow_plan
from skill_runtime import SkillRegistry
from target_evidence import TargetEvidenceError, parse_target_terms, review_target_evidence


def fake_open_targets(_url, request):
    query = request["query"]
    if "SearchDisease" in query:
        return {
            "data": {
                "search": {
                    "total": 1,
                    "hits": [
                        {
                            "id": "MONDO_0004979",
                            "name": "asthma",
                            "entity": "disease",
                            "description": "A bronchial disease.",
                        }
                    ],
                }
            }
        }
    if "ResolveTargets" in query:
        return {
            "data": {
                "mapIds": {
                    "mappings": [
                        {"term": "IL4R", "hits": [{"id": "ENSG00000077238", "name": "IL4R", "entity": "target"}]},
                        {"term": "TSLP", "hits": [{"id": "ENSG00000145777", "name": "TSLP", "entity": "target"}]},
                    ]
                }
            }
        }
    if "ReviewTargets" in query:
        return {
            "data": {
                "disease": {
                    "id": "MONDO_0004979",
                    "name": "asthma",
                    "description": "A bronchial disease.",
                    "associatedTargets": {
                        "count": 2,
                        "rows": [
                            {
                                "score": 0.72,
                                "novelty": 0.2,
                                "target": {"id": "ENSG00000145777", "approvedSymbol": "TSLP", "approvedName": "thymic stromal lymphopoietin", "biotype": "protein_coding"},
                                "datatypeScores": [{"id": "clinical", "score": 0.94}, {"id": "genetic_association", "score": 0.88}],
                                "datasourceScores": [{"id": "clinical_precedence", "score": 0.94}],
                            },
                            {
                                "score": 0.74,
                                "novelty": 0.1,
                                "target": {"id": "ENSG00000077238", "approvedSymbol": "IL4R", "approvedName": "interleukin 4 receptor", "biotype": "protein_coding"},
                                "datatypeScores": [{"id": "clinical", "score": 0.97}, {"id": "genetic_association", "score": 0.93}],
                                "datasourceScores": [{"id": "clinical_precedence", "score": 0.97}],
                            },
                        ],
                    },
                    "clinical": {
                        "count": 1,
                        "rows": [
                            {
                                "id": "e1",
                                "target": {"id": "ENSG00000077238", "approvedSymbol": "IL4R"},
                                "score": 1.0,
                                "literature": ["12345"],
                                "drug": {"id": "CHEMBL2108675", "name": "DUPILUMAB", "maximumClinicalStage": "APPROVAL", "drugType": "Antibody"},
                                "directionOnTarget": "LoF",
                                "directionOnTrait": "protect",
                            }
                        ],
                    },
                    "literature": {"count": 1, "rows": [{"target": {"id": "ENSG00000145777"}, "literature": ["67890"]}]},
                },
                "targets": [
                    {
                        "id": "ENSG00000077238",
                        "approvedSymbol": "IL4R",
                        "approvedName": "interleukin 4 receptor",
                        "biotype": "protein_coding",
                        "tractability": [{"label": "Approved Drug", "modality": "AB", "value": True}],
                        "pathways": [{"pathwayId": "R-HSA-6785807", "pathway": "Interleukin-4 and Interleukin-13 signaling"}],
                        "safetyLiabilities": [],
                    },
                    {
                        "id": "ENSG00000145777",
                        "approvedSymbol": "TSLP",
                        "approvedName": "thymic stromal lymphopoietin",
                        "biotype": "protein_coding",
                        "tractability": [],
                        "pathways": [],
                        "safetyLiabilities": [],
                    },
                ],
            }
        }
    raise AssertionError("unexpected GraphQL query")


class TargetEvidenceTests(unittest.TestCase):
    def test_candidate_parser_is_bounded_and_rejects_duplicates(self):
        self.assertEqual(parse_target_terms("IL4R, TSLP\nIL6R"), ["IL4R", "TSLP", "IL6R"])
        with self.assertRaises(TargetEvidenceError):
            parse_target_terms("IL4R, il4r")
        with self.assertRaises(TargetEvidenceError):
            parse_target_terms(",".join(f"GENE{i}" for i in range(9)))

    def test_review_preserves_source_score_and_persists_auditable_outputs(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "target_evidence.post_json", side_effect=fake_open_targets
        ), patch("target_evidence.WORKSPACE_ROOT", Path(temporary)):
            result = review_target_evidence("哮喘", "IL4R, TSLP")

            self.assertEqual([item["symbol"] for item in result["candidates"]], ["IL4R", "TSLP"])
            self.assertEqual(result["candidates"][0]["association_score"], 0.74)
            self.assertNotIn("composite_score", json.dumps(result))
            self.assertEqual(result["candidates"][0]["drugs"][0]["name"], "DUPILUMAB")
            self.assertTrue((Path(temporary) / result["outputs"]["report"]).is_file())
            self.assertTrue((Path(temporary) / result["outputs"]["evidence_table"]).is_file())

    def test_agent_creates_review_plan_and_cannot_call_comparison_directly(self):
        template, inputs = local_workflow_plan(
            "比较 IL4R、TSLP、IL6R、JAK1 在哮喘中的靶点证据",
            {},
        )
        registry = SkillRegistry()
        exposed_names = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(template, "target-evidence-review")
        self.assertEqual(inputs["disease"], "哮喘")
        self.assertEqual(inputs["candidates"], "IL4R, TSLP, IL6R, JAK1")
        self.assertIn("target_evidence_preflight", exposed_names)
        self.assertNotIn("target_evidence_compare", exposed_names)


if __name__ == "__main__":
    unittest.main()
