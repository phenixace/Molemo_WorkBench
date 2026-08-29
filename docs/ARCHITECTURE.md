# Architecture

## Main line

```text
research question
  -> local Agent
  -> direct registered skill
     or guided plan -> researcher approval -> ordered registered skills
  -> local data or computation
  -> typed artifact and tool trace
  -> inspectable conclusion and next analysis
```

## Components

`server.py` is the local boundary. It serves the workbench and exposes molecule, protein, chat, skills, tool-call, workspace, workflow-plan and run-approval endpoints.

`agent_runtime.py` implements the OpenAI-compatible Chat Completions tool loop. Provider credentials are accepted only in the request body, forwarded once, and omitted from results and logs. Native mode lets the provider choose tools; grounded mode precomputes active scientific context for providers without tool support.

`skill_runtime.py` discovers every `skills/*/skill.json`, loads its declared handler, exports compatible function schemas and normalizes execution metadata. A tool can declare `agent_callable: false`; it remains available to approved workflows but is absent from third-party model schemas and rejected by direct tool calls. Oversized literature and clinical-trial previews are compacted for model context by removing duplicate artifacts while retaining citable paper or NCT identifiers, source URLs and the bounded evidence fields needed for synthesis. `SKILL.md` keeps each workflow usable as a standalone Codex/ChatGPT skill.

`workflow_runtime.py` turns fourteen supported research workflows into concrete, persisted plans. A new run starts as `pending_approval` with an empty trace. RNA-seq, VCF cohort, target-evidence, literature, clinical-trial landscape, exact clinical-trial results and variant-evidence plans additionally run bounded preflight before they can be created. Approval is available only through the local run API, which moves the run through `running`, `completed` or `failed` while recording each tool result. The Agent-facing guided-workflows skill can list, create and inspect plans but exposes no approval tool.

`workspace_utils.py` confines file access to `workspace/`, limits text size and accepts only supported scientific text formats. Agent tools can list and read files. Writes occur only through an explicit UI upload or an approved bounded pipeline output.

`bio_clients.py` is the outbound data boundary. It accepts only HTTPS requests to fixed Europe PMC, ClinicalTrials.gov, ClinVar/NLM, Ensembl, gnomAD, PubChem, UniProt, RCSB and Open Targets hosts, and applies request/response limits.

`literature_review.py` builds an explicit Europe PMC query from the user's terms and approved filters, performs a bounded `core` metadata search, preserves source relevance order, and normalizes identifiers, publication types, access state and abstracts. Preview is capped at ten records for Agent synthesis. Approved collection atomically publishes `papers.tsv`, a full JSON report, manifest and Markdown summary under `workspace/analyses/`. It records citation counts only as bibliographic context and performs no quality grading from them.

`target_evidence.py` resolves disease and target entities through the Open Targets GraphQL API, keeps candidate sets bounded, and normalizes association scores, evidence types, tractability, pathways, safety liabilities, clinical precedence and publication IDs. The preflight is read-only. Approved execution atomically publishes a TSV comparison, full JSON report, manifest and Markdown summary under `workspace/analyses/`; it never converts the association score into a probability or custom confidence value.

`variant_evidence.py` resolves a versioned RefSeq HGVS, rsID or ClinVar identifier to one simple allele. Ambiguous rsIDs, haplotypes and complex records stop during preflight. Approved execution retrieves ClinVar aggregate assertions, Ensembl VEP transcript consequences and gnomAD v4 population observations, keeps those evidence lanes separate, and atomically publishes a TSV evidence table, JSON report, manifest and Markdown summary under `workspace/analyses/`. It performs no de novo ACMG/AMP classification.

`vcf_cohort.py` validates a bounded uncompressed VCF 4.x file and optional exact-match sample metadata from the workspace. It preserves REF/ALT order, handles multiallelic `GT`, `AD`, `DP` and allele-specific `AF`, reproduces `CSQ/ANN` annotations, and separates observed calls from calls excluded by FILTER, depth or VAF. Approved execution atomically publishes variant, call, sample-QC and trajectory TSVs plus JSON, manifest, Markdown and input SHA-256 hashes under `workspace/analyses/`. It does not perform raw-read calling, somatic/germline classification, driver inference, treatment-response assessment or clinical interpretation.

`clinical_trials.py` builds a bounded ClinicalTrials.gov API v2 query from an approved condition, optional intervention, status scope and study scope. Preview is capped at ten source-ordered records. Approved collection normalizes NCT IDs, status, phase, sponsor, design, registered endpoints, eligibility, dates, countries, posted-results availability and linked publications, then atomically publishes `trials.tsv`, a JSON report, manifest and Markdown summary under `workspace/analyses/`. It does not treat registry metadata as efficacy or safety evidence.

`clinical_trial_results.py` retrieves one exact NCT record only after posted tabular results are confirmed. It keeps participant-flow, baseline and outcome group mappings separate, preserves submitted units, denominators, p-values and confidence intervals, and captures adverse-event totals, protocol/SAP documents and linked publications in source order. Approved execution atomically publishes five TSV tables, a JSON report, manifest and Markdown summary under `workspace/analyses/`. It does not reanalyze participant-level data or calculate a custom effect, safety, certainty or quality score.

`structure_io.py` parses the first PDB/mmCIF model, derives chain sequences and ligands, and produces a bounded atom-level viewer representation. `ngs_qc.py` streams workspace FASTQ files and calculates Phred+33, Q20/Q30, GC, N, read-length and per-cycle statistics.

`transcriptomics.py` is the bulk RNA-seq boundary. It accepts workspace CSV/TSV raw integer counts and sample metadata, enforces exact sample matching, replication, estimable contrast and bounded dimensions, then invokes `tools/run_pydeseq2.py` without a shell only after workflow approval. The runner fixes CPU use, writes into a temporary directory, and atomically publishes differential-expression tables, normalized counts, package versions, manifest and summary under `workspace/analyses/`.

`sequence_search.py` is the local NCBI BLAST+ boundary. It accepts only workspace FASTA databases, validates sequence alphabets and file size, caps query length, hits, threads and runtime, executes without a shell in a disposable hidden directory, disables BLAST usage reporting, parses JSON output and removes temporary database files after each run.

The frontend renders typed artifacts rather than arbitrary model HTML. Its primary layout keeps the research conversation beside the active evidence viewer. Data and design tabs retain the structure viewer; run, result and skill tabs switch to an unframed, full-height document surface for dense inspection. This keeps visual output reviewable and prevents provider responses from injecting executable UI.

## Extending the workbench

Add a skill directory containing:

```text
skills/new-skill/
├── SKILL.md
├── agents/openai.yaml
├── skill.json
└── scripts/handler.py
```

`skill.json` declares tool names, descriptions, JSON schemas and handler references. A handler receives JSON arguments and returns a JSON object. Return `artifacts` when the frontend should visualize a result.

New multi-step or mutating pipelines must use the workflow approval boundary, a bounded working directory, explicit resource limits and a resumable run identifier before they are exposed to an LLM.
