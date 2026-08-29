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
Keep the user's biological question as the main line. Use the smallest useful set of tools, distinguish computed results from hypotheses, and cite tool names when they materially support a claim. Do not invent tool results. Literature claims must cite PMID, PMCID, DOI, or a source URL returned by a tool; distinguish abstract-reported findings from independent validation, and never treat relevance order or citation counts as study quality. For clinical trials, cite NCT IDs and official links, distinguish registry status and registered endpoints from posted results and publications, and never infer efficacy, safety, or failure from registry metadata or missing results. For human variants, preserve the exact allele, transcript, assembly, phenotype, and inheritance context; distinguish ClinVar submitted classifications, VEP computational annotations, and gnomAD population observations, and never invent a pathogenicity or ACMG/AMP score. Variant evidence is not a diagnosis or treatment recommendation. Local workspace files may be read only through registered tools. Multi-step workflows must remain pending until the researcher explicitly approves them in the local WorkBench; never claim that a proposed plan has executed. Return a concise answer in the user's language with: working conclusion, supporting evidence, caveats, and the next useful analysis. Molecular or protein design suggestions are hypotheses that require experimental validation."""


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

    raw_lanes = route.get("lanes") or ["general life science"]
    lane_labels = {
        "target evidence and prioritization": "靶点证据与优先级",
        "transcriptomics and expression": "转录组与表达",
        "sequence similarity search": "序列相似性搜索",
        "protein structure and sequence": "蛋白结构与序列",
        "molecular chemistry": "分子化学",
        "literature and study discovery": "文献与研究发现",
        "human genetics and variant evidence": "人类遗传与变异证据",
        "clinical and translational evidence": "临床与转化证据",
    }
    lane = ", ".join(lane_labels.get(item, item) for item in raw_lanes)
    evidence_text = " ".join(evidence) if evidence else "No structured molecule or protein is active yet."
    if plan_request:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "计划尚未执行；请在“运行”页审阅输入与步骤，并由研究者明确批准。"
        )
    elif "literature and study discovery" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "结果按 Europe PMC relevance 保留，并附 PMID、DOI 或来源链接；该顺序不代表研究质量，形成结论前仍需检查摘要、全文与研究设计。"
        )
    elif "clinical and translational evidence" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "ClinicalTrials.gov 登记状态、研究设计和注册终点不等同于疗效或安全性结论；请用 NCT ID 核对实时记录，并分别审阅 posted results、方案与关联论文。"
        )
    elif "human genetics and variant evidence" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "请先确认等位基因、转录本与组装版本；ClinVar、VEP 与 gnomAD 分属提交分类、计算注释和人群观察，不能直接合成为诊断结论。"
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

    variant = extract_variant_identifier(message)
    if variant and re.search(r"variant|mutation|clinvar|hgvs|变异|突变|位点", message, re.I):
        selected.append(("variant_evidence_preflight", {"variant": variant}))

    literature_query = extract_literature_query(message)
    if literature_query and re.search(r"paper|publication|literature|study|文献|论文|研究", message, re.I):
        start_year, end_year = extract_year_window(message)
        selected.append(
            (
                "literature_search_preview",
                {
                    "query": literature_query,
                    "start_year": start_year,
                    "end_year": end_year,
                    "max_results": 8,
                    "include_preprints": bool(re.search(r"preprint|bioRxiv|medRxiv|预印本", message, re.I)),
                    "require_abstract": True,
                },
            )
        )

    pubchem_query = extract_pubchem_query(message)
    if pubchem_query:
        selected.append(("database_lookup_pubchem", {"query": pubchem_query}))
    return selected


def local_workflow_plan(message: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Build a guided plan request without granting execution authority."""
    clinical_trials = extract_clinical_trial_plan(message)
    if clinical_trials:
        return "clinical-trial-landscape-review", clinical_trials
    variant = extract_variant_identifier(message)
    if variant and re.search(
        r"variant\s+(?:interpretation|review|evidence)|interpret\s+(?:the\s+)?variant|"
        r"pathogenic|population\s+frequency|clinvar|gnomad|vep|"
        r"变异(?:解释|审阅|证据)|解释.{0,12}(?:变异|突变)|致病|人群频率|临床意义",
        message,
        re.I,
    ):
        return "variant-evidence-review", {"variant": variant}
    target_review = extract_target_evidence_plan(message)
    if target_review:
        return "target-evidence-review", target_review
    literature_query = extract_literature_query(message)
    if literature_query and re.search(
        r"literature\s+(?:review|map)|evidence\s+review|systematic\s+search|文献(?:综述|审阅)|证据地图|系统检索|论文证据",
        message,
        re.I,
    ):
        start_year, end_year = extract_year_window(message)
        return "literature-evidence-review", {
            "query": literature_query,
            "start_year": start_year,
            "end_year": end_year,
            "max_results": 15,
            "include_preprints": bool(re.search(r"preprint|bioRxiv|medRxiv|预印本", message, re.I)),
            "require_abstract": True,
        }
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


