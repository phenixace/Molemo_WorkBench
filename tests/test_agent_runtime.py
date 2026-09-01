import json
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.agent_runtime import extract_variant_structure_plan, local_workflow_plan, normalize_content, run_agent
from molemo.skill_runtime import SkillRegistry


class AgentRuntimeTests(unittest.TestCase):
    def test_workbench_frontend_submits_interface_language(self):
        script = (Path(__file__).resolve().parents[1] / "app.js").read_text(encoding="utf-8")

        self.assertIn("response_language: state.language", script)

    def test_provider_reasoning_tags_are_not_user_visible(self):
        content = "<think>private reasoning</think>\n\nFinal scientific answer."

        self.assertEqual(normalize_content(content), "Final scientific answer.")

    def test_local_agent_respects_explicit_interface_language(self):
        registry = SkillRegistry()
        context = {"type": "molecule", "smiles": "CCO"}

        english = run_agent(
            {"message": "分析乙醇", "context": context, "response_language": "en"},
            registry,
        )
        chinese = run_agent(
            {"message": "Analyze ethanol", "context": context, "response_language": "zh-CN"},
            registry,
        )

        self.assertIn("This question was routed", english["message"])
        self.assertNotIn("当前问题被路由", english["message"])
        self.assertIn("当前问题被路由", chinese["message"])

    def test_variant_structure_request_requires_explicit_chain_and_creates_plan(self):
        message = "审阅 PDB 6OIM 作者链 A 中 G12C 变体的结构口袋和配体接触，距离 4.5 Å"
        inputs = extract_variant_structure_plan(message)

        self.assertEqual(inputs["pdb_id"], "6OIM")
        self.assertEqual(inputs["chain"], "A")
        self.assertEqual(inputs["variant"], "G12C")
        self.assertEqual(inputs["contact_cutoff"], 4.5)
        self.assertEqual(local_workflow_plan(message, {})[0], "protein-variant-structure-review")
        self.assertIsNone(extract_variant_structure_plan("审阅 PDB 6OIM 中 G12C 的结构口袋"))

    def test_native_tool_loop_executes_local_skill_and_redacts_provider_key(self):
        provider_responses = [
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "chem_analyze_molecule",
                                        "arguments": json.dumps({"smiles": "CCO"}),
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
            {"choices": [{"message": {"content": "乙醇已由本地 RDKit 管线解析。"}}], "usage": {"total_tokens": 42}},
        ]
        payload = {
            "message": "分析乙醇",
            "context": {"type": "molecule", "smiles": "CCO"},
            "provider": {
                "endpoint": "https://provider.example/v1/chat/completions",
                "model": "test-model",
                "key": "secret-provider-key",
                "tool_mode": "native",
            },
        }

        with patch("molemo.agent_runtime.provider_chat", side_effect=provider_responses):
            result = run_agent(payload, SkillRegistry())

        self.assertEqual(result["trace"][0]["name"], "chem_analyze_molecule")
        self.assertEqual(result["artifacts"][0]["type"], "molecule")
        self.assertNotIn("secret-provider-key", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
