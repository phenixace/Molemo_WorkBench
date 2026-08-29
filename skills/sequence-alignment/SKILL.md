---
name: sequence-alignment
description: Create a local global pairwise protein alignment and inspect residue-level differences. Use for two concrete protein sequences; do not use alignment identity alone to claim shared function or homology.
---

# Sequence Alignment

Use `sequence_align` for two protein sequences. The tool returns a deterministic Needleman-Wunsch alignment, identity, score, and a viewer artifact.

Treat identity as descriptive evidence. Functional or evolutionary claims require appropriate database searches, domain context, and statistical alignment tools such as BLAST or HMMER.
