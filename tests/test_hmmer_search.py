import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_runtime import extract_hmmer_profile_plan, local_workflow_plan
from hmmer_search import (
    HmmerSearchError,
    parse_hmmer_domtblout,
    preflight_hmmer_profile_search,
    run_hmmer_profile_search,
)
from skill_runtime import SkillRegistry
from workflow_runtime import WorkflowManager


EXAMPLE_HMM = "examples/ubiquitin_demo.hmm"
EXAMPLE_FASTA = "examples/hmmer_targets.faa"


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "hmmer-profile-search",
            "summary": "HMMER search completed.",
            "artifacts": [{"id": "hmmer-search", "type": "hmmer-profile-search", "data": {}}],
        }


class HmmerSearchTests(unittest.TestCase):
    def test_preflight_validates_profile_database_and_runtime(self):
        result = preflight_hmmer_profile_search(EXAMPLE_HMM, EXAMPLE_FASTA, 1e-3, 1e-3)

        self.assertTrue(result["ready"])
        self.assertEqual(result["version"], "3.4 (Aug 2023)")
        self.assertEqual(result["model_count"], 1)
        self.assertEqual(result["models"][0]["name"], "Molemo_Ubiquitin_demo")
        self.assertEqual(result["models"][0]["length"], 76)
        self.assertEqual(result["sequence_count"], 4)
        self.assertEqual(result["residue_count"], 409)

    def test_real_hmmsearch_preserves_repeat_domains_and_outputs(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "hmmer_search.WORKSPACE_ROOT", Path(temporary)
        ), patch("workspace_utils.WORKSPACE_ROOT", Path(temporary)):
            examples = Path(temporary) / "examples"
            examples.mkdir()
            source_root = Path(__file__).resolve().parents[1] / "workspace" / "examples"
            for name in ("ubiquitin_demo.hmm", "hmmer_targets.faa"):
                (examples / name).write_bytes((source_root / name).read_bytes())
            result = run_hmmer_profile_search(EXAMPLE_HMM, EXAMPLE_FASTA, 1e-3, 1e-3)
            tandem = next(item for item in result["hits"] if item["target_name"] == "tandem_domain")
            files_exist = all(
                (Path(temporary) / relative).is_file()
                for relative in result["outputs"].values()
            )
            manifest = json.loads(
                (Path(temporary) / result["outputs"]["manifest"]).read_text(encoding="utf-8")
            )
            domtblout = (Path(temporary) / result["outputs"]["domtblout"]).read_text(
                encoding="utf-8"
            )

        self.assertEqual(result["reported_hit_count"], 3)
        self.assertEqual(result["reported_domain_count"], 4)
        self.assertEqual(tandem["domain_count"], 2)
        self.assertEqual(
            [(item["alignment_from"], item["alignment_to"]) for item in tandem["domains"]],
            [(1, 76), (82, 157)],
        )
        self.assertEqual(tandem["domains"][0]["conditional_evalue"], 9e-58)
        self.assertEqual(tandem["domains"][0]["independent_evalue"], 1.2e-57)
        self.assertTrue(files_exist)
        self.assertEqual(len(result["outputs"]), 6)
        self.assertEqual(len(manifest["input_sha256"]["hmm"]), 64)
        self.assertEqual(len(manifest["input_sha256"]["database"]), 64)
        self.assertIn("# Query file:      examples/ubiquitin_demo.hmm", domtblout)
        self.assertNotIn("# Current dir:", domtblout)
        self.assertNotIn(temporary, domtblout)

    def test_domtbl_parser_rejects_inconsistent_coordinates(self):
        invalid = (
            "target - 10 profile - 5 1e-4 20 0 1 1 1e-4 1e-4 20 0 "
            "1 5 2 12 1 10 0.9 description\n"
        )

        with self.assertRaisesRegex(HmmerSearchError, "inconsistent domain coordinates"):
            parse_hmmer_domtblout(invalid)

    def test_agent_routes_hmmer_plan_and_hides_execution_tool(self):
        question = (
            "用 examples/ubiquitin_demo.hmm 对 examples/hmmer_targets.faa 做 HMMER "
            "蛋白家族结构域搜索，E-value 1e-3"
        )
        plan = extract_hmmer_profile_plan(question)
        template, inputs = local_workflow_plan(question, {})
        exposed = {item["function"]["name"] for item in SkillRegistry().openai_tools()}

        self.assertEqual(plan["hmm_path"], EXAMPLE_HMM)
        self.assertEqual(plan["database_path"], EXAMPLE_FASTA)
        self.assertEqual(plan["evalue"], 1e-3)
        self.assertEqual(plan["domain_evalue"], 1e-3)
        self.assertEqual(template, "hmmer-profile-search")
        self.assertEqual(inputs, plan)
        self.assertIn("hmmer_profile_preflight", exposed)
        self.assertNotIn("hmmer_profile_search", exposed)

    def test_workflow_preflights_but_runs_only_after_approval(self):
        preflight = {
            "ready": True,
            "summary": "Validated one HMM profile against four proteins.",
            "hmm_path": EXAMPLE_HMM,
            "database_path": EXAMPLE_FASTA,
            "model_count": 1,
            "sequence_count": 4,
        }
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "workflow_runtime.preflight_hmmer_profile_search", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "hmmer-profile-search",
                {
                    "hmm_path": EXAMPLE_HMM,
                    "database_path": EXAMPLE_FASTA,
                    "evalue": 1e-3,
                    "domain_evalue": 1e-3,
                    "max_hits": 25,
                    "threads": 1,
                },
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "hmmer_profile_search")
        self.assertEqual(registry.calls[0][1]["threads"], 1)


if __name__ == "__main__":
    unittest.main()
