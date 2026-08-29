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
Keep the user's biological question as the main line. Use the smallest useful set of tools, distinguish computed results from hypotheses, and cite tool names when they materially support a claim. Do not invent tool results. Literature claims must cite PMID, PMCID, DOI, or a source URL returned by a tool; distinguish abstract-reported findings from independent validation, and never treat relevance order or citation counts as study quality. For ChEMBL bioactivity, preserve the exact UniProt and ChEMBL target, pChEMBL, endpoint, relation, value, unit, assay type and format, confidence score, document, filters, and retrieval bounds. Confidence score 9 supports direct single-protein target assignment but does not prove direct physical binding or assay quality; mixed IC50, Ki, Kd, EC50 and assay contexts are not interchangeable, and potency does not establish selectivity, mechanism, developability, safety, or efficacy. For clinical trials, cite NCT IDs and official links, distinguish registry status and registered endpoints from posted results and publications, and never infer efficacy, safety, or failure from registry metadata or missing results. For human variants, preserve the exact allele, transcript, assembly, phenotype, and inheritance context; distinguish ClinVar submitted classifications, VEP computational annotations, and gnomAD population observations, and never invent a pathogenicity or ACMG/AMP score. Variant evidence is not a diagnosis or treatment recommendation. For cohort VCFs, preserve sample and subject identity, coordinate, REF/ALT, FILTER, depth, VAF, annotation source, threshold exclusions, and upstream caller limitations; never equate VAF with tumor fraction or infer somatic status, drivers, response, treatment, or clinical actionability. For HMMER profile searches, preserve profile and target identity, search-space-dependent E-values, scores, bias, profile and target coordinates, domain count, thresholds, and database version context; a profile match does not by itself prove function, mechanism, activity, localization, or phenotype. For single-cell analyses, preserve the input format, selected raw-count layer, QC thresholds, retained cells and genes, normalization, feature selection, random seed, graph and clustering parameters, biological sample metadata, and any Scrublet batch key, thresholds, prediction count, and exclusion decision. UMAP geometry, Leiden clusters, Scrublet predictions, and cell-level marker rankings are exploratory; never name a cell type without external annotation evidence or treat cells as biological replicates. For gene-set functional analysis, preserve organism, exact inputs and mappings, reference coverage, FDR threshold, database versions, STRING confidence threshold, and unmapped identifiers. Reactome overrepresentation is not causal evidence, FDR is not a truth probability, STRING functional associations are not necessarily direct physical interactions, and genes are not biological replicates. Local workspace files may be read only through registered tools. Multi-step workflows must remain pending until the researcher explicitly approves them in the local WorkBench; never claim that a proposed plan has executed. Return a concise answer in the user's language with: working conclusion, supporting evidence, caveats, and the next useful analysis. Molecular or protein design suggestions are hypotheses that require experimental validation."""


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
        "target-ligand bioactivity": "靶点-配体活性",
        "transcriptomics and expression": "转录组与表达",
        "single-cell transcriptomics": "单细胞转录组",
        "pathway and network biology": "通路与功能网络",
        "sequence similarity search": "序列相似性搜索",
        "protein structure and sequence": "蛋白结构与序列",
        "protein family and domain analysis": "蛋白家族与结构域",
        "molecular chemistry": "分子化学",
        "literature and study discovery": "文献与研究发现",
        "human genetics and variant evidence": "人类遗传与变异证据",
        "clinical and translational evidence": "临床与转化证据",
        "sequencing and cohort variants": "测序与队列变异",
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
    elif "sequencing and cohort variants" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "VCF 调用依赖上游 caller、FILTER、测序深度和 assay 误差模型；VAF 不是肿瘤比例或疗效指标，低频信号需要结合 LOD 与 read-level 证据复核。"
        )
    elif "single-cell transcriptomics" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "UMAP、Leiden cluster 与按细胞计算的 marker 排名都是探索性结果；细胞不是生物学重复，细胞类型命名和组间推断仍需样本信息、外部 marker 证据与 pseudobulk 复核。"
        )
    elif "pathway and network biology" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "Reactome 富集依赖输入列表与参考覆盖；STRING 边是功能关联而非必然的直接物理互作。请在审批前核对物种、标识符映射、FDR 与网络置信阈值。"
        )
    elif "protein family and domain analysis" in raw_lanes:
        reply = (
            f"当前问题被路由到 {lane}。{evidence_text} "
            "HMMER 命中需要结合 profile 来源、搜索空间、E-value、覆盖度、bias 和结构域架构解释；单个 profile match 不等同于功能证明。"
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
    nct_id = extract_nct_id(message)
    if nct_id and re.search(
        r"clinical\s+trial|trial\s+result|posted\s+result|outcome|adverse\s+event|"
        r"临床试验|试验结果|结果审阅|结局|不良事件|安全性结果",
        message,
        re.I,
    ):
        selected.append(("clinical_trial_results_preflight", {"nct_id": nct_id}))
    pdb = re.search(r"(?:pdb|rcsb|structure|结构)\s*(?:id|编号|条目)?\s*[:：#-]?\s*([0-9][a-z0-9]{3})\b", message, re.I)
    if pdb:
        selected.append(("structure_fetch_pdb", {"pdb_id": pdb.group(1).upper()}))

    alphafold_accession = extract_alphafold_accession(message)
    if alphafold_accession:
        selected.append(("structure_fetch_alphafold", {"accession": alphafold_accession}))

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


def extract_strict_uniprot_accession(message: str) -> str | None:
    pattern = (
        r"\b((?:[OPQ][0-9][A-Z0-9]{3}[0-9]|"
        r"[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9]|"
        r"[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){2})(?:-\d+)?)\b"
    )
    match = re.search(pattern, str(message or "").upper())
    return match.group(1) if match else None


def extract_alphafold_accession(message: str) -> str | None:
    if not re.search(r"alphafold|pLDDT|predicted structure|预测结构|结构预测|预测蛋白", message, re.I):
        return None
    return extract_strict_uniprot_accession(message)


def extract_chembl_bioactivity_plan(message: str) -> dict[str, Any] | None:
    if not re.search(
        r"chembl|pchembl|bioactivit|potency|\bic50\b|\bki\b|\bkd\b|\bec50\b|"
        r"靶点.{0,10}(?:小分子|配体|活性)|(?:小分子|配体).{0,10}靶点|活性证据",
        message,
        re.I,
    ):
        return None
    accession = extract_strict_uniprot_accession(message)
    if not accession:
        return None
    has_binding = bool(re.search(r"\bbinding\b|结合", message, re.I))
    has_functional = bool(re.search(r"\bfunctional\b|功能(?:性)?(?:测定|实验|活性)?", message, re.I))
    assay_scope = (
        "binding_functional"
        if has_binding == has_functional
        else ("binding" if has_binding else "functional")
    )
    threshold_match = re.search(
        r"pchembl\s*(?:>=|=>|≥|大于等于|至少|不低于)?\s*([0-9]+(?:\.[0-9]+)?)",
        message,
        re.I,
    )
    max_match = re.search(
        r"(?:top|前|最多|保留)\s*([0-9]{1,3})\s*(?:条|个|records?|activities?|活性)?",
        message,
        re.I,
    )
    return {
        "accession": accession,
        "assay_scope": assay_scope,
        "min_pchembl": float(threshold_match.group(1)) if threshold_match else 5.0,
        "max_activities": int(max_match.group(1)) if max_match else 50,
    }


def local_workflow_plan(message: str, context: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    """Build a guided plan request without granting execution authority."""
    single_cell = extract_single_cell_plan(message)
    if single_cell:
        return "single-cell-exploratory-analysis", single_cell
    functional_analysis = extract_functional_analysis_plan(message)
    if functional_analysis:
        return "gene-set-functional-analysis", functional_analysis
    chembl_bioactivity = extract_chembl_bioactivity_plan(message)
    if chembl_bioactivity:
        return "target-ligand-bioactivity-review", chembl_bioactivity
    hmmer_search = extract_hmmer_profile_plan(message)
    if hmmer_search:
        return "hmmer-profile-search", hmmer_search
    vcf_cohort = extract_vcf_cohort_plan(message)
    if vcf_cohort:
        return "vcf-cohort-review", vcf_cohort
    clinical_results = extract_clinical_results_plan(message)
    if clinical_results:
        return "clinical-trial-results-review", clinical_results
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

    alphafold_accession = extract_alphafold_accession(message)
    if alphafold_accession:
        return "protein-structure-review", {
            "source": "alphafold",
            "uniprot_accession": alphafold_accession,
        }

    sample_type = str(context.get("type") or "")
    if sample_type == "molecule" and context.get("smiles"):
        return "molecule-profile", {"smiles": context["smiles"]}
    if sample_type == "protein" and context.get("pdb_id"):
        return "protein-structure-review", {"source": "rcsb", "pdb_id": context["pdb_id"]}
    if sample_type == "protein" and context.get("metadata", {}).get("coordinateType") == "predicted":
        return "protein-structure-review", {
            "source": "alphafold",
            "uniprot_accession": context.get("metadata", {}).get("accession", ""),
        }
    if sample_type == "protein" and context.get("sequence"):
        return "protein-sequence-review", {"sequence": context["sequence"]}
    return None


def extract_single_cell_plan(message: str) -> dict[str, Any] | None:
    paths = re.findall(
        r"([\w./-]+(?:matrix\.mtx(?:\.gz)?|\.(?:h5ad|hdf5|h5|csv|tsv)))\b",
        message,
        re.I,
    )
    if not paths or not re.search(
        r"single[- ]?cell|scRNA-?seq|single cell RNA|单细胞|单细胞转录组|细胞聚类|Leiden|UMAP",
        message,
        re.I,
    ):
        return None
    count_path = next((path for path in paths if not re.search(r"meta|annot|metadata|注释", path, re.I)), paths[0])
    table_paths = [path for path in paths if re.search(r"\.(?:csv|tsv)$", path, re.I)]
    metadata_path = next(
        (path for path in table_paths if path != count_path and re.search(r"meta|annot|cell|样本|注释", path, re.I)),
        next((path for path in table_paths if path != count_path), ""),
    )

    def number(pattern: str, default: float) -> float:
        match = re.search(r"(?:" + pattern + r")\s*[:：=]?\s*([0-9.]+)", message, re.I)
        return float(match.group(1)) if match else default

    count_layer = re.search(r"(?:count|raw)[_ -]?layer\s*[:：=]?\s*([\w.-]+)|(?:计数|原始)层\s*[:：=]?\s*([\w.-]+)", message, re.I)
    batch_key = re.search(r"(?:doublet[_ -]?)?batch(?:[_ -]?key|\s*列)?\s*[:：=]?\s*([\w.-]+)|Scrublet\s*批次(?:字段|列)?\s*[:：=]?\s*([\w.-]+)", message, re.I)
    run_scrublet = bool(re.search(r"Scrublet|doublet|双细胞", message, re.I))
    keep_doublets = bool(
        re.search(r"(?:不|不要)(?:予以)?(?:排除|删除|过滤)|(?:保留|仅标记|只标记)[^。,.]{0,16}(?:doublet|双细胞)", message, re.I)
    )
    exclude_doublets = not keep_doublets and bool(
        re.search(r"(?:exclude|remove|filter|排除|删除|过滤)[^。,.]{0,16}(?:doublet|双细胞)", message, re.I)
    )
    return {
        "count_matrix_path": count_path,
        "metadata_path": metadata_path,
        "cell_id_column": "cell_id",
        "count_layer": next((value for value in (count_layer.groups() if count_layer else []) if value), ""),
        "min_genes": int(number(r"min[_ -]?genes|每细胞最少(?:检测)?基因", 20)),
        "min_cells": int(number(r"min[_ -]?cells|每基因最少(?:检测)?细胞", 3)),
        "max_mito_percent": number(r"max(?:imum)?[_ -]?(?:mt|mito)(?:[_ -]?percent)?|线粒体(?:比例|计数)?上限", 20),
        "n_top_genes": int(number(r"n[_ -]?top[_ -]?genes|高变基因(?:数)?", 2000)),
        "n_neighbors": int(number(r"n[_ -]?neighbors|邻居数", 15)),
        "leiden_resolution": number(r"(?:leiden[_ -]?)?resolution|分辨率", 1),
        "marker_genes": int(number(r"marker[_ -]?genes|每群 marker(?: 数)?", 10)),
        "run_scrublet": run_scrublet,
        "doublet_batch_key": next((value for value in (batch_key.groups() if batch_key else []) if value), ""),
        "expected_doublet_rate": number(r"expected[_ -]?doublet[_ -]?rate|预期双细胞率|预期 doublet rate", 0.05),
        "exclude_predicted_doublets": exclude_doublets,
    }


def extract_hmmer_profile_plan(message: str) -> dict[str, Any] | None:
    hmm = re.search(r"([\w./-]+\.hmm)\b", message, re.I)
    database = re.search(r"([\w./-]+\.(?:fa|fasta|faa))\b", message, re.I)
    if not hmm or not database or not re.search(
        r"\bhmm(?:er|search)?\b|profile\s+hmm|protein\s+(?:family|domain)|"
        r"结构域|蛋白家族|隐马尔可夫",
        message,
        re.I,
    ):
        return None
    domain_evalue = re.search(
        r"(?:domain\s+e-?value|domE|结构域\s*e-?value)\s*[:：=]?\s*([0-9.eE+-]+)",
        message,
        re.I,
    )
    sequence_evalue = re.search(
        r"(?<!domain\s)(?<!结构域)(?:sequence\s+)?e-?value(?:\s*(?:threshold|cutoff|阈值))?\s*[:：=]?\s*([0-9.eE+-]+)",
        message,
        re.I,
    )
    max_hits = re.search(
        r"(?:max(?:imum)?\s+hits?|最多(?:命中)?)\s*[:：=]?\s*(\d+)",
        message,
        re.I,
    )
    try:
        sequence_threshold = float(sequence_evalue.group(1)) if sequence_evalue else 1e-5
        domain_threshold = float(domain_evalue.group(1)) if domain_evalue else sequence_threshold
    except ValueError:
        return None
    return {
        "hmm_path": hmm.group(1),
        "database_path": database.group(1),
        "evalue": sequence_threshold,
        "domain_evalue": domain_threshold,
        "max_hits": int(max_hits.group(1)) if max_hits else 25,
        "threads": 1,
    }


def extract_vcf_cohort_plan(message: str) -> dict[str, Any] | None:
    vcf = re.search(r"([\w./-]+\.vcf)\b", message, re.I)
    if not vcf or not re.search(
        r"\bvcf\b|ctdna|liquid\s+biopsy|variant\s+(?:landscape|cohort|trajectory|review)|"
        r"变异(?:景观|队列|轨迹|审阅)|样本轨迹|液体活检|低频(?:变异|调用|信号)",
        message,
        re.I,
    ):
        return None
    metadata_paths = re.findall(r"([\w./-]+\.(?:csv|tsv))\b", message, re.I)
    metadata_path = next(
        (path for path in metadata_paths if re.search(r"meta|sample|clinical|样本|信息", path, re.I)),
        metadata_paths[0] if metadata_paths else "",
    )
    vaf_match = re.search(
        r"(?:min(?:imum)?\s*vaf|vaf\s*(?:threshold|cutoff)|最小\s*vaf|vaf\s*阈值)\s*[:：=]?\s*(0(?:\.\d+)?|1(?:\.0+)?)",
        message,
        re.I,
    )
    depth_match = re.search(
        r"(?:min(?:imum)?\s*(?:depth|dp)|最小(?:深度|dp)|深度阈值)\s*[:：=]?\s*(\d+)",
        message,
        re.I,
    )
    return {
        "vcf_path": vcf.group(1),
        "metadata_path": metadata_path,
        "sample_column": "sample",
        "subject_column": "subject",
        "timepoint_column": "timepoint",
        "time_order_column": "time_order",
        "min_vaf": float(vaf_match.group(1)) if vaf_match else 0.01,
        "min_depth": int(depth_match.group(1)) if depth_match else 10,
        "include_filtered": bool(
            re.search(r"include\s+(?:non-pass|filtered)|包含(?:非\s*pass|过滤记录)", message, re.I)
        ),
    }


def extract_nct_id(message: str) -> str:
    match = re.search(r"\bNCT\d{8}\b", str(message or ""), re.I)
    return match.group(0).upper() if match else ""


def extract_clinical_results_plan(message: str) -> dict[str, Any] | None:
    nct_id = extract_nct_id(message)
    if not nct_id or not re.search(
        r"posted\s+results?|trial\s+results?|result\s+tables?|outcomes?|adverse\s+events?|"
        r"results?\s+review|试验结果|结果审阅|结果表|结局|不良事件|安全性结果",
        message,
        re.I,
    ):
        return None
    return {"nct_id": nct_id}


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


def extract_functional_analysis_plan(message: str) -> dict[str, Any] | None:
    if not re.search(
        r"reactome|string(?:-db)?|pathway\s+(?:enrichment|overrepresentation)|"
        r"functional\s+enrichment|protein\s+(?:association|interaction)\s+network|"
        r"\bppi\b|gene\s*set|基因集|通路(?:富集|过表达)|功能富集|蛋白(?:功能|互作)网络|互作网络",
        message,
        re.I,
    ):
        return None
    ignored = {
        "ANALYSIS", "ASSOCIATION", "ENRICHMENT", "FDR", "FUNCTIONAL", "GENE", "GENES",
        "NETWORK", "PATHWAY", "PPI", "PROTEIN", "PROTEINS", "REACTOME", "REVIEW", "STRING",
    }
    tokens = re.findall(r"\b(?:ENSG\d{11}|[A-Z][A-Z0-9_.:-]{1,63})\b", message)
    genes = []
    for token in tokens:
        normalized = token.upper()
        if normalized in ignored or normalized in genes:
            continue
        genes.append(normalized)
    if len(genes) < 2 or len(genes) > 50:
        return None

    score_match = re.search(
        r"(?:required[_ -]?score|string(?:\s+confidence)?|置信(?:分|阈值))\s*[:：=]?\s*(\d{3})",
        message,
        re.I,
    )
    fdr_match = re.search(r"\bfdr(?:\s*(?:threshold|cutoff|阈值))?\s*[:：=]?\s*(0?\.\d+)", message, re.I)
    max_terms_match = re.search(
        r"(?:max(?:imum)?\s+terms?|top\s+terms?|最多(?:展示)?条目)\s*[:：=]?\s*(\d+)",
        message,
        re.I,
    )
    return {
        "genes": ", ".join(genes),
        "required_score": int(score_match.group(1)) if score_match else 400,
        "fdr_threshold": float(fdr_match.group(1)) if fdr_match else 0.05,
        "max_terms": int(max_terms_match.group(1)) if max_terms_match else 20,
        "include_disease_pathways": bool(
            re.search(r"include\s+disease\s+pathways|包含疾病通路", message, re.I)
        ),
    }


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
