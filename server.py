"""Local HTTP server for Molemo_Bench, its agent, and scientific skills."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from agent_runtime import AgentError, run_agent
from pipeline import PipelineError, parse_molecule, parse_protein
from skill_runtime import SkillError, SkillRegistry
from workspace_utils import (
    MAX_UPLOAD_BYTES,
    WorkspaceError,
    list_workspace_files,
    write_workspace_file,
    write_workspace_text,
)
from workflow_runtime import WORKFLOW_MANAGER, WorkflowError


ROOT = Path(__file__).resolve().parent
REGISTRY = SkillRegistry()
MAX_REQUEST_BYTES = 24 * 1024 * 1024
STATIC_FILES = {"index.html", "styles.css", "app.js"}


class MolemoHandler(BaseHTTPRequestHandler):
    server_version = "molemo-bench/0.18"

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(
                {
                    "ok": True,
                    "service": "molemo-bench",
                    "skills": len(REGISTRY.catalog()),
                    "tools": len(REGISTRY.tools),
                    "workflows": len(WORKFLOW_MANAGER.catalog()),
                }
            )
            return
        if parsed.path == "/api/skills":
            self._send_json({"ok": True, "skills": REGISTRY.catalog()})
            return
        if parsed.path == "/api/workspace":
            self._send_json({"ok": True, "files": list_workspace_files()})
            return
        if parsed.path == "/api/workflows":
            self._send_json({"ok": True, "workflows": WORKFLOW_MANAGER.catalog()})
            return
        if parsed.path == "/api/runs":
            self._send_json({"ok": True, "runs": WORKFLOW_MANAGER.list_runs()})
            return
        run_route = self._workflow_run_route(parsed.path)
        if run_route and run_route[1] == "view":
            try:
                self._send_json({"ok": True, "run": WORKFLOW_MANAGER.get_run(run_route[0])})
            except WorkflowError as exc:
                self._send_json({"ok": False, **exc.to_dict()}, exc.status)
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/workspace/upload":
                query = parse_qs(parsed.query)
                path = str((query.get("path") or [""])[0]).strip()
                result = write_workspace_file(path, self._read_bytes(MAX_UPLOAD_BYTES))
                self._send_json({"ok": True, "file": result}, HTTPStatus.CREATED)
                return
            payload = self._read_json()
            if parsed.path == "/api/molecule":
                sample = parse_molecule(str(payload.get("smiles", "")))
                self._send_json({"ok": True, "sample": sample})
                return
            if parsed.path == "/api/protein":
                sample = parse_protein(str(payload.get("sequence", "")))
                self._send_json({"ok": True, "sample": sample})
                return
            if parsed.path == "/api/chat":
                result = run_agent(payload, REGISTRY)
                self._send_json(result)
                return
            if parsed.path == "/api/tools/call":
                result = REGISTRY.execute_agent(str(payload.get("name") or ""), payload.get("arguments") or {})
                self._send_json(result)
                return
            if parsed.path == "/api/workspace/write":
                result = write_workspace_text(str(payload.get("path") or ""), str(payload.get("content") or ""))
                self._send_json({"ok": True, "file": result}, HTTPStatus.CREATED)
                return
            if parsed.path == "/api/workflows/plan":
                raw_inputs = payload.get("inputs")
                if raw_inputs is not None and not isinstance(raw_inputs, dict):
                    raise WorkflowError("Workflow inputs must be a JSON object.", "invalid_workflow_inputs")
                run = WORKFLOW_MANAGER.create_plan(
                    str(payload.get("template_id") or ""),
                    raw_inputs or {},
                    str(payload.get("objective") or ""),
                )
                self._send_json({"ok": True, "run": run}, HTTPStatus.CREATED)
                return
            run_route = self._workflow_run_route(parsed.path)
            if run_route and run_route[1] == "approve":
                run = WORKFLOW_MANAGER.approve(run_route[0], REGISTRY)
                self._send_json({"ok": True, "run": run})
                return
            if run_route and run_route[1] == "cancel":
                run = WORKFLOW_MANAGER.cancel(run_route[0])
                self._send_json({"ok": True, "run": run})
                return
            self._send_json({"ok": False, "error": "Unknown endpoint."}, HTTPStatus.NOT_FOUND)
        except AgentError as exc:
            self._send_json({"ok": False, **exc.to_dict()}, exc.status)
        except PipelineError as exc:
            self._send_json({"ok": False, **exc.to_dict()}, HTTPStatus.BAD_REQUEST)
        except (SkillError, WorkspaceError) as exc:
            self._send_json(
                {"ok": False, "error": str(exc), "code": "local_skill_error"},
                HTTPStatus.BAD_REQUEST,
            )
        except WorkflowError as exc:
            self._send_json({"ok": False, **exc.to_dict()}, exc.status)
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "Invalid JSON body.", "code": "invalid_json"}, HTTPStatus.BAD_REQUEST)

    @staticmethod
    def _workflow_run_route(path: str) -> tuple[str, str] | None:
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[:2] == ["api", "runs"] and parts[2]:
            return parts[2], "view"
        if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] in {"approve", "cancel"}:
            return parts[2], parts[3]
        return None

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > MAX_REQUEST_BYTES:
            raise AgentError("Request body exceeds the local 24 MB limit.", "request_too_large", 413)
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _read_bytes(self, maximum: int) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > maximum:
            raise AgentError(
                f"Request body exceeds the local {maximum // (1024 * 1024)} MB upload limit.",
                "request_too_large",
                413,
            )
        return self.rfile.read(length)

    def _serve_static(self, request_path: str) -> None:
        path = unquote(request_path)
        if path in {"", "/"}:
            path = "/index.html"
        relative = path.lstrip("/")
        if relative not in STATIC_FILES:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        target = (ROOT / relative).resolve()
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Molemo_Bench local workbench.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MolemoHandler)
    print(f"Molemo_Bench: http://{args.host}:{args.port}")
    print(f"Loaded {len(REGISTRY.catalog())} skills and {len(REGISTRY.tools)} tools.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
