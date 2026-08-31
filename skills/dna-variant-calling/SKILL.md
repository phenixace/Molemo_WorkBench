---
name: dna-variant-calling
description: Preflight and run a bounded, researcher-approved paired-end short-read DNA alignment and candidate variant-calling workflow with local BWA, samtools, and bcftools.
---

# DNA Variant Calling

Use `dna_variant_calling_preflight` to validate two synchronized paired-end FASTQ files, a small workspace reference FASTA, sample identity, resource limits, and the local toolchain. Preflight must not create BAM or VCF outputs.

Use `dna_variant_calling_run` only through a researcher-approved workflow. Preserve input hashes, tool versions, read-group sample identity, parameters, stage timings, BAM/BAI, coverage, normalized candidate VCF, tabular calls, manifest, and interpretation boundaries.

This bounded workflow is a reproducible engineering example for small references and short-read research data. It is not production human WGS/WES, clinical diagnostics, a somatic caller, or a germline classification workflow. Do not infer pathogenicity, actionability, treatment response, or sample identity from its output.
