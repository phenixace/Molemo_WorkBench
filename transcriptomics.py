"""Bounded bulk RNA-seq validation and PyDESeq2 execution."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from workspace_utils import MAX_UPLOAD_BYTES, WORKSPACE_ROOT, WorkspaceError, resolve_workspace_path


ROOT = Path(__file__).resolve().parent
RUNNER_PATH = ROOT / "tools" / "run_pydeseq2.py"
PROJECT_RNASEQ_PYTHON = ROOT / ".molemo-tools" / "rnaseq" / "bin" / "python"
TABLE_SUFFIXES = {".csv", ".tsv"}
MAX_GENES = 100_000
MAX_SAMPLES = 100
MAX_COUNT = 1_000_000_000_000
PROCESS_TIMEOUT_SECONDS = 600
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class TranscriptomicsError(ValueError):
    """Raised when a transcriptomics analysis is invalid or cannot run."""


def transcriptomics_toolchain_status() -> dict[str, Any]:
    python = find_pydeseq2_python()
    if python is None:
        return {"available": False, "python": None, "pydeseq2_version": None}
    version = _probe_pydeseq2(python)
    return {
        "available": version is not None,
        "python": str(python),
        "pydeseq2_version": version,
    }


def find_pydeseq2_python() -> Path | None:
    configured = str(os.environ.get("MOLEMO_RNASEQ_PYTHON") or "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(PROJECT_RNASEQ_PYTHON)
    if importlib.util.find_spec("pydeseq2") is not None:
        candidates.append(Path(sys.executable))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK) and _probe_pydeseq2(candidate):
            return candidate.expanduser().absolute()
    return None


def preflight_bulk_rnaseq(
    count_matrix_path: str,
    metadata_path: str,
    condition_column: str = "condition",
    test_level: str = "treated",
    reference_level: str = "control",
    sample_column: str = "sample",
    batch_column: str = "",
    min_total_count: int = 10,
) -> dict[str, Any]:
    condition_column = _validate_column_name(condition_column, "condition_column")
    sample_column = _validate_column_name(sample_column, "sample_column")
    batch_column = str(batch_column or "").strip()
    if batch_column:
        batch_column = _validate_column_name(batch_column, "batch_column")
    test_level = str(test_level or "").strip()
    reference_level = str(reference_level or "").strip()
    if not test_level or not reference_level:
        raise TranscriptomicsError("Both test_level and reference_level are required.")
    if test_level == reference_level:
        raise TranscriptomicsError("test_level and reference_level must be different.")
    try:
        min_total_count = int(min_total_count)
    except (TypeError, ValueError) as exc:
        raise TranscriptomicsError("min_total_count must be an integer.") from exc
    if not 1 <= min_total_count <= MAX_COUNT:
        raise TranscriptomicsError(f"min_total_count must be between 1 and {MAX_COUNT}.")

    count_path, count_relative = _resolve_table(count_matrix_path, "count matrix")
    metadata_file, metadata_relative = _resolve_table(metadata_path, "sample metadata")
    metadata_rows, metadata_headers = _read_metadata(metadata_file, sample_column)
    for required in (condition_column, batch_column):
        if required and required not in metadata_headers:
            raise TranscriptomicsError(f"Sample metadata is missing column: {required}")

    sample_names, count_metrics = _inspect_count_matrix(count_path, min_total_count)
    metadata_by_sample = {row[sample_column].strip(): row for row in metadata_rows}
    count_samples = set(sample_names)
    metadata_samples = set(metadata_by_sample)
    missing = sorted(count_samples - metadata_samples)
    extra = sorted(metadata_samples - count_samples)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing metadata for {', '.join(missing[:5])}")
        if extra:
            details.append(f"metadata has extra samples {', '.join(extra[:5])}")
        raise TranscriptomicsError("Count matrix and metadata samples must match exactly: " + "; ".join(details) + ".")

    condition_counts: Counter[str] = Counter()
    batch_conditions: dict[str, set[str]] = defaultdict(set)
    sample_qc = []
    for index, sample in enumerate(sample_names):
        row = metadata_by_sample[sample]
        condition = str(row.get(condition_column) or "").strip()
        if not condition:
            raise TranscriptomicsError(f"Sample {sample} has no {condition_column} value.")
        condition_counts[condition] += 1
        batch = str(row.get(batch_column) or "").strip() if batch_column else ""
        if batch_column and not batch:
            raise TranscriptomicsError(f"Sample {sample} has no {batch_column} value.")
        if batch_column:
            batch_conditions[batch].add(condition)
        sample_qc.append(
            {
                "sample": sample,
                "condition": condition,
                "batch": batch or None,
                "library_size": count_metrics["library_sizes"][index],
                "detected_genes": count_metrics["detected_genes"][index],
            }
        )

    for level in (test_level, reference_level):
        if level not in condition_counts:
            raise TranscriptomicsError(f"Contrast level not found in {condition_column}: {level}")
        if condition_counts[level] < 2:
            raise TranscriptomicsError(f"Contrast level {level} needs at least two biological replicates.")
    if batch_column and batch_conditions and all(len(values) == 1 for values in batch_conditions.values()):
        raise TranscriptomicsError(
            f"{batch_column} is fully confounded with {condition_column}; the requested effect is not estimable."
        )

    warnings = []
    if condition_counts[test_level] < 3 or condition_counts[reference_level] < 3:
        warnings.append("At least three biological replicates per contrast level are recommended; interpret small-n results cautiously.")
    library_sizes = count_metrics["library_sizes"]
    positive_libraries = [value for value in library_sizes if value > 0]
    if positive_libraries and max(positive_libraries) / min(positive_libraries) >= 5:
        warnings.append("Library sizes vary by at least five-fold; inspect normalization and sample quality before interpretation.")
    if count_metrics["genes_after_filter"] < 20:
        warnings.append("Fewer than 20 genes pass the count filter; dispersion and multiple-testing estimates may be unstable.")

    design_formula = f"~{batch_column}+{condition_column}" if batch_column else f"~{condition_column}"
    return {
        "ready": True,
        "input_mode": "raw_counts",
        "count_matrix_path": count_relative,
        "metadata_path": metadata_relative,
        "gene_id_column": count_metrics["gene_id_column"],
        "genes": count_metrics["genes"],
        "genes_after_filter": count_metrics["genes_after_filter"],
        "samples": len(sample_names),
        "sample_names": sample_names,
        "sample_qc": sample_qc,
        "condition_counts": dict(sorted(condition_counts.items())),
        "condition_column": condition_column,
        "sample_column": sample_column,
        "batch_column": batch_column or None,
        "design_formula": design_formula,
        "contrast": {
            "factor": condition_column,
            "test": test_level,
            "reference": reference_level,
        },
        "min_total_count": min_total_count,
        "warnings": warnings,
        "summary": (
            f"Validated {count_metrics['genes']:,} genes across {len(sample_names)} samples; "
            f"{count_metrics['genes_after_filter']:,} genes pass total count >= {min_total_count}."
        ),
    }


def run_bulk_rnaseq_de(
    count_matrix_path: str,
    metadata_path: str,
    condition_column: str = "condition",
    test_level: str = "treated",
    reference_level: str = "control",
    sample_column: str = "sample",
    batch_column: str = "",
    min_total_count: int = 10,
    fdr_threshold: float = 0.05,
    lfc_threshold: float = 1.0,
) -> dict[str, Any]:
    preflight = preflight_bulk_rnaseq(
        count_matrix_path=count_matrix_path,
        metadata_path=metadata_path,
        condition_column=condition_column,
        test_level=test_level,
        reference_level=reference_level,
        sample_column=sample_column,
        batch_column=batch_column,
        min_total_count=min_total_count,
    )
    try:
        fdr_threshold = float(fdr_threshold)
        lfc_threshold = float(lfc_threshold)
    except (TypeError, ValueError) as exc:
        raise TranscriptomicsError("fdr_threshold and lfc_threshold must be numeric.") from exc
    if not 0 < fdr_threshold <= 1:
        raise TranscriptomicsError("fdr_threshold must be greater than 0 and at most 1.")
    if not 0 <= lfc_threshold <= 20:
        raise TranscriptomicsError("lfc_threshold must be between 0 and 20.")

    python = find_pydeseq2_python()
    if python is None:
        raise TranscriptomicsError(
            "PyDESeq2 is not available. Install the project environment or set MOLEMO_RNASEQ_PYTHON."
        )
    if not RUNNER_PATH.is_file():
        raise TranscriptomicsError("The local PyDESeq2 runner is missing.")

    count_path = resolve_workspace_path(preflight["count_matrix_path"])
    metadata_file = resolve_workspace_path(preflight["metadata_path"])
    analysis_id = f"rnaseq-{uuid.uuid4().hex[:12]}"
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / analysis_id
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    environment = {
        **os.environ,
        "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    }
    with tempfile.TemporaryDirectory(prefix="rnaseq-", dir=temp_root) as temporary:
        temporary_path = Path(temporary)
        runner_output = temporary_path / "output"
        config_path = temporary_path / "config.json"
        config = {
            "count_matrix": str(count_path),
            "metadata": str(metadata_file),
            "count_delimiter": _delimiter(count_path),
            "metadata_delimiter": _delimiter(metadata_file),
            "condition_column": preflight["condition_column"],
            "sample_column": preflight["sample_column"],
            "batch_column": preflight["batch_column"],
            "design_formula": preflight["design_formula"],
            "test_level": preflight["contrast"]["test"],
            "reference_level": preflight["contrast"]["reference"],
            "sample_names": preflight["sample_names"],
            "min_total_count": preflight["min_total_count"],
            "fdr_threshold": fdr_threshold,
            "lfc_threshold": lfc_threshold,
            "source_paths": {
                "count_matrix": preflight["count_matrix_path"],
                "metadata": preflight["metadata_path"],
            },
        }
        config_path.write_text(json.dumps(config, ensure_ascii=True, indent=2), encoding="utf-8")
        _run_process([str(python), str(RUNNER_PATH), str(config_path), str(runner_output)], environment)
        summary_path = runner_output / "summary.json"
        try:
            result = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TranscriptomicsError("PyDESeq2 did not return a valid analysis summary.") from exc
        if final_output.exists():
            raise TranscriptomicsError(f"Analysis output already exists: {analysis_id}")
        shutil.move(str(runner_output), str(final_output))

    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result.update(
        {
            "analysis_id": analysis_id,
            "preflight": preflight,
            "output_root": relative_root,
            "outputs": {
                "differential_expression": f"{relative_root}/differential_expression.tsv",
                "normalized_counts": f"{relative_root}/normalized_counts.tsv",
                "manifest": f"{relative_root}/run_manifest.json",
                "analysis_summary": f"{relative_root}/summary.json",
                "artifact_index": f"{relative_root}/artifact_index.json",
                "summary": f"{relative_root}/summary.md",
            },
        }
    )
    result["warnings"] = list(dict.fromkeys([*preflight["warnings"], *(result.get("warnings") or [])]))
    return result


def _inspect_count_matrix(path: Path, min_total_count: int) -> tuple[list[str], dict[str, Any]]:
    delimiter = _delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise TranscriptomicsError("The count matrix is empty.") from exc
        header = [value.strip() for value in header]
        if len(header) < 3 or not header[0]:
            raise TranscriptomicsError("The count matrix needs a gene ID column and at least two sample columns.")
        sample_names = header[1:]
        if any(not sample for sample in sample_names):
            raise TranscriptomicsError("Count matrix sample names cannot be empty.")
        if len(sample_names) > MAX_SAMPLES:
            raise TranscriptomicsError(f"Count matrices are limited to {MAX_SAMPLES} samples.")
        duplicates = [name for name, count in Counter(sample_names).items() if count > 1]
        if duplicates:
            raise TranscriptomicsError(f"Duplicate count matrix sample name: {duplicates[0]}")

        gene_ids: set[str] = set()
        library_sizes = [0] * len(sample_names)
        detected_genes = [0] * len(sample_names)
        genes_after_filter = 0
        gene_count = 0
        for line_number, row in enumerate(reader, 2):
            if not row or not any(value.strip() for value in row):
                continue
            if len(row) != len(header):
                raise TranscriptomicsError(
                    f"Count matrix line {line_number} has {len(row)} columns; expected {len(header)}."
                )
            gene_id = row[0].strip()
            if not gene_id:
                raise TranscriptomicsError(f"Count matrix line {line_number} has an empty gene ID.")
            if gene_id in gene_ids:
                raise TranscriptomicsError(f"Duplicate gene ID in count matrix: {gene_id}")
            gene_ids.add(gene_id)
            gene_count += 1
            if gene_count > MAX_GENES:
                raise TranscriptomicsError(f"Count matrices are limited to {MAX_GENES:,} genes.")
            total = 0
            for index, raw_value in enumerate(row[1:]):
                value = _parse_count(raw_value, line_number, sample_names[index])
                total += value
                library_sizes[index] += value
                if value > 0:
                    detected_genes[index] += 1
            if total >= min_total_count:
                genes_after_filter += 1
    if gene_count == 0:
        raise TranscriptomicsError("The count matrix contains no genes.")
    if any(value == 0 for value in library_sizes):
        empty = sample_names[library_sizes.index(0)]
        raise TranscriptomicsError(f"Sample {empty} has a zero-size count library.")
    if genes_after_filter < 2:
        raise TranscriptomicsError("Fewer than two genes pass the total-count filter.")
    return sample_names, {
        "gene_id_column": header[0],
        "genes": gene_count,
        "genes_after_filter": genes_after_filter,
        "library_sizes": library_sizes,
        "detected_genes": detected_genes,
    }


def _read_metadata(path: Path, sample_column: str) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=_delimiter(path))
        headers = [str(value or "").strip() for value in (reader.fieldnames or [])]
        if not headers:
            raise TranscriptomicsError("The sample metadata is empty.")
        if len(headers) != len(set(headers)):
            raise TranscriptomicsError("Sample metadata column names must be unique.")
        if sample_column not in headers:
            raise TranscriptomicsError(f"Sample metadata is missing column: {sample_column}")
        rows = []
        seen = set()
        for line_number, raw_row in enumerate(reader, 2):
            row = {str(key or "").strip(): str(value or "").strip() for key, value in raw_row.items()}
            sample = row.get(sample_column, "")
            if not sample:
                raise TranscriptomicsError(f"Sample metadata line {line_number} has an empty sample ID.")
            if sample in seen:
                raise TranscriptomicsError(f"Duplicate sample metadata row: {sample}")
            seen.add(sample)
            rows.append(row)
    if len(rows) < 4:
        raise TranscriptomicsError("Differential expression requires at least four samples.")
    if len(rows) > MAX_SAMPLES:
        raise TranscriptomicsError(f"Sample metadata is limited to {MAX_SAMPLES} rows.")
    return rows, headers


def _resolve_table(relative_path: str, label: str) -> tuple[Path, str]:
    try:
        target = resolve_workspace_path(relative_path)
    except WorkspaceError as exc:
        raise TranscriptomicsError(str(exc)) from exc
    if not target.is_file():
        raise TranscriptomicsError(f"Workspace {label} not found: {relative_path}")
    if target.suffix.lower() not in TABLE_SUFFIXES:
        raise TranscriptomicsError(f"The {label} must be a workspace .csv or .tsv file.")
    if target.stat().st_size > MAX_UPLOAD_BYTES:
        raise TranscriptomicsError(f"The {label} exceeds the {MAX_UPLOAD_BYTES:,}-byte workspace limit.")
    return target, target.relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def _delimiter(path: Path) -> str:
    return "," if path.suffix.lower() == ".csv" else "\t"


def _validate_column_name(value: str, label: str) -> str:
    value = str(value or "").strip()
    if not IDENTIFIER.fullmatch(value):
        raise TranscriptomicsError(f"{label} must be a simple column name using letters, numbers, or underscores.")
    return value


def _parse_count(raw_value: str, line_number: int, sample: str) -> int:
    text = str(raw_value or "").strip()
    try:
        value = float(text)
    except ValueError as exc:
        raise TranscriptomicsError(f"Non-numeric count at line {line_number}, sample {sample}: {text or 'empty'}") from exc
    if not math.isfinite(value) or value < 0 or not value.is_integer() or value > MAX_COUNT:
        raise TranscriptomicsError(
            f"Counts must be non-negative integers up to {MAX_COUNT} (line {line_number}, sample {sample})."
        )
    return int(value)


def _run_process(command: list[str], environment: dict[str, str]) -> None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PROCESS_TIMEOUT_SECONDS,
            env=environment,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TranscriptomicsError(f"PyDESeq2 exceeded the {PROCESS_TIMEOUT_SECONDS}s runtime limit.") from exc
    except OSError as exc:
        raise TranscriptomicsError(f"Could not start PyDESeq2: {exc}") from exc
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        detail = re.sub(r"\s+", " ", detail)[:1200]
        raise TranscriptomicsError(f"PyDESeq2 failed: {detail}")


def _probe_pydeseq2(python: Path) -> str | None:
    try:
        completed = subprocess.run(
            [str(python), "-c", "import pydeseq2; print(pydeseq2.__version__)"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, "PYTHONNOUSERSITE": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode:
        return None
    return (completed.stdout or "").strip().splitlines()[-1] or None
