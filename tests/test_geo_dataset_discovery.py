import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_runtime import extract_geo_dataset_plan, local_intent_tools, local_workflow_plan
from geo_dataset_discovery import (
    GeoDatasetError,
    collect_geo_datasets,
    normalize_geo_dataset_inputs,
    preflight_geo_dataset_discovery,
    search_geo_dataset_preview,
)
from skill_runtime import SkillRegistry, compact_tool_result
from workflow_runtime import WorkflowManager


SEARCH_PAYLOAD = {
    "header": {"type": "esearch", "version": "0.3"},
    "esearchresult": {
        "count": "221",
        "retmax": "2",
        "idlist": ["200000001", "200000002"],
        "querytranslation": '(asthma[All Fields]) AND "gse"[Filter]',
    },
}

SUMMARY_PAYLOAD = {
    "header": {"type": "esummary", "version": "0.3"},
    "result": {
        "uids": ["200000001", "200000002"],
        "200000001": {
            "uid": "200000001",
            "accession": "GSE100001",
            "title": "Airway epithelial RNA sequencing in asthma",
            "summary": "Submitter summary describing airway samples and disease groups.",
            "taxon": "Homo sapiens",
            "entrytype": "GSE",
            "gdstype": "Expression profiling by high throughput sequencing",
            "gpl": "24676",
            "pdat": "2025/06/10",
            "suppfile": "TXT; SRA",
            "n_samples": 9,
            "samples": [
                {"accession": f"GSM10000{index}", "title": f"Airway sample {index}"}
                for index in range(1, 10)
            ],
            "pubmedids": ["12345678"],
            "ftplink": "ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE100nnn/GSE100001/",
            "geo2r": "yes",
            "bioproject": "PRJNA100001",
        },
        "200000002": {
            "uid": "200000002",
            "accession": "GSE100002",
            "title": "Asthma expression array cohort",
            "summary": "Array cohort metadata.",
            "taxon": "Homo sapiens",
            "entrytype": "GSE",
            "gdstype": "Expression profiling by array",
            "gpl": "GPL570",
            "pdat": "2024/03/02",
            "suppfile": "CEL",
            "n_samples": 12,
            "samples": [{"accession": "GSM200001", "title": "Case 1"}],
            "pubmedids": [],
            "ftplink": "ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE100nnn/GSE100002/",
            "geo2r": "yes",
            "bioproject": "",
        },
    },
}


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "geo-dataset-discovery",
            "summary": "GEO datasets collected.",
            "artifacts": [{"id": "geo", "type": "geo-dataset-landscape", "data": {}}],
        }


