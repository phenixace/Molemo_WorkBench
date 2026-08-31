# Molemo Showcase

[简体中文](README.zh-CN.md) | English

These cases are small, deterministic demonstrations of real Molemo WorkBench code paths. They are not substitutes for production cohort validation.

```bash
python -m molemo.showcase
python -m molemo.showcase --full
```

The quick run verifies a caffeine molecular graph, a Trp-cage protein profile, and an approved paired-end FASTQ-to-BAM/VCF workflow. The full run also executes PyDESeq2 bulk RNA-seq and Scanpy single-cell workflows. A machine-readable report is written to `reports/showcase.json`.

The synthetic DNA case contains 80 read pairs and one heterozygous truth variant at `molemo_demo_reference:1201 A>C`. A passing run must recover that exact allele as `0/1` while retaining BAM, BAI, VCF, coverage, tabular calls, hashes, and the run manifest.

Production human WGS/WES, metagenomics, proteomics, pathology slides, and FASTQ-to-expression quantification remain separate roadmap tracks. The demo caller is deliberately bounded to a small reference and does not perform clinical interpretation.
