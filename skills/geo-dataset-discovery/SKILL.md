---
name: geo-dataset-discovery
description: Discover public NCBI GEO Series from a biological question with exact GSE-only query provenance, bounded metadata, study-design caveats, and an approved persistence workflow.
---

# GEO Dataset Discovery

Use this skill when a researcher wants to find public expression or methylation studies before selecting data for a local analysis.

## Boundary

- Search the NCBI GEO DataSets database through E-utilities and require exact `GSE[ETYP]` Series filtering.
- Preserve the free-text query, organism, assay scope, minimum GEO sample count, source relevance order, query translation, accessions, retrieval time, and public links.
- Keep the agent-callable preview to eight records. Persist up to twenty records only through a researcher-approved workflow.
- Treat sample count as submitter metadata, not the number of independent biological replicates.
- Do not score dataset quality, infer analysis readiness from a file extension, or treat GEO relevance as scientific priority.
- Flag SuperSeries/SubSeries, overlapping cohorts, incomplete metadata, normalization state, subject design, batch structure, and raw-data availability for researcher review.
- Discovery does not download or analyze expression data.
