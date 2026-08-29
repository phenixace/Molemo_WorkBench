"""Deterministic routing for broad life-science questions."""

from __future__ import annotations

import re
from typing import Any


LANES = (
    ("molecular chemistry", r"smiles|molecule|compound|ligand|药|分子|化合物|配体|logp|tpsa"),
    ("protein structure and sequence", r"protein|peptide|fasta|sequence|mutation|蛋白|多肽|序列|突变"),
    ("public biological databases", r"pubchem|uniprot|rcsb|database|accession|数据库|条目"),
    ("target evidence and prioritization", r"target evidence|target priorit|disease association|靶点证据|靶点优先|疾病关联"),
    ("experimental protein structure", r"pdb|rcsb|mmcif|coordinate|atom-level|原子|坐标|三维结构"),
    ("sequencing quality control", r"fastq|phred|q20|q30|read quality|测序|质控|读长"),
    ("transcriptomics and expression", r"rna-?seq|count matrix|differential expression|transcriptom|差异表达|转录组|表达矩阵"),
    ("sequence similarity search", r"blast|homolog|sequence search|同源|相似序列|序列搜索"),
    ("sequence comparison", r"align|alignment|identity|比对|相似度"),
    ("scientific visualization", r"plot|chart|visual|viewer|图|可视化|显示|结构"),
    ("local workspace", r"workspace|file|dataset|本地|文件|数据集"),
    ("design and validation", r"design|optimi[sz]e|candidate|validate|设计|优化|候选|验证"),
)


def route_question(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    question = str(arguments.get("question") or "").strip()
    if not question:
        raise ValueError("question is required")
    lanes = [lane for lane, pattern in LANES if re.search(pattern, question, re.I)]
    if not lanes:
        lanes = ["general life science"]
    suggested = []
    if "molecular chemistry" in lanes:
        suggested.append("chem_analyze_molecule")
    if "protein structure and sequence" in lanes:
        suggested.append("protein_analyze_sequence")
    if "public biological databases" in lanes:
        suggested.extend(["database_lookup_pubchem", "database_lookup_uniprot"])
    if "target evidence and prioritization" in lanes:
        suggested.extend(["target_evidence_preflight", "workflow_create_plan"])
    if "experimental protein structure" in lanes:
        suggested.extend(["structure_fetch_pdb", "structure_parse_workspace"])
    if "sequencing quality control" in lanes:
        suggested.append("ngs_fastq_qc")
    if "transcriptomics and expression" in lanes:
        suggested.extend(["transcriptomics_preflight", "workflow_create_plan"])
    if "sequence similarity search" in lanes:
        suggested.append("workflow_create_plan")
    if "sequence comparison" in lanes:
        suggested.append("sequence_align")
    if "scientific visualization" in lanes:
        suggested.extend(["visualization_property_chart", "visualization_sequence_track"])
    if "local workspace" in lanes:
        suggested.extend(["workspace_list_files", "workspace_read_text"])
    return {
        "summary": f"Routed the question to {', '.join(lanes)}.",
        "lanes": lanes[:3],
        "suggested_tools": list(dict.fromkeys(suggested)),
        "caveat": "Routing selects tools; it does not establish a biological conclusion.",
    }
