# Roadmap

English | [简体中文](ROADMAP.zh-CN.md)

Molemo is being developed as two connected products: **Molemo WorkBench**, the auditable local Agent runtime, and **Molemo**, the editor experience that connects code, scientific files, conversation, approvals, and artifacts.

## Validated now

- WorkBench: 26 skills, 50 tools, and 23 approval-aware workflow templates.
- Molecule, protein, public-evidence, bulk RNA, single-cell, processed VCF, and bounded local sequence workflows.
- A deterministic paired-end DNA demonstration from FASTQ to BAM/BAI, coverage, and candidate VCF.
- A five-case showcase covering RDKit, protein sequence analysis, BWA/samtools/bcftools, PyDESeq2, and Scanpy.
- Molemo editor MVP: a bilingual VS Code/Cursor extension connected to the loopback WorkBench runtime.

## Next capability tracks

1. **Production WGS/WES:** versioned reference bundles, interval/shard planning, production QC and callers, annotation, cohort validation, retries, provenance, and scalable execution.
2. **FASTQ to expression:** read QC, trimming policy, alignment or pseudoalignment, gene/transcript quantification, MultiQC-style review, then the existing matrix workflows.
3. **Metagenomics:** taxonomic profiling, assembly/binning where appropriate, functional profiling, contamination controls, and database versioning.
4. **Proteomics:** raw MS ingestion, search configuration, peptide/protein FDR, label-free or labeled quantification, and inspectable spectra/evidence tables.
5. **Pathology:** tiled WSI/DICOM viewing, annotations, model overlays, provenance, and bounded local inference.
6. **Molemo desktop:** bundle the validated extension into a branded Code-OSS distribution with scientific editors, artifact tabs, environment management, and terminal-aware pipeline controls.

Each track moves to “implemented” only after a reproducible example, approval boundary, typed artifacts, persisted provenance, automated tests, and benchmark coverage are present.
