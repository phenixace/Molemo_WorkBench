# Capability matrix

Molemo WorkBench 的目标不是复制某个专用模型，而是实现同一类可审计研究闭环：从问题出发，连接本地数据和科学工具，在同一工作区检查结果，并保留下一步决策所需的上下文。

| Research workflow | Molemo WorkBench v0.21 | Current boundary |
| --- | --- | --- |
| Chat-centered workspace | Implemented | Chinese and English chat with local traces |
| Bring-your-own model API | Implemented | OpenAI-compatible Chat Completions; native tools or grounded mode |
| Local skill orchestration | Implemented | Auto-discovered, schema-constrained Python handlers |
| Guided plans and researcher approval | Implemented | Twenty-one concrete templates; Agent may propose and inspect, while only the local UI can approve execution |
| Small-molecule structure | Implemented | RDKit SMILES graph, rings, bond order and core descriptors |
| Protein sequence analysis | Implemented | FASTA cleaning and sequence-derived properties |
| Sequence alignment viewer | Implemented | Deterministic pairwise global alignment plus bounded MAFFT protein MSA, conservation track and exact reference-site window |
| Scientific artifacts | Implemented | GEO dataset landscape, experimental variant-site contact document/viewer, ChEMBL target-bioactivity document, human gene-set pathway/network document, literature evidence map, clinical-trial landscape and posted-results document, multi-sample VCF landscape/trajectory, HMMER domain architecture, single-cell UMAP/QC/marker document, target-evidence matrix, variant evidence document, molecule, protein sequence/structure, pairwise alignment, BLAST hits, database record, FASTQ QC, PCA, volcano, heatmap, ranked genes, bar chart and hydropathy track |
| Local file workspace | Implemented | Explicit uploads up to 20 MB; read-only access for Agent; path constrained |
| Reviewable execution record | Implemented | Plan inputs, per-step state, tool arguments, timing, summary, chat and artifacts |
| Process benchmark | Implemented | Deterministic v0.21 suite including real local BLAST+, HMMER, MAFFT, PyDESeq2 and Scanpy/Scrublet/Leiden tasks, routing, approval boundary, provenance and artifacts |
| Atom-level protein structures | Implemented | RCSB experimental structures, AlphaFold DB predictions with per-residue pLDDT and interactive directional PAE matrices, and local PDB/mmCIF first-model parsing; atoms are sampled above 12,000 and PAE is mean-downsampled above 384 bins; no automatic domain inference |
| Public biological databases | Implemented | Source-linked NCBI GEO, ChEMBL, Europe PMC, ClinicalTrials.gov, ClinVar, Ensembl VEP, gnomAD, PubChem, UniProtKB, RCSB, AlphaFold DB, Open Targets, Reactome and STRING retrieval through fixed official hosts |
| Public omics dataset discovery | Implemented | Bounded NCBI GEO Series search by topic, organism, assay scope and minimum sample count; exact query, source ordering, accessions, summaries, sample examples, publications, downloads and provenance are retained; no matrix download, batch assessment, dataset scoring or downstream analysis |
| Human gene-set functional analysis | Implemented | Two to fifty unique identifiers; human STRING mapping, Reactome overrepresentation, STRING enrichment, functional network and PPI enrichment with approval and provenance; no arbitrary species, custom background, causal inference or direct-physical-interaction claim |
| Target evidence review | Implemented | Disease and up to eight targets; Open Targets association/data-type scores, tractability, pathways, safety, clinical drugs, publications and saved provenance; no custom confidence score or internal evidence ingestion |
| Target-ligand bioactivity review | Implemented | Exact UniProt to one ChEMBL single-protein target; bounded confidence-9 direct binding/functional rows with pChEMBL, endpoint, assay, document, canonical SMILES and persisted provenance; no cross-endpoint potency synthesis, selectivity, mechanism, ADME, safety or efficacy claim |
| Protein variant structural context | Implemented | Exact experimental PDB author chain/residue and one-letter substitution; first-model heavy-atom protein/hetero-group proximity with saved provenance and site/global viewer; no numbering guess, covalent assignment, energy calculation, functional-effect or pathogenicity inference |
| Protein family site conservation | Implemented | Three to 100 proteins, exact FASTA reference ID and position/substitution; MAFFT 7.526, unweighted column statistics, persisted alignment/provenance and compact site viewer; no orthology check, phylogenetic weighting, functional-effect or pathogenicity inference |
| Literature evidence review | Implemented | Europe PMC preview and approved evidence map with exact query, filters, source ordering, IDs, publication types and bounded abstracts; no full-text screening, risk-of-bias grading or meta-analysis |
| Human variant evidence review | Implemented | One exact simple allele; ClinVar assertions, VEP transcript consequences and gnomAD v4 frequencies with provenance; no haplotype/SV support, segregation analysis, diagnosis or de novo ACMG/AMP classification |
| Multi-sample VCF cohort review | Implemented | Bounded uncompressed VCF 4.x plus optional longitudinal metadata; ALT-aware AD/AF, explicit depth/VAF/FILTER rules, sample QC, mutation matrix, low-frequency calls, trajectories and input hashes; no raw calling, VCF.gz/BCF, CNV/SV, somatic/germline classification or clinical actionability |
| Clinical trial landscape | Implemented | Condition plus optional intervention, status and study-scope filters; source-ordered ClinicalTrials.gov registry metadata, NCT links, endpoints, results availability, publications and saved provenance; no efficacy/safety inference, result-table synthesis, regulatory review or meta-analysis |
| Exact clinical trial results | Implemented | One exact NCT ID; posted participant flow, baseline, outcomes, submitted statistics, adverse events, protocol/SAP and linked publications with persisted tables; no IPD reanalysis, custom effect/safety score, risk-of-bias grading, cross-trial synthesis or regulatory conclusion |
| BLAST/HMMER workflows | Implemented | Bounded BLASTP/BLASTN against workspace FASTA and HMMER3 `hmmsearch` from local amino-acid profile HMMs to protein FASTA are approval-gated with inspectable alignments/domain coordinates and saved provenance; no `hmmscan`, profile construction, Pfam download or remote/large database orchestration |
| Single-cell RNA-seq exploration | Implemented | Bounded raw-count CSV/TSV, AnnData `.h5ad` layer, 10x H5 and compressed/uncompressed MTX plus exact optional cell metadata; QC, optional whole-dataset or batch-aware Scrublet with explicit exclusion approval, CP10k/log1p, HVG, PCA, neighbors, UMAP, Leiden, cluster markers, `.h5ad` and provenance; no ambient-RNA correction, integration, automatic cell typing, trajectory or donor-aware pseudobulk |
| NGS analysis workbench | Partial | FASTQ QC, processed multi-sample VCF review, raw-count bulk RNA-seq DE and processed single-cell exploration implemented with preflight, approval, visualization and saved outputs; no FASTQ-to-count or raw-read variant calling |
| Pathology slide viewer | Planned | No WSI/DICOM viewer |
| Experimental validation and procurement | Planned | Can discuss validation, but does not call vendors or lab systems |

The table describes observable product behavior. A visible control or placeholder is not counted as implemented.
