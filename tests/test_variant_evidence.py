import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from molemo.agent_runtime import extract_variant_identifier, local_workflow_plan
from molemo.skill_runtime import SkillRegistry
from molemo.variant_evidence import (
    VariantEvidenceError,
    normalize_variant_query,
    resolve_variant,
    review_variant_evidence,
)


CLINVAR_CANDIDATE = {
    "variation_id": "15333",
    "name": "NM_000518.5(HBB):c.20A>T (p.Glu7Val)",
    "gene_symbol": "HBB",
    "hgvs_c": "NM_000518.5:c.20A>T",
    "hgvs_p": "NP_000509.1:p.Glu7Val",
    "hgvs_exprs": ["NM_000518.5:c.20A>T", "NP_000509.1:p.Glu7Val"],
    "db_snp": "rs334",
}

CLINVAR_SUMMARY = {
    "result": {
        "uids": ["15333"],
        "15333": {
            "uid": "15333",
            "obj_type": "single nucleotide variant",
            "accession": "VCV000015333",
            "accession_version": "VCV000015333.180",
            "title": "NM_000518.5(HBB):c.20A>T (p.Glu7Val)",
            "variation_set": [
                {
                    "variation_name": "NM_000518.5(HBB):c.20A>T (p.Glu7Val)",
                    "aliases": ["HbS"],
                    "variant_type": "single nucleotide variant",
                    "canonical_spdi": "NC_000011.10:5227001:T:A",
                    "variation_xrefs": [
                        {"db_source": "dbSNP", "db_id": "334"},
                        {"db_source": "ClinGen", "db_id": "CA125138"},
                    ],
                    "variation_loc": [
                        {
                            "status": "current",
                            "assembly_name": "GRCh38",
                            "chr": "11",
                            "start": "5227002",
                            "stop": "5227002",
                            "band": "11p15.4",
                            "assembly_acc_ver": "GCF_000001405.38",
                        },
                        {
                            "status": "previous",
                            "assembly_name": "GRCh37",
                            "chr": "11",
                            "start": "5248232",
                            "stop": "5248232",
                            "band": "11p15.4",
                            "assembly_acc_ver": "GCF_000001405.25",
                        },
                    ],
                    "allele_freq_set": [
                        {"source": "The Genome Aggregation Database (gnomAD)", "value": "0.01298"}
                    ],
                }
            ],
            "supporting_submissions": {"scv": ["SCV1", "SCV2"], "rcv": ["RCV1"]},
            "germline_classification": {
                "description": "Pathogenic",
                "last_evaluated": "2026/07/01 00:00",
                "review_status": "criteria provided, multiple submitters, no conflicts",
                "trait_set": [
                    {
                        "trait_name": "Hb SS disease",
                        "trait_xrefs": [{"db_source": "MONDO", "db_id": "MONDO:0011382"}],
                    }
                ],
            },
            "clinical_impact_classification": {"description": ""},
            "oncogenicity_classification": {"description": ""},
            "genes": [{"symbol": "HBB", "geneid": "3043"}],
            "molecular_consequence_list": ["missense variant"],
            "protein_change": "E7V",
        },
    }
}

VEP_RESPONSE = [
    {
        "input": "NM_000518.5:c.20A>T",
        "assembly_name": "GRCh38",
        "seq_region_name": "11",
        "start": 5227002,
        "end": 5227002,
        "strand": -1,
        "allele_string": "A/T",
        "variant_class": "SNV",
        "most_severe_consequence": "missense_variant",
        "colocated_variants": [{"id": "rs334"}],
        "transcript_consequences": [
            {
                "transcript_id": "ENST00000408104",
                "gene_id": "ENSG00000221031",
                "biotype": "ribozyme",
                "consequence_terms": ["upstream_gene_variant"],
                "impact": "MODIFIER",
                "canonical": 1,
            },
            {
                "transcript_id": "ENST00000335295",
                "gene_symbol": "HBB",
                "gene_id": "ENSG00000244734",
                "biotype": "protein_coding",
                "consequence_terms": ["missense_variant"],
                "impact": "MODERATE",
                "canonical": 1,
                "mane_select": "NM_000518.5",
                "hgvsc": "ENST00000335295.4:c.20A>T",
                "hgvsp": "ENSP00000333994.3:p.Glu7Val",
                "protein_start": 7,
                "amino_acids": "E/V",
                "codons": "gAg/gTg",
                "sift_prediction": "deleterious_low_confidence",
                "sift_score": 0,
            }
        ],
    }
]

