# Capability matrix

Molemo WorkBench 的目标不是复制某个专用模型，而是实现同一类可审计研究闭环：从问题出发，连接本地数据和科学工具，在同一工作区检查结果，并保留下一步决策所需的上下文。

| Research workflow | Molemo WorkBench v0 | Current boundary |
| --- | --- | --- |
| Chat-centered workspace | Implemented | Chinese and English chat with local traces |
| Bring-your-own model API | Implemented | OpenAI-compatible Chat Completions; native tools or grounded mode |
| Local skill orchestration | Implemented | Auto-discovered, schema-constrained Python handlers |
| Small-molecule structure | Implemented | RDKit SMILES graph, rings, bond order and core descriptors |
| Protein sequence analysis | Implemented | FASTA cleaning and sequence-derived properties |
| Sequence alignment viewer | Implemented | Deterministic pairwise global alignment |
| Scientific artifacts | Implemented | Molecule, protein sequence, alignment, bar chart and hydropathy track |
| Local file workspace | Implemented | Explicit text upload; read-only access for Agent; path constrained |
| Reviewable execution record | Implemented | Tool arguments, status, timing, summary, chat and artifacts |
| Process benchmark | Implemented | Deterministic v0 suite for tool correctness and artifacts |
| Atom-level protein structures | Partial | Current protein canvas is sequence-derived; PDB/mmCIF viewer is next |
| Public biological databases | Planned | Registry supports new skills; RCSB, UniProt and PubChem are not bundled yet |
| BLAST/HMMER workflows | Planned | Pairwise local alignment only |
| NGS analysis workbench | Planned | No FASTQ QC, sample sheet, bulk RNA-seq or single-cell pipeline yet |
| Pathology slide viewer | Planned | No WSI/DICOM viewer |
| Experimental validation and procurement | Planned | Can discuss validation, but does not call vendors or lab systems |

The table describes observable product behavior. A visible control or placeholder is not counted as implemented.
