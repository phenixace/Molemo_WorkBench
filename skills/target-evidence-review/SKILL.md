---
name: target-evidence-review
description: Resolve and compare candidate therapeutic targets for a disease using source-linked Open Targets association evidence, data-type scores, tractability, pathways, safety liabilities, clinical drugs, and publications. Use preflight for entity confirmation; persist the full review only after researcher approval.
---

# Target Evidence Review

Use `target_evidence_preflight` to confirm the exact disease ontology record and target Ensembl IDs. Keep candidate sets to eight or fewer so each target remains inspectable.

Use `target_evidence_compare` only through a researcher-approved workflow. Preserve the Open Targets association score as the ranking signal and show individual evidence types rather than inventing a composite score. Include source links, retrieval time, output paths, and the interpretation caveats in the result.

An association score is not a probability, confidence estimate, or proof of causality. Low scores can reflect sparse evidence, while clinical precedence and tractability do not establish efficacy or safety for a new program.
