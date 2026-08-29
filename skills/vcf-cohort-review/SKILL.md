---
name: vcf-cohort-review
description: Validate and review a bounded multi-sample workspace VCF with explicit depth, VAF and FILTER rules, optional longitudinal sample metadata, mutation-landscape artifacts and auditable outputs. Use for processed cohort, tumor, ctDNA or longitudinal VCF review; not raw-read variant calling or clinical interpretation.
---

# Multi-sample VCF Review

Use `vcf_cohort_preflight` before proposing execution. Confirm the exact VCF path, sample identifiers, optional subject/timepoint metadata, reference header, annotation source, minimum depth, minimum VAF and treatment of non-PASS records.

Use `vcf_cohort_review` only through a researcher-approved workflow. Preserve source coordinates, REF/ALT order, genotype, allele depth, depth, VAF, FILTER status, supplied annotations, exclusions, sample metadata, input hashes and output paths.

Treat each VCF call as an upstream caller result. Missing or excluded calls do not prove biological absence. VAF is not tumor fraction, clonality or response. Low-frequency calls require assay-specific limit-of-detection and read-level review. INFO annotations are reproduced, not independently reannotated.

Do not classify somatic versus germline status, infer drivers or resistance, recommend therapy, or claim clinical actionability. The workflow accepts bounded uncompressed text VCF 4.x; BCF, VCF.gz, raw-read calling, copy number, structural-variant interpretation and clinical reporting remain outside scope.
