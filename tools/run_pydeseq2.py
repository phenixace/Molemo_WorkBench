"""Isolated PyDESeq2 runner invoked by the approved Molemo workflow."""

from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pydeseq2
from pydeseq2.dds import DeseqDataSet
from pydeseq2.ds import DeseqStats


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_pydeseq2.py CONFIG_JSON OUTPUT_DIR")
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=False)

    counts_by_gene = pd.read_csv(
        config["count_matrix"],
        sep=config["count_delimiter"],
        index_col=0,
    )
    counts_by_gene.index = counts_by_gene.index.astype(str)
    counts_by_gene.columns = counts_by_gene.columns.astype(str)
    counts_by_gene = counts_by_gene.loc[:, config["sample_names"]]
    retained = counts_by_gene.sum(axis=1) >= int(config["min_total_count"])
    filtered_counts = counts_by_gene.loc[retained].astype(np.int64)

    metadata = pd.read_csv(config["metadata"], sep=config["metadata_delimiter"], dtype=str)
    metadata = metadata.set_index(config["sample_column"]).loc[config["sample_names"]]
    design_columns = [config["condition_column"]]
    if config.get("batch_column"):
        design_columns.insert(0, config["batch_column"])
    metadata = metadata.loc[:, design_columns].astype(str)
    counts_by_sample = filtered_counts.T

    captured_warnings = []
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        dds = DeseqDataSet(
            counts=counts_by_sample,
            metadata=metadata,
            design=config["design_formula"],
            n_cpus=1,
            quiet=True,
            low_memory=True,
        )
        dds.deseq2()
        stats = DeseqStats(
            dds,
            contrast=[
                config["condition_column"],
                config["test_level"],
                config["reference_level"],
            ],
            alpha=float(config["fdr_threshold"]),
            n_cpus=1,
            quiet=True,
        )
        stats.summary()
        for item in warning_records:
            message = " ".join(str(item.message).split())
            if message and message not in captured_warnings:
                captured_warnings.append(message[:500])

    results = stats.results_df.copy()
    results.index = results.index.astype(str)
    results.index.name = "gene_id"
    alpha = float(config["fdr_threshold"])
    lfc_threshold = float(config["lfc_threshold"])
    results["status"] = "not_significant"
    significant = results["padj"].notna() & (results["padj"] <= alpha)
    results.loc[significant & (results["log2FoldChange"] >= lfc_threshold), "status"] = "up"
    results.loc[significant & (results["log2FoldChange"] <= -lfc_threshold), "status"] = "down"
    results["abs_log2_fold_change"] = results["log2FoldChange"].abs()
    ordered_results = results.sort_values(
        ["padj", "abs_log2_fold_change"],
        ascending=[True, False],
        na_position="last",
    )

    normalized = pd.DataFrame(
        np.asarray(dds.layers["normed_counts"]),
        index=counts_by_sample.index,
        columns=counts_by_sample.columns,
    )
    log_normalized = np.log2(normalized + 1.0)
    pca = _build_pca(log_normalized, metadata, config["condition_column"])
    heatmap = _build_heatmap(log_normalized, ordered_results)
    volcano = _build_volcano(ordered_results)
    top_genes = [_result_record(gene_id, row) for gene_id, row in ordered_results.head(50).iterrows()]

    export_results = ordered_results.drop(columns=["abs_log2_fold_change"])
    export_results.to_csv(output_dir / "differential_expression.tsv", sep="\t", na_rep="")
    normalized.T.to_csv(output_dir / "normalized_counts.tsv", sep="\t", float_format="%.6f")

    condition_values = metadata[config["condition_column"]].astype(str)
    sample_qc = []
    for sample in counts_by_sample.index:
        sample_qc.append(
            {
                "sample": str(sample),
                "condition": str(condition_values.loc[sample]),
                "batch": (
                    str(metadata.loc[sample, config["batch_column"]]) if config.get("batch_column") else None
                ),
                "library_size": int(counts_by_gene[sample].sum()),
                "detected_genes": int((counts_by_gene[sample] > 0).sum()),
            }
        )

    summary = {
        "method": "PyDESeq2",
        "method_version": pydeseq2.__version__,
        "design_formula": config["design_formula"],
        "contrast": {
            "factor": config["condition_column"],
            "test": config["test_level"],
            "reference": config["reference_level"],
        },
        "thresholds": {"fdr": alpha, "absolute_log2_fold_change": lfc_threshold},
        "genes_input": int(counts_by_gene.shape[0]),
        "genes_tested": int(filtered_counts.shape[0]),
        "samples": int(counts_by_sample.shape[0]),
        "significant_genes": int((results["status"] != "not_significant").sum()),
        "upregulated": int((results["status"] == "up").sum()),
        "downregulated": int((results["status"] == "down").sum()),
        "sample_qc": sample_qc,
        "pca": pca,
        "volcano": volcano,
        "heatmap": heatmap,
        "top_genes": top_genes,
        "warnings": captured_warnings,
        "caveats": [
            "PyDESeq2 is a Python implementation of the DESeq2 method and may differ numerically from Bioconductor DESeq2.",
            "Log2 fold-change shrinkage is not applied in this workflow.",
            "Differential expression is associative and requires biological validation.",
        ],
        "package_versions": {
            "pydeseq2": pydeseq2.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    manifest = {
        "method": summary["method"],
        "method_version": summary["method_version"],
        "input_mode": "raw_counts",
        "source_paths": config["source_paths"],
        "design_formula": summary["design_formula"],
        "contrast": summary["contrast"],
        "thresholds": summary["thresholds"],
        "min_total_count": int(config["min_total_count"]),
        "samples": config["sample_names"],
        "package_versions": summary["package_versions"],
        "outputs": [
            "differential_expression.tsv",
            "normalized_counts.tsv",
            "run_manifest.json",
            "summary.json",
            "artifact_index.json",
            "summary.md",
        ],
    }
    artifact_index = {
        "artifacts": [
            {"type": "table", "path": "differential_expression.tsv"},
            {"type": "matrix", "path": "normalized_counts.tsv"},
            {"type": "manifest", "path": "run_manifest.json"},
            {"type": "analysis-summary", "path": "summary.json"},
            {"type": "summary", "path": "summary.md"},
        ]
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "run_manifest.json", manifest)
    _write_json(output_dir / "artifact_index.json", artifact_index)
    (output_dir / "summary.md").write_text(_summary_markdown(summary), encoding="utf-8")


def _build_pca(log_normalized: pd.DataFrame, metadata: pd.DataFrame, condition_column: str) -> dict[str, Any]:
    values = log_normalized.to_numpy(dtype=float)
    gene_variance = np.var(values, axis=0)
    selected = np.argsort(gene_variance)[::-1][: min(500, values.shape[1])]
    matrix = values[:, selected]
    matrix = matrix - matrix.mean(axis=0, keepdims=True)
    u, singular_values, _ = np.linalg.svd(matrix, full_matrices=False)
    available = min(2, singular_values.size)
    coordinates = np.zeros((matrix.shape[0], 2), dtype=float)
    if available:
        coordinates[:, :available] = u[:, :available] * singular_values[:available]
    variance = singular_values**2
    explained = variance / variance.sum() * 100 if variance.sum() else np.zeros_like(variance)
    return {
        "variance_explained": [round(float(explained[index]), 2) if index < explained.size else 0.0 for index in range(2)],
        "points": [
            {
                "sample": str(sample),
                "condition": str(metadata.loc[sample, condition_column]),
                "pc1": round(float(coordinates[index, 0]), 4),
                "pc2": round(float(coordinates[index, 1]), 4),
            }
            for index, sample in enumerate(log_normalized.index)
        ],
    }


def _build_heatmap(log_normalized: pd.DataFrame, ordered_results: pd.DataFrame) -> dict[str, Any]:
    ranked = [gene for gene in ordered_results.index if gene in log_normalized.columns]
    genes = ranked[: min(20, len(ranked))]
    matrix = log_normalized.loc[:, genes].T.to_numpy(dtype=float)
    means = matrix.mean(axis=1, keepdims=True)
    standard_deviations = matrix.std(axis=1, keepdims=True)
    standard_deviations[standard_deviations == 0] = 1.0
    z_scores = np.clip((matrix - means) / standard_deviations, -3, 3)
    return {
        "genes": [str(gene) for gene in genes],
        "samples": [str(sample) for sample in log_normalized.index],
        "values": [[round(float(value), 3) for value in row] for row in z_scores],
        "scale": "gene-wise z-score of log2 normalized counts",
    }


def _build_volcano(ordered_results: pd.DataFrame) -> dict[str, Any]:
    selected = ordered_results.head(2000)
    points = []
    for gene_id, row in selected.iterrows():
        padj = _finite(row.get("padj"))
        pvalue = _finite(row.get("pvalue"))
        significance_value = padj if padj is not None else pvalue
        neg_log10 = -math.log10(max(significance_value, 1e-300)) if significance_value is not None else 0.0
        points.append(
            {
                "gene_id": str(gene_id),
                "log2_fold_change": _finite(row.get("log2FoldChange")),
                "padj": padj,
                "pvalue": pvalue,
                "neg_log10_padj": round(min(neg_log10, 300.0), 4),
                "status": str(row.get("status") or "not_significant"),
            }
        )
    return {"points": points, "shown": len(points), "total": int(ordered_results.shape[0])}


def _result_record(gene_id: str, row: pd.Series) -> dict[str, Any]:
    return {
        "gene_id": str(gene_id),
        "base_mean": _finite(row.get("baseMean")),
        "log2_fold_change": _finite(row.get("log2FoldChange")),
        "lfc_standard_error": _finite(row.get("lfcSE")),
        "statistic": _finite(row.get("stat")),
        "pvalue": _finite(row.get("pvalue")),
        "padj": _finite(row.get("padj")),
        "status": str(row.get("status") or "not_significant"),
    }


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _summary_markdown(summary: dict[str, Any]) -> str:
    contrast = summary["contrast"]
    return (
        "# Bulk RNA-seq differential expression\n\n"
        f"- Method: {summary['method']} {summary['method_version']}\n"
        f"- Design: `{summary['design_formula']}`\n"
        f"- Contrast: {contrast['test']} vs {contrast['reference']}\n"
        f"- Samples: {summary['samples']}\n"
        f"- Genes tested: {summary['genes_tested']}\n"
        f"- Significant: {summary['significant_genes']} "
        f"({summary['upregulated']} up, {summary['downregulated']} down)\n\n"
        "Interpret the result together with sample QC, study design, and independent biological validation.\n"
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
