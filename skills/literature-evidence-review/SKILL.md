---
name: literature-evidence-review
description: Search Europe PMC with explicit filters and source provenance, then synthesize a concise biomedical evidence answer from publication metadata and bounded abstracts. Use preview for focused questions and the researcher-approved collection workflow for a durable evidence map.
---

# Literature Evidence Review

Translate non-English concepts into a precise English biomedical query while preserving gene symbols, drug names, disease terms, and requested date limits. Prefer a focused Boolean query over a broad natural-language sentence.

Use `literature_search_preview` for a focused answer that needs no more than ten publications. Cite every material literature claim with PMID, PMCID, DOI, or the returned Europe PMC URL. Attribute claims to the paper or abstract, distinguish reviews from primary studies and preprints, and report conflicts or missing evidence.

Use `literature_review_collect` only through a researcher-approved workflow when the user needs a durable evidence map. Preserve the exact query, source order, filters, identifiers, metadata, abstracts, manifest, and output paths.

Europe PMC relevance and citation counts are not evidence-quality grades. This skill does not perform full-text risk-of-bias assessment, systematic-review screening, or meta-analysis. Never invent a study, identifier, result, or conclusion that is absent from the returned records.
