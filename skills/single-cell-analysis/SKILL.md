---
name: single-cell-analysis
description: Validate local single-cell raw-count matrices and propose researcher-approved Scanpy QC, embedding, clustering, and marker exploration.
---

# Single-cell Analysis

Use `single_cell_preflight` before proposing analysis. Confirm that the matrix contains cell-by-gene non-negative integer raw counts, cell IDs match optional metadata exactly, QC thresholds retain a useful dataset, and the local Scanpy runtime is available.

Use `single_cell_run_analysis` only through a researcher-approved workflow. The bounded pipeline performs count QC, CP10k normalization, log1p transformation, highly variable gene selection, PCA, nearest-neighbor graph construction, UMAP, Leiden clustering, and descriptive Wilcoxon marker ranking with a fixed random seed and persisted provenance.

Never call a Leiden cluster a cell type without external annotation evidence. Treat UMAP geometry and cell-level marker p-values as exploratory. The workflow does not perform doublet detection, ambient-RNA correction, batch integration, trajectory inference, or donor-aware differential expression.
