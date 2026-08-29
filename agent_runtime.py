"""OpenAI-compatible tool-calling agent for the local Molemo workbench."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from skill_runtime import SkillError, SkillRegistry, compact_tool_result


MAX_AGENT_STEPS = 6
MAX_PROVIDER_BYTES = 4 * 1024 * 1024


class AgentError(RuntimeError):
    def __init__(self, message: str, code: str = "agent_error", status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status

    def to_dict(self) -> dict[str, object]:
        return {"error": self.message, "code": self.code}


SYSTEM_PROMPT = """You are Molemo, a local-first molecular and protein research agent.
Keep the user's biological question as the main line. Use the smallest useful set of tools, distinguish computed results from hypotheses, and cite tool names when they materially support a claim. Do not invent tool results. Local workspace files may be read only through registered tools. Multi-step workflows must remain pending until the researcher explicitly approves them in the local WorkBench; never claim that a proposed plan has executed. Return a concise answer in the user's language with: working conclusion, supporting evidence, caveats, and the next useful analysis. Molecular or protein design suggestions are hypotheses that require experimental validation."""


def run_agent(payload: dict[str, Any], registry: SkillRegistry) -> dict[str, Any]:
    message = str(payload.get("message") or "").strip()
    if not message:
        raise AgentError("A chat message is required.", "empty_message")

    provider = dict(payload.get("provider") or {})
    context = dict(payload.get("context") or {})
    history = list(payload.get("history") or [])[-12:]
    tool_mode = str(provider.get("tool_mode") or "native")

    if not provider.get("endpoint"):
        return run_local_agent(message, context, registry)

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history:
        role = str(item.get("role") or "")
        content = str(item.get("content") or item.get("text") or "")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    local_trace: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    if tool_mode == "grounded":
        preload = preload_context_tool(context, registry)
        if preload:
            local_trace.append(preload[0])
            artifacts.extend(preload[1].get("artifacts") or [])
            messages.append(
                {
                    "role": "system",
                    "content": "Local scientific context: " + compact_tool_result(preload[1]),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": json.dumps({"question": message, "active_workspace": context}, ensure_ascii=False),
        }
    )

    tools = registry.openai_tools() if tool_mode == "native" else []
    usage: dict[str, Any] = {}
    for _ in range(MAX_AGENT_STEPS):
        response = provider_chat(provider, messages, tools)
        usage = dict(response.get("usage") or usage)
        choice = (response.get("choices") or [{}])[0]
        assistant = dict(choice.get("message") or {})
        tool_calls = list(assistant.get("tool_calls") or [])
        if not tool_calls:
            content = normalize_content(assistant.get("content"))
            if not content:
                raise AgentError("The provider returned an empty response.", "empty_provider_response", 502)
            return {
                "ok": True,
                "message": content,
                "trace": local_trace,
                "artifacts": dedupe_artifacts(artifacts),
                "usage": usage,
                "provider": {
                    "model": provider.get("model"),
                    "tool_mode": tool_mode,
                },
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant.get("content"),
                "tool_calls": tool_calls,
            }
        )
        for call in tool_calls:
            function = dict(call.get("function") or {})
            name = str(function.get("name") or "")
            raw_arguments = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else dict(raw_arguments)
            except (json.JSONDecodeError, TypeError, ValueError):
                arguments = {}
            started = time.perf_counter()
            trace_item = {
                "name": name,
                "skill": registry.tools.get(name).skill_id if name in registry.tools else "unknown",
                "args": redact_arguments(arguments),
                "status": "completed",
            }
            try:
                result = registry.execute_agent(name, arguments)
                artifacts.extend(result.get("artifacts") or [])
                trace_item["summary"] = str(result.get("summary") or "Skill completed.")
                tool_content = compact_tool_result(result)
            except SkillError as exc:
                trace_item["status"] = "error"
                trace_item["summary"] = str(exc)
                tool_content = json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
            trace_item["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            local_trace.append(trace_item)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id") or name,
                    "content": tool_content,
                }
            )

    raise AgentError("The agent reached the local tool-step limit.", "tool_step_limit", 502)


def run_local_agent(message: str, context: dict[str, Any], registry: SkillRegistry) -> dict[str, Any]:
    route = registry.execute("research_route", {"question": message})
    trace = [trace_from_result(route, {"question": message})]
    artifacts: list[dict[str, Any]] = []
    evidence: list[str] = []
    plan_request = local_workflow_plan(message, context)
    if plan_request:
        template_id, inputs = plan_request
        try:
            result = registry.execute(
                "workflow_create_plan",
                {"template_id": template_id, "inputs": inputs, "objective": message},
            )
            trace.append(trace_from_result(result, {"template_id": template_id, "inputs": inputs}))
            artifacts.extend(result.get("artifacts") or [])
            evidence.append(str(result.get("summary") or "Workflow plan created."))
        except SkillError as exc:
            evidence.append(f"Workflow plan could not be created: {exc}")

    for tool_name, arguments in [] if plan_request else local_intent_tools(message):
        try:
            result = registry.execute(tool_name, arguments)
            trace.append(trace_from_result(result, arguments))
            artifacts.extend(result.get("artifacts") or [])
            evidence.append(str(result.get("summary") or f"{tool_name} completed."))
        except SkillError as exc:
            evidence.append(f"{tool_name} could not complete: {exc}")
    sample_type = str(context.get("type") or "")
    try:
        if not plan_request and sample_type == "molecule" and context.get("smiles"):
            result = registry.execute("chem_analyze_molecule", {"smiles": context["smiles"]})
            trace.append(trace_from_result(result, {"smiles": context["smiles"]}))
            artifacts.extend(result.get("artifacts") or [])
            sample = result.get("data") or {}
            props = sample.get("properties") or {}
            evidence.append(
                f"RDKit: {sample.get('formula', 'molecule')}, MW {props.get('MW', 'n/a')}, logP {props.get('logP', 'n/a')}, TPSA {props.get('TPSA', 'n/a')}."
            )
        elif not plan_request and sample_type == "protein" and context.get("sequence"):
            result = registry.execute("protein_analyze_sequence", {"sequence": context["sequence"]})
            trace.append(trace_from_result(result, {"sequence": context["sequence"]}))
            artifacts.extend(result.get("artifacts") or [])
            sample = result.get("data") or {}
            props = sample.get("properties") or {}
            evidence.append(
                f"Sequence pipeline: {props.get('Length', 'n/a')}, pI {props.get('pI', 'n/a')}, GRAVY {props.get('GRAVY', 'n/a')}, aggregation flag {props.get('Risk', 'n/a')}."
            )
    except SkillError as exc:
        evidence.append(f"Local analysis could not complete: {exc}")

    lane = ", ".join(route.get("lanes") or ["general life science"])
    evidence_text = " ".join(evidence) if evidence else "No structured molecule or protein is active yet."
    if plan_request:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "计划尚未执行；请在“运行”页审阅输入与步骤，并由研究者明确批准。"
        )
    else:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "这些结果是本地计算或结构解析，不等同于实验结论。下一步可继续要求序列比对、性质图、候选设计，或把 FASTA/SMILES 文件导入 workspace 后再分析。"
        )
    return {
        "ok": True,
        "message": reply,
        "trace": trace,
        "artifacts": dedupe_artifacts(artifacts),
        "usage": {},
        "provider": {"model": "local-skill-runtime", "tool_mode": "local"},
    }


def local_intent_tools(message: str) -> list[tuple[str, dict[str, Any]]]:
    """Select explicit retrieval/QC tools when no external LLM is configured."""
    selected: list[tuple[str, dict[str, Any]]] = []
    pdb = re.search(r"(?:pdb|rcsb|structure|结构)\s*(?:id|编号|条目)?\s*[:：#-]?\s*([0-9][a-z0-9]{3})\b", message, re.I)
    if pdb:
        selected.append(("structure_fetch_pdb", {"pdb_id": pdb.group(1).upper()}))

    uniprot = re.search(
        r"(?:uniprot(?:kb)?|accession|蛋白条目)\s*(?:id|编号)?\s*[:：#-]?\s*([a-z0-9]{6,10}(?:-\d+)?)\b",
        message,
        re.I,
    )
    if uniprot:
        selected.append(("database_lookup_uniprot", {"accession": uniprot.group(1).upper()}))

    fastq = re.search(r"([\w./-]+\.(?:fastq|fq))\b", message, re.I)
    if fastq and re.search(r"fastq|qc|quality|phred|q20|q30|质控|质量", message, re.I):
        selected.append(("ngs_fastq_qc", {"path": fastq.group(1)}))

    pubchem_query = extract_pubchem_query(message)
    if pubchem_query:
        selected.append(("database_lookup_pubchem", {"query": pubchem_query}))
    return selected


def local_workflow_plan(message: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Build a guided plan request without granting execution authority."""
    table_paths = re.findall(r"([\w./-]+\.(?:csv|tsv))\b", message, re.I)
    if len(table_paths) >= 2 and re.search(
        r"rna-?seq|count matrix|differential expression|transcriptom|差异表达|转录组",
        message,
        re.I,
    ):
        count_path = next((path for path in table_paths if re.search(r"count|matrix", path, re.I)), table_paths[0])
        metadata_path = next(
            (path for path in table_paths if re.search(r"meta|sample|design", path, re.I)),
            table_paths[1],
        )
        contrast = re.search(r"\b([A-Za-z][\w.-]*)\s+(?:vs\.?|versus)\s+([A-Za-z][\w.-]*)\b", message, re.I)
        test_level = contrast.group(1) if contrast else "treated"
        reference_level = contrast.group(2) if contrast else "control"
        batch_match = re.search(r"(?:batch|批次)(?:\s+column|\s*列)?\s*[:：=]?\s*([A-Za-z_][A-Za-z0-9_]*)", message, re.I)
        return "bulk-rnaseq-differential-expression", {
            "count_matrix_path": count_path,
            "metadata_path": metadata_path,
            "sample_column": "sample",
            "condition_column": "condition",
            "test_level": test_level,
            "reference_level": reference_level,
            "batch_column": batch_match.group(1) if batch_match else "",
            "min_total_count": 10,
            "fdr_threshold": 0.05,
            "lfc_threshold": 1.0,
        }
    sequence_database = re.search(r"([\w./-]+\.(?:fa|fasta|faa|fna))\b", message, re.I)
    if sequence_database and re.search(r"\bblast[ pn]?\b|homolog|sequence search|同源|相似序列|序列搜索", message, re.I):
        query = str(context.get("sequence") or "").strip()
        if query:
            compact_query = re.sub(r"[^A-Za-z]", "", query).upper()
            nucleotide_only = bool(compact_query) and not (set(compact_query) - set("ACGTURYKMSWBDHVN"))
            program = "blastn" if re.search(r"\bblastn\b|nucleotide|dna|rna|核酸|核苷酸", message, re.I) else "blastp"
            if nucleotide_only and str(context.get("type") or "") != "protein":
                program = "blastn"
            return "sequence-similarity-search", {
                "query": query,
                "database_path": sequence_database.group(1),
                "program": program,
                "evalue": 1e-5,
                "max_hits": 10,
            }
    if not re.search(r"(?:制定|生成|创建|准备|给我)?.{0,4}(?:分析计划|执行计划|研究计划|分析流程|管线)|\bworkflow\b|\bpipeline\b|\bplan\b", message, re.I):
        return None

    fastq = re.search(r"([\w./-]+\.(?:fastq|fq))\b", message, re.I)
    if fastq:
        return "fastq-qc-review", {"path": fastq.group(1), "max_reads": 10000}

    pdb = re.search(r"(?:pdb|rcsb|structure|结构)\s*(?:id|编号|条目)?\s*[:：#-]?\s*([0-9][a-z0-9]{3})\b", message, re.I)
    if pdb:
        return "protein-structure-review", {"source": "rcsb", "pdb_id": pdb.group(1).upper()}

    sample_type = str(context.get("type") or "")
    if sample_type == "molecule" and context.get("smiles"):
        return "molecule-profile", {"smiles": context["smiles"]}
    if sample_type == "protein" and context.get("pdb_id"):
        return "protein-structure-review", {"source": "rcsb", "pdb_id": context["pdb_id"]}
    if sample_type == "protein" and context.get("sequence"):
        return "protein-sequence-review", {"sequence": context["sequence"]}
    return None


