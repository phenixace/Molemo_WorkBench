---
name: sequence-search
description: Search one concrete protein or nucleotide sequence against a FASTA database inside the local Molemo workspace with NCBI BLAST+. Use for ranked similarity or homolog candidates after the researcher has reviewed and approved a workflow plan.
---

# Local Sequence Search

Use `sequence_search_local` only through a researcher-approved guided workflow. The tool builds a temporary local BLAST database, runs bounded BLASTP or BLASTN, and returns ranked hits with E-value, bit score, identity, query coverage, and the top alignment for inspection.

Use `blastp-short` automatically for protein queries shorter than 30 residues and `blastn-short` for nucleotide queries shorter than 50 bases. Keep the database inside the constrained workspace.

Treat similarity as evidence, not a functional annotation. Interpret hits with domain architecture, taxonomy, experiment, and database provenance when those claims matter.
