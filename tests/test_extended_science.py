import unittest

from agent_runtime import extract_pubchem_query, local_intent_tools
from bio_clients import parse_pubchem_payload, parse_rcsb_payload, parse_uniprot_payload
from ngs_qc import FastqError, analyze_fastq_text
from skill_runtime import SkillRegistry
from structure_io import parse_structure_text


PDB_TEXT = """\
ATOM      1  N   ALA A   1      -1.458   0.000   0.000  1.00 20.00           N
ATOM      2  CA  ALA A   1       0.000   0.000   0.000  1.00 20.00           C
ATOM      3  C   ALA A   1       0.600   1.410   0.000  1.00 20.00           C
HETATM    4  O1  LIG A 101       2.500  -1.600   0.500  1.00 20.00           O
END
"""

MMCIF_TEXT = """\
data_demo
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.pdbx_PDB_model_num
ATOM 1 N N . ALA A 1 0.0 0.0 0.0 1
ATOM 2 C CA . ALA A 1 1.4 0.0 0.0 1
#
"""

FASTQ_TEXT = """\
@read-1
ACGT
+
IIII
@read-2
GCGC
+
5555
@read-3
NNNN
+
!!!!
"""


class PublicDatabaseParsingTests(unittest.TestCase):
    def test_pubchem_payload_normalizes_current_property_names(self):
        result = parse_pubchem_payload(
            {
                "PropertyTable": {
                    "Properties": [
                        {
                            "CID": 2519,
                            "Title": "Caffeine",
                            "MolecularFormula": "C8H10N4O2",
                            "MolecularWeight": "194.19",
                            "SMILES": "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
                            "HBondAcceptorCount": 3,
                            "HBondDonorCount": 0,
                        }
                    ]
                }
            },
            "caffeine",
        )

        self.assertEqual(result["cid"], 2519)
        self.assertEqual(result["hba"], 3)
        self.assertTrue(result["smiles"])

    def test_uniprot_payload_preserves_source_sequence_and_pdb_links(self):
        result = parse_uniprot_payload(
            {
                "primaryAccession": "P69905",
                "entryType": "UniProtKB reviewed (Swiss-Prot)",
                "proteinDescription": {"recommendedName": {"fullName": {"value": "Hemoglobin subunit alpha"}}},
                "organism": {"scientificName": "Homo sapiens", "taxonId": 9606},
                "sequence": {"value": "VLSPADKTNVK", "length": 11, "molWeight": 1200},
                "uniProtKBCrossReferences": [{"database": "PDB", "id": "1A3N"}],
            }
        )

        self.assertTrue(result["reviewed"])
        self.assertEqual(result["sequence"], "VLSPADKTNVK")
        self.assertEqual(result["pdb_ids"], ["1A3N"])

    def test_rcsb_payload_keeps_experimental_metadata(self):
        result = parse_rcsb_payload(
            {
                "rcsb_entry_container_identifiers": {"entry_id": "1ABC"},
                "struct": {"title": "Example structure"},
                "exptl": [{"method": "X-RAY DIFFRACTION"}],
                "rcsb_entry_info": {"resolution_combined": [1.8], "deposited_atom_count": 99},
            }
        )

        self.assertEqual(result["pdb_id"], "1ABC")
        self.assertEqual(result["resolution_angstrom"], 1.8)


class StructureAndNgsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = SkillRegistry()

    def test_pdb_and_mmcif_coordinate_parsers(self):
        pdb = parse_structure_text(PDB_TEXT, "demo", "pdb")
        cif = parse_structure_text(MMCIF_TEXT, "demo", "mmcif")

        self.assertEqual(pdb["atom_count"], 4)
        self.assertEqual(pdb["sequence"], "A")
        self.assertEqual(pdb["ligands"], ["LIG"])
        self.assertEqual(cif["atom_count"], 2)
        self.assertEqual(cif["sequence"], "A")

    def test_fastq_qc_reports_quality_and_composition(self):
        result = analyze_fastq_text(FASTQ_TEXT)

        self.assertEqual(result["reads_analyzed"], 3)
        self.assertEqual(result["mean_quality"], 20.0)
        self.assertAlmostEqual(result["q30_percent"], 33.33, places=2)
        self.assertEqual(result["gc_percent"], 50.0)
        self.assertEqual(result["n_percent"], 33.333)

    def test_fastq_rejects_incomplete_records(self):
        with self.assertRaises(FastqError):
            analyze_fastq_text("@read\nACGT\n+\n")

    def test_workspace_structure_and_fastq_skills_return_artifacts(self):
        structure = self.registry.execute("structure_parse_workspace", {"path": "examples/mini-protein.pdb"})
        fastq = self.registry.execute("ngs_fastq_qc", {"path": "examples/tiny.fastq"})

        self.assertEqual(structure["artifacts"][0]["type"], "protein-structure")
        self.assertEqual(structure["data"]["structure"]["sequence"], "AG")
        self.assertEqual(fastq["artifacts"][0]["type"], "fastq-qc")
        self.assertEqual(fastq["data"]["reads_analyzed"], 3)

    def test_local_agent_intent_extractors_select_new_tools(self):
        self.assertEqual(extract_pubchem_query("lookup PubChem caffeine"), "caffeine")
        selected = local_intent_tools("检查 PDB 1L2Y，并对 examples/tiny.fastq 做 QC")
        names = [name for name, _ in selected]
        self.assertIn("structure_fetch_pdb", names)
        self.assertIn("ngs_fastq_qc", names)


if __name__ == "__main__":
    unittest.main()
