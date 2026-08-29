import unittest

from molemo.agent_runtime import run_local_agent
from molemo.skill_runtime import SkillError, SkillRegistry


class SkillRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_catalog_discovers_pipeline_visualization_and_workspace_skills(self):
        kinds = {skill["kind"] for skill in self.registry.catalog()}

        self.assertGreaterEqual(len(self.registry.catalog()), 9)
        self.assertIn("pipeline", kinds)
        self.assertIn("visualization", kinds)
        self.assertIn("workspace", kinds)
        self.assertIn("retrieval", kinds)

    def test_alignment_returns_viewer_artifact(self):
        result = self.registry.execute(
            "sequence_align",
            {"sequence_a": "ACDEFG", "sequence_b": "ACDFFG"},
        )

        self.assertAlmostEqual(result["data"]["identity"], 83.33, places=2)
        self.assertEqual(result["artifacts"][0]["type"], "sequence-alignment")

    def test_workspace_rejects_path_traversal(self):
        with self.assertRaises(SkillError):
            self.registry.execute("workspace_read_text", {"path": "../README.md"})

    def test_local_agent_is_grounded_in_skill_outputs(self):
        result = run_local_agent(
            "解释这个分子的性质",
            {"type": "molecule", "smiles": "Cn1cnc2c1c(=O)n(C)c(=O)n2C"},
            self.registry,
        )

        names = [item["name"] for item in result["trace"]]
        self.assertIn("research_route", names)
        self.assertIn("chem_analyze_molecule", names)
        self.assertTrue(result["artifacts"])


if __name__ == "__main__":
    unittest.main()
