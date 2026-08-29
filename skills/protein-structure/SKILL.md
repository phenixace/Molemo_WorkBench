---
name: protein-structure
description: Retrieve experimental structures from RCSB PDB or parse PDB/mmCIF files in the local workspace. Use when atom coordinates, chain composition, ligands, or structure-backed inspection are required; do not infer experimental confidence beyond deposited metadata.
---

# Protein Structure

Use `structure_fetch_pdb` for a four-character PDB identifier. Use `structure_parse_workspace` for a `.pdb`, `.cif`, or `.mmcif` file already imported into the constrained workspace.

The parser reads the first model, removes water, preserves protein and ligand atoms, derives chain sequences from C-alpha residues, and returns an atom-level viewer artifact. Large structures may be sampled for rendering while retaining the full parsed atom count.
