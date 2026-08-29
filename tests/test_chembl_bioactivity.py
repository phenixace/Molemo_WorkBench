import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.agent_runtime import extract_chembl_bioactivity_plan, local_workflow_plan
from molemo.chembl_bioactivity import (
    ChemblBioactivityError,
    collect_chembl_bioactivity,
    normalize_chembl_inputs,
    parse_chembl_activities,
    parse_chembl_target,
    summarize_chembl_compounds,
)
from molemo.skill_runtime import SkillRegistry, compact_tool_result
from molemo.workflow_runtime import WorkflowManager


TARGET_PAYLOAD = {
    "targets": [
        {
            "target_chembl_id": "CHEMBL203",
            "pref_name": "Epidermal growth factor receptor",
            "target_type": "SINGLE PROTEIN",
            "organism": "Homo sapiens",
            "tax_id": 9606,
        },
        {
            "target_chembl_id": "CHEMBL_MIXED",
            "pref_name": "EGFR complex",
            "target_type": "PROTEIN COMPLEX",
            "organism": "Homo sapiens",
        },
    ]
}

ACTIVITY_PAYLOAD = {
    "page_meta": {"total_count": 125},
    "activities": [
        {
            "activity_id": 1,
            "molecule_chembl_id": "CHEMBL1",
            "molecule_pref_name": "Compound one",
            "canonical_smiles": "CCO",
            "pchembl_value": "9.0",
            "standard_type": "IC50",
            "standard_relation": "=",
            "standard_value": "1",
            "standard_units": "nM",
            "assay_chembl_id": "CHEMBL_A9",
            "assay_type": "B",
            "bao_label": "cell-based format",
            "document_chembl_id": "CHEMBL_DOC1",
            "document_journal": "J Med Chem",
            "document_year": 2024,
        },
        {
            "activity_id": 2,
            "molecule_chembl_id": "CHEMBL1",
            "canonical_smiles": "CCO",
            "pchembl_value": "8.0",
            "standard_type": "IC50",
            "assay_chembl_id": "CHEMBL_A8",
            "assay_type": "B",
        },
        {
            "activity_id": 3,
            "molecule_chembl_id": "CHEMBL2",
            "canonical_smiles": "CCN",
            "pchembl_value": "7.5",
            "standard_type": "EC50",
            "assay_chembl_id": "CHEMBL_AN",
            "assay_type": "F",
        },
        {
            "activity_id": 4,
            "molecule_chembl_id": "CHEMBL3",
            "canonical_smiles": "",
            "pchembl_value": "7.4",
            "standard_type": "Kd",
            "assay_chembl_id": "CHEMBL_A9",
            "assay_type": "B",
        },
        {
            "activity_id": 5,
            "molecule_chembl_id": "CHEMBL4",
            "molecule_pref_name": "Compound four",
            "canonical_smiles": "CCN",
            "pchembl_value": "7.2",
            "standard_type": "Ki",
            "standard_relation": ">",
            "standard_value": "50",
            "standard_units": "nM",
            "assay_chembl_id": "CHEMBL_A9",
            "assay_type": "B",
            "bao_label": "cell-based format",
            "document_chembl_id": "CHEMBL_DOC2",
            "document_year": 2020,
        },
    ],
}

ASSAY_PAYLOAD = {
    "assays": [
        {
            "assay_chembl_id": "CHEMBL_A9",
            "assay_type": "B",
            "confidence_score": 9,
            "relationship_type": "D",
            "bao_format": "BAO_0000219",
            "description": "Cell-based inhibition assay.",
        },
        {
            "assay_chembl_id": "CHEMBL_A8",
            "assay_type": "B",
            "confidence_score": 8,
            "relationship_type": "D",
        },
        {
            "assay_chembl_id": "CHEMBL_AN",
            "assay_type": "F",
            "confidence_score": 9,
            "relationship_type": "N",
        },
    ]
}


class RecordingRegistry:
    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "skill": "chembl-bioactivity",
            "summary": "ChEMBL review completed.",
            "artifacts": [{"id": "review", "type": "chembl-bioactivity-review", "data": {}}],
        }