GNOMAD_RESPONSE = {
    "data": {
        "variant": {
            "variant_id": "11-5227002-T-A",
            "rsid": "rs334",
            "ref": "T",
            "alt": "A",
            "joint": {
                "ac": 4272,
                "an": 1610650,
                "homozygote_count": 40,
                "filters": ["discrepant_frequencies"],
                "populations": [
                    {"id": "afr", "ac": 3707, "an": 74908, "homozygote_count": 36},
                    {"id": "nfe", "ac": 46, "an": 1176872, "homozygote_count": 0},
                    {"id": "afr_XX", "ac": 2029, "an": 41402, "homozygote_count": 12},
                ],
            },
        }
    }
}


class VariantEvidenceTests(unittest.TestCase):
    def test_identifier_normalization_and_multiallelic_rsid_rejection(self):
        self.assertEqual(normalize_variant_query(" RS334 "), "rs334")
        self.assertEqual(normalize_variant_query("NM_000518.5:c.20A>T"), "NM_000518.5:c.20A>T")
        with self.assertRaises(VariantEvidenceError):
            normalize_variant_query("HBB E7V")

        candidates = [
            {**CLINVAR_CANDIDATE, "variation_id": "15175", "hgvs_c": "NM_000518.5:c.20A>C"},
            CLINVAR_CANDIDATE,
        ]
        with patch("molemo.variant_evidence._search_clinvar", return_value=candidates):
            with self.assertRaisesRegex(VariantEvidenceError, "allele-ambiguous"):
                resolve_variant("rs334")

    def test_review_preserves_source_lanes_and_persists_outputs(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
            "molemo.variant_evidence._search_clinvar", return_value=[CLINVAR_CANDIDATE]
        ), patch(
            "molemo.variant_evidence._clinvar_summary", return_value=CLINVAR_SUMMARY
        ), patch(
            "molemo.variant_evidence.get_json_array", return_value=VEP_RESPONSE
        ), patch(
            "molemo.variant_evidence.post_json", return_value=GNOMAD_RESPONSE
        ), patch(
            "molemo.variant_evidence.WORKSPACE_ROOT", Path(temporary)
        ):
            result = review_variant_evidence("NM_000518.5:c.20A>T")
            files_exist = all((Path(temporary) / path).is_file() for path in result["outputs"].values())

        self.assertEqual(result["variant"]["accession"], "VCV000015333.180")
        self.assertEqual(result["variant"]["gnomad_variant_id"], "11-5227002-T-A")
        self.assertEqual(result["vep"]["most_severe_consequence"], "missense_variant")
        self.assertEqual(result["vep"]["transcripts"][0]["gene_symbol"], "HBB")
        self.assertAlmostEqual(result["gnomad"]["allele_frequency"], 4272 / 1610650)
        self.assertEqual([item["id"] for item in result["gnomad"]["populations"]], ["afr", "nfe"])
        self.assertNotIn("pathogenicity_score", json.dumps(result))
        self.assertTrue(files_exist)

    def test_agent_routes_review_and_exposes_only_preflight(self):
        question = "请解释并审阅 NM_000518.5:c.20A>T 的变异证据和人群频率"
        template, inputs = local_workflow_plan(question, {})
        registry = SkillRegistry()
        exposed = {item["function"]["name"] for item in registry.openai_tools()}

        self.assertEqual(extract_variant_identifier(question), "NM_000518.5:c.20A>T")
        self.assertEqual(template, "variant-evidence-review")
        self.assertEqual(inputs["variant"], "NM_000518.5:c.20A>T")
        self.assertIn("variant_evidence_preflight", exposed)
        self.assertNotIn("variant_evidence_review", exposed)


if __name__ == "__main__":
    unittest.main()
