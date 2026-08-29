---
name: ngs-qc
description: Run deterministic FASTQ quality control on a file inside the constrained local workspace. Use for read counts, length, GC, N content, Phred quality, Q20/Q30, and per-cycle diagnostics before downstream sequencing analysis.
---

# NGS QC

Use `ngs_fastq_qc` only after a `.fastq` or `.fq` file has been imported into the workspace. Report whether the result is sampled, the number of reads inspected, and any low-quality cycles.

This skill performs local quality control. It does not align reads, call variants, quantify transcripts, or establish biological differential expression.
