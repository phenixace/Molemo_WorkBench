"""Agent-facing workflow proposal tools without execution authority."""

from __future__ import annotations

from typing import Any

from workflow_runtime import WORKFLOW_MANAGER


def list_templates(_arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    templates = WORKFLOW_MANAGER.catalog()
    return {
        "summary": f"Found {len(templates)} researcher-approved workflow templates.",
        "data": {"templates": templates},
    }


def create_plan(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    inputs = arguments.get("inputs")
    if inputs is not None and not isinstance(inputs, dict):
        raise ValueError("workflow inputs must be an object")
    run = WORKFLOW_MANAGER.create_plan(
        str(arguments.get("template_id") or ""),
        inputs or {},
        str(arguments.get("objective") or ""),
    )
    return {
        "summary": f"Created {run['title']} plan with {len(run['steps'])} steps; researcher approval is required.",
        "data": run,
        "artifacts": run["artifacts"],
    }


def get_run(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    run = WORKFLOW_MANAGER.get_run(str(arguments.get("run_id") or ""))
    return {
        "summary": f"Workflow {run['title']} is {run['status']}.",
        "data": run,
        "artifacts": run.get("artifacts") or [],
    }
