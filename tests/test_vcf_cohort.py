import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.agent_runtime import extract_vcf_cohort_plan, local_workflow_plan
from molemo.skill_runtime import SkillRegistry
from molemo.vcf_cohort import (
    VcfCohortError,
    _annotation_for_alt,
    preflight_vcf_cohort,
    review_vcf_cohort,
)
from molemo.workflow_runtime import WorkflowManager


EXAMPLE_VCF = "examples/ctdna_variants.vcf"
EXAMPLE_METADATA = "examples/ctdna_metadata.csv"


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "vcf-cohort-review",
            "summary": "VCF cohort reviewed.",
            "artifacts": [{"id": "vcf-review", "type": "vcf-cohort-review", "data": {}}],
        }


class VcfCohortTests(unittest.TestCase):
    def test_preflight_validates_samples_annotations_and_explicit_filters(self):
        result = preflight_vcf_cohort(EXAMPLE_VCF, EXAMPLE_METADATA)

        self.assertEqual(result["fileformat"], "VCFv4.3")
        self.assertEqual(result["reference"], "GRCh38")
        self.assertEqual(result["sample_count"], 6)
        self.assertEqual(result["subject_count"], 2)
        self.assertEqual(result["record_count"], 6)
        self.assertEqual(result["allele_count"], 7)
        self.assertEqual(result["included_call_count"], 20)
        self.assertEqual(result["low_frequency_call_count"], 2)
        self.assertEqual(result["annotation_sources"], ["CSQ"])
        self.assertEqual(result["thresholds"]["min_vaf"], 0.01)

    def test_multiallelic_ad_and_af_remain_aligned_to_each_alt(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.vcf_cohort.WORKSPACE_ROOT", Path(temporary)
        ), patch("molemo.workspace_utils.WORKSPACE_ROOT", Path(temporary)):
            examples = Path(temporary) / "examples"
            examples.mkdir()
            source_root = Path(__file__).resolve().parents[1] / "workspace" / "examples"
            (examples / "ctdna_variants.vcf").write_bytes(
                (source_root / "ctdna_variants.vcf").read_bytes()
            )
            (examples / "ctdna_metadata.csv").write_bytes(
                (source_root / "ctdna_metadata.csv").read_bytes()
            )
            result = review_vcf_cohort(EXAMPLE_VCF, EXAMPLE_METADATA)

        pik3ca = [item for item in result["variants"] if item["gene"] == "PIK3CA"]
        self.assertEqual(len(pik3ca), 2)
        self.assertEqual(pik3ca[0]["alt"], "A")
        self.assertEqual(pik3ca[0]["included_samples"], ["P01_BASELINE", "P01_WEEK4"])
        self.assertEqual(pik3ca[1]["alt"], "T")
        self.assertEqual(
            pik3ca[1]["included_samples"],
            ["P02_BASELINE", "P02_WEEK4", "P02_WEEK8"],
        )
        self.assertEqual(result["sample_qc"][0]["records_with_depth"], 6)

    def test_annotation_is_not_reused_for_a_different_alt(self):
        info = {
            "CSQ": "A|missense_variant|MODERATE|GENE1|ENSG1|Transcript|ENST1|protein_coding|1/2|c.1G>A|p.Ala1Thr"
        }

        annotation = _annotation_for_alt(info, "T", {})

        self.assertEqual(annotation["annotation_count"], 1)
        self.assertEqual(annotation["annotation_source"], "CSQ")
        self.assertEqual(annotation["gene"], "")
        self.assertEqual(annotation["consequence"], "")

    def test_approved_review_persists_tables_report_manifest_and_input_hashes(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.vcf_cohort.WORKSPACE_ROOT", Path(temporary)
        ), patch("molemo.workspace_utils.WORKSPACE_ROOT", Path(temporary)):
            examples = Path(temporary) / "examples"
            examples.mkdir()
            source_root = Path(__file__).resolve().parents[1] / "workspace" / "examples"
            for name in ("ctdna_variants.vcf", "ctdna_metadata.csv"):
                (examples / name).write_bytes((source_root / name).read_bytes())
            result = review_vcf_cohort(EXAMPLE_VCF, EXAMPLE_METADATA)
            files_exist = all(
                (Path(temporary) / relative).is_file()
                for relative in result["outputs"].values()
            )
            manifest = json.loads(
                (Path(temporary) / result["outputs"]["manifest"]).read_text(encoding="utf-8")
            )

        self.assertTrue(files_exist)
        self.assertEqual(len(result["outputs"]), 7)
        self.assertEqual(len(manifest["input_sha256"]["vcf"]), 64)
        self.assertEqual(len(manifest["input_sha256"]["metadata"]), 64)
        self.assertIn("No somatic, germline, driver", result["summary"])

    def test_metadata_must_exactly_match_vcf_samples(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.vcf_cohort.WORKSPACE_ROOT", Path(temporary)
        ), patch("molemo.workspace_utils.WORKSPACE_ROOT", Path(temporary)):
            examples = Path(temporary) / "examples"
            examples.mkdir()
            source_root = Path(__file__).resolve().parents[1] / "workspace" / "examples"
            (examples / "ctdna_variants.vcf").write_bytes(
                (source_root / "ctdna_variants.vcf").read_bytes()
            )
            (examples / "bad.csv").write_text(
                "sample,subject,timepoint,time_order\nP01_BASELINE,P01,Baseline,0\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(VcfCohortError, "exactly match VCF samples"):
                preflight_vcf_cohort(EXAMPLE_VCF, "examples/bad.csv")

    def test_agent_routes_vcf_plan_and_hides_execution_tool(self):
        question = (
            "审阅 examples/ctdna_variants.vcf 和 examples/ctdna_metadata.csv 的低频变异、"
            "变异景观和样本轨迹，最小 VAF 0.01，最小深度 10"
        )
        plan = extract_vcf_cohort_plan(question)
        template, inputs = local_workflow_plan(question, {})
        exposed = {item["function"]["name"] for item in SkillRegistry().openai_tools()}

        self.assertEqual(plan["vcf_path"], EXAMPLE_VCF)
        self.assertEqual(plan["metadata_path"], EXAMPLE_METADATA)
        self.assertEqual(template, "vcf-cohort-review")
        self.assertEqual(inputs, plan)
        self.assertIn("vcf_cohort_preflight", exposed)
        self.assertNotIn("vcf_cohort_review", exposed)

    def test_workflow_preflights_but_executes_only_after_approval(self):
        preflight = {
            "ready": True,
            "summary": "Validated VCFv4.3 with six samples.",
            "vcf_path": EXAMPLE_VCF,
            "sample_count": 6,
            "record_count": 6,
        }
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.workflow_runtime.preflight_vcf_cohort", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "vcf-cohort-review",
                {
                    "vcf_path": EXAMPLE_VCF,
                    "metadata_path": EXAMPLE_METADATA,
                    "sample_column": "sample",
                    "subject_column": "subject",
                    "timepoint_column": "timepoint",
                    "time_order_column": "time_order",
                    "min_vaf": 0.01,
                    "min_depth": 10,
                    "include_filtered": "false",
                },
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "vcf_cohort_review")
        self.assertFalse(registry.calls[0][1]["include_filtered"])


if __name__ == "__main__":
    unittest.main()
