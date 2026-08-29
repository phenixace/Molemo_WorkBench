import unittest

from molemo.pipeline import PipelineError, parse_molecule, parse_protein


class MoleculePipelineTests(unittest.TestCase):
    def test_caffeine_rdkit_graph_has_real_atoms_and_bonds(self):
        sample = parse_molecule("Cn1cnc2c1c(=O)n(C)c(=O)n2C")

        self.assertEqual(sample["type"], "molecule")
        self.assertEqual(sample["formula"], "C8H10N4O2")
        self.assertEqual(len(sample["atoms"]), 14)
        self.assertEqual(len(sample["bonds"]), 15)
        self.assertGreaterEqual(len(sample["rings"]), 2)
        self.assertEqual(sample["metadata"]["source"], "rdkit")

        nitrogen_degrees = []
        for index, atom in enumerate(sample["atoms"]):
            if atom["e"] != "N":
                continue
            degree = sum(1 for bond in sample["bonds"] if bond[0] == index or bond[1] == index)
            nitrogen_degrees.append(degree)
        self.assertTrue(all(degree <= 3 for degree in nitrogen_degrees))

    def test_aspirin_properties_are_rdkit_descriptors(self):
        sample = parse_molecule("CC(=O)OC1=CC=CC=C1C(=O)O")

        self.assertEqual(sample["formula"], "C9H8O4")
        self.assertEqual(sample["properties"]["HBD"], "1")
        self.assertEqual(sample["properties"]["HBA"], "3")
        self.assertEqual(sample["properties"]["Rings"], "1")

    def test_invalid_smiles_raises_pipeline_error(self):
        with self.assertRaises(PipelineError):
            parse_molecule("C1CC")


class ProteinPipelineTests(unittest.TestCase):
    def test_fasta_sequence_pipeline(self):
        sample = parse_protein(">trpcage\nNLYIQWLKDGGPSSGRPPPS\n")

        self.assertEqual(sample["type"], "protein")
        self.assertEqual(sample["sequence"], "NLYIQWLKDGGPSSGRPPPS")
        self.assertEqual(sample["properties"]["Length"], "20 aa")
        self.assertEqual(sample["metadata"]["source"], "local_sequence_pipeline")
        self.assertIn("GRAVY", sample["properties"])

    def test_invalid_amino_acid_raises_pipeline_error(self):
        with self.assertRaises(PipelineError):
            parse_protein("ACDZ")


if __name__ == "__main__":
    unittest.main()
