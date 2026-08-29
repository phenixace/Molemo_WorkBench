"""Constrained file access for the local Molemo workspace."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT / "workspace"
MAX_TEXT_BYTES = 512 * 1024
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
TEXT_SUFFIXES = {
    ".txt",
    ".md",
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".fa",
    ".fasta",
    ".faa",
    ".fna",
    ".afa",
    ".aln",
    ".hmm",
    ".smi",
    ".smiles",
    ".pdb",
    ".cif",
    ".mmcif",
    ".fastq",
    ".fq",
    ".vcf",
}


class WorkspaceError(ValueError):
    """Raised when a workspace operation is invalid or unsafe."""


def ensure_workspace() -> Path:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    return WORKSPACE_ROOT


def resolve_workspace_path(relative_path: str) -> Path:
    root = ensure_workspace().resolve()
    cleaned = str(relative_path or "").strip().lstrip("/")
    if not cleaned:
        raise WorkspaceError("A workspace-relative path is required.")
    target = (root / cleaned).resolve()
    if target != root and root not in target.parents:
        raise WorkspaceError("Path must stay inside the Molemo workspace.")
    return target


def list_workspace_files(pattern: str = "", limit: int = 100) -> list[dict[str, object]]:
    root = ensure_workspace().resolve()
    query = str(pattern or "").lower().strip()
    bounded_limit = max(1, min(int(limit or 100), 500))
    items: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part.startswith(".") for part in Path(relative).parts):
            continue
        if query and query not in relative.lower():
            continue
        items.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "type": path.suffix.lower().lstrip(".") or "file",
            }
        )
        if len(items) >= bounded_limit:
            break
    return items


def read_workspace_text(relative_path: str, max_bytes: int = 64 * 1024) -> dict[str, object]:
    target = resolve_workspace_path(relative_path)
    if not target.is_file():
        raise WorkspaceError(f"Workspace file not found: {relative_path}")
    if target.suffix.lower() not in TEXT_SUFFIXES:
        raise WorkspaceError(f"Unsupported text file type: {target.suffix or 'unknown'}")
    bounded_max = max(1, min(int(max_bytes or 65536), MAX_TEXT_BYTES))
    raw = target.read_bytes()
    truncated = len(raw) > bounded_max
    text = raw[:bounded_max].decode("utf-8", errors="replace")
    return {
        "path": target.relative_to(ensure_workspace().resolve()).as_posix(),
        "text": text,
        "size": len(raw),
        "truncated": truncated,
    }


def write_workspace_text(relative_path: str, content: str) -> dict[str, object]:
    encoded = str(content).encode("utf-8")
    if len(encoded) > MAX_UPLOAD_BYTES:
        raise WorkspaceError(f"Workspace uploads are limited to {MAX_UPLOAD_BYTES} bytes.")
    target = resolve_workspace_path(relative_path)
    if target.suffix.lower() not in TEXT_SUFFIXES:
        raise WorkspaceError(f"Unsupported text file type: {target.suffix or 'unknown'}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded)
    return {
        "path": target.relative_to(ensure_workspace().resolve()).as_posix(),
        "size": len(encoded),
    }
