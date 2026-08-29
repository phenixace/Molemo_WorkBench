# Protein Alignment and Conservation

Use this skill when a researcher supplies a workspace protein FASTA, an exact reference identifier, and a reference position or substitution such as `G12C`.

## Boundary

- Validate 3–100 unique protein sequences and the exact reference residue before execution.
- Keep MAFFT execution behind researcher approval, single-threaded, time-bounded, and free of shell interpolation.
- Preserve the full alignment, per-column statistics, reference-site mapping, input hash, MAFFT version, command options, and interpretation caveats.
- Describe conservation only within the approved input set.
- Do not infer orthology, family completeness, phylogenetic independence, evolutionary constraint, function, pathogenicity, or mutational effect from consensus support alone.
