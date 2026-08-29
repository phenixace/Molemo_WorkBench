---
name: molecule-analysis
description: Parse and inspect small molecules from SMILES with the local RDKit pipeline. Use for molecular graphs, bond orders, rings, formulae, and core drug-like descriptors; do not use it as an experimental ADMET prediction.
---

# Molecule Analysis

Use `chem_analyze_molecule` for concrete SMILES work. Report calculated descriptors as RDKit outputs and keep medicinal-chemistry interpretations separate from computed facts.

When suggesting analogues, preserve the stated scaffold and constraints, label every design as a hypothesis, and name the assay or calculation needed to validate it. The returned molecule artifact can be opened in the Molemo structure viewer.
