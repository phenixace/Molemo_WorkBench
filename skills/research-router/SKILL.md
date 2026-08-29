---
name: research-router
description: Route broad life-science research questions to the smallest useful set of Molemo skills. Use when a request spans multiple evidence or analysis lanes, or the correct scientific workflow is unclear.
---

# Research Router

Keep the biological question as the main line. Normalize the active entity, select one to three relevant lanes, and use the minimum useful tools before synthesizing a conclusion.

Prefer a direct molecule, protein, variant preflight, clinical-trial preview, literature preview, GEO dataset preview, alignment, local HMM profile-search preflight, single-cell count-matrix preflight, gene-set functional-analysis preflight, visualization, or workspace skill when it already matches the request. Route public expression and methylation dataset questions to bounded GEO Series discovery, preserving exact filters and study-design uncertainty. Route protein-family or domain questions with a supplied `.hmm` profile and protein FASTA to the approved HMMER workflow. Route single-cell raw-count matrices to the approved Scanpy workflow, keeping clusters, cell-type annotations, and sample-level inference distinct. Route bounded human gene sets to Reactome and STRING only after identifier mapping is reviewed. Use an approved workflow when execution expands scope or persists an analysis. Distinguish computed evidence, submitted database assertions, population observations, registry metadata, external literature, and design hypotheses in the final answer.

Use `research_route` when the request is broad or ambiguous. Return a conclusion organized around the user's question, then the supporting tool results, caveats, and the next useful analysis.
