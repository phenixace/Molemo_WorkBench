"""Run the deterministic Molemo_Bench skill benchmark."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from skill_runtime import SkillError, SkillRegistry
from workspace_utils import WORKSPACE_ROOT, WorkspaceError, resolve_workspace_path


ROOT = Path(__file__).resolve().parent
DEFAULT_TASKS = ROOT / "benchmarks" / "tasks.jsonl"


def load_tasks(path: Path) -> list[dict[str, Any]]:
    tasks = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            tasks.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
    return tasks


def resolve_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split(".") if path else []:
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def check_assertion(result: dict[str, Any], assertion: dict[str, Any]) -> tuple[bool, str]:
    path = str(assertion.get("path") or "")
    operation = str(assertion.get("op") or "equals")
    try:
        actual = resolve_path(result, path)
    except (KeyError, IndexError, TypeError, ValueError):
        return False, f"missing path {path}"
    expected = assertion.get("value")
    if operation == "equals":
        passed = actual == expected
    elif operation == "contains":
        passed = expected in actual
    elif operation == "length":
        passed = len(actual) == int(expected)
    elif operation == "approx":
        tolerance = float(assertion.get("tolerance", 0.01))
        passed = abs(float(actual) - float(expected)) <= tolerance
    elif operation == "gte":
        passed = float(actual) >= float(expected)
    else:
        return False, f"unsupported assertion op {operation}"
    return passed, f"{path}: expected {operation} {expected!r}, got {actual!r}"


def run_benchmark(tasks_path: Path = DEFAULT_TASKS) -> dict[str, Any]:
    previous_storage = os.environ.get("MOLEMO_WORKFLOW_STORAGE_ROOT")
    with tempfile.TemporaryDirectory(prefix="molemo-bench-runs-") as storage:
        os.environ["MOLEMO_WORKFLOW_STORAGE_ROOT"] = storage
        try:
            return _run_benchmark(tasks_path)
        finally:
            if previous_storage is None:
                os.environ.pop("MOLEMO_WORKFLOW_STORAGE_ROOT", None)
            else:
                os.environ["MOLEMO_WORKFLOW_STORAGE_ROOT"] = previous_storage


def _run_benchmark(tasks_path: Path) -> dict[str, Any]:
    registry = SkillRegistry()
    task_results = []
    artifact_expected = 0
    artifact_passed = 0
    trace_complete = 0
    for task in load_tasks(tasks_path):
        result = None
        error = None
        try:
            result = registry.execute(task["tool"], task.get("arguments") or {})
        except SkillError as exc:
            error = str(exc)

        expected_error = task.get("expected_error")
        checks = []
        if expected_error:
            passed = error is not None and str(expected_error).lower() in error.lower()
            checks.append({"passed": passed, "detail": error or "expected an error"})
        elif error:
            passed = False
            checks.append({"passed": False, "detail": error})
        else:
            for assertion in task.get("assertions") or []:
                check_passed, detail = check_assertion(result or {}, assertion)
                checks.append({"passed": check_passed, "detail": detail})
            passed = all(check["passed"] for check in checks)

        if result and all(key in result for key in ("tool", "skill", "duration_ms")):
            trace_complete += 1
        if task.get("expects_artifact"):
            artifact_expected += 1
            if result and result.get("artifacts"):
                artifact_passed += 1
        cleanup_task_output(task, result)
        task_results.append(
            {
                "id": task["id"],
                "tool": task["tool"],
                "passed": passed,
                "checks": checks,
                "error": error,
            }
        )

    passed_count = sum(1 for item in task_results if item["passed"])
    total = len(task_results)
    successful_outputs = sum(1 for item in task_results if item["error"] is None)
    metrics = {
        "task_accuracy": round(passed_count / total, 4) if total else 0,
        "tool_success_rate": round(passed_count / total, 4) if total else 0,
        "trace_completeness": round(trace_complete / max(1, successful_outputs), 4),
        "artifact_rate": round(artifact_passed / max(1, artifact_expected), 4),
        "failure_rate": round((total - passed_count) / total, 4) if total else 0,
    }
    return {
        "benchmark": "Molemo_Bench v0.10",
        "tasks": total,
        "passed": passed_count,
        "metrics": metrics,
        "results": task_results,
    }


def cleanup_task_output(task: dict[str, Any], result: dict[str, Any] | None) -> None:
    if not task.get("cleanup_output") or not result:
        return
    output_root = str((result.get("data") or {}).get("output_root") or "")
    if not output_root:
        return
    try:
        target = resolve_workspace_path(output_root)
    except WorkspaceError:
        return
    analyses_root = (WORKSPACE_ROOT / "analyses").resolve()
    if target.parent == analyses_root and target.name.startswith("rnaseq-"):
        shutil.rmtree(target, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Molemo_Bench v0.10 against the local skill registry.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_benchmark(args.tasks)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"{report['benchmark']}: {report['passed']}/{report['tasks']} tasks passed")
    for name, value in report["metrics"].items():
        print(f"  {name}: {value:.1%}")
    for result in report["results"]:
        marker = "PASS" if result["passed"] else "FAIL"
        print(f"  [{marker}] {result['id']}")
    if report["passed"] != report["tasks"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
