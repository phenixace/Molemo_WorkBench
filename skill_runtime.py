"""Auto-discovered scientific skill registry for Molemo_Bench."""

from __future__ import annotations

import importlib.util
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = ROOT / "skills"


class SkillError(RuntimeError):
    """Raised when a skill cannot be discovered or executed."""


@dataclass(frozen=True)
class ToolDefinition:
    skill_id: str
    skill_title: str
    skill_kind: str
    name: str
    description: str
    input_schema: dict[str, Any]
    agent_callable: bool
    handler: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class SkillRegistry:
    def __init__(self, skills_root: Path = SKILLS_ROOT) -> None:
        self.skills_root = Path(skills_root)
        self.skills: list[dict[str, Any]] = []
        self.tools: dict[str, ToolDefinition] = {}
        self.reload()

    def reload(self) -> None:
        self.skills = []
        self.tools = {}
        if not self.skills_root.exists():
            return
        for manifest_path in sorted(self.skills_root.glob("*/skill.json")):
            self._load_manifest(manifest_path)

    def _load_manifest(self, manifest_path: Path) -> None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill_id = str(manifest.get("id") or manifest_path.parent.name)
        title = str(manifest.get("title") or skill_id.replace("-", " ").title())
        kind = str(manifest.get("kind") or "pipeline")
        description = str(manifest.get("description") or "")
        tool_summaries = []
        for raw_tool in manifest.get("tools", []):
            name = str(raw_tool["name"])
            if name in self.tools:
                raise SkillError(f"Duplicate tool name: {name}")
            handler = self._load_handler(manifest_path.parent, str(raw_tool["handler"]), name)
            definition = ToolDefinition(
                skill_id=skill_id,
                skill_title=title,
                skill_kind=kind,
                name=name,
                description=str(raw_tool.get("description") or description),
                input_schema=dict(raw_tool.get("input_schema") or {"type": "object", "properties": {}}),
                agent_callable=bool(raw_tool.get("agent_callable", True)),
                handler=handler,
            )
            self.tools[name] = definition
            tool_summaries.append(
                {
                    "name": name,
                    "description": definition.description,
                    "agent_callable": definition.agent_callable,
                }
            )
        self.skills.append(
            {
                "id": skill_id,
                "title": title,
                "kind": kind,
                "description": description,
                "tools": tool_summaries,
            }
        )

    def _load_handler(self, skill_dir: Path, handler_ref: str, tool_name: str) -> Callable:
        try:
            relative_path, function_name = handler_ref.split(":", 1)
        except ValueError as exc:
            raise SkillError(f"Invalid handler for {tool_name}: {handler_ref}") from exc
        module_path = (skill_dir / relative_path).resolve()
        if skill_dir.resolve() not in module_path.parents or not module_path.is_file():
            raise SkillError(f"Handler file not found for {tool_name}: {relative_path}")
        module_name = f"molemo_skill_{skill_dir.name.replace('-', '_')}_{function_name}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise SkillError(f"Could not load handler module for {tool_name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = getattr(module, function_name, None)
        if not callable(handler):
            raise SkillError(f"Handler function not found for {tool_name}: {function_name}")
        return handler

    def catalog(self) -> list[dict[str, Any]]:
        return self.skills

    def openai_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": definition.name,
                    "description": definition.description,
                    "parameters": definition.input_schema,
                },
            }
            for definition in self.tools.values()
            if definition.agent_callable
        ]

    def execute_agent(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        definition = self.tools.get(name)
        if definition is None:
            raise SkillError(f"Unknown skill tool: {name}")
        if not definition.agent_callable:
            raise SkillError(f"{name} requires a researcher-approved workflow.")
        return self.execute(name, arguments)

    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        definition = self.tools.get(name)
        if definition is None:
            raise SkillError(f"Unknown skill tool: {name}")
        started = time.perf_counter()
        context = {"root": ROOT, "skills_root": self.skills_root}
        try:
            result = definition.handler(dict(arguments or {}), context)
        except SkillError:
            raise
        except Exception as exc:
            raise SkillError(f"{name} failed: {exc}") from exc
        if not isinstance(result, dict):
            raise SkillError(f"{name} must return a JSON object")
        result.setdefault("ok", True)
        result.setdefault("tool", name)
        result.setdefault("skill", definition.skill_id)
        result.setdefault("duration_ms", round((time.perf_counter() - started) * 1000, 2))
        return result


def compact_tool_result(result: dict[str, Any], limit: int = 12000) -> str:
    encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
    if len(encoded) <= limit:
        return encoded
    compact = {
        "ok": result.get("ok", True),
        "tool": result.get("tool"),
        "skill": result.get("skill"),
        "summary": result.get("summary", "Tool output was truncated before sending to the model."),
        "truncated": True,
    }
    return json.dumps(compact, ensure_ascii=False, separators=(",", ":"))
