import json
import tempfile
import unittest
from pathlib import Path

from agent_runtime import local_workflow_plan
from skill_runtime import SkillRegistry
from workflow_runtime import WorkflowError, WorkflowManager


class RecordingRegistry:
    def __init__(self, fail_on: str = "") -> None:
        self.calls = []
        self.fail_on = fail_on

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        if name == self.fail_on:
            raise RuntimeError("deliberate tool failure")
        if name == "chem_analyze_molecule":
            return {
                "skill": "molecule-analysis",
                "summary": "Molecule analyzed.",
                "data": {"properties": {"MW": "46.07", "logP": "-0.3", "TPSA": "20.2"}},
                "artifacts": [{"id": "molecule", "type": "molecule", "data": {}}],
            }
        return {
            "skill": "scientific-visualization",
            "summary": "Chart created.",
            "artifacts": [{"id": "chart", "type": "bar-chart", "data": {}}],
        }


class WorkflowRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.manager = WorkflowManager(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def test_plan_does_not_execute_until_explicit_approval(self):
        registry = RecordingRegistry()
        run = self.manager.create_plan("molecule-profile", {"smiles": "CCO"}, "Review ethanol")

        self.assertEqual(run["status"], "pending_approval")
        self.assertEqual(registry.calls, [])

        completed = self.manager.approve(run["id"], registry)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual([name for name, _ in registry.calls], ["chem_analyze_molecule", "visualization_property_chart"])
        self.assertEqual(completed["trace"][1]["args"]["properties"]["MW"], 46.07)

        with self.assertRaises(WorkflowError):
            self.manager.approve(run["id"], registry)

    def test_failed_step_stops_remaining_pipeline(self):
        registry = RecordingRegistry(fail_on="chem_analyze_molecule")
        run = self.manager.create_plan("molecule-profile", {"smiles": "CCO"})
        failed = self.manager.approve(run["id"], registry)

        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["steps"][0]["status"], "error")
        self.assertEqual(failed["steps"][1]["status"], "skipped")
        self.assertEqual(len(registry.calls), 1)

    def test_plan_persistence_drops_undeclared_sensitive_inputs(self):
        run = self.manager.create_plan(
            "fastq-qc-review",
            {"path": "examples/tiny.fastq", "max_reads": 3, "api_key": "do-not-store"},
        )
        stored = json.loads((Path(self.temp.name) / f"{run['id']}.json").read_text(encoding="utf-8"))

        self.assertNotIn("api_key", stored["inputs"])
        self.assertNotIn("do-not-store", json.dumps(stored))
        reloaded = WorkflowManager(Path(self.temp.name)).get_run(run["id"])
        self.assertEqual(reloaded["status"], "pending_approval")

    def test_pending_plan_can_be_cancelled_but_not_run_afterwards(self):
        run = self.manager.create_plan("protein-sequence-review", {"sequence": "ACDEFG"})
        cancelled = self.manager.cancel(run["id"])

        self.assertEqual(cancelled["status"], "cancelled")
        with self.assertRaises(WorkflowError):
            self.manager.approve(run["id"], RecordingRegistry())

    def test_agent_can_propose_but_has_no_approval_tool(self):
        registry = SkillRegistry()
        request = local_workflow_plan(
            "为当前蛋白制定分析计划",
            {"type": "protein", "sequence": "ACDEFGHIK"},
        )

        self.assertEqual(request[0], "protein-sequence-review")
        self.assertIn("workflow_create_plan", registry.tools)
        self.assertFalse(any("approve" in name for name in registry.tools))


if __name__ == "__main__":
    unittest.main()
