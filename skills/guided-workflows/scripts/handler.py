"""Agent-facing workflow proposal tools without execution authority."""

from __future__ import annotations

from typing import Any

from workflow_runtime import WORKFLOW_MANAGER


def list_templates(_arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    templates = WORKFLOW_MANAGER.catalog()
    return {
        "summary": f"当前有 {len(templates)} 个需要研究者审批的工作流模板。",
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
        "summary": f"已创建“{run['title']}”计划，共 {len(run['steps'])} 步；需研究者审批后执行。",
        "data": run,
        "artifacts": run["artifacts"],
    }


def get_run(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    run = WORKFLOW_MANAGER.get_run(str(arguments.get("run_id") or ""))
    return {
        "summary": f"“{run['title']}”当前状态：{run['status']}。",
        "data": run,
        "artifacts": run.get("artifacts") or [],
    }
