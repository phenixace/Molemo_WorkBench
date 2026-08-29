---
name: protein-structure
description: Retrieve experimental structures from RCSB PDB, predicted structures from AlphaFold DB, or parse PDB/mmCIF files in the local workspace. Use when atom coordinates, chain composition, ligands, pLDDT, or structure-backed inspection are required; keep experimental evidence and prediction confidence distinct.
---

# Protein Structure

Use `structure_fetch_pdb` for a four-character PDB identifier, `structure_fetch_alphafold` for an exact UniProt accession, and `structure_parse_workspace` for a `.pdb`, `.cif`, or `.mmcif` file already imported into the constrained workspace.

AlphaFold coordinates are predictions. Interpret B-factor values as pLDDT only for models retrieved through `structure_fetch_alphafold`: scores above 90 are very high local confidence, 70–90 confident, 50–70 low, and below 50 very low. pLDDT does not establish relative domain placement; direct the researcher to PAE for that question.

The parser reads the first model, removes water, preserves protein and ligand atoms, derives chain sequences from C-alpha residues, and returns an atom-level viewer artifact. Large structures may be sampled for rendering while retaining the full parsed atom count.
