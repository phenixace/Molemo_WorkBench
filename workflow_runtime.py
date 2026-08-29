"""Researcher-approved workflow plans built from registered scientific tools."""

from __future__ import annotations

import copy
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
DEFAULT_STORAGE_ROOT = ROOT / "workspace" / ".molemo" / "runs"


class WorkflowError(RuntimeError):
    def __init__(self, message: str, code: str = "workflow_error", status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {"error": self.message, "code": self.code}


def _field(name: str, label: str, field_type: str = "text", **extra: Any) -> dict[str, Any]:
    return {"name": name, "label": label, "type": field_type, **extra}


TEMPLATES: dict[str, dict[str, Any]] = {
    "molecule-profile": {
        "title": "分子性质画像",
        "description": "解析 SMILES，计算分子描述符并生成性质图。",
        "fields": [
            _field("smiles", "SMILES", "textarea", required=True, rows=4),
        ],
        "assumptions": ["输入代表单一可由 RDKit 解析的分子。"],
    },
    "protein-sequence-review": {
        "title": "蛋白序列审阅",
        "description": "计算序列性质，并生成逐残基疏水性轨道。",
        "fields": [
            _field("sequence", "FASTA / amino-acid sequence", "textarea", required=True, rows=6),
        ],
        "assumptions": ["序列使用标准单字母氨基酸编码。"],
    },
    "protein-structure-review": {
        "title": "蛋白结构审阅",
        "description": "从 RCSB PDB 或本地 workspace 读取原子坐标。",
        "fields": [
            _field(
                "source",
                "坐标来源",
                "select",
                required=True,
                options=[
                    {"value": "rcsb", "label": "RCSB PDB"},
                    {"value": "workspace", "label": "本地 workspace"},
                ],
            ),
            _field("pdb_id", "PDB ID", "text", placeholder="1L2Y"),
            _field("path", "Workspace 文件", "text", placeholder="examples/mini-protein.pdb"),
        ],
        "assumptions": ["仅解析坐标文件的第一个模型。"],
    },
    "fastq-qc-review": {
        "title": "FASTQ 质量审阅",
        "description": "流式计算 reads、质量、GC、N 与逐循环指标。",
        "fields": [
            _field("path", "Workspace FASTQ", "text", required=True, placeholder="examples/tiny.fastq"),
            _field("max_reads", "最多分析 reads", "number", value=10000, min=1, max=100000),
        ],
        "assumptions": ["输入为 Phred+33 编码的 FASTQ 文件。"],
    },
    "pairwise-alignment-review": {
        "title": "双序列比对",
        "description": "执行全局蛋白序列比对并返回可检查的 alignment。",
        "fields": [
            _field("sequence_a", "Sequence A", "textarea", required=True, rows=4),
            _field("sequence_b", "Sequence B", "textarea", required=True, rows=4),
            _field("label_a", "Label A", "text", value="Sequence A"),
            _field("label_b", "Label B", "text", value="Sequence B"),
        ],
        "assumptions": ["当前使用确定性的 Needleman-Wunsch 全局比对。"],
    },
    "database-record-review": {
        "title": "公共数据库记录",
        "description": "检索 PubChem 化合物或 UniProtKB 蛋白记录。",
        "fields": [
            _field(
                "source",
                "数据库",
                "select",
                required=True,
                options=[
                    {"value": "pubchem", "label": "PubChem"},
                    {"value": "uniprot", "label": "UniProtKB"},
                ],
            ),
            _field("query", "名称 / accession", "text", required=True, placeholder="caffeine or P69905"),
        ],
        "assumptions": ["公共数据库访问固定官方域名，不使用模型 API key。"],
    },
}


def _require_text(inputs: dict[str, Any], key: str, label: str | None = None) -> str:
    value = str(inputs.get(key) or "").strip()
    if not value:
        raise WorkflowError(f"{label or key} is required.", "invalid_workflow_inputs")
    return value


def _molecule_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    smiles = _require_text(inputs, "smiles", "SMILES")
    inputs["smiles"] = smiles
    return [
        _step("解析分子并计算描述符", "chem_analyze_molecule", {"smiles": smiles}),
        _step(
            "生成分子性质图",
            "visualization_property_chart",
            {"title": "Molecular property profile", "properties": {}},
            derive="molecule-properties",
            source_step=0,
        ),
    ]


def _protein_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    sequence = _require_text(inputs, "sequence", "Protein sequence")
    inputs["sequence"] = sequence
    return [
        _step("计算蛋白序列性质", "protein_analyze_sequence", {"sequence": sequence}),
        _step(
            "生成逐残基疏水性轨道",
            "visualization_sequence_track",
            {"title": "Protein hydropathy track", "sequence": sequence},
        ),
    ]


def _structure_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    source = str(inputs.get("source") or "rcsb").strip().lower()
    if source == "rcsb":
        pdb_id = _require_text(inputs, "pdb_id", "PDB ID").upper()
        inputs.update({"source": source, "pdb_id": pdb_id})
        return [_step("获取并解析 RCSB 原子坐标", "structure_fetch_pdb", {"pdb_id": pdb_id})]
    if source == "workspace":
        path = _require_text(inputs, "path", "Workspace structure path")
        inputs.update({"source": source, "path": path})
        return [_step("解析本地原子坐标", "structure_parse_workspace", {"path": path})]
    raise WorkflowError("Structure source must be rcsb or workspace.", "invalid_workflow_inputs")


def _fastq_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    path = _require_text(inputs, "path", "Workspace FASTQ path")
    try:
        max_reads = int(inputs.get("max_reads") or 10000)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("max_reads must be an integer.", "invalid_workflow_inputs") from exc
    if not 1 <= max_reads <= 100000:
        raise WorkflowError("max_reads must be between 1 and 100000.", "invalid_workflow_inputs")
    inputs.update({"path": path, "max_reads": max_reads})
    return [_step("计算 FASTQ 质量指标", "ngs_fastq_qc", {"path": path, "max_reads": max_reads})]


def _alignment_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    sequence_a = _require_text(inputs, "sequence_a", "Sequence A")
    sequence_b = _require_text(inputs, "sequence_b", "Sequence B")
    label_a = str(inputs.get("label_a") or "Sequence A").strip() or "Sequence A"
    label_b = str(inputs.get("label_b") or "Sequence B").strip() or "Sequence B"
    inputs.update({"sequence_a": sequence_a, "sequence_b": sequence_b, "label_a": label_a, "label_b": label_b})
    return [
        _step(
            "执行全局序列比对",
            "sequence_align",
            {"sequence_a": sequence_a, "sequence_b": sequence_b, "label_a": label_a, "label_b": label_b},
        )
    ]


def _database_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    source = str(inputs.get("source") or "pubchem").strip().lower()
    query = _require_text(inputs, "query", "Database query")
    inputs.update({"source": source, "query": query})
    if source == "pubchem":
        return [_step("检索 PubChem 并解析结构", "database_lookup_pubchem", {"query": query})]
    if source == "uniprot":
        return [_step("检索 UniProtKB 并解析序列", "database_lookup_uniprot", {"accession": query.upper()})]
    raise WorkflowError("Database source must be pubchem or uniprot.", "invalid_workflow_inputs")


BUILDERS: dict[str, Callable[[dict[str, Any]], list[dict[str, Any]]]] = {
    "molecule-profile": _molecule_steps,
    "protein-sequence-review": _protein_steps,
    "protein-structure-review": _structure_steps,
    "fastq-qc-review": _fastq_steps,
    "pairwise-alignment-review": _alignment_steps,
    "database-record-review": _database_steps,
}


def _step(title: str, tool: str, arguments: dict[str, Any], **internal: Any) -> dict[str, Any]:
    return {
        "id": f"step-{uuid.uuid4().hex[:8]}",
        "title": title,
        "tool": tool,
        "arguments": arguments,
        "status": "pending",
        **internal,
    }


class WorkflowManager:
    def __init__(self, storage_root: Path | None = None) -> None:
        self.storage_root = Path(storage_root or DEFAULT_STORAGE_ROOT)
        self._lock = threading.RLock()
        self._runs: dict[str, dict[str, Any]] = {}
        self._load_runs()

    def catalog(self) -> list[dict[str, Any]]:
        return [
            {
                "id": template_id,
                "title": template["title"],
                "description": template["description"],
                "fields": copy.deepcopy(template["fields"]),
                "requires_approval": True,
            }
            for template_id, template in TEMPLATES.items()
        ]

    def create_plan(
        self,
        template_id: str,
        inputs: dict[str, Any] | None,
        objective: str = "",
    ) -> dict[str, Any]:
        template_id = str(template_id or "").strip()
        template = TEMPLATES.get(template_id)
        builder = BUILDERS.get(template_id)
        if template is None or builder is None:
            raise WorkflowError(f"Unknown workflow template: {template_id}", "unknown_workflow", 404)
        allowed_inputs = {str(field["name"]) for field in template["fields"]}
        normalized_inputs = {key: value for key, value in dict(inputs or {}).items() if key in allowed_inputs}
        steps = builder(normalized_inputs)
        now = _timestamp()
        run_id = uuid.uuid4().hex
        run = {
            "id": run_id,
            "template_id": template_id,
            "title": template["title"],
            "objective": str(objective or template["description"]).strip(),
            "description": template["description"],
            "status": "pending_approval",
            "requires_approval": True,
            "inputs": normalized_inputs,
            "assumptions": list(template.get("assumptions") or []),
            "steps": steps,
            "trace": [],
            "artifacts": [],
            "created_at": now,
            "updated_at": now,
        }
        run["artifacts"] = [_plan_artifact(run)]
        with self._lock:
            self._runs[run_id] = run
            self._persist(run)
            return copy.deepcopy(run)

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            runs = sorted(self._runs.values(), key=lambda item: item.get("created_at", ""), reverse=True)
            return copy.deepcopy(runs[: max(1, min(int(limit), 200))])

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            run = self._runs.get(str(run_id))
            if run is None:
                raise WorkflowError(f"Workflow run not found: {run_id}", "workflow_not_found", 404)
            return copy.deepcopy(run)

    def approve(self, run_id: str, registry: Any) -> dict[str, Any]:
        with self._lock:
            run = self._runs.get(str(run_id))
            if run is None:
                raise WorkflowError(f"Workflow run not found: {run_id}", "workflow_not_found", 404)
            if run.get("status") != "pending_approval":
                raise WorkflowError(
                    f"Workflow cannot be approved from status {run.get('status')}.",
                    "invalid_workflow_state",
                    409,
                )
            run["status"] = "running"
            run["approved_at"] = _timestamp()
            run["updated_at"] = run["approved_at"]
            self._persist(run)

        outputs: list[dict[str, Any]] = []
        for index, step in enumerate(run["steps"]):
            started = time.perf_counter()
            with self._lock:
                step["status"] = "running"
                step["started_at"] = _timestamp()
                run["updated_at"] = step["started_at"]
                self._persist(run)
            try:
                arguments = _resolve_arguments(step, outputs)
                result = registry.execute(step["tool"], arguments)
                outputs.append(result)
                artifacts = list(result.get("artifacts") or [])
                trace_item = {
                    "name": step["tool"],
                    "skill": result.get("skill", ""),
                    "args": copy.deepcopy(arguments),
                    "status": "completed",
                    "summary": str(result.get("summary") or "Skill completed."),
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
                with self._lock:
                    step.update(
                        {
                            "status": "completed",
                            "summary": trace_item["summary"],
                            "duration_ms": trace_item["duration_ms"],
                            "completed_at": _timestamp(),
                        }
                    )
                    run["trace"].append(trace_item)
                    run["artifacts"].extend(artifacts)
                    run["updated_at"] = step["completed_at"]
                    self._persist(run)
            except Exception as exc:
                trace_item = {
                    "name": step["tool"],
                    "skill": "",
                    "args": copy.deepcopy(step.get("arguments") or {}),
                    "status": "error",
                    "summary": str(exc),
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                }
                with self._lock:
                    step.update({"status": "error", "summary": str(exc), "completed_at": _timestamp()})
                    for remaining in run["steps"][index + 1 :]:
                        remaining["status"] = "skipped"
                    run["trace"].append(trace_item)
                    run["status"] = "failed"
                    run["error"] = str(exc)
                    run["completed_at"] = step["completed_at"]
                    run["updated_at"] = step["completed_at"]
                    run["artifacts"].append(_run_artifact(run))
                    self._persist(run)
                    return copy.deepcopy(run)

        with self._lock:
            run["status"] = "completed"
            run["completed_at"] = _timestamp()
            run["updated_at"] = run["completed_at"]
            run["artifacts"].append(_run_artifact(run))
            self._persist(run)
            return copy.deepcopy(run)

    def cancel(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            run = self._runs.get(str(run_id))
            if run is None:
                raise WorkflowError(f"Workflow run not found: {run_id}", "workflow_not_found", 404)
            if run.get("status") != "pending_approval":
                raise WorkflowError(
                    f"Workflow cannot be cancelled from status {run.get('status')}.",
                    "invalid_workflow_state",
                    409,
                )
            run["status"] = "cancelled"
            run["cancelled_at"] = _timestamp()
            run["updated_at"] = run["cancelled_at"]
            for step in run["steps"]:
                step["status"] = "cancelled"
            self._persist(run)
            return copy.deepcopy(run)

    def _persist(self, run: dict[str, Any]) -> None:
        plan_id = f"workflow-plan-{run['id']}"
        refreshed_plan = _plan_artifact(run)
        for index, artifact in enumerate(run.get("artifacts") or []):
            if artifact.get("id") == plan_id:
                run["artifacts"][index] = refreshed_plan
                break
        self.storage_root.mkdir(parents=True, exist_ok=True)
        target = self.storage_root / f"{run['id']}.json"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(target)

    def _load_runs(self) -> None:
        if not self.storage_root.is_dir():
            return
        for path in sorted(self.storage_root.glob("*.json")):
            try:
                run = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(run, dict) or not run.get("id") or not run.get("template_id"):
                continue
            if run.get("status") == "running":
                run["status"] = "failed"
                run["error"] = "Local server stopped while this workflow was running."
                run["updated_at"] = _timestamp()
                for step in run.get("steps") or []:
                    if step.get("status") == "running":
                        step["status"] = "error"
                        step["summary"] = run["error"]
                    elif step.get("status") == "pending":
                        step["status"] = "skipped"
                run.setdefault("artifacts", []).append(_run_artifact(run))
                self._persist(run)
            self._runs[str(run["id"])] = run


def _resolve_arguments(step: dict[str, Any], outputs: list[dict[str, Any]]) -> dict[str, Any]:
    arguments = copy.deepcopy(step.get("arguments") or {})
    if step.get("derive") != "molecule-properties":
        return arguments
    source_index = int(step.get("source_step", 0))
    try:
        properties = dict((outputs[source_index].get("data") or {}).get("properties") or {})
    except (IndexError, TypeError, ValueError) as exc:
        raise WorkflowError("Could not derive molecular properties from the previous step.") from exc
    selected: dict[str, float] = {}
    for key in ("MW", "logP", "TPSA", "HBA", "HBD", "RotB"):
        try:
            selected[key] = float(properties[key])
        except (KeyError, TypeError, ValueError):
            continue
    if not selected:
        raise WorkflowError("The molecule analysis did not return numeric properties.")
    arguments["properties"] = selected
    return arguments


def _plan_artifact(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"workflow-plan-{run['id']}",
        "type": "workflow-plan",
        "title": run["title"],
        "data": {
            "id": run["id"],
            "template_id": run["template_id"],
            "title": run["title"],
            "objective": run["objective"],
            "status": run["status"],
            "requires_approval": True,
            "steps": [
                {"id": step["id"], "title": step["title"], "tool": step["tool"], "status": step["status"]}
                for step in run["steps"]
            ],
        },
    }


def _run_artifact(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"workflow-run-{run['id']}",
        "type": "workflow-run",
        "title": f"{run['title']} · {run['status']}",
        "data": {
            "id": run["id"],
            "template_id": run["template_id"],
            "status": run["status"],
            "completed_steps": sum(step.get("status") == "completed" for step in run["steps"]),
            "total_steps": len(run["steps"]),
            "error": run.get("error"),
        },
    }


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


WORKFLOW_MANAGER = WorkflowManager()
