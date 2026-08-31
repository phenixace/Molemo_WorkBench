"""Reproducible Molemo WorkBench showcase runner."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .skill_runtime import SkillRegistry
from .workflow_runtime import WorkflowManager


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "showcase.json"
TRP_CAGE = "NLYIQWLKDGGPSSGRPPPS"


def _artifact_types(result: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(str(item.get("type") or "") for item in result.get("artifacts") or [] if item.get("type")))


def _run_case(case_id: str, title: str, action: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        result = action()
        return {
            "id": case_id,
            "title": title,
            "status": "passed",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            **result,
        }
    except Exception as exc:
        return {
            "id": case_id,
            "title": title,
            "status": "failed",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": str(exc),
        }


def _tool_case(registry: SkillRegistry, name: str, arguments: dict[str, Any], metrics) -> dict[str, Any]:
    result = registry.execute(name, arguments)
    return {
        "mode": "direct_skill",
        "tools": [name],
        "summary": result.get("summary"),
        "artifact_types": _artifact_types(result),
        "metrics": metrics(result.get("data") or {}),
    }


def _workflow_case(
    manager: WorkflowManager,
    registry: SkillRegistry,
    template_id: str,
    inputs: dict[str, Any],
    objective: str,
    metrics,
) -> dict[str, Any]:
    plan = manager.create_plan(template_id, inputs, objective)
    if plan["status"] != "pending_approval" or plan["trace"]:
        raise RuntimeError("Workflow did not stop at the approval boundary.")
    completed = manager.approve(plan["id"], registry)
    if completed["status"] != "completed":
        raise RuntimeError(completed.get("error") or "Workflow failed.")
    result_artifacts = [
        item
        for item in completed.get("artifacts") or []
        if item.get("type") not in {"workflow-plan", "workflow-run"}
    ]
    data = result_artifacts[-1].get("data") if result_artifacts else {}
    return {
        "mode": "approved_workflow",
        "template_id": template_id,
        "approval_boundary_verified": True,
        "tools": [item["name"] for item in completed.get("trace") or []],
        "summary": completed["trace"][-1].get("summary") if completed.get("trace") else "",
        "artifact_types": list(dict.fromkeys(item.get("type") for item in result_artifacts)),
        "metrics": metrics(data or {}),
    }


def run_showcase(full: bool = False) -> dict[str, Any]:
    registry = SkillRegistry()
    with tempfile.TemporaryDirectory(prefix="molemo-showcase-") as storage:
        manager = WorkflowManager(Path(storage))
        cases = [
            _run_case(
                "caffeine-molecule",
                "Caffeine molecular profile",
                lambda: _tool_case(
                    registry,
                    "chem_analyze_molecule",
                    {"smiles": "CN1C=NC2=C1C(=O)N(C)C(=O)N2C"},
                    lambda data: {
                        "formula": data.get("formula"),
                        "molecular_weight": (data.get("properties") or {}).get("MW"),
                        "atoms": len(data.get("atoms") or []),
                        "bonds": len(data.get("bonds") or []),
                    },
                ),
            ),
            _run_case(
                "trp-cage-protein",
                "Trp-cage protein sequence profile",
                lambda: _tool_case(
                    registry,
                    "protein_analyze_sequence",
                    {"sequence": TRP_CAGE},
                    lambda data: {
                        "length": (data.get("properties") or {}).get("Length"),
                        "molecular_weight": (data.get("properties") or {}).get("MW"),
                        "estimated_pi": (data.get("properties") or {}).get("pI"),
                    },
                ),
            ),
            _run_case(
                "paired-dna-variant",
                "Paired FASTQ to BAM and candidate VCF",
                lambda: _workflow_case(
                    manager,
                    registry,
                    "paired-end-dna-variant-calling",
                    {
                        "read1_path": "examples/dna_variant_R1.fastq",
                        "read2_path": "examples/dna_variant_R2.fastq",
                        "reference_path": "examples/dna_variant_reference.fa",
                        "sample_id": "MOLEMO_DEMO",
                        "ploidy": 2,
                        "min_base_quality": 13,
                        "min_mapping_quality": 20,
                        "max_depth": 10000,
                        "threads": 1,
                    },
                    "Recover the synthetic heterozygous SNV from paired-end reads",
                    lambda data: {
                        "read_pairs": (data.get("reads") or {}).get("read_pairs"),
                        "mapped_percent": (data.get("alignment") or {}).get("mapped_percent"),
                        "mean_depth": (data.get("coverage") or {}).get("mean_depth"),
                        "candidate_variants": data.get("variant_count"),
                        "truth_variant_recovered": any(
                            item.get("chrom") == "molemo_demo_reference"
                            and item.get("pos") == 1201
                            and item.get("ref") == "A"
                            and item.get("alt") == "C"
                            and item.get("genotype") == "0/1"
                            for item in data.get("variants") or []
                        ),
                    },
                ),
            ),
        ]
        if full:
            cases.extend(
                [
                    _run_case(
                        "bulk-rnaseq",
                        "Bulk RNA-seq differential expression",
                        lambda: _workflow_case(
                            manager,
                            registry,
                            "bulk-rnaseq-differential-expression",
                            {
                                "count_matrix_path": "examples/rnaseq_counts.csv",
                                "metadata_path": "examples/rnaseq_metadata.csv",
                                "sample_column": "sample",
                                "condition_column": "condition",
                                "test_level": "treated",
                                "reference_level": "control",
                                "batch_column": "batch",
                                "min_total_count": 10,
                                "fdr_threshold": 0.05,
                                "lfc_threshold": 1.0,
                            },
                            "Find expression changes in the synthetic treated cohort",
                            lambda data: {
                                "samples": data.get("samples"),
                                "genes_tested": data.get("genes_tested"),
                                "significant_genes": data.get("significant_genes"),
                                "upregulated": data.get("upregulated"),
                                "downregulated": data.get("downregulated"),
                            },
                        ),
                    ),
                    _run_case(
                        "single-cell-rnaseq",
                        "Single-cell RNA-seq exploration",
                        lambda: _workflow_case(
                            manager,
                            registry,
                            "single-cell-exploratory-analysis",
                            {
                                "count_matrix_path": "examples/single_cell_counts.csv",
                                "metadata_path": "examples/single_cell_metadata.csv",
                                "cell_id_column": "cell_id",
                                "min_genes": 20,
                                "min_cells": 3,
                                "max_mito_percent": 20,
                                "n_top_genes": 40,
                                "n_neighbors": 10,
                                "leiden_resolution": 0.4,
                                "marker_genes": 8,
                                "run_scrublet": False,
                            },
                            "Recover the three known synthetic single-cell populations",
                            lambda data: {
                                "cells_retained": data.get("cells_retained"),
                                "genes_retained": data.get("genes_retained"),
                                "clusters": data.get("clusters"),
                                "cluster_sizes": [
                                    item.get("cells") for item in data.get("cluster_summary") or []
                                ],
                            },
                        ),
                    ),
                ]
            )

    passed = sum(item["status"] == "passed" for item in cases)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "full" if full else "quick",
        "service": {
            "skills": len(registry.skills),
            "tools": len(registry.tools),
            "workflows": len(WorkflowManager().catalog()),
        },
        "summary": {"passed": passed, "total": len(cases), "success": passed == len(cases)},
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run reproducible Molemo WorkBench showcase cases.")
    parser.add_argument("--full", action="store_true", help="Also run bulk and single-cell workflows.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT, help="JSON report path.")
    arguments = parser.parse_args()
    report = run_showcase(arguments.full)
    output = arguments.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for case in report["cases"]:
        print(f"[{case['status'].upper()}] {case['title']} ({case['duration_ms']:.0f} ms)")
        if case.get("error"):
            print(f"  {case['error']}")
    summary = report["summary"]
    print(f"Molemo showcase: {summary['passed']}/{summary['total']} cases passed")
    print(f"Report: {output}")
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
