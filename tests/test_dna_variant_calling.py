import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.dna_variant_calling import (
    DnaVariantCallingError,
    inspect_fastq_pair,
    inspect_reference_fasta,
    ngs_toolchain_status,
    normalize_dna_variant_inputs,
    run_dna_variant_calling,
)
from molemo.skill_runtime import SkillRegistry
from molemo.workflow_runtime import WorkflowManager


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "workspace" / "examples"


class RecordingRegistry:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "dna-variant-calling",
            "summary": "Synthetic DNA pipeline completed.",
            "artifacts": [],
        }


class DnaVariantCallingTests(unittest.TestCase):
    def test_demo_inputs_are_synchronized_and_truth_is_explicit(self):
        reference = inspect_reference_fasta(EXAMPLES / "dna_variant_reference.fa")
        reads = inspect_fastq_pair(
            EXAMPLES / "dna_variant_R1.fastq",
            EXAMPLES / "dna_variant_R2.fastq",
        )
        truth = (EXAMPLES / "dna_variant_truth.tsv").read_text(encoding="ascii")

        self.assertEqual(reference["total_bases"], 2400)
        self.assertEqual(reads["read_pairs"], 80)
        self.assertIn("molemo_demo_reference\t1201\tA\tC\t0/1", truth)

    def test_input_normalization_rejects_same_read_file(self):
        with self.assertRaises(DnaVariantCallingError):
            normalize_dna_variant_inputs(
                "examples/dna_variant_R1.fastq",
                "examples/dna_variant_R1.fastq",
                "examples/dna_variant_reference.fa",
                "MOLEMO_DEMO",
            )

    def test_skill_execution_requires_workflow_approval(self):
        registry = SkillRegistry()
        with self.assertRaisesRegex(Exception, "researcher-approved"):
            registry.execute_agent(
                "dna_variant_calling_run",
                {
                    "read1_path": "examples/dna_variant_R1.fastq",
                    "read2_path": "examples/dna_variant_R2.fastq",
                    "reference_path": "examples/dna_variant_reference.fa",
                    "sample_id": "MOLEMO_DEMO",
                },
            )

    def test_workflow_preflights_but_runs_only_after_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = WorkflowManager(Path(temporary))
            registry = RecordingRegistry()
            plan = manager.create_plan(
                "paired-end-dna-variant-calling",
                {
                    "read1_path": "examples/dna_variant_R1.fastq",
                    "read2_path": "examples/dna_variant_R2.fastq",
                    "reference_path": "examples/dna_variant_reference.fa",
                    "sample_id": "MOLEMO_DEMO",
                    "ploidy": 2,
                    "min_base_quality": 13,
                    "min_mapping_quality": 20,
                    "max_depth": 10000,
                    "threads": 1,
                },
            )

            self.assertEqual(plan["status"], "pending_approval")
            self.assertEqual(plan["preflight"]["reads"]["read_pairs"], 80)
            self.assertEqual(registry.calls, [])

            completed = manager.approve(plan["id"], registry)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(registry.calls[0][0], "dna_variant_calling_run")

    @unittest.skipUnless(ngs_toolchain_status()["available"], "local NGS toolchain unavailable")
    def test_real_toolchain_recovers_the_synthetic_heterozygous_snv(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            examples = workspace / "examples"
            examples.mkdir()
            for name in (
                "dna_variant_R1.fastq",
                "dna_variant_R2.fastq",
                "dna_variant_reference.fa",
            ):
                shutil.copy2(EXAMPLES / name, examples / name)

            def resolve(path):
                return (workspace / str(path)).resolve()

            with (
                patch("molemo.dna_variant_calling.WORKSPACE_ROOT", workspace),
                patch("molemo.dna_variant_calling.resolve_workspace_path", side_effect=resolve),
            ):
                result = run_dna_variant_calling(
                    read1_path="examples/dna_variant_R1.fastq",
                    read2_path="examples/dna_variant_R2.fastq",
                    reference_path="examples/dna_variant_reference.fa",
                    sample_id="MOLEMO_DEMO",
                )

            self.assertEqual(result["variant_count"], 1)
            variant = result["variants"][0]
            self.assertEqual(
                (variant["chrom"], variant["pos"], variant["ref"], variant["alt"]),
                ("molemo_demo_reference", 1201, "A", "C"),
            )
            self.assertEqual(variant["genotype"], "0/1")
            self.assertAlmostEqual(variant["vaf"], 0.5, places=2)
            self.assertEqual(result["alignment"]["mapped_percent"], 100.0)
            report = resolve(result["outputs"]["report"])
            self.assertTrue(report.is_file())
            self.assertFalse(json.loads(report.read_text())["clinical_interpretation"])


if __name__ == "__main__":
    unittest.main()
