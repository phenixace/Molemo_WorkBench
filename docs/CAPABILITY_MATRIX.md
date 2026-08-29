# Capability matrix

Molemo WorkBench 的目标不是复制某个专用模型，而是实现同一类可审计研究闭环：从问题出发，连接本地数据和科学工具，在同一工作区检查结果，并保留下一步决策所需的上下文。

| Research workflow | Molemo WorkBench v0.10 | Current boundary |
| --- | --- | --- |
| Chat-centered workspace | Implemented | Chinese and English chat with local traces |
| Bring-your-own model API | Implemented | OpenAI-compatible Chat Completions; native tools or grounded mode |
| Local skill orchestration | Implemented | Auto-discovered, schema-constrained Python handlers |
| Guided plans and researcher approval | Implemented | Thirteen concrete templates; Agent may propose and inspect, while only the local UI can approve execution |
| Small-molecule structure | Implemented | RDKit SMILES graph, rings, bond order and core descriptors |
| Protein sequence analysis | Implemented | FASTA cleaning and sequence-derived properties |
| Sequence alignment viewer | Implemented | Deterministic pairwise global alignment |
| Scientific artifacts | Implemented | Literature evidence map, clinical-trial landscape and posted-results document, target-evidence matrix, variant evidence document, molecule, protein sequence/structure, pairwise alignment, BLAST hits, database record, FASTQ QC, PCA, volcano, heatmap, ranked genes, bar chart and hydropathy track |
| Local file workspace | Implemented | Explicit uploads up to 20 MB; read-only access for Agent; path constrained |
| Reviewable execution record | Implemented | Plan inputs, per-step state, tool arguments, timing, summary, chat and artifacts |
| Process benchmark | Implemented | Deterministic v0.10 suite including real local BLAST+ and PyDESeq2 tasks, target/literature/clinical-trial/variant routing, approval boundary and artifacts |
| Atom-level protein structures | Implemented | RCSB PDB retrieval and local PDB/mmCIF first-model parsing; rendering is sampled above 12,000 atoms |
| Public biological databases | Implemented | Source-linked Europe PMC, ClinicalTrials.gov, ClinVar, Ensembl VEP, gnomAD, PubChem, UniProtKB, RCSB and Open Targets retrieval through fixed official hosts |
| Target evidence review | Implemented | Disease and up to eight targets; Open Targets association/data-type scores, tractability, pathways, safety, clinical drugs, publications and saved provenance; no custom confidence score or internal evidence ingestion |
| Literature evidence review | Implemented | Europe PMC preview and approved evidence map with exact query, filters, source ordering, IDs, publication types and bounded abstracts; no full-text screening, risk-of-bias grading or meta-analysis |
| Human variant evidence review | Implemented | One exact simple allele; ClinVar assertions, VEP transcript consequences and gnomAD v4 frequencies with provenance; no batch VCF, haplotype/SV support, segregation analysis, diagnosis or de novo ACMG/AMP classification |
| Clinical trial landscape | Implemented | Condition plus optional intervention, status and study-scope filters; source-ordered ClinicalTrials.gov registry metadata, NCT links, endpoints, results availability, publications and saved provenance; no efficacy/safety inference, result-table synthesis, regulatory review or meta-analysis |
| Exact clinical trial results | Implemented | One exact NCT ID; posted participant flow, baseline, outcomes, submitted statistics, adverse events, protocol/SAP and linked publications with persisted tables; no IPD reanalysis, custom effect/safety score, risk-of-bias grading, cross-trial synthesis or regulatory conclusion |
| BLAST/HMMER workflows | Partial | Bounded BLASTP/BLASTN against workspace FASTA is implemented behind approval; no HMMER or remote/large database orchestration |
| NGS analysis workbench | Partial | FASTQ QC and raw-count bulk RNA-seq DE implemented with sample/design preflight, PyDESeq2, PCA, volcano, heatmap and saved outputs; no FASTQ-to-count or single-cell pipeline |
| Pathology slide viewer | Planned | No WSI/DICOM viewer |
| Experimental validation and procurement | Planned | Can discuss validation, but does not call vendors or lab systems |

The table describes observable product behavior. A visible control or placeholder is not counted as implemented.
