---
name: transcriptomics-analysis
description: Validate raw bulk RNA-seq count matrices and sample metadata, then run researcher-approved PyDESeq2 differential expression with explicit design, contrast, QC, provenance, and saved outputs. Use when the user already has gene-level raw counts; do not present it as a FASTQ-to-count pipeline.
---

# Bulk RNA-seq Analysis

Use `transcriptomics_preflight` before proposing differential expression. Confirm exact sample matching, biological replication, condition levels, optional batch variables, and the requested direction of the contrast.

Use `transcriptomics_run_de` only through a researcher-approved workflow. It accepts non-negative integer raw counts, filters only on total count before modeling, fits an explicit PyDESeq2 design, and persists the full result table, normalized counts, manifest, and summary.

Review PCA and sample-level library metrics before interpreting the volcano plot or ranked genes. Report effect size and adjusted p-value together. PyDESeq2 may differ numerically from Bioconductor DESeq2, this workflow does not apply LFC shrinkage, and differential expression does not establish causal biology.
