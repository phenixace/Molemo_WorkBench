import tempfile
import unittest
from pathlib import Path

from molemo.agent_runtime import local_workflow_plan
from molemo.sequence_search import SequenceSearchError, find_executable, parse_blast_json, run_local_blast
from molemo.skill_runtime import SkillError, SkillRegistry
from molemo.workflow_runtime import WorkflowError, WorkflowManager


BLAST_JSON = {
    "BlastOutput2": [
        {
            "report": {
                "results": {
                    "search": {
                        "query_id": "Query_1",
                        "query_len": 20,
                        "hits": [
                            {
                                "description": [
                                    {"id": "ref|TEST|", "accession": "TEST", "title": "Test sequence"}
                                ],
                                "len": 22,
                                "hsps": [
                                    {
                                        "bit_score": 40.2,
                                        "score": 88,
                                        "evalue": 1e-10,
                                        "identity": 19,
                                        "positive": 20,
                                        "gaps": 0,
                                        "align_len": 20,
                                        "query_from": 1,
                                        "query_to": 20,
                                        "hit_from": 2,
                                        "hit_to": 21,
                                        "qseq": "NLYIQWLKDGGPSSGRPPPS",
                                        "midline": "NLYIQWLKDGGPSSGRPPP+",
                                        "hseq": "NLYIQWLKDGGPSSGRPPPT",
                                    }
                                ],
                            }
                        ],
                        "stat": {"db_num": 1},
                    }
                }
            }
        }
    ]
}


class SequenceSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_blast_json_parser_preserves_ranking_evidence_and_alignment(self):
        result = parse_blast_json(BLAST_JSON)

        self.assertEqual(result["hit_count"], 1)
        self.assertEqual(result["hits"][0]["identity_percent"], 95.0)
        self.assertEqual(result["hits"][0]["query_coverage_percent"], 100.0)
        self.assertEqual(result["hits"][0]["hit_alignment"], "NLYIQWLKDGGPSSGRPPPT")

    @unittest.skipUnless(find_executable("blastp") and find_executable("makeblastdb"), "NCBI BLAST+ not installed")
    def test_real_blastp_short_search_returns_workspace_hits(self):
        result = run_local_blast(
            "NLYIQWLKDGGPSSGRPPPS",
            "examples/homologs.faa",
            program="blastp",
            max_hits=10,
        )

        self.assertEqual(result["task"], "blastp-short")
        self.assertEqual(result["database_sequences"], 4)
        self.assertEqual(result["hits"][0]["title"], "trpcage_native synthetic Trp-cage reference")
        self.assertEqual(result["hits"][0]["identity_percent"], 100.0)
        self.assertGreaterEqual(result["hit_count"], 2)

    def test_search_rejects_database_path_traversal(self):
        with self.assertRaises(SequenceSearchError):
            run_local_blast("ACDEFGHIK", "../README.md")

    def test_sequence_search_tool_is_hidden_from_direct_agent_execution(self):
        visible = {tool["function"]["name"] for tool in self.registry.openai_tools()}

        self.assertIn("sequence_search_local", self.registry.tools)
        self.assertNotIn("sequence_search_local", visible)
        with self.assertRaisesRegex(SkillError, "researcher-approved workflow"):
            self.registry.execute_agent(
                "sequence_search_local",
                {"query": "ACDEFGHIK", "database_path": "examples/homologs.faa"},
            )

    @unittest.skipUnless(find_executable("blastp") and find_executable("makeblastdb"), "NCBI BLAST+ not installed")
    def test_approved_workflow_executes_real_blast_after_pending_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = WorkflowManager(Path(temporary))
            plan = manager.create_plan(
                "sequence-similarity-search",
                {
                    "query": "NLYIQWLKDGGPSSGRPPPS",
                    "database_path": "examples/homologs.faa",
                    "program": "blastp",
                    "evalue": "1e-5",
                    "max_hits": 10,
                },
            )

            self.assertEqual(plan["status"], "pending_approval")
            self.assertEqual(plan["trace"], [])
            completed = manager.approve(plan["id"], self.registry)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["trace"][0]["name"], "sequence_search_local")
            self.assertEqual(completed["artifacts"][1]["type"], "sequence-search")

    def test_local_agent_proposes_blast_workflow_for_active_sequence(self):
        request = local_workflow_plan(
            "用 BLAST 搜索 examples/homologs.faa 里的同源序列",
            {"type": "protein", "sequence": "NLYIQWLKDGGPSSGRPPPS"},
        )

        self.assertEqual(request[0], "sequence-similarity-search")
        self.assertEqual(request[1]["program"], "blastp")
        self.assertEqual(request[1]["database_path"], "examples/homologs.faa")

    def test_workflow_rejects_zero_search_limits_instead_of_defaulting(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = WorkflowManager(Path(temporary))
            with self.assertRaises(WorkflowError):
                manager.create_plan(
                    "sequence-similarity-search",
                    {
                        "query": "NLYIQWLKDGGPSSGRPPPS",
                        "database_path": "examples/homologs.faa",
                        "evalue": 0,
                        "max_hits": 0,
                    },
                )


if __name__ == "__main__":
    unittest.main()
