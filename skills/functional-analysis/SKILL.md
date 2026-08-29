---
name: functional-analysis
description: Review a bounded human gene set with Reactome pathway overrepresentation and STRING identifier mapping, enrichment, functional association networks, and PPI enrichment. Use preflight to confirm mappings and parameters; persist the full analysis only after researcher approval.
---

# Gene-set Functional Analysis

Use `functional_analysis_preflight` for two to fifty human gene or protein identifiers. Confirm every STRING mapping, unmapped identifier, the STRING confidence threshold, FDR threshold, reported-term limit, and whether disease pathways are included.

Use `functional_analysis_run` only through a researcher-approved workflow. Keep Reactome and STRING results separate in the evidence record; do not merge their statistics into an invented score. Preserve official source links, STRING version, retrieval time, parameters, input identifiers, mappings, output tables, and the run manifest.

Reactome overrepresentation depends on list construction and reference coverage. FDR is a multiple-testing correction, not the probability that a pathway is true. STRING edges are functional associations and do not necessarily represent direct physical interactions. Database enrichment is a hypothesis-generating result, not causal or replicate-level evidence.
