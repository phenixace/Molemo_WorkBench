import json
import shutil
import tempfile
import unittest
from pathlib import Path

from agent_runtime import extract_protein_conservation_plan, local_workflow_plan
from multiple_alignment import (
    MultipleAlignmentError,
    calculate_conservation,
    find_mafft_executable,
    map_reference_site,
    preflight_multiple_alignment,
    read_protein_fasta,
)
from skill_runtime import SkillRegistry, compact_tool_result
from workflow_runtime import WorkflowManager
from workspace_utils import WORKSPACE_ROOT


EXAMPLE_FASTA = "examples/ras_family.faa"


class RecordingRegistry:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "protein-conservation",
            "summary": "Alignment completed.",
            "artifacts": [{"id": "alignment", "type": "protein-conservation-review", "data": {}}],
        }


class MultipleAlignmentTests(unittest.TestCase):
    def test_fasta_validation_and_reference_mismatch(self):
        records = read_protein_fasta(WORKSPACE_ROOT / EXAMPLE_FASTA)

        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]["id"], "P01116|KRAS")
        self.assertEqual(records[0]["sequence"][11], "G")
        with self.assertRaisesRegex(MultipleAlignmentError, "expects C"):
            preflight_multiple_alignment(
                fasta_path=EXAMPLE_FASTA,
                reference_id="P01116|KRAS",
                site="C12G",
            )

    def test_conservation_and_reference_position_mapping_are_exact(self):
        aligned = [
            {"id": "ref", "sequence": "A-CD"},
            {"id": "same", "sequence": "A-CD"},
            {"id": "other", "sequence": "ATCE"},
        ]
        columns = calculate_conservation(aligned)
        site = map_reference_site(
            aligned,
            columns,
            {
                "reference_id": "ref",
                "reference_position": 2,
                "expected_residue": "C",
                "alternate_residue": "T",
                "site": "C2T",
            },
        )

        self.assertEqual(site["alignment_column"], 3)
        self.assertEqual(site["matching_sequence_count"], 3)
        self.assertTrue(site["fully_conserved"])
        self.assertAlmostEqual(columns[1]["occupancy"], 1 / 3, places=4)

    @unittest.skipUnless(find_mafft_executable(), "MAFFT is not installed")
    def test_real_mafft_run_persists_alignment_and_compacts_model_context(self):
        registry = SkillRegistry()
        result = registry.execute(
            "protein_conservation_run",
            {
                "fasta_path": EXAMPLE_FASTA,
                "reference_id": "P01116|KRAS",
                "site": "G12C",
            },
        )
        data = result["data"]
        output_root = WORKSPACE_ROOT / data["output_root"]
        self.addCleanup(shutil.rmtree, output_root, True)

        self.assertEqual(data["sequence_count"], 5)
        self.assertEqual(data["site"]["alignment_column"], 23)
        self.assertEqual(data["site"]["matching_sequence_count"], 5)
        self.assertTrue(data["site"]["fully_conserved"])
        for name in (
            "alignment.fasta",
            "conservation.tsv",
            "site_observations.tsv",
            "report.json",
            "run_manifest.json",
            "summary.md",
        ):
            self.assertTrue((output_root / name).is_file())
        manifest = json.loads((output_root / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["version"], "7.526")
        self.assertEqual(manifest["bounds"]["threads"], 1)

        compact = json.loads(compact_tool_result(result))
        self.assertTrue(compact["alignment_display_omitted"])
        self.assertNotIn("display", compact["data"])
        self.assertEqual(compact["data"]["site"]["reference_id"], "P01116|KRAS")

    def test_agent_extracts_workspace_prefix_and_creates_pending_plan(self):
        question = (
            "对 workspace/examples/ras_family.faa 做 MAFFT 多序列比对，"
            "以 P01116|KRAS 为参考，审阅 G12C 保守性"
        )
        inputs = extract_protein_conservation_plan(question)

        self.assertEqual(inputs["fasta_path"], EXAMPLE_FASTA)
        self.assertEqual(inputs["reference_id"], "P01116|KRAS")
        self.assertEqual(inputs["site"], "G12C")
        self.assertEqual(local_workflow_plan(question, {})[0], "protein-family-conservation-review")

        registry = SkillRegistry()
        route = registry.execute("research_route", {"question": question})
        self.assertIn("protein alignment and conservation", route["lanes"])
        self.assertIn("protein_conservation_preflight", route["suggested_tools"])
        self.assertFalse(registry.tools["protein_conservation_run"].agent_callable)

    def test_workflow_preflights_but_runs_only_after_approval(self):
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as directory:
            manager = WorkflowManager(Path(directory))
            run = manager.create_plan(
                "protein-family-conservation-review",
                {
                    "fasta_path": EXAMPLE_FASTA,
                    "reference_id": "P01116|KRAS",
                    "site": "G12C",
                },
            )

            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(run["preflight"]["reference"]["residue"], "G")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "protein_conservation_run")


if __name__ == "__main__":
    unittest.main()
