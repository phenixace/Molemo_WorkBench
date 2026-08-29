import shutil
import tempfile
import unittest
from pathlib import Path

from agent_runtime import local_workflow_plan
from skill_runtime import SkillError, SkillRegistry
from transcriptomics import (
    TranscriptomicsError,
    preflight_bulk_rnaseq,
    transcriptomics_toolchain_status,
)
from workflow_runtime import WorkflowManager
from workspace_utils import WORKSPACE_ROOT, resolve_workspace_path


COUNTS = "examples/rnaseq_counts.csv"
METADATA = "examples/rnaseq_metadata.csv"


class TranscriptomicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_preflight_validates_design_and_sample_qc(self):
        result = preflight_bulk_rnaseq(
            COUNTS,
            METADATA,
            test_level="treated",
            reference_level="control",
            batch_column="batch",
        )

        self.assertTrue(result["ready"])
        self.assertEqual(result["genes"], 40)
        self.assertEqual(result["samples"], 8)
        self.assertEqual(result["genes_after_filter"], 40)
        self.assertEqual(result["condition_counts"], {"control": 4, "treated": 4})
        self.assertEqual(result["design_formula"], "~batch+condition")
        self.assertEqual(len(result["sample_qc"]), 8)

    def test_preflight_rejects_workspace_escape(self):
        with self.assertRaises(TranscriptomicsError):
            preflight_bulk_rnaseq("../counts.csv", METADATA)

    def test_run_tool_is_hidden_from_external_agents(self):
        exposed = {item["function"]["name"] for item in self.registry.openai_tools()}

        self.assertIn("transcriptomics_preflight", exposed)
        self.assertNotIn("transcriptomics_run_de", exposed)
        with self.assertRaises(SkillError):
            self.registry.execute_agent(
                "transcriptomics_run_de",
                {
                    "count_matrix_path": COUNTS,
                    "metadata_path": METADATA,
                    "test_level": "treated",
                    "reference_level": "control",
                },
            )

    @unittest.skipUnless(transcriptomics_toolchain_status()["available"], "PyDESeq2 runtime is unavailable")
    def test_approved_workflow_runs_real_differential_expression(self):
        with tempfile.TemporaryDirectory() as storage:
            manager = WorkflowManager(Path(storage))
            run = manager.create_plan(
                "bulk-rnaseq-differential-expression",
                {
                    "count_matrix_path": COUNTS,
                    "metadata_path": METADATA,
                    "sample_column": "sample",
                    "condition_column": "condition",
                    "test_level": "treated",
                    "reference_level": "control",
                    "batch_column": "batch",
                    "min_total_count": 10,
                    "fdr_threshold": 0.05,
                    "lfc_threshold": 1.0,
                },
                "Find expression changes in treated samples",
            )

            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(run["trace"], [])
            self.assertEqual(run["preflight"]["design_formula"], "~batch+condition")

            completed = manager.approve(run["id"], self.registry)
            result_artifact = next(
                artifact for artifact in completed["artifacts"] if artifact["type"] == "transcriptomics-de"
            )
            result = result_artifact["data"]
            output_root = resolve_workspace_path(result["output_root"])
            try:
                self.assertEqual(completed["status"], "completed")
                self.assertEqual(completed["trace"][0]["name"], "transcriptomics_run_de")
                self.assertEqual(result["method"], "PyDESeq2")
                self.assertEqual(result["significant_genes"], 10)
                self.assertEqual(result["upregulated"], 6)
                self.assertEqual(result["downregulated"], 4)
                self.assertIn("IL6", {gene["gene_id"] for gene in result["top_genes"]})
                self.assertTrue(resolve_workspace_path(result["outputs"]["manifest"]).is_file())
                self.assertTrue(resolve_workspace_path(result["outputs"]["differential_expression"]).is_file())
            finally:
                if output_root.parent == (WORKSPACE_ROOT / "analyses").resolve():
                    shutil.rmtree(output_root, ignore_errors=True)

    def test_local_agent_builds_rnaseq_plan_without_running_it(self):
        request = local_workflow_plan(
            "对 examples/rnaseq_counts.csv 和 examples/rnaseq_metadata.csv 做 RNA-seq 差异表达，"
            "treated vs control，batch column batch",
            {},
        )

        self.assertIsNotNone(request)
        template, inputs = request
        self.assertEqual(template, "bulk-rnaseq-differential-expression")
        self.assertEqual(inputs["test_level"], "treated")
        self.assertEqual(inputs["reference_level"], "control")
        self.assertEqual(inputs["batch_column"], "batch")


if __name__ == "__main__":
    unittest.main()