def extract_pubchem_query(message: str) -> str:
    if not re.search(r"pubchem", message, re.I):
        return ""
    quoted = re.search(r"[\"']([^\"']{1,100})[\"']", message)
    if quoted:
        return quoted.group(1).strip()
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+_.-]*", message)
    ignored = {"pubchem", "lookup", "search", "find", "compound", "cid", "for", "in", "the"}
    candidates = [word for word in words if word.lower() not in ignored]
    return candidates[-1][:100] if candidates else ""


def preload_context_tool(context: dict[str, Any], registry: SkillRegistry):
    if context.get("type") == "molecule" and context.get("smiles"):
        result = registry.execute("chem_analyze_molecule", {"smiles": context["smiles"]})
        return trace_from_result(result, {"smiles": context["smiles"]}), result
    if context.get("type") == "protein" and context.get("sequence"):
        result = registry.execute("protein_analyze_sequence", {"sequence": context["sequence"]})
        return trace_from_result(result, {"sequence": context["sequence"]}), result
    return None


def provider_chat(provider: dict[str, Any], messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, Any]:
    endpoint = normalize_endpoint(str(provider.get("endpoint") or ""))
    model = str(provider.get("model") or "").strip()
    if not model:
        raise AgentError("A provider model is required.", "missing_model")
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": float(provider.get("temperature", 0.2)),
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    key = str(provider.get("key") or "")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    for key_name, value in dict(provider.get("headers") or {}).items():
        if key_name.lower() not in {"host", "content-length"}:
            headers[str(key_name)] = str(value)
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            raw = response.read(MAX_PROVIDER_BYTES + 1)
    except urllib.error.HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        safe_detail = redact_provider_error(detail)
        raise AgentError(f"Provider returned HTTP {exc.code}: {safe_detail}", "provider_http_error", 502) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AgentError(f"Could not reach the provider: {exc}", "provider_unavailable", 502) from exc
    if len(raw) > MAX_PROVIDER_BYTES:
        raise AgentError("Provider response exceeded the local size limit.", "provider_response_too_large", 502)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentError("Provider returned invalid JSON.", "invalid_provider_json", 502) from exc
    if not isinstance(data, dict):
        raise AgentError("Provider returned an unexpected response shape.", "invalid_provider_response", 502)
    return data


