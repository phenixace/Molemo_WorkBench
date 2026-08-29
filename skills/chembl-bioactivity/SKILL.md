---
name: chembl-bioactivity
description: Review source-linked ChEMBL small-molecule activity evidence for an exact UniProt single-protein target. Use for target-to-ligand bioactivity questions, medicinal-chemistry starting points, assay-context review, and bounded SAR evidence; do not turn pChEMBL into a lead-quality, selectivity, safety, or efficacy score.
---

# ChEMBL Bioactivity Evidence

Use `chembl_bioactivity_preflight` to resolve the target and inspect a bounded preview. Full collection uses `chembl_bioactivity_collect` only through a researcher-approved `target-ligand-bioactivity-review` workflow.

The review retains only ChEMBL assay-to-target confidence score 9 with direct relationship type `D`, standardized activity rows, non-duplicate records without data-validity comments, and a canonical small-molecule structure. Preserve pChEMBL, endpoint type, relation, value, unit, BAO format, assay description, document, and ChEMBL identifiers.

Confidence score 9 supports direct single-protein target assignment; it does not prove direct physical binding or assay quality. Binding-class assays can still be cell-based. Do not directly compare mixed IC50, Ki, Kd, EC50, assay formats, variants, constructs, or organisms without reviewing their context. A high pChEMBL row is not evidence of selectivity, developability, safety, mechanism, or clinical efficacy.
