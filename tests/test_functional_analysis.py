import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_runtime import local_workflow_plan
from bio_clients import ExternalDataError
from functional_analysis import (
    FunctionalAnalysisError,
    parse_gene_terms,
    parse_reactome_payload,
    run_functional_analysis,
)
from skill_runtime import SkillError, SkillRegistry
from workflow_runtime import WorkflowManager


MAPPING = [
    {
        "queryIndex": index,
        "queryItem": name,
        "stringId": f"9606.ENSP{index + 1:011d}",
        "preferredName": name,
        "annotation": f"{name} annotation",
    }
    for index, name in enumerate(["TP53", "MDM2", "ATM", "CDKN1A"])
]

REACTOME = {
    "summary": {"token": "test-token", "type": "OVERREPRESENTATION"},
    "identifiersNotFound": 0,
    "pathwaysFound": 2,
    "pathways": [
        {
            "stId": "R-HSA-3700989",
            "name": "Transcriptional Regulation by TP53",
            "species": {"taxId": "9606", "name": "Homo sapiens"},
            "entities": {"found": 10, "total": 487, "pValue": 5.55e-16, "fdr": 1.3e-13},
            "inDisease": False,
        },
        {
            "stId": "R-HSA-999",
            "name": "Disease pathway",
            "species": {"taxId": "9606", "name": "Homo sapiens"},
            "entities": {"found": 2, "total": 20, "pValue": 0.01, "fdr": 0.03},
            "inDisease": True,
        },
    ],
}

NETWORK = [
    {
        "stringId_A": MAPPING[0]["stringId"],
        "stringId_B": MAPPING[1]["stringId"],
        "preferredName_A": "TP53",
        "preferredName_B": "MDM2",
        "score": 0.991,
        "escore": 0.8,
        "dscore": 0.7,
        "tscore": 0.6,
    },
    {
        "stringId_A": MAPPING[0]["stringId"],
        "stringId_B": MAPPING[2]["stringId"],
        "preferredName_A": "TP53",
        "preferredName_B": "ATM",
        "score": 0.95,
    },
]

PPI = [
    {
        "number_of_nodes": 4,
        "number_of_edges": 2,
        "average_node_degree": 1.0,
        "local_clustering_coefficient": 0.0,
        "expected_number_of_edges": 1,
        "p_value": 0.04,
    }
]

ENRICHMENT = [
    {
        "category": "Process",
        "term": "GO:0006974",
        "description": "DNA damage response",
        "preferredNames": ["TP53", "ATM"],
        "number_of_genes": 2,
        "number_of_genes_in_background": 300,
        "p_value": 1e-5,
        "fdr": 0.002,
    }
]


def string_response(url, _fields):
    if url.endswith("/get_string_ids"):
        return MAPPING
    if url.endswith("/network"):
        return NETWORK
    if url.endswith("/ppi_enrichment"):
        return PPI
    if url.endswith("/enrichment"):
        return ENRICHMENT
    raise AssertionError(f"Unexpected STRING URL: {url}")


class FunctionalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_gene_terms_are_bounded_and_unique(self):
        self.assertEqual(parse_gene_terms("TP53, MDM2\nATM"), ["TP53", "MDM2", "ATM"])
        with self.assertRaises(FunctionalAnalysisError):
            parse_gene_terms("TP53")
        with self.assertRaises(FunctionalAnalysisError):
            parse_gene_terms("TP53, tp53")

    def test_reactome_parser_preserves_small_fdr_and_excludes_disease_pathways(self):
        result = parse_reactome_payload(
            REACTOME,
            {"fdr_threshold": 0.05, "max_terms": 20, "include_disease_pathways": False},
        )

        self.assertEqual(result["significant_count"], 1)
        self.assertEqual(result["pathways"][0]["fdr"], 1.3e-13)
        self.assertEqual(result["pathways"][0]["id"], "R-HSA-3700989")

    def test_approved_analysis_persists_tables_and_provenance(self):
        with tempfile.TemporaryDirectory() as workspace:
            with (
                patch("functional_analysis.WORKSPACE_ROOT", Path(workspace)),
                patch("functional_analysis.post_text_json", return_value=REACTOME),
                patch("functional_analysis.post_form_json_array", side_effect=string_response),
            ):
                result = run_functional_analysis("TP53, MDM2, ATM, CDKN1A", max_terms=10)

            output = Path(workspace) / result["output_root"]
            self.assertEqual(result["network"]["node_count"], 4)
            self.assertEqual(result["network"]["edge_count"], 2)
            self.assertEqual(result["ppi_enrichment"]["p_value"], 0.04)
            self.assertEqual(result["reactome"]["significant_count"], 1)
            self.assertTrue((output / "reactome_pathways.tsv").is_file())
            self.assertTrue((output / "string_edges.tsv").is_file())
            manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["api_versions"]["STRING"], "12.0")
            self.assertEqual(manifest["organism"]["taxon_id"], 9606)

    def test_workflow_preflights_then_runs_only_after_approval(self):
        with tempfile.TemporaryDirectory() as storage, tempfile.TemporaryDirectory() as workspace:
            manager = WorkflowManager(Path(storage))
            with (
                patch("functional_analysis.WORKSPACE_ROOT", Path(workspace)),
                patch("functional_analysis.post_text_json", return_value=REACTOME),
                patch("functional_analysis.post_form_json_array", side_effect=string_response),
            ):
                plan = manager.create_plan(
                    "gene-set-functional-analysis",
                    {
                        "genes": "TP53, MDM2, ATM, CDKN1A",
                        "required_score": 400,
                        "fdr_threshold": 0.05,
                        "max_terms": 10,
                        "include_disease_pathways": "false",
                    },
                )
                self.assertEqual(plan["status"], "pending_approval")
                self.assertEqual(plan["trace"], [])
                self.assertEqual(plan["preflight"]["mapped_count"], 4)
                completed = manager.approve(plan["id"], self.registry)

            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["trace"][0]["name"], "functional_analysis_run")
            self.assertIn("functional-analysis", {item["type"] for item in completed["artifacts"]})

    def test_one_string_channel_can_fail_without_discarding_other_results(self):
        def partial_response(url, fields):
            if url.endswith("/enrichment"):
                raise ExternalDataError("temporary enrichment outage")
            return string_response(url, fields)

        with tempfile.TemporaryDirectory() as workspace:
            with (
                patch("functional_analysis.WORKSPACE_ROOT", Path(workspace)),
                patch("functional_analysis.post_text_json", return_value=REACTOME),
                patch("functional_analysis.post_form_json_array", side_effect=partial_response),
            ):
                result = run_functional_analysis("TP53, MDM2, ATM, CDKN1A", max_terms=10)

        self.assertTrue(result["network"]["available"])
        self.assertTrue(result["ppi_enrichment"]["available"])
        self.assertFalse(result["string_enrichment"]["available"])
        self.assertIn("temporary enrichment outage", result["source_warnings"][0])

    def test_agent_builds_gene_set_plan_and_execution_tool_is_hidden(self):
        request = local_workflow_plan(
            "对 TP53, MDM2, ATM, CDKN1A 做 Reactome 通路富集和 STRING 网络，FDR 0.05",
            {},
        )
        exposed = {item["function"]["name"] for item in self.registry.openai_tools()}

        self.assertIsNotNone(request)
        self.assertEqual(request[0], "gene-set-functional-analysis")
        self.assertEqual(request[1]["genes"], "TP53, MDM2, ATM, CDKN1A")
        self.assertIn("functional_analysis_preflight", exposed)
        self.assertNotIn("functional_analysis_run", exposed)
        with self.assertRaises(SkillError):
            self.registry.execute_agent("functional_analysis_run", {"genes": "TP53, MDM2"})


if __name__ == "__main__":
    unittest.main()
