"""Deterministic routing for broad life-science questions."""

from __future__ import annotations

import re
from typing import Any


LANES = (
    ("molecular chemistry", r"smiles|molecule|compound|ligand|药|分子|化合物|配体|logp|tpsa"),
    (
        "protein family and domain analysis",
        r"\bhmm(?:er|search)?\b|profile\s+hmm|protein\s+(?:family|domain)|结构域|蛋白家族|隐马尔可夫",
    ),
    ("protein structure and sequence", r"protein|peptide|fasta|sequence|mutation|蛋白|多肽|序列|突变"),
    ("public biological databases", r"pubchem|uniprot|rcsb|database|accession|数据库|条目"),
    ("target evidence and prioritization", r"target evidence|target priorit|disease association|靶点证据|靶点优先|疾病关联"),
    (
        "pathway and network biology",
        r"reactome|string(?:-db)?|pathway\s+(?:enrichment|overrepresentation)|functional\s+enrichment|"
        r"protein\s+(?:association|interaction)\s+network|\bppi\b|gene\s*set|"
        r"基因集|通路(?:富集|过表达)|功能富集|蛋白(?:功能|互作)网络|互作网络",
    ),
    ("human genetics and variant evidence", r"clinvar|gnomad|hgvs|\brs\d+\b|variant interpret|pathogenic|人类遗传|变异解释|致病|人群频率"),
    (
        "clinical and translational evidence",
        r"clinical trial|trial landscape|clinical development|posted results|trial results|"
        r"\bNCT\d{8}\b|临床试验|临床开发|试验版图|试验结果|结果审阅|不良事件",
    ),
    ("literature and study discovery", r"paper|publication|literature|pubmed|europe pmc|文献|论文|研究综述|证据地图"),
    ("experimental protein structure", r"pdb|rcsb|mmcif|coordinate|atom-level|原子|坐标|三维结构"),
    ("sequencing quality control", r"fastq|phred|q20|q30|read quality|测序|质控|读长"),
    ("single-cell transcriptomics", r"single[- ]?cell|scrna-?seq|单细胞|细胞聚类|leiden|umap"),
    ("transcriptomics and expression", r"rna-?seq|count matrix|differential expression|transcriptom|差异表达|转录组|表达矩阵"),
    (
        "sequencing and cohort variants",
        r"\bvcf\b|ctdna|liquid biopsy|variant landscape|variant trajectory|"
        r"变异景观|变异轨迹|样本轨迹|液体活检|低频变异|低频调用",
    ),
    ("sequence similarity search", r"blast|homolog|sequence search|同源|相似序列|序列搜索"),
    ("sequence comparison", r"align|alignment|identity|比对|相似度"),
    ("scientific visualization", r"plot|chart|visual|viewer|绘图|作图|画图|图表|可视化|显示|结构"),
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
    if "protein family and domain analysis" in lanes:
        suggested.extend(["hmmer_profile_preflight", "workflow_create_plan"])
    if "public biological databases" in lanes:
        suggested.extend(["database_lookup_pubchem", "database_lookup_uniprot"])
    if "target evidence and prioritization" in lanes:
        suggested.extend(["target_evidence_preflight", "workflow_create_plan"])
    if "pathway and network biology" in lanes:
        suggested.extend(["functional_analysis_preflight", "workflow_create_plan"])
    if "human genetics and variant evidence" in lanes:
        suggested.extend(["variant_evidence_preflight", "workflow_create_plan"])
    if "clinical and translational evidence" in lanes:
        suggested.extend(
            ["clinical_trials_preview", "clinical_trial_results_preflight", "workflow_create_plan"]
        )
    if "literature and study discovery" in lanes:
        suggested.extend(["literature_search_preview", "workflow_create_plan"])
    if "experimental protein structure" in lanes:
        suggested.extend(["structure_fetch_pdb", "structure_parse_workspace"])
    if "sequencing quality control" in lanes:
        suggested.append("ngs_fastq_qc")
    if "single-cell transcriptomics" in lanes:
        suggested.extend(["single_cell_preflight", "workflow_create_plan"])
    if "transcriptomics and expression" in lanes:
        suggested.extend(["transcriptomics_preflight", "workflow_create_plan"])
    if "sequencing and cohort variants" in lanes:
        suggested.extend(["vcf_cohort_preflight", "workflow_create_plan"])
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
