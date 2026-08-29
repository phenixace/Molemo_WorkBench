# Protein Variant Structure Context

Use this skill when a researcher supplies an experimental PDB entry, exact author chain, and a one-letter protein substitution such as `G12C`.

## Boundary

- Match author chain and author residue number exactly in the first deposited coordinate model.
- Accept the site only when the observed residue is the reference or alternate amino acid.
- Report minimum heavy-atom distances to nearby protein residues and coordinate hetero groups.
- Treat HETATM records as coordinate groups, not automatically as inhibitors or biologically relevant ligands.
- Do not infer covalency, binding energy, functional impact, pathogenicity, or clinical actionability from proximity.
- Keep collection and persisted outputs behind researcher approval; preflight may resolve and preview the public entry.
