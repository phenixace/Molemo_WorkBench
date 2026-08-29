---
name: hmmer-profile-search
description: Validate and run bounded local HMMER3 profile-to-protein searches with domain coordinates, explicit thresholds, researcher approval and auditable outputs. Use when the user supplies an amino-acid profile HMM and a workspace protein FASTA database; not for downloading Pfam, asserting function from a match, or unbounded remote searches.
---

# HMMER Profile Search

Use `hmmer_profile_preflight` before proposing execution. Confirm the exact HMM and protein FASTA paths, model identities, model and database sizes, sequence and domain E-value reporting thresholds, hit limit, HMMER version and runtime availability.

Use `hmmer_profile_search` only through a researcher-approved workflow. Preserve profile and target names, full-sequence E-value and score, domain conditional and independent E-values, HMM coordinates, target alignment and envelope coordinates, accuracy, bias, input hashes and output paths. `--domE` is a conditional E-value reporting threshold; never label it as the independent E-value threshold.

HMMER E-values depend on the search space and profile. A profile match supports sequence-family or domain relatedness; it does not by itself prove molecular function, mechanism, activity, localization or phenotype. Review domain coverage, repeat architecture, composition bias, profile construction and independent evidence.

The workflow accepts bounded local HMMER3 amino-acid profiles and protein FASTA files. It does not download or version Pfam, execute arbitrary commands, search remote databases, build profiles from alignments, or convert hits into functional annotations.