def normalize_endpoint(endpoint: str) -> str:
    value = endpoint.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AgentError("Provider endpoint must be an http(s) URL.", "invalid_endpoint")
    if value.rstrip("/").endswith("/v1"):
        return value.rstrip("/") + "/chat/completions"
    return value


def normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                chunks.append(str(item.get("text") or ""))
        return "\n".join(chunks).strip()
    return ""


def trace_from_result(result: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": result.get("tool"),
        "skill": result.get("skill"),
        "args": redact_arguments(arguments),
        "status": "completed" if result.get("ok", True) else "error",
        "summary": result.get("summary", "Skill completed."),
        "duration_ms": result.get("duration_ms", 0),
    }


def redact_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in arguments.items():
        if re.search(r"key|token|secret|password|authorization", str(key), re.I):
            redacted[key] = "[redacted]"
        elif isinstance(value, str) and len(value) > 240:
            redacted[key] = value[:237] + "..."
        else:
            redacted[key] = value
    return redacted


def redact_provider_error(detail: str) -> str:
    cleaned = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+\-/=]+", r"\1[redacted]", detail)
    cleaned = re.sub(r"(?i)(api[_-]?key[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+", r"\1[redacted]", cleaned)
    return cleaned[:1000]


def dedupe_artifacts(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for artifact in artifacts:
        key = str(artifact.get("id") or json.dumps(artifact, sort_keys=True, ensure_ascii=False)[:400])
        if key in seen:
            continue
        seen.add(key)
        result.append(artifact)
    return result
