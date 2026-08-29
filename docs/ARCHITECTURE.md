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

`skill_runtime.py` discovers every `skills/*/skill.json`, loads its declared handler, exports compatible function schemas and normalizes execution metadata. A tool can declare `agent_callable: false`; it remains available to approved workflows but is absent from third-party model schemas and rejected by direct tool calls. `SKILL.md` keeps each workflow usable as a standalone Codex/ChatGPT skill.

`workflow_runtime.py` turns eight supported research workflows into concrete, persisted plans. A new run starts as `pending_approval` with an empty trace. RNA-seq plans additionally run bounded input and design preflight before they can be created. Approval is available only through the local run API, which moves the run through `running`, `completed` or `failed` while recording each tool result. The Agent-facing guided-workflows skill can list, create and inspect plans but exposes no approval tool.

`workspace_utils.py` confines file access to `workspace/`, limits text size and accepts only supported scientific text formats. Agent tools can list and read files. Writes occur only through an explicit UI upload or an approved bounded pipeline output.

`bio_clients.py` is the outbound data boundary. It accepts only HTTPS requests to fixed PubChem, UniProt, RCSB Data API and RCSB coordinate hosts, applies response limits and normalizes source URLs.

`structure_io.py` parses the first PDB/mmCIF model, derives chain sequences and ligands, and produces a bounded atom-level viewer representation. `ngs_qc.py` streams workspace FASTQ files and calculates Phred+33, Q20/Q30, GC, N, read-length and per-cycle statistics.

`transcriptomics.py` is the bulk RNA-seq boundary. It accepts workspace CSV/TSV raw integer counts and sample metadata, enforces exact sample matching, replication, estimable contrast and bounded dimensions, then invokes `tools/run_pydeseq2.py` without a shell only after workflow approval. The runner fixes CPU use, writes into a temporary directory, and atomically publishes differential-expression tables, normalized counts, package versions, manifest and summary under `workspace/analyses/`.

`sequence_search.py` is the local NCBI BLAST+ boundary. It accepts only workspace FASTA databases, validates sequence alphabets and file size, caps query length, hits, threads and runtime, executes without a shell in a disposable hidden directory, disables BLAST usage reporting, parses JSON output and removes temporary database files after each run.

The frontend renders typed artifacts rather than arbitrary model HTML. Its primary layout keeps the research conversation beside the active evidence viewer, with execution traces and artifacts in a compact inspector. This keeps visual output reviewable and prevents provider responses from injecting executable UI.

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