class ChemblBioactivityTests(unittest.TestCase):
    def test_inputs_are_strict_and_bounded(self):
        normalized = normalize_chembl_inputs("p00533", "binding", "7.25", 25)

        self.assertEqual(normalized["accession"], "P00533")
        self.assertEqual(normalized["assay_types"], ["B"])
        self.assertEqual(normalized["min_pchembl"], 7.25)
        with self.assertRaises(ChemblBioactivityError):
            normalize_chembl_inputs("EGFR", "binding", 7, 25)
        with self.assertRaises(ChemblBioactivityError):
            normalize_chembl_inputs("P00533", "all", 7, 25)
        with self.assertRaises(ChemblBioactivityError):
            normalize_chembl_inputs("P00533", "binding", 13, 25)

    def test_target_parser_selects_only_exact_single_protein(self):
        target = parse_chembl_target(TARGET_PAYLOAD, "P00533")

        self.assertEqual(target["target_chembl_id"], "CHEMBL203")
        with self.assertRaises(ChemblBioactivityError):
            parse_chembl_target({"targets": TARGET_PAYLOAD["targets"] * 2}, "P00533")
        with self.assertRaises(ChemblBioactivityError):
            parse_chembl_target({"targets": [TARGET_PAYLOAD["targets"][1]]}, "P00533")

    def test_activity_parser_preserves_measurements_and_exclusion_reasons(self):
        parsed = parse_chembl_activities(
            ACTIVITY_PAYLOAD,
            ASSAY_PAYLOAD,
            min_pchembl=7,
            limit=100,
        )
        activities = parsed["activities"]

        self.assertEqual([item["activity_id"] for item in activities], ["1", "5"])
        self.assertEqual(activities[0]["standard_type"], "IC50")
        self.assertEqual(activities[1]["standard_type"], "Ki")
        self.assertEqual(activities[1]["standard_relation"], ">")
        self.assertEqual(activities[0]["bao_label"], "cell-based format")
        self.assertEqual(parsed["confidence_9_rows"], 4)
        self.assertEqual(
            parsed["excluded"],
            {
                "confidence_below_9": 1,
                "missing_small_molecule_structure": 1,
                "non_direct_relationship": 1,
            },
        )
        compounds = summarize_chembl_compounds(activities)
        self.assertEqual(len(compounds), 2)
        self.assertEqual(compounds[0]["retrieved_activity_count"], 1)
        self.assertNotIn("lead_score", json.dumps(compounds))

    def test_collection_persists_activity_compound_report_and_manifest(self):
        def fake_request(resource, _parameters):
            return {
                "status": {
                    "chembl_db_version": "ChEMBL_37",
                    "chembl_release_date": "2026-05-01",
                    "status": "UP",
                },
                "target": TARGET_PAYLOAD,
                "activity": ACTIVITY_PAYLOAD,
                "assay": ASSAY_PAYLOAD,
            }[resource]

        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.chembl_bioactivity._request", side_effect=fake_request
        ), patch("molemo.chembl_bioactivity.WORKSPACE_ROOT", Path(temporary)):
            result = collect_chembl_bioactivity(
                accession="P00533",
                assay_scope="binding_functional",
                min_pchembl=7,
                max_activities=25,
            )
            output_files = {
                name: Path(temporary) / relative
                for name, relative in result["outputs"].items()
            }
            manifest = json.loads(output_files["manifest"].read_text(encoding="utf-8"))
            outputs_exist = all(path.is_file() for path in output_files.values())

        self.assertEqual(set(output_files), {"activities", "compounds", "report", "manifest", "summary"})
        self.assertTrue(outputs_exist)
        self.assertEqual(manifest["target"]["target_chembl_id"], "CHEMBL203")
        self.assertEqual(result["retrieval"]["reported_activities"], 2)
        self.assertTrue(result["retrieval"]["truncated"])

    def test_agent_routes_plan_and_hides_approved_collection_tool(self):
        question = "审阅 ChEMBL 中 UniProt P00533 的小分子 binding 活性，pChEMBL >= 7"
        extracted = extract_chembl_bioactivity_plan(question)
        template, inputs = local_workflow_plan(question, {})
        exposed = {item["function"]["name"] for item in SkillRegistry().openai_tools()}

        self.assertEqual(extracted["accession"], "P00533")
        self.assertEqual(extracted["assay_scope"], "binding")
        self.assertEqual(extracted["min_pchembl"], 7)
        self.assertEqual(template, "target-ligand-bioactivity-review")
        self.assertEqual(inputs, extracted)
        self.assertIn("chembl_bioactivity_preflight", exposed)
        self.assertNotIn("chembl_bioactivity_collect", exposed)

    def test_model_context_compacts_preview_without_duplicate_artifact_or_smiles(self):
        activities = [
            {
                "rank": index,
                "molecule_chembl_id": f"CHEMBL{index}",
                "molecule_name": f"Compound {index}",
                "canonical_smiles": "C" * 800,
                "pchembl_value": 8,
                "standard_type": "IC50",
                "assay_description": "A" * 1200,
                "assay_chembl_id": f"CHEMBL_A{index}",
            }
            for index in range(1, 21)
        ]
        data = {
            "source": "ChEMBL",
            "target": {"accession": "P00533", "target_chembl_id": "CHEMBL203"},
            "activities": activities,
            "compounds": [],
        }
        encoded = compact_tool_result(
            {
                "ok": True,
                "tool": "chembl_bioactivity_preflight",
                "skill": "chembl-bioactivity",
                "summary": "Previewed ChEMBL activity.",
                "data": data,
                "artifacts": [{"type": "chembl-bioactivity-preflight", "data": data}],
            }
        )
        compacted = json.loads(encoded)

        self.assertLessEqual(len(encoded), 24000)
        self.assertEqual(len(compacted["data"]["activities"]), 12)
        self.assertEqual(compacted["data"]["target"]["target_chembl_id"], "CHEMBL203")
        self.assertTrue(compacted["artifacts_omitted"])
        self.assertNotIn("canonical_smiles", encoded)
        self.assertNotIn("assay_description", encoded)

    def test_workflow_preflights_but_collects_only_after_approval(self):
        preflight = {
            "ready": True,
            "summary": "Resolved EGFR and previewed 20 activities.",
            "target": {"accession": "P00533", "target_chembl_id": "CHEMBL203"},
        }
        registry = RecordingRegistry()
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.workflow_runtime.preflight_chembl_bioactivity", return_value=preflight
        ):
            manager = WorkflowManager(Path(temporary))
            run = manager.create_plan(
                "target-ligand-bioactivity-review",
                {
                    "accession": "P00533",
                    "assay_scope": "binding_functional",
                    "min_pchembl": 7,
                    "max_activities": 25,
                },
            )
            self.assertEqual(run["status"], "pending_approval")
            self.assertEqual(run["preflight"]["target"]["target_chembl_id"], "CHEMBL203")
            self.assertEqual(registry.calls, [])
            completed = manager.approve(run["id"], registry)

        self.assertEqual(completed["status"], "completed")
        self.assertEqual(registry.calls[0][0], "chembl_bioactivity_collect")
        self.assertEqual(registry.calls[0][1]["max_activities"], 25)


if __name__ == "__main__":
    unittest.main()