def extract_clinical_trial_plan(message: str) -> dict[str, Any] | None:
    if not re.search(
        r"clinical\s+trials?(?:\s+(?:landscape|pipeline|progress|review))?|trial\s+landscape|"
        r"临床试验(?:版图|进展|布局|审阅|管线)?|临床开发版图",
        message,
        re.I,
    ):
        return None

    aliases = {
        "哮喘": "asthma",
        "乳腺癌": "breast cancer",
        "肺癌": "lung cancer",
        "阿尔茨海默病": "Alzheimer disease",
        "类风湿关节炎": "rheumatoid arthritis",
        "克罗恩病": "Crohn disease",
        "溃疡性结肠炎": "ulcerative colitis",
        "2型糖尿病": "type 2 diabetes mellitus",
        "二型糖尿病": "type 2 diabetes mellitus",
    }
    condition = ""
    intervention = ""

    labeled_condition = re.search(
        r"(?:condition|disease|indication|疾病|适应症)\s*[:：=]\s*([^,，;；.。]{1,100})",
        message,
        re.I,
    )
    labeled_intervention = re.search(
        r"(?:intervention|drug|therapy|干预|药物|疗法)\s*[:：=]\s*([^,，;；.。]{1,100})",
        message,
        re.I,
    )
    if labeled_condition:
        condition = labeled_condition.group(1).strip()
    if labeled_intervention:
        intervention = labeled_intervention.group(1).strip()

    if not condition:
        chinese_pair = re.search(
            r"([^，。；,;:：]{1,60}?)\s*在\s*([^，。；,;:：]{1,60}?)(?:中|中的)(?:的)?\s*临床试验",
            message,
        )
        if chinese_pair:
            intervention = intervention or _clean_trial_term(chinese_pair.group(1))
            condition = _clean_trial_term(chinese_pair.group(2))

    if not condition:
        english_pair = re.search(
            r"clinical\s+trials?(?:\s+(?:landscape|pipeline|progress|review))?\s+(?:for|of)\s+"
            r"(.{1,80}?)\s+in\s+(.{1,80}?)(?:[.,;]|$)",
            message,
            re.I,
        )
        if english_pair:
            intervention = intervention or _clean_trial_term(english_pair.group(1))
            condition = _clean_trial_term(english_pair.group(2))

    if not condition:
        chinese_condition = re.search(
            r"(?:在|针对)\s*([^，。；,;]{1,80}?)(?:中|中的|的)\s*(?:临床)?试验",
            message,
        )
        if chinese_condition:
            condition = _clean_trial_term(chinese_condition.group(1))

    if not condition:
        english_condition = re.search(
            r"clinical\s+trials?(?:\s+(?:landscape|pipeline|progress|review))?\s+(?:for|in|of)\s+"
            r"(.{1,100}?)(?:[.,;]|$)",
            message,
            re.I,
        )
        if english_condition:
            condition = _clean_trial_term(english_condition.group(1))

    condition = aliases.get(condition, condition)
    if not condition:
        return None
    status_scope = "all"
    if re.search(r"active|recruiting|not yet recruiting|正在招募|尚未招募|活跃", message, re.I):
        status_scope = "active"
    elif re.search(r"completed|complete studies|已完成|完成试验", message, re.I):
        status_scope = "completed"
    study_scope = "all" if re.search(r"observational|all studies|观察性|全部研究", message, re.I) else "interventional"
    return {
        "condition": condition,
        "intervention": intervention,
        "status_scope": status_scope,
        "study_scope": study_scope,
        "max_results": 20,
    }


def _clean_trial_term(value: str) -> str:
    cleaned = re.sub(
        r"^(?:(?:请|帮我|看看|梳理|整理|map|review|show|find)\s*)+",
        "",
        str(value or "").strip(),
        flags=re.I,
    )
    return cleaned.strip(" ：:,，。.;；")


def extract_variant_identifier(message: str) -> str:
    hgvs = re.search(
        r"\bN[CMPRG]_[0-9]+(?:\.[0-9]+)?(?:\([A-Za-z0-9_.-]+\))?:[cgmnpr]\.[A-Za-z0-9_*+?=><.-]+",
        message,
        re.I,
    )
    if hgvs:
        return hgvs.group(0)
    accession = re.search(r"\bVCV\d{1,12}(?:\.\d+)?\b", message, re.I)
    if accession:
        return accession.group(0).upper()
    rsid = re.search(r"\brs\d{1,12}\b", message, re.I)
    if rsid:
        return rsid.group(0).lower()
    variation_id = re.search(
        r"(?:ClinVar\s+)?(?:Variation\s+ID|变异编号)\s*[:：#]?\s*(\d{1,12})\b",
        message,
        re.I,
    )
    return variation_id.group(1) if variation_id else ""


