import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_runtime import local_workflow_plan
from single_cell import (
    SingleCellError,
    preflight_single_cell,
    single_cell_toolchain_status,
)
from skill_runtime import SkillError, SkillRegistry
from workflow_runtime import WorkflowManager
from workspace_utils import WORKSPACE_ROOT, resolve_workspace_path


COUNTS = "examples/single_cell_counts.csv"
METADATA = "examples/single_cell_metadata.csv"
PARAMETERS = {
    "count_matrix_path": COUNTS,
    "metadata_path": METADATA,
    "cell_id_column": "cell_id",
    "min_genes": 20,
    "min_cells": 3,
    "max_mito_percent": 20,
    "n_top_genes": 40,
    "n_neighbors": 10,
    "leiden_resolution": 0.4,
    "marker_genes": 8,
}


class SingleCellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_preflight_validates_raw_counts_qc_and_metadata(self):
        result = preflight_single_cell(**PARAMETERS)

        self.assertTrue(result["ready"])
        self.assertEqual(result["input_mode"], "cell_by_gene_raw_counts")
        self.assertEqual(result["cells"], 90)
        self.assertEqual(result["genes"], 57)
        self.assertEqual(result["cells_after_filter"], 90)
        self.assertEqual(result["genes_after_filter"], 57)
        self.assertEqual(result["mitochondrial_genes"], 3)
        self.assertEqual(
            [item["column"] for item in result["metadata"]["categorical_columns"]],
            ["donor", "condition", "synthetic_truth"],
        )

    def test_preflight_rejects_workspace_escape(self):
        with self.assertRaises(SingleCellError):
            preflight_single_cell("../single_cell_counts.csv")

    def test_execution_tool_is_hidden_from_external_agents(self):
        exposed = {item["function"]["name"] for item in self.registry.openai_tools()}

        self.assertIn("single_cell_preflight", exposed)
        self.assertNotIn("single_cell_run_analysis", exposed)
        with self.assertRaises(SkillError):
            self.registry.execute_agent("single_cell_run_analysis", PARAMETERS)

    @unittest.skipUnless(single_cell_toolchain_status()["available"], "Scanpy runtime is unavailable")
    def test_approved_workflow_runs_real_scanpy_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as storage:
            manager = WorkflowManager(Path(storage))
            run = manager.create_plan(
                "single-cell-exploratory-analysis",
                PARAMETERS,
                "Explore the synthetic single-cell count matrix",
            )

            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(run["trace"], [])
            self.assertEqual(run["preflight"]["cells_after_filter"], 90)

            completed = manager.approve(run["id"], self.registry)
            artifact = next(
                item for item in completed["artifacts"] if item["type"] == "single-cell-analysis"
            )
            result = artifact["data"]
            output_root = resolve_workspace_path(result["output_root"])
            try:
                self.assertEqual(completed["status"], "completed")
                self.assertEqual(completed["trace"][0]["name"], "single_cell_run_analysis")
                self.assertEqual(result["method"], "Scanpy")
                self.assertEqual(result["cells_retained"], 90)
                self.assertEqual(result["genes_retained"], 57)
                self.assertEqual(result["highly_variable_genes"], 40)
                self.assertEqual(result["clusters"], 3)
                self.assertEqual(
                    [item["cells"] for item in result["cluster_summary"]],
                    [30, 30, 30],
                )
                marker_text = " ".join(item["top_markers"] for item in result["cluster_summary"])
                for expected in ("CD3D", "MS4A1", "S100A9"):
                    self.assertIn(expected, marker_text)
                manifest_path = resolve_workspace_path(result["outputs"]["manifest"])
                manifest_text = manifest_path.read_text(encoding="utf-8")
                manifest = json.loads(manifest_text)
                self.assertEqual(manifest["random_seed"], 0)
                self.assertEqual(len(manifest["input_sha256"]["count_matrix"]), 64)
                self.assertNotIn(str(WORKSPACE_ROOT.parent), manifest_text)
                self.assertTrue(resolve_workspace_path(result["outputs"]["anndata"]).is_file())
            finally:
                if output_root.parent == (WORKSPACE_ROOT / "analyses").resolve():
                    shutil.rmtree(output_root, ignore_errors=True)

    def test_local_agent_builds_single_cell_plan_without_running_it(self):
        request = local_workflow_plan(
            "用 examples/single_cell_counts.csv 和 examples/single_cell_metadata.csv 做单细胞 RNA-seq "
            "QC、UMAP、Leiden 聚类和 marker 分析，resolution 0.4",
            {},
        )

        self.assertIsNotNone(request)
        template, inputs = request
        self.assertEqual(template, "single-cell-exploratory-analysis")
        self.assertEqual(inputs["count_matrix_path"], COUNTS)
        self.assertEqual(inputs["metadata_path"], METADATA)
        self.assertEqual(inputs["leiden_resolution"], 0.4)


if __name__ == "__main__":
    unittest.main()
