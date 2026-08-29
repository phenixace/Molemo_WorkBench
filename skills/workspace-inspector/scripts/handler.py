"""Read-only access to the constrained Molemo workspace."""

from __future__ import annotations

from typing import Any

from molemo.workspace_utils import list_workspace_files, read_workspace_text


def list_files(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    files = list_workspace_files(str(arguments.get("pattern") or ""), int(arguments.get("limit") or 100))
    return {"summary": f"Found {len(files)} workspace files.", "files": files}


def read_text(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = read_workspace_text(str(arguments.get("path") or ""), int(arguments.get("max_bytes") or 65536))
    return {"summary": f"Read {result['path']} ({result['size']} bytes).", "file": result}
