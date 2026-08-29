import gzip
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from molemo.agent_runtime import local_workflow_plan
from molemo.single_cell import (
    SingleCellError,
    preflight_single_cell,
    single_cell_toolchain_status,
)
from molemo.skill_runtime import SkillError, SkillRegistry
from molemo.workflow_runtime import WorkflowManager
from molemo.workspace_utils import WORKSPACE_ROOT, resolve_workspace_path


COUNTS = "examples/single_cell_counts.csv"
METADATA = "examples/single_cell_metadata.csv"
H5AD = "examples/single_cell_demo.h5ad"
TENX_MTX = "examples/single_cell_10x/matrix.mtx"
TENX_H5 = "examples/single_cell_10x.h5"
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

    def test_preflight_reads_h5ad_count_layer_and_rejects_normalized_x(self):
        result = preflight_single_cell(
            H5AD,
            count_layer="counts",
            min_genes=20,
            min_cells=3,
        )

        self.assertEqual(result["input_format"], "h5ad")
        self.assertEqual(result["count_layer"], "counts")
        self.assertEqual(result["available_layers"], ["counts"])
        self.assertEqual(result["cells"], 90)
        self.assertEqual(
            [item["column"] for item in result["metadata"]["categorical_columns"]],
            ["donor", "condition", "synthetic_truth"],
        )
        with self.assertRaisesRegex(SingleCellError, "raw counts"):
            preflight_single_cell(H5AD, min_genes=20, min_cells=3)

    def test_preflight_reads_standard_10x_mtx_and_h5(self):
        matrix = preflight_single_cell(TENX_MTX, min_genes=20, min_cells=3)
        h5 = preflight_single_cell(TENX_H5, min_genes=20, min_cells=3)

        self.assertEqual(matrix["input_format"], "10x_mtx")
        self.assertEqual(len(matrix["input_files"]), 3)
        self.assertEqual(h5["input_format"], "10x_h5")
        self.assertEqual((matrix["cells"], matrix["genes"]), (90, 57))
        self.assertEqual((h5["cells"], h5["genes"]), (90, 57))

    def test_preflight_reads_compressed_10x_mtx(self):
        temporary_root = WORKSPACE_ROOT / ".molemo" / "test-inputs"
        temporary_root.mkdir(parents=True, exist_ok=True)
        source = WORKSPACE_ROOT / "examples" / "single_cell_10x"
        with tempfile.TemporaryDirectory(dir=temporary_root) as temporary:
            target = Path(temporary)
            for name in ("matrix.mtx", "features.tsv", "barcodes.tsv"):
                with (source / name).open("rb") as input_handle, gzip.open(
                    target / f"{name}.gz", "wb"
                ) as output_handle:
                    shutil.copyfileobj(input_handle, output_handle)
            relative = (target / "matrix.mtx.gz").relative_to(WORKSPACE_ROOT).as_posix()
            result = preflight_single_cell(relative, min_genes=20, min_cells=3)

        self.assertEqual(result["input_format"], "10x_mtx_gz")
        self.assertEqual((result["cells"], result["genes"]), (90, 57))

    def test_doublet_settings_require_scrublet_and_valid_batch(self):
        with self.assertRaisesRegex(SingleCellError, "requires run_scrublet"):
            preflight_single_cell(COUNTS, exclude_predicted_doublets=True)
        with self.assertRaisesRegex(SingleCellError, "not found"):
            preflight_single_cell(
                COUNTS,
                METADATA,
                run_scrublet=True,
                doublet_batch_key="missing_batch",
            )

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

    @unittest.skipUnless(single_cell_toolchain_status()["available"], "Scanpy runtime is unavailable")
    def test_approved_h5ad_workflow_records_scrublet_without_excluding_by_default(self):
        parameters = {
            **PARAMETERS,
            "count_matrix_path": H5AD,
            "metadata_path": "",
            "count_layer": "counts",
            "run_scrublet": True,
            "doublet_batch_key": "donor",
            "exclude_predicted_doublets": False,
        }
        with tempfile.TemporaryDirectory() as storage:
            manager = WorkflowManager(Path(storage))
            run = manager.create_plan(
                "single-cell-exploratory-analysis",
                parameters,
                "Score likely doublets without removing them",
            )
            completed = manager.approve(run["id"], self.registry)
            result = next(
                item["data"]
                for item in completed["artifacts"]
                if item["type"] == "single-cell-analysis"
            )
            output_root = resolve_workspace_path(result["output_root"])
            try:
                self.assertEqual(result["input_format"], "h5ad")
                self.assertEqual(result["count_layer"], "counts")
                self.assertTrue(result["doublet"]["enabled"])
                self.assertGreater(result["doublet"]["predicted"], 0)
                self.assertEqual(result["doublet"]["excluded"], 0)
                self.assertEqual(result["cells_retained"], 90)
                self.assertEqual(set(result["doublet"]["batch_thresholds"]), {"D1", "D2", "D3"})
            finally:
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

    def test_local_agent_extracts_h5ad_layer_and_scrublet_boundary(self):
        request = local_workflow_plan(
            "用 examples/single_cell_demo.h5ad 做单细胞 UMAP，count layer=counts，"
            "运行 Scrublet，batch key donor，只标记不排除 doublet",
            {},
        )

        self.assertIsNotNone(request)
        _, inputs = request
        self.assertEqual(inputs["count_matrix_path"], H5AD)
        self.assertEqual(inputs["count_layer"], "counts")
        self.assertTrue(inputs["run_scrublet"])
        self.assertEqual(inputs["doublet_batch_key"], "donor")
        self.assertFalse(inputs["exclude_predicted_doublets"])


if __name__ == "__main__":
    unittest.main()
