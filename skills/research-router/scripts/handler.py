"""Deterministic routing for broad life-science questions."""

from __future__ import annotations

import re
from typing import Any


LANES = (
    ("molecular chemistry", r"smiles|molecule|compound|ligand|药|分子|化合物|配体|logp|tpsa"),
    ("protein structure and sequence", r"protein|peptide|fasta|sequence|mutation|蛋白|多肽|序列|突变"),
    ("sequence comparison", r"align|alignment|homolog|identity|比对|同源|相似度"),
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
