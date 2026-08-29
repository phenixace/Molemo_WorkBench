---
name: protein-analysis
description: Analyze protein FASTA sequences with local sequence-derived calculations. Use for composition, molecular weight, charge, pI, hydropathy, and initial developability flags; do not present sequence heuristics as a solved 3D structure.
---

# Protein Analysis

Use `protein_analyze_sequence` for plain amino-acid or FASTA input. State that pI, charge, hydropathy, helix propensity, and aggregation flags are sequence-derived calculations.

Do not infer a binding interface or stable fold from sequence alone. For mutation proposals, preserve the user's functional constraints and pair each hypothesis with expression, stability, aggregation, and binding validation as appropriate.
