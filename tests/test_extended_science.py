import unittest
from unittest.mock import patch

from agent_runtime import extract_alphafold_accession, extract_pubchem_query, local_intent_tools
from bio_clients import (
    ExternalDataError,
    fetch_alphafold_pae_payload,
    parse_alphafold_predictions,
    parse_pubchem_payload,
    parse_rcsb_payload,
    parse_uniprot_payload,
)
from ngs_qc import FastqError, analyze_fastq_text
from skill_runtime import SkillRegistry, compact_tool_result
from structure_io import (
    StructureError,
    build_structure_sample,
    parse_alphafold_pae,
    parse_structure_text,
    summarize_plddt,
)


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

ALPHAFOLD_PDB_TEXT = """\
ATOM      1  CA  ALA A   1       0.000   0.000   0.000  1.00 95.00           C
ATOM      2  CA  GLY A   2       1.500   0.000   0.000  1.00 45.00           C
END
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

    def test_alphafold_payload_selects_exact_accession_not_first_isoform(self):
        result = parse_alphafold_predictions(
            [
                {
                    "uniprotAccession": "P04637-9",
                    "entryId": "AF-P04637-9-F1",
                    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P04637-9-F1-model_v6.pdb",
                },
                {
                    "uniprotAccession": "P04637",
                    "entryId": "AF-P04637-F1",
                    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v6.pdb",
                    "globalMetricValue": 75.06,
                },
            ],
            "P04637",
        )

        self.assertEqual(result["entry_id"], "AF-P04637-F1")
        self.assertEqual(result["mean_plddt"], 75.06)
        self.assertEqual(result["coordinate_type"], "predicted")

    def test_alphafold_payload_rejects_missing_exact_accession(self):
        with self.assertRaises(ExternalDataError):
            parse_alphafold_predictions(
                [
                    {
                        "uniprotAccession": "P04637-9",
                        "entryId": "AF-P04637-9-F1",
                        "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P04637-9-F1-model_v6.pdb",
                    }
                ],
                "P04637",
            )

    def test_alphafold_pae_download_accepts_only_official_versioned_path(self):
        url = "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-predicted_aligned_error_v6.json"
        with patch("bio_clients.get_json_array", return_value=[{"predicted_aligned_error": [[0]]}]) as get:
            payload = fetch_alphafold_pae_payload(url)

        self.assertEqual(payload[0]["predicted_aligned_error"], [[0]])
        get.assert_called_once_with(url)
        with self.assertRaises(ExternalDataError):
            fetch_alphafold_pae_payload("https://example.org/AF-P04637-F1-predicted_aligned_error_v6.json")


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

    def test_alphafold_plddt_is_retained_and_labeled_as_prediction(self):
        structure = parse_structure_text(ALPHAFOLD_PDB_TEXT, "AF-P04637-F1", "pdb")
        structure["confidence"] = summarize_plddt(structure, 70.0)
        sample = build_structure_sample(
            structure,
            "TP53 predicted structure",
            {
                "source": "AlphaFold Protein Structure Database",
                "coordinate_type": "predicted",
                "entry_id": "AF-P04637-F1",
                "accession": "P04637",
            },
        )

        self.assertEqual(structure["backbone"][0]["points"][0]["bfactor"], 95.0)
        self.assertEqual(structure["confidence"]["counts"]["very_high"], 1)
        self.assertEqual(structure["confidence"]["counts"]["very_low"], 1)
        self.assertEqual(sample["metadata"]["coordinateType"], "predicted")
        self.assertIn("mean pLDDT 70.00", sample["confidence"])
        self.assertNotIn("experimental", sample["confidence"])

    def test_alphafold_pae_preserves_direction_and_residue_axes(self):
        matrix = [
            [0, 1, 8, 9],
            [2, 0, 7, 8],
            [15, 14, 0, 1],
            [16, 15, 2, 0],
        ]
        pae = parse_alphafold_pae(
            [{"predicted_aligned_error": matrix, "max_predicted_aligned_error": 31.75}],
            expected_residues=4,
        )

        self.assertEqual(pae["matrix"], matrix)
        self.assertNotEqual(pae["matrix"][0][1], pae["matrix"][1][0])
        self.assertEqual(pae["orientation"]["rows"], "scored residue")
        self.assertEqual(pae["orientation"]["columns"], "aligned residue")
        self.assertEqual(pae["max_error"], 31.75)

    def test_alphafold_pae_downsamples_by_residue_blocks(self):
        matrix = [[float(row + column) for column in range(40)] for row in range(40)]
        pae = parse_alphafold_pae(
            [{"predicted_aligned_error": matrix, "max_predicted_aligned_error": 78}],
            expected_residues=40,
            max_bins=32,
        )

        self.assertTrue(pae["downsampled"])
        self.assertEqual(pae["bin_size"], 2)
        self.assertEqual(pae["matrix_size"], 20)
        self.assertEqual(pae["matrix"][0][0], 1.0)

    def test_alphafold_pae_rejects_shape_and_residue_mismatch(self):
        with self.assertRaises(StructureError):
            parse_alphafold_pae([{"predicted_aligned_error": [[0, 1], [1]]}])
        with self.assertRaises(StructureError):
            parse_alphafold_pae(
                [{"predicted_aligned_error": [[0, 1], [1, 0]]}],
                expected_residues=3,
            )

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

    def test_alphafold_structure_survives_optional_pae_failure(self):
        handler = self.registry.tools["structure_fetch_alphafold"].handler
        metadata = {
            "source": "AlphaFold Protein Structure Database",
            "source_url": "https://alphafold.ebi.ac.uk/entry/P04637",
            "coordinate_type": "predicted",
            "accession": "P04637",
            "entry_id": "AF-P04637-F1",
            "gene": "TP53",
            "mean_plddt": 70,
            "model_url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v6.pdb",
            "pae_url": "https://alphafold.ebi.ac.uk/files/AF-P04637-F1-predicted_aligned_error_v6.json",
        }
        with patch.dict(
            handler.__globals__,
            {
                "lookup_alphafold_prediction": lambda _accession: metadata,
                "fetch_alphafold_pdb_text": lambda _url: ALPHAFOLD_PDB_TEXT,
                "fetch_alphafold_pae_payload": lambda _url: (_ for _ in ()).throw(
                    ExternalDataError("temporary PAE failure")
                ),
            },
        ):
            result = handler({"accession": "P04637"}, {})

        sample = result["artifacts"][0]["data"]
        self.assertEqual(result["data"]["structure"]["atom_count"], 2)
        self.assertFalse(sample["metadata"]["paeAvailable"])
        self.assertTrue(any("temporary PAE failure" in caveat for caveat in result["caveats"]))

    def test_pae_matrix_is_not_forwarded_into_model_tool_context(self):
        result = {
            "ok": True,
            "tool": "structure_fetch_alphafold",
            "skill": "protein-structure",
            "summary": "AlphaFold structure with PAE loaded.",
            "data": {"structure": {"pae": {"matrix": [[12.5] * 80 for _ in range(80)]}}},
            "artifacts": [{"type": "protein-structure", "data": {"pae": "viewer artifact"}}],
        }

        compact = compact_tool_result(result)

        self.assertIn('"truncated":true', compact)
        self.assertNotIn('"matrix"', compact)

    def test_local_agent_intent_extractors_select_new_tools(self):
        self.assertEqual(extract_pubchem_query("lookup PubChem caffeine"), "caffeine")
        selected = local_intent_tools("检查 PDB 1L2Y，并对 examples/tiny.fastq 做 QC")
        names = [name for name, _ in selected]
        self.assertIn("structure_fetch_pdb", names)
        self.assertIn("ngs_fastq_qc", names)

        alphafold = local_intent_tools("从 AlphaFold DB 加载 UniProt P04637 预测结构并按 pLDDT 显示")
        self.assertEqual(extract_alphafold_accession("AlphaFold P04637"), "P04637")
        self.assertIn("structure_fetch_alphafold", [name for name, _ in alphafold])


if __name__ == "__main__":
    unittest.main()
