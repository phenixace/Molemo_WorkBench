import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skill_runtime import SkillRegistry, compact_tool_result
from structure_io import parse_structure_atoms, parse_structure_text
from variant_structure import (
    VariantStructureError,
    analyze_variant_contacts,
    collect_variant_structure,
    normalize_variant_structure_inputs,
    preflight_variant_structure,
)


PDB_TEXT = """\
ATOM      1  N   CYS A  12       0.000   0.000   1.000  1.00 20.00           N  
ATOM      2  CA  CYS A  12       0.000   0.000   0.500  1.00 20.00           C  
ATOM      3  SG  CYS A  12       0.000   0.000   0.000  1.00 20.00           S  
ATOM      4  N   ALA A  13       3.200   0.000   0.000  1.00 20.00           N  
ATOM      5  CA  ALA A  13       3.500   0.000   0.000  1.00 20.00           C  
ATOM      6  CA  GLY B  12      20.000   0.000   0.000  1.00 20.00           C  
HETATM    7  C1  MOV A 303       1.805   0.000   0.000  1.00 20.00           C  
HETATM    8  O1  GDP A 302       5.500   0.000   0.000  1.00 20.00           O  
END
"""

RCSB_METADATA = {
    "source": "RCSB PDB",
    "source_url": "https://www.rcsb.org/structure/6OIM",
    "pdb_id": "6OIM",
    "title": "KRAS G12C test structure",
    "methods": ["X-RAY DIFFRACTION"],
    "resolution_angstrom": 1.65,
    "release_date": "2019-11-06",
}


class VariantStructureTests(unittest.TestCase):
    def test_full_atom_parser_is_available_without_viewer_sampling(self):
        atoms, source_format = parse_structure_atoms(PDB_TEXT, "pdb")
        structure = parse_structure_text(PDB_TEXT, "demo", "pdb")

        self.assertEqual(source_format, "PDB")
        self.assertEqual(len(atoms), 8)
        self.assertEqual(structure["atom_count"], 8)

    def test_alternate_allele_and_contacts_use_exact_author_residue(self):
        atoms, _ = parse_structure_atoms(PDB_TEXT, "pdb")
        site = analyze_variant_contacts(
            atoms,
            chain="A",
            author_residue_number="12",
            reference_aa="G",
            alternate_aa="C",
            variant="G12C",
            contact_cutoff_angstrom=4.5,
        )

        self.assertEqual(site["observed_residue"], "CYS")
        self.assertEqual(site["structure_allele"], "alternate")
        self.assertEqual(site["protein_contact_count"], 1)
        self.assertEqual(site["sequence_adjacent_count"], 1)
        self.assertEqual(site["nonlocal_protein_contact_count"], 0)
        self.assertEqual(site["protein_contacts"][0]["sequence_relation"], "sequence-adjacent")
        self.assertEqual(site["hetero_contact_count"], 1)
        self.assertEqual(site["hetero_contacts"][0]["instance_id"], "MOV:A:303")
        self.assertEqual(site["hetero_contacts"][0]["min_distance_angstrom"], 1.805)
        self.assertTrue(site["hetero_contacts"][0]["short_contact_below_2_1_angstrom"])
        self.assertEqual(len(site["ligand_instances"]), 2)

    def test_residue_mismatch_and_wrong_chain_stop_without_guessing(self):
        atoms, _ = parse_structure_atoms(PDB_TEXT, "pdb")
        common = {
            "atoms": atoms,
            "author_residue_number": "12",
            "reference_aa": "V",
            "alternate_aa": "D",
            "variant": "V12D",
            "contact_cutoff_angstrom": 4.5,
        }
        with self.assertRaisesRegex(VariantStructureError, "expects V or D"):
            analyze_variant_contacts(chain="A", **common)
        with self.assertRaisesRegex(VariantStructureError, "was not found"):
            analyze_variant_contacts(chain="Z", **common)

    def test_input_normalization_is_bounded(self):
        result = normalize_variant_structure_inputs("6oim", "A", "p.G12C", 4.5)
        self.assertEqual(result["pdb_id"], "6OIM")
        self.assertEqual(result["variant"], "G12C")
        with self.assertRaises(VariantStructureError):
            normalize_variant_structure_inputs("6OIM", "A", "G12C", 9)
        with self.assertRaises(VariantStructureError):
            normalize_variant_structure_inputs("6OIM", "A", "Gly12Cys", 4.5)
        with self.assertRaises(VariantStructureError):
            normalize_variant_structure_inputs("6OIM", "A", "G12G", 4.5)

    @patch("variant_structure.fetch_rcsb_pdb_text", return_value=PDB_TEXT)
    @patch("variant_structure.lookup_rcsb_entry", return_value=RCSB_METADATA)
    def test_preflight_returns_viewer_and_compact_model_context(self, _metadata, _coordinates):
        result = preflight_variant_structure(pdb_id="6OIM", chain="A", variant="G12C")
        self.assertTrue(result["ready"])
        self.assertEqual(result["sample"]["structure"]["focus"]["variant"], "G12C")
        registry = SkillRegistry()
        tool_result = registry.tools["variant_structure_preflight"].handler(
            {"pdb_id": "6OIM", "chain": "A", "variant": "G12C"}, {}
        )
        encoded = compact_tool_result(
            {**tool_result, "tool": "variant_structure_preflight", "skill": "variant-structure"}
        )
        payload = json.loads(encoded)
        self.assertTrue(payload["viewer_coordinates_omitted"])
        self.assertNotIn("sample", payload["data"])
        self.assertEqual(payload["data"]["site"]["hetero_contacts"][0]["residue"], "MOV")

    @patch("variant_structure.fetch_rcsb_pdb_text", return_value=PDB_TEXT)
    @patch("variant_structure.lookup_rcsb_entry", return_value=RCSB_METADATA)
    def test_approved_review_persists_bounded_outputs(self, _metadata, _coordinates):
        with tempfile.TemporaryDirectory() as directory, patch(
            "variant_structure.WORKSPACE_ROOT", Path(directory)
        ):
            result = collect_variant_structure(pdb_id="6OIM", chain="A", variant="G12C")
            output_root = Path(directory) / result["output_root"]
            self.assertTrue((output_root / "contacts.tsv").is_file())
            self.assertTrue((output_root / "ligands.tsv").is_file())
            report = json.loads((output_root / "report.json").read_text(encoding="utf-8"))
            self.assertNotIn("sample", report)
            self.assertEqual(report["site"]["structure_allele"], "alternate")

    def test_collection_tool_requires_workflow_approval(self):
        registry = SkillRegistry()
        self.assertIn("variant_structure_preflight", registry.tools)
        self.assertFalse(registry.tools["variant_structure_collect"].agent_callable)


if __name__ == "__main__":
    unittest.main()