def extract_target_evidence_plan(message: str) -> dict[str, Any] | None:
    if not re.search(
        r"target\s+(?:evidence|prioriti[sz]ation)|disease\s+association|靶点(?:证据|优先|比较)|疾病关联",
        message,
        re.I,
    ):
        return None
    disease = ""
    patterns = [
        r"(?:在|针对)\s*([^，。；,;]{1,80}?)(?:中|中的|进行|做)?\s*(?:的)?靶点",
        r"(?:disease|indication)\s*[:：=]\s*([A-Za-z][A-Za-z0-9 _.-]{0,79})",
        r"\bfor\s+([A-Za-z][A-Za-z0-9 _.-]{0,79}?)\s+target\s+(?:evidence|prioriti[sz]ation)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.I)
        if match:
            disease = match.group(1).strip(" .")
            break
    if not disease:
        return None

    candidate_segment = message
    marker = re.search(r"(?:在|针对)\s*" + re.escape(disease), message, re.I)
    if marker:
        candidate_segment = message[: marker.start()]
    elif re.search(r"\bfor\s+" + re.escape(disease), message, re.I):
        candidate_segment = re.split(r"\bfor\s+" + re.escape(disease), message, maxsplit=1, flags=re.I)[0]
    tokens = re.findall(r"\b(?:ENSG\d{11}|[A-Za-z][A-Za-z0-9.-]{1,31})\b", candidate_segment)
    ignored = {
        "and", "compare", "comparison", "evidence", "for", "prioritize", "prioritization",
        "review", "target", "targets", "versus", "vs",
    }
    candidates = []
    for token in tokens:
        if token.casefold() in ignored:
            continue
        if not (token.upper().startswith("ENSG") or any(char.isdigit() for char in token) or token.isupper()):
            continue
        normalized = token.upper()
        if normalized not in candidates:
            candidates.append(normalized)
    if not candidates or len(candidates) > 8:
        return None
    return {
        "disease": disease,
        "candidates": ", ".join(candidates),
        "include_indirect": bool(re.search(r"indirect|descendant|下位疾病|间接证据", message, re.I)),
    }


def extract_literature_query(message: str) -> str:
    if not re.search(r"paper|publication|literature|study|evidence\s+review|文献|论文|研究|证据地图", message, re.I):
        return ""
    quoted = re.search(r"[\"']([^\"']{2,300})[\"']|“([^”]{2,300})”|‘([^’]{2,300})’", message)
    if quoted:
        quoted_value = next((value for value in quoted.groups() if value), "")
        if re.search(r"[A-Za-z]", quoted_value):
            return quoted_value.strip()

    aliases = {
        "哮喘": "asthma",
        "乳腺癌": "breast cancer",
        "肺癌": "lung cancer",
        "阿尔茨海默病": "Alzheimer disease",
        "类风湿关节炎": "rheumatoid arthritis",
        "克罗恩病": "Crohn disease",
        "溃疡性结肠炎": "ulcerative colitis",
        "2型糖尿病": "type 2 diabetes mellitus",
        "二型糖尿病": "type 2 diabetes mellitus",
    }
    disease = ""
    chinese = re.search(r"(?:在|针对)\s*([^，。；,;]{1,60}?)(?:中|中的)(?:文献|论文|研究|证据)", message)
    if chinese:
        disease = aliases.get(chinese.group(1).strip(), "")
    if not disease:
        english = re.search(
            r"\bin\s+([A-Za-z][A-Za-z -]{1,60}?)(?:\s+(?:literature|papers?|studies|evidence|from|since|between)|[.,;]|$)",
            message,
            re.I,
        )
        if english:
            disease = english.group(1).strip()

    ignored = {
        "AND", "ABOUT", "EVIDENCE", "FIND", "FOR", "IN", "LITERATURE", "MAP", "OR",
        "PAPER", "PAPERS", "PUBLICATION", "PUBLICATIONS", "REVIEW", "STUDIES", "STUDY",
    }
    symbols = []
    for token in re.findall(r"\b[A-Z][A-Z0-9.-]{1,20}\b", message):
        if token in ignored or re.fullmatch(r"(?:19|20)\d{2}", token):
            continue
        if token not in symbols:
            symbols.append(token)
    if symbols and disease:
        target_clause = symbols[0] if len(symbols) == 1 else f"({' OR '.join(symbols)})"
        return f"{target_clause} AND {disease}"

    english_topic = re.search(
        r"(?:papers?|publications?|literature|studies)\s+(?:about|on|for)\s+(.{2,240}?)(?:\s+(?:since|between|from)\s+(?:19|20)\d{2}|[。;]|$)",
        message,
        re.I,
    )
    if english_topic and re.search(r"[A-Za-z]", english_topic.group(1)):
        return english_topic.group(1).strip(" .")
    return ""


def extract_year_window(message: str) -> tuple[int | None, int | None]:
    years = [int(value) for value in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", message)]
    if len(years) >= 2:
        return min(years[0], years[1]), max(years[0], years[1])
    if years and re.search(r"since|from|自|以来|起", message, re.I):
        return years[0], None
    return None, None


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
