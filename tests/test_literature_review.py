import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_runtime import extract_literature_query, local_workflow_plan
from literature_review import (
    LiteratureReviewError,
    collect_literature_review,
    normalize_literature_inputs,
    search_literature_preview,
)
from skill_runtime import SkillRegistry, compact_tool_result


EUROPE_PMC_PAYLOAD = {
    "version": "6.9",
    "hitCount": 28,
    "request": {"sort": ""},
    "resultList": {
        "result": [
            {
                "id": "111",
                "source": "MED",
                "pmid": "111",
                "pmcid": "PMC111",
                "doi": "10.1000/example.1",
                "title": "Randomized comparison of IL4R blockade in asthma.",
                "authorString": "A One, B Two.",
                "journalInfo": {"yearOfPublication": 2024, "journal": {"title": "Example Medicine"}},
                "pubYear": "2024",
                "abstractText": "Background sentence. Trial-reported finding with <i>source markup</i>.",
                "language": "eng",
                "pubTypeList": {"pubType": ["Randomized Controlled Trial", "Journal Article"]},
                "keywordList": {"keyword": ["Asthma", "IL4R"]},
                "isOpenAccess": "Y",
                "inPMC": "Y",
                "hasPDF": "Y",
                "citedByCount": 7,
                "firstPublicationDate": "2024-04-02",
            },
            {
                "id": "222",
                "source": "MED",
                "pmid": "222",
                "title": "Systematic review of TSLP and asthma.",
                "authorString": "C Three.",
                "journalInfo": {"yearOfPublication": 2023, "journal": {"title": "Evidence Journal"}},
                "pubYear": "2023",
                "abstractText": "Review-reported finding.",
                "language": "eng",
                "pubTypeList": {"pubType": ["Systematic Review", "Meta-Analysis"]},
                "isOpenAccess": "N",
                "inPMC": "N",
                "hasPDF": "N",
                "citedByCount": 19,
                "firstPublicationDate": "2023-07-01",
            },
        ]
    },
}


class LiteratureReviewTests(unittest.TestCase):
    def test_query_normalization_preserves_exact_strategy_and_bounds(self):
        result = normalize_literature_inputs(
            "(IL4R OR TSLP) AND asthma",
            start_year=2020,
            end_year=2026,
            max_results=15,
            include_preprints=False,
            require_abstract=True,
        )

        self.assertIn("FIRST_PDATE:[2020-01-01 TO 2026-12-31]", result["exact_query"])
        self.assertIn("HAS_ABSTRACT:Y", result["exact_query"])
        self.assertIn("NOT SRC:PPR", result["exact_query"])
        with self.assertRaises(LiteratureReviewError):
            normalize_literature_inputs("asthma", start_year=2025, end_year=2020)
        with self.assertRaises(LiteratureReviewError):
            normalize_literature_inputs("asthma", max_results=26)
        with self.assertRaises(LiteratureReviewError):
            normalize_literature_inputs("asthma sort_cited:y")

    def test_preview_preserves_source_order_types_and_identifiers(self):
        with patch("literature_review.get_json", return_value=EUROPE_PMC_PAYLOAD):
            result = search_literature_preview(query="IL4R AND asthma", max_results=2)

        self.assertEqual([paper["pmid"] for paper in result["papers"]], ["111", "222"])
        self.assertEqual(result["papers"][0]["study_type"], "Randomized controlled trial")
        self.assertEqual(result["papers"][1]["study_type"], "Systematic review / meta-analysis")
        self.assertNotIn("<i>", result["papers"][0]["abstract"])
        self.assertEqual(result["papers"][0]["cited_by_count"], 7)
        self.assertIn("not used to rank", " ".join(result["caveats"]))

    def test_approved_collection_persists_query_manifest_and_tables(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "literature_review.get_json", return_value=EUROPE_PMC_PAYLOAD
        ), patch("literature_review.WORKSPACE_ROOT", Path(temporary)):
            result = collect_literature_review(query="IL4R AND asthma", max_results=2)

            report_path = Path(temporary) / result["outputs"]["report"]
            manifest_path = Path(temporary) / result["outputs"]["manifest"]
            self.assertTrue(report_path.is_file())
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["query"], "IL4R AND asthma")
            self.assertIn("HAS_ABSTRACT:Y", manifest["exact_query"])

    def test_agent_routes_review_and_exposes_only_bounded_preview(self):
        question = "综述 IL4R 和 TSLP 在哮喘中的论文证据"
        template, inputs = local_workflow_plan(question, {})
        registry = SkillRegistry()
        exposed = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(extract_literature_query(question), "(IL4R OR TSLP) AND asthma")
        self.assertEqual(template, "literature-evidence-review")
        self.assertEqual(inputs["max_results"], 15)
        self.assertIn("literature_search_preview", exposed)
        self.assertNotIn("literature_review_collect", exposed)

    def test_model_compaction_keeps_citable_literature_fields(self):
        result = {
            "ok": True,
            "tool": "literature_search_preview",
            "skill": "literature-evidence-review",
            "summary": "Mapped papers.",
            "data": {
                "query": "asthma",
                "papers": [
                    {
                        "pmid": str(index),
                        "title": f"Paper {index}",
                        "abstract": "evidence " * 1000,
                        "url": f"https://europepmc.org/article/MED/{index}",
                    }
                    for index in range(8)
                ],
            },
            "artifacts": [{"data": {"papers": EUROPE_PMC_PAYLOAD}}] * 5,
        }

        encoded = compact_tool_result(result)
        compact = json.loads(encoded)
        self.assertIn("papers", compact["data"])
        self.assertEqual(compact["data"]["papers"][0]["pmid"], "0")
        self.assertLessEqual(len(encoded), 24000)


if __name__ == "__main__":
    unittest.main()
