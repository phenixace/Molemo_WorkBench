# Human Variant Evidence Review

Use this skill for a focused question about one simple human variant.

## Input discipline

- Prefer an exact, versioned RefSeq coding HGVS expression.
- An rsID may be multiallelic. If preflight reports ambiguity, ask for one of the returned HGVS alleles instead of guessing.
- Confirm allele, transcript, assembly, phenotype, and inheritance context before interpreting the evidence.
- Complex alleles, haplotypes, structural variants, and batch VCF interpretation are outside this workflow.

## Evidence lanes

- Treat the ClinVar aggregate classification as a submitted source assertion. Preserve its review status, last evaluation date, condition scope, and source link.
- Treat Ensembl VEP consequence terms, SIFT, and PolyPhen as computational annotations, not clinical classifications.
- Treat gnomAD allele counts and frequencies as population observations. Check filters and ancestry-specific variation; rarity is not proof of pathogenicity.
- Never combine these lanes into a custom pathogenicity, confidence, or ACMG/AMP score.

## Execution boundary

- `variant_evidence_preflight` may resolve the identifier before approval.
- `variant_evidence_review` is only available inside a researcher-approved workflow.
- Cite the ClinVar accession and source URLs when using the result.
- State explicitly that the report is not a diagnosis, treatment recommendation, or de novo clinical classification.
