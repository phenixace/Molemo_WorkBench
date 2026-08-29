import json
import unittest
from unittest.mock import patch

from agent_runtime import run_agent
from skill_runtime import SkillRegistry


class AgentRuntimeTests(unittest.TestCase):
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

        with patch("agent_runtime.provider_chat", side_effect=provider_responses):
            result = run_agent(payload, SkillRegistry())

        self.assertEqual(result["trace"][0]["name"], "chem_analyze_molecule")
        self.assertEqual(result["artifacts"][0]["type"], "molecule")
        self.assertNotIn("secret-provider-key", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
