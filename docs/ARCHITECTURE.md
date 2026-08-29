# Architecture

## Main line

```text
research question
  -> local Agent
  -> registered scientific skill
  -> local data or computation
  -> typed artifact and tool trace
  -> inspectable conclusion and next analysis
```

## Components

`server.py` is the local boundary. It serves the workbench and exposes molecule, protein, chat, skills, tool-call and workspace endpoints.

`agent_runtime.py` implements the OpenAI-compatible Chat Completions tool loop. Provider credentials are accepted only in the request body, forwarded once, and omitted from results and logs. Native mode lets the provider choose tools; grounded mode precomputes active scientific context for providers without tool support.

`skill_runtime.py` discovers every `skills/*/skill.json`, loads its declared handler, exports compatible function schemas and normalizes execution metadata. `SKILL.md` keeps each workflow usable as a standalone Codex/ChatGPT skill.

`workspace_utils.py` confines file access to `workspace/`, limits text size and accepts only supported scientific text formats. Agent tools can list and read files; only an explicit UI upload can write them.

`bio_clients.py` is the outbound data boundary. It accepts only HTTPS requests to fixed PubChem, UniProt, RCSB Data API and RCSB coordinate hosts, applies response limits and normalizes source URLs.

`structure_io.py` parses the first PDB/mmCIF model, derives chain sequences and ligands, and produces a bounded atom-level viewer representation. `ngs_qc.py` streams workspace FASTQ files and calculates Phred+33, Q20/Q30, GC, N, read-length and per-cycle statistics.

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

Long-running or mutating pipelines should add an approval state, bounded working directory, explicit resource limits and resumable run identifier before they are exposed to an LLM.
