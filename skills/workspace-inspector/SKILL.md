---
name: workspace-inspector
description: List and read supported scientific text files from Molemo's constrained local workspace. Use when a chat task refers to uploaded FASTA, SMILES, PDB, tabular, JSON, or Markdown files; never read paths outside the workspace.
---

# Workspace Inspector

Use `workspace_list_files` to discover available local inputs and `workspace_read_text` for the specific file needed by the current question.

Read the minimum required content. Respect truncation markers, do not infer missing rows, and never attempt path traversal. This skill is read-only; files enter the workspace only through an explicit user upload action.