class GeoDatasetDiscoveryTests(unittest.TestCase):
    def test_skill_handler_defaults_match_public_schema(self):
        handler_path = Path(__file__).parents[1] / "skills" / "geo-dataset-discovery" / "scripts" / "handler.py"
        spec = importlib.util.spec_from_file_location("geo_dataset_handler_test", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        preview = module._arguments({"query": "asthma"}, default_max_results=8)
        collect = module._arguments({"query": "asthma"}, default_max_results=12)
        any_organism = module._arguments(
            {"query": "asthma", "organism": ""},
            default_max_results=8,
        )

        self.assertEqual(preview["organism"], "Homo sapiens")
        self.assertEqual(preview["max_results"], 8)
        self.assertEqual(collect["max_results"], 12)
        self.assertEqual(any_organism["organism"], "")

    def test_normalization_builds_exact_gse_query_and_bounds(self):
        result = normalize_geo_dataset_inputs(
            "asthma",
            organism="Homo sapiens",
            assay_scope="single_cell",
            min_samples=6,
            max_results=20,
        )

        self.assertIn("GSE[ETYP]", result["exact_query"])
        self.assertIn('"Homo sapiens"[ORGN]', result["exact_query"])
        self.assertIn('"single cell"[ALL]', result["exact_query"])
        self.assertIn("6:100000[NSAM]", result["exact_query"])
        self.assertEqual(result["sort"], "NCBI GEO relevance")
        with self.assertRaises(GeoDatasetError):
            normalize_geo_dataset_inputs("asthma", max_results=21)
        with self.assertRaises(GeoDatasetError):
            normalize_geo_dataset_inputs("asthma", organism="Homo_sapiens")
        with self.assertRaises(GeoDatasetError):
            normalize_geo_dataset_inputs("asthma sort:date")

    def test_preview_preserves_source_order_and_caps_sample_examples(self):
        with patch("geo_dataset_discovery.get_json", side_effect=[SEARCH_PAYLOAD, SUMMARY_PAYLOAD]):
            result = search_geo_dataset_preview(
                query="asthma",
                organism="Homo sapiens",
                assay_scope="rna_seq",
                min_samples=4,
                max_results=8,
            )

        self.assertEqual([item["accession"] for item in result["datasets"]], ["GSE100001", "GSE100002"])
        self.assertEqual(len(result["datasets"][0]["sample_examples"]), 5)
        self.assertEqual(result["datasets"][0]["platform_accessions"], ["GPL24676"])
        self.assertEqual(result["total_samples"], 21)
        self.assertEqual(result["publication_count"], 1)
        self.assertTrue(result["datasets"][0]["download_url"].startswith("https://ftp.ncbi.nlm.nih.gov/"))
        self.assertNotIn("samples", result["datasets"][0])

    def test_preflight_uses_count_only_and_records_query_translation(self):
        with patch("geo_dataset_discovery.get_json", return_value=SEARCH_PAYLOAD) as mocked:
            result = preflight_geo_dataset_discovery(query="asthma", max_results=12)

        self.assertEqual(result["hit_count"], 221)
        self.assertIn("asthma", result["query_translation"])
        self.assertIn("retmax=0", mocked.call_args.args[0])

    def test_approved_collection_persists_manifest_and_tables(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "geo_dataset_discovery.get_json", side_effect=[SEARCH_PAYLOAD, SUMMARY_PAYLOAD]
        ), patch("geo_dataset_discovery.WORKSPACE_ROOT", Path(temporary)):
            result = collect_geo_datasets(query="asthma", assay_scope="rna_seq", max_results=12)

            root = Path(temporary) / result["output_root"]
            self.assertTrue((root / "datasets.tsv").is_file())
            self.assertTrue((root / "sample_examples.tsv").is_file())
            manifest = json.loads((root / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertIn("GSE[ETYP]", manifest["exact_query"])
            self.assertEqual(manifest["filters"]["assay_scope"], "rna_seq")
            self.assertIn("no API key", manifest["api"]["authentication"])
            self.assertEqual(len(manifest["files"]), 5)

    def test_agent_routes_preview_and_approved_collection_separately(self):
        question = "在 GEO 中查找 Homo sapiens 哮喘 RNA-seq 公共数据集，至少 4 个样本"
        preview = "先预览 GEO 中的哮喘 RNA-seq 公共数据集，至少 4 个样本"
        registry = SkillRegistry()
        exposed = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(extract_geo_dataset_plan(question)["query"], "asthma")
        self.assertEqual(local_workflow_plan(question, {})[0], "public-omics-dataset-discovery")
        self.assertIsNone(local_workflow_plan(preview, {}))
        self.assertEqual(local_intent_tools(preview)[0][0], "geo_dataset_preview")
        self.assertIn("geo_dataset_preview", exposed)
        self.assertNotIn("geo_dataset_collect", exposed)

    def test_workflow_preflights_then_collects_only_after_approval(self):
        registry = RecordingRegistry()
        preflight = {
            "ready": True,
            "source": "NCBI GEO",
            "summary": "NCBI GEO found 221 Series.",
            "exact_query": "(asthma) AND GSE[ETYP]",
            "hit_count": 221,
        }
        with tempfile.TemporaryDirectory() as temporary, patch(
            "workflow_runtime.preflight_geo_dataset_discovery", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "public-omics-dataset-discovery",
                {
                    "query": "asthma",
                    "organism": "Homo sapiens",
                    "assay_scope": "rna_seq",
                    "min_samples": 4,
                    "max_results": 12,
                },
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "geo_dataset_collect")

    def test_model_compaction_keeps_dataset_identifiers_without_full_samples(self):
        with patch("geo_dataset_discovery.get_json", side_effect=[SEARCH_PAYLOAD, SUMMARY_PAYLOAD]):
            data = search_geo_dataset_preview(query="asthma", max_results=8)
        result = {
            "ok": True,
            "tool": "geo_dataset_preview",
            "skill": "geo-dataset-discovery",
            "summary": data["summary"],
            "data": data,
            "artifacts": [{"data": SUMMARY_PAYLOAD}] * 5,
        }

        encoded = compact_tool_result(result)
        compact = json.loads(encoded)
        self.assertEqual(compact["data"]["datasets"][0]["accession"], "GSE100001")
        self.assertLessEqual(len(compact["data"]["datasets"][0]["sample_examples"]), 3)
        self.assertNotIn("artifacts", compact)
        self.assertLessEqual(len(encoded), 24000)


if __name__ == "__main__":
    unittest.main()
