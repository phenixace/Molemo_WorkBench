"""Researcher-approved workflow plans built from registered scientific tools."""

from __future__ import annotations

import copy
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from transcriptomics import TranscriptomicsError, preflight_bulk_rnaseq
from target_evidence import TargetEvidenceError, resolve_target_review_inputs
from literature_review import LiteratureReviewError, preflight_literature_review
from variant_evidence import VariantEvidenceError, preflight_variant_evidence
from clinical_trials import ClinicalTrialsError, preflight_clinical_trial_landscape


ROOT = Path(__file__).resolve().parent
DEFAULT_STORAGE_ROOT = Path(
    os.environ.get("MOLEMO_WORKFLOW_STORAGE_ROOT") or ROOT / "workspace" / ".molemo" / "runs"
)


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
    "bulk-rnaseq-differential-expression": {
        "title": "Bulk RNA-seq 差异表达",
        "description": "预检 raw count matrix 与样本设计，批准后用 PyDESeq2 执行差异表达。",
        "fields": [
            _field(
                "count_matrix_path",
                "Raw count matrix",
                "text",
                required=True,
                placeholder="examples/rnaseq_counts.csv",
            ),
            _field(
                "metadata_path",
                "Sample metadata",
                "text",
                required=True,
                placeholder="examples/rnaseq_metadata.csv",
            ),
            _field("sample_column", "样本列", "text", value="sample"),
            _field("condition_column", "条件列", "text", value="condition"),
            _field("test_level", "Test level", "text", required=True, value="treated"),
            _field("reference_level", "Reference level", "text", required=True, value="control"),
            _field("batch_column", "批次列（可选）", "text", value=""),
            _field("min_total_count", "最小基因总计数", "number", value=10, min=1),
            _field("fdr_threshold", "FDR 阈值", "text", value="0.05"),
            _field("lfc_threshold", "|log2 fold change| 阈值", "number", value=1.0, min=0, max=20, step=0.1),
        ],
        "assumptions": [
            "输入是基因级非负整数 raw counts，不是 TPM、CPM 或 log expression。",
            "样本 metadata 代表生物学重复，contrast 方向已经由研究者确认。",
            "差异表达是关联性证据，需要结合实验设计与生物学验证。",
        ],
    },
    "target-evidence-review": {
        "title": "靶点证据比较",
        "description": "解析疾病与候选靶点，批准后比较 Open Targets 遗传、临床、表达与文献证据。",
        "fields": [
            _field("disease", "疾病名称 / ontology ID", "text", required=True, placeholder="asthma"),
            _field(
                "candidates",
                "候选靶点（最多 8 个）",
                "textarea",
                required=True,
                rows=4,
                placeholder="IL4R, TSLP, IL6R, JAK1",
            ),
            _field(
                "include_indirect",
                "证据范围",
                "select",
                required=True,
                options=[
                    {"value": "false", "label": "仅当前疾病"},
                    {"value": "true", "label": "包含 ontology descendants"},
                ],
            ),
        ],
        "assumptions": [
            "Open Targets association score 仅用于证据排序，不是概率、置信度或因果结论。",
            "候选靶点按解析后的 Ensembl Gene ID 确认；同名或模糊实体应在审批前检查。",
            "临床先例、可成药性与安全注释需要结合适应症和实验验证解释。",
        ],
    },
    "literature-evidence-review": {
        "title": "文献证据审阅",
        "description": "用明确检索式收集 Europe PMC 论文元数据与摘要，形成可追溯 evidence map。",
        "fields": [
            _field(
                "query",
                "Europe PMC 检索式",
                "textarea",
                required=True,
                rows=4,
                placeholder="(IL4R OR TSLP) AND asthma",
            ),
            _field("start_year", "起始年份（可选）", "number", value=2020, min=1900),
            _field("end_year", "结束年份（可选）", "number", value=datetime.now(timezone.utc).year, min=1900),
            _field("max_results", "最多收集论文", "number", value=15, min=1, max=25),
            _field(
                "include_preprints",
                "预印本",
                "select",
                required=True,
                options=[
                    {"value": "false", "label": "排除预印本"},
                    {"value": "true", "label": "包含预印本"},
                ],
            ),
            _field(
                "require_abstract",
                "摘要",
                "select",
                required=True,
                options=[
                    {"value": "true", "label": "仅保留有摘要记录"},
                    {"value": "false", "label": "允许无摘要记录"},
                ],
            ),
        ],
        "assumptions": [
            "Europe PMC relevance 仅表示检索排序，不代表研究质量或证据确定性。",
            "当前 evidence map 基于元数据与摘要，不等同于全文系统综述或风险偏倚评价。",
            "引用次数仅作书目信息展示，不参与排序或证据评级。",
        ],
    },
    "variant-evidence-review": {
        "title": "人类变异证据审阅",
        "description": "解析单个简单变异，批准后整理 ClinVar、Ensembl VEP 与 gnomAD v4 证据。",
        "fields": [
            _field(
                "variant",
                "RefSeq HGVS / rsID / ClinVar ID",
                "text",
                required=True,
                placeholder="NM_000518.5:c.20A>T",
            ),
        ],
        "assumptions": [
            "审批前必须确认具体等位基因、转录本与基因组版本；rsID 可能对应多个等位基因。",
            "ClinVar 分类是提交者断言，VEP 是计算注释，gnomAD 是人群观察，三者不合成为自定义致病性分数。",
            "结果不是诊断、治疗建议或新的 ACMG/AMP 临床分类。",
        ],
    },
    "clinical-trial-landscape-review": {
        "title": "临床试验版图",
        "description": "用明确疾病、干预与状态过滤检索 ClinicalTrials.gov，形成可追溯的转化证据版图。",
        "fields": [
            _field("condition", "疾病 / 条件", "text", required=True, placeholder="asthma"),
            _field("intervention", "干预（可选）", "text", placeholder="dupilumab"),
            _field(
                "status_scope",
                "试验状态",
                "select",
                required=True,
                options=[
                    {"value": "all", "label": "全部状态"},
                    {"value": "active", "label": "活跃 / 招募相关"},
                    {"value": "completed", "label": "已完成"},
                ],
            ),
            _field(
                "study_scope",
                "研究类型",
                "select",
                required=True,
                options=[
                    {"value": "interventional", "label": "干预性研究"},
                    {"value": "all", "label": "全部研究"},
                ],
            ),
            _field("max_results", "最多收集试验", "number", value=20, min=1, max=30),
        ],
        "assumptions": [
            "ClinicalTrials.gov 登记信息描述研究计划和状态，不直接证明疗效或安全性。",
            "总体状态不等于每个研究中心的实时招募状态；采取行动前应检查最新官方记录。",
            "登记终点不是结果值；posted results、方案、统计分析和关联论文需要分别审阅。",
        ],
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
    "sequence-similarity-search": {
        "title": "本地序列相似性搜索",
        "description": "用 NCBI BLAST+ 在 workspace FASTA 数据库中检索相似蛋白或核酸序列。",
        "fields": [
            _field("query", "Query FASTA / sequence", "textarea", required=True, rows=6),
            _field(
                "database_path",
                "Workspace FASTA 数据库",
                "text",
                required=True,
                placeholder="examples/homologs.faa",
            ),
            _field(
                "program",
                "搜索程序",
                "select",
                required=True,
                options=[
                    {"value": "blastp", "label": "BLASTP · protein"},
                    {"value": "blastn", "label": "BLASTN · nucleotide"},
                ],
            ),
            _field("evalue", "E-value 阈值", "text", value="1e-5"),
            _field("max_hits", "最多命中", "number", value=10, min=1, max=100),
        ],
        "assumptions": [
            "输入数据库是与所选程序匹配的 workspace FASTA 文件。",
            "序列相似性支持相关性判断，但不单独证明功能或活性。",
        ],
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


def _rnaseq_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    count_matrix_path = _require_text(inputs, "count_matrix_path", "Raw count matrix")
    metadata_path = _require_text(inputs, "metadata_path", "Sample metadata")
    sample_column = str(inputs.get("sample_column") or "sample").strip()
    condition_column = str(inputs.get("condition_column") or "condition").strip()
    test_level = _require_text(inputs, "test_level", "Test level")
    reference_level = _require_text(inputs, "reference_level", "Reference level")
    batch_column = str(inputs.get("batch_column") or "").strip()
    try:
        min_total_count = int(inputs.get("min_total_count", 10))
        fdr_threshold = float(inputs.get("fdr_threshold", 0.05))
        lfc_threshold = float(inputs.get("lfc_threshold", 1.0))
    except (TypeError, ValueError) as exc:
        raise WorkflowError("RNA-seq thresholds must be numeric.", "invalid_workflow_inputs") from exc
    if min_total_count < 1:
        raise WorkflowError("min_total_count must be at least 1.", "invalid_workflow_inputs")
    if not 0 < fdr_threshold <= 1:
        raise WorkflowError("fdr_threshold must be greater than 0 and at most 1.", "invalid_workflow_inputs")
    if not 0 <= lfc_threshold <= 20:
        raise WorkflowError("lfc_threshold must be between 0 and 20.", "invalid_workflow_inputs")
    arguments = {
        "count_matrix_path": count_matrix_path,
        "metadata_path": metadata_path,
        "sample_column": sample_column,
        "condition_column": condition_column,
        "test_level": test_level,
        "reference_level": reference_level,
        "batch_column": batch_column,
        "min_total_count": min_total_count,
        "fdr_threshold": fdr_threshold,
        "lfc_threshold": lfc_threshold,
    }
    inputs.update(arguments)
    return [_step("拟合 PyDESeq2 模型并生成可检查结果", "transcriptomics_run_de", arguments)]


def _rnaseq_preflight(inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return preflight_bulk_rnaseq(
            count_matrix_path=inputs["count_matrix_path"],
            metadata_path=inputs["metadata_path"],
            sample_column=inputs["sample_column"],
            condition_column=inputs["condition_column"],
            test_level=inputs["test_level"],
            reference_level=inputs["reference_level"],
            batch_column=inputs["batch_column"],
            min_total_count=inputs["min_total_count"],
        )
    except TranscriptomicsError as exc:
        raise WorkflowError(str(exc), "workflow_preflight_failed") from exc


def _target_evidence_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    disease = _require_text(inputs, "disease", "Disease")
    candidates = _require_text(inputs, "candidates", "Candidate targets")
    raw_indirect = inputs.get("include_indirect", False)
    include_indirect = raw_indirect is True or str(raw_indirect).strip().lower() in {"1", "true", "yes"}
    inputs.update(
        {"disease": disease, "candidates": candidates, "include_indirect": include_indirect}
    )
    return [
        _step(
            "检索并整理候选靶点证据",
            "target_evidence_compare",
            {
                "disease": disease,
                "candidates": candidates,
                "include_indirect": include_indirect,
            },
        )
    ]


def _target_evidence_preflight(inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return resolve_target_review_inputs(
            disease=inputs["disease"],
            candidates=inputs["candidates"],
            include_indirect=inputs["include_indirect"],
        )
    except TargetEvidenceError as exc:
        raise WorkflowError(str(exc), "workflow_preflight_failed") from exc


def _literature_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    query = _require_text(inputs, "query", "Literature query")
    try:
        start_year = int(inputs["start_year"]) if str(inputs.get("start_year") or "").strip() else None
        end_year = int(inputs["end_year"]) if str(inputs.get("end_year") or "").strip() else None
        max_results = int(inputs.get("max_results") or 15)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("Literature years and result limit must be integers.", "invalid_workflow_inputs") from exc
    include_preprints = _workflow_boolean(inputs.get("include_preprints", False))
    require_abstract = _workflow_boolean(inputs.get("require_abstract", True))
    arguments = {
        "query": query,
        "start_year": start_year,
        "end_year": end_year,
        "max_results": max_results,
        "include_preprints": include_preprints,
        "require_abstract": require_abstract,
    }
    inputs.update(arguments)
    return [_step("收集并整理文献证据地图", "literature_review_collect", arguments)]


def _literature_preflight(inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return preflight_literature_review(**inputs)
    except LiteratureReviewError as exc:
        raise WorkflowError(str(exc), "workflow_preflight_failed") from exc


def _variant_evidence_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    variant = _require_text(inputs, "variant", "Variant identifier")
    inputs["variant"] = variant
    return [
        _step(
            "整理 ClinVar、VEP 与 gnomAD 变异证据",
            "variant_evidence_review",
            {"variant": variant},
        )
    ]


def _variant_evidence_preflight(inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return preflight_variant_evidence(inputs["variant"])
    except VariantEvidenceError as exc:
        raise WorkflowError(str(exc), "workflow_preflight_failed") from exc


def _clinical_trials_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    condition = _require_text(inputs, "condition", "Condition")
    intervention = str(inputs.get("intervention") or "").strip()
    status_scope = str(inputs.get("status_scope") or "all").strip().casefold()
    study_scope = str(inputs.get("study_scope") or "interventional").strip().casefold()
    try:
        max_results = int(inputs.get("max_results") or 20)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("Clinical trial result limit must be an integer.", "invalid_workflow_inputs") from exc
    arguments = {
        "condition": condition,
        "intervention": intervention,
        "status_scope": status_scope,
        "study_scope": study_scope,
        "max_results": max_results,
    }
    inputs.update(arguments)
    return [_step("收集并整理临床试验版图", "clinical_trials_collect", arguments)]


def _clinical_trials_preflight(inputs: dict[str, Any]) -> dict[str, Any]:
    try:
        return preflight_clinical_trial_landscape(**inputs)
    except ClinicalTrialsError as exc:
        raise WorkflowError(str(exc), "workflow_preflight_failed") from exc


def _workflow_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y"}


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


def _sequence_search_steps(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    query = _require_text(inputs, "query", "Query sequence")
    database_path = _require_text(inputs, "database_path", "Workspace FASTA database")
    program = str(inputs.get("program") or "blastp").strip().lower()
    if program not in {"blastp", "blastn"}:
        raise WorkflowError("program must be blastp or blastn.", "invalid_workflow_inputs")
    raw_evalue = inputs.get("evalue", 1e-5)
    if raw_evalue is None or raw_evalue == "":
        raw_evalue = 1e-5
    try:
        evalue = float(raw_evalue)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("evalue must be numeric.", "invalid_workflow_inputs") from exc
    if not 1e-200 <= evalue <= 1e6:
        raise WorkflowError("evalue must be between 1e-200 and 1e6.", "invalid_workflow_inputs")
    raw_max_hits = inputs.get("max_hits", 10)
    if raw_max_hits is None or raw_max_hits == "":
        raw_max_hits = 10
    try:
        max_hits = int(raw_max_hits)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("max_hits must be an integer.", "invalid_workflow_inputs") from exc
    if not 1 <= max_hits <= 100:
        raise WorkflowError("max_hits must be between 1 and 100.", "invalid_workflow_inputs")
    inputs.update(
        {
            "query": query,
            "database_path": database_path,
            "program": program,
            "evalue": evalue,
            "max_hits": max_hits,
        }
    )
    return [
        _step(
            f"运行本地 {program.upper()} 并解析命中",
            "sequence_search_local",
            {
                "query": query,
                "database_path": database_path,
                "program": program,
                "evalue": evalue,
                "max_hits": max_hits,
                "threads": 1,
            },
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
    "bulk-rnaseq-differential-expression": _rnaseq_steps,
    "target-evidence-review": _target_evidence_steps,
    "literature-evidence-review": _literature_steps,
    "variant-evidence-review": _variant_evidence_steps,
    "clinical-trial-landscape-review": _clinical_trials_steps,
    "pairwise-alignment-review": _alignment_steps,
    "sequence-similarity-search": _sequence_search_steps,
    "database-record-review": _database_steps,
}

PREFLIGHTS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "bulk-rnaseq-differential-expression": _rnaseq_preflight,
    "target-evidence-review": _target_evidence_preflight,
    "literature-evidence-review": _literature_preflight,
    "variant-evidence-review": _variant_evidence_preflight,
    "clinical-trial-landscape-review": _clinical_trials_preflight,
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
        preflight_builder = PREFLIGHTS.get(template_id)
        preflight = preflight_builder(normalized_inputs) if preflight_builder else None
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
            "preflight": preflight,
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
            "preflight": copy.deepcopy(run.get("preflight")),
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
