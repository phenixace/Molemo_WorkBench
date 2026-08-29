---
name: geo-series-matrix-import
description: Inspect and import one official NCBI GEO Series Matrix through a researcher-approved, bounded local workflow while preserving sample metadata, values and provenance without treating processed measurements as raw counts.
---

# GEO Series Matrix Import

Use this skill after a researcher selects an exact GSE accession and wants to bring its submitter-processed matrix into the local workspace.

## Boundary

- Resolve only the official HTTPS mirror of the accession's GEO `matrix/` directory.
- If multiple platform-specific matrices exist, require one exact filename before approval.
- Keep the Agent-callable step to directory and source-size preflight. Download only after local researcher approval.
- Enforce compressed, uncompressed, sample, feature and matrix-cell limits while parsing gzip content line by line.
- Preserve the original compressed file, source URL, retrieval time, SHA-256, expression table, sample metadata and manifest.
- Treat Series Matrix values as submitter-processed measurements with unknown transformation until the record and publication are reviewed.
- Do not send the imported matrix directly to a raw-count PyDESeq2 workflow, infer experimental groups, map probes, remove batches or fit a statistical model.
