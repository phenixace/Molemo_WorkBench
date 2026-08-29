"""Bounded single-cell count-matrix validation and Scanpy execution."""

from __future__ import annotations

import csv
import functools
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from workspace_utils import MAX_UPLOAD_BYTES, WORKSPACE_ROOT, resolve_workspace_path


ROOT = Path(__file__).resolve().parent
RUNNER_PATH = ROOT / "tools" / "run_scanpy.py"
INSPECTOR_PATH = ROOT / "tools" / "inspect_single_cell.py"
PROJECT_SCANPY_PYTHON = ROOT / ".molemo-tools" / "bin" / "python"
TABLE_SUFFIXES = {".csv", ".tsv"}
MAX_CELLS = 20_000
MAX_GENES = 20_000
MAX_ENTRIES = 60_000_000
MAX_COUNT = 2_147_483_647
PROCESS_TIMEOUT_SECONDS = 900


class SingleCellError(ValueError):
    """Raised when a single-cell analysis is invalid or cannot run."""


def single_cell_toolchain_status() -> dict[str, Any]:
    python = find_scanpy_python()
    if python is None:
        return {
            "available": False,
            "python": None,
            "scanpy_version": None,
            "leidenalg_version": None,
            "scikit_image_version": None,
        }
    versions = _probe_scanpy(python)
    return {
        "available": versions is not None,
        "python": str(python),
        "scanpy_version": versions.get("scanpy") if versions else None,
        "leidenalg_version": versions.get("leidenalg") if versions else None,
        "scikit_image_version": versions.get("scikit_image") if versions else None,
    }


def find_scanpy_python() -> Path | None:
    configured = str(os.environ.get("MOLEMO_SCANPY_PYTHON") or "").strip()
    candidates = [Path(configured).expanduser()] if configured else []
    candidates.append(PROJECT_SCANPY_PYTHON)
    if importlib.util.find_spec("scanpy") is not None:
        candidates.append(Path(sys.executable))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK) and _probe_scanpy(candidate):
            return candidate.expanduser().absolute()
    return None


def preflight_single_cell(
    count_matrix_path: str,
    metadata_path: str = "",
    cell_id_column: str = "cell_id",
    count_layer: str = "",
    min_genes: int = 20,
    min_cells: int = 3,
    max_mito_percent: float = 20.0,
    n_top_genes: int = 2_000,
    n_neighbors: int = 15,
    leiden_resolution: float = 1.0,
    marker_genes: int = 10,
    run_scrublet: bool = False,
    doublet_batch_key: str = "",
    expected_doublet_rate: float = 0.05,
    exclude_predicted_doublets: bool = False,
) -> dict[str, Any]:
    parameters = _normalize_parameters(
        min_genes=min_genes,
        min_cells=min_cells,
        max_mito_percent=max_mito_percent,
        n_top_genes=n_top_genes,
        n_neighbors=n_neighbors,
        leiden_resolution=leiden_resolution,
        marker_genes=marker_genes,
        run_scrublet=run_scrublet,
        doublet_batch_key=doublet_batch_key,
        expected_doublet_rate=expected_doublet_rate,
        exclude_predicted_doublets=exclude_predicted_doublets,
    )
    cell_id_column = str(cell_id_column or "cell_id").strip()
    if not cell_id_column:
        raise SingleCellError("cell_id_column is required.")
    count_layer = str(count_layer or "").strip()
    if count_layer == "X":
        count_layer = ""
    count_input = _resolve_count_input(count_matrix_path)
    count_path = count_input["path"]

    metadata_relative = None
    metadata_file = None
    if str(metadata_path or "").strip():
        metadata_file, metadata_relative = _resolve_table(metadata_path, "cell metadata")

    toolchain = single_cell_toolchain_status()
    python = find_scanpy_python()
    if not toolchain["available"] or python is None:
        raise SingleCellError(
            "Scanpy runtime is unavailable; install the project environment before inspecting this input."
        )
    if parameters["run_scrublet"] and not toolchain["scikit_image_version"]:
        raise SingleCellError(
            "Scrublet automatic thresholding requires scikit-image in the Scanpy runtime."
        )
    matrix = _inspect_with_scanpy(
        python,
        {
            "count_matrix": str(count_path),
            "input_format": count_input["input_format"],
            "count_layer": count_layer,
            "count_delimiter": _delimiter(count_path),
            "metadata": str(metadata_file) if metadata_file else None,
            "metadata_delimiter": _delimiter(metadata_file) if metadata_file else None,
            "cell_id_column": cell_id_column,
            "parameters": parameters,
        },
    )
    if matrix["cells"] > MAX_CELLS:
        raise SingleCellError(f"Count matrix exceeds the {MAX_CELLS:,}-cell limit.")
    if matrix["genes"] > MAX_GENES:
        raise SingleCellError(f"Count matrix exceeds the {MAX_GENES:,}-gene limit.")
    if matrix["entries"] > MAX_ENTRIES:
        raise SingleCellError(f"Count matrix exceeds the {MAX_ENTRIES:,}-entry limit.")
    if matrix["cells_after_filter"] < 10:
        raise SingleCellError(
            "Configured QC thresholds retain fewer than 10 cells; relax the thresholds or inspect the matrix."
        )
    if matrix["genes_after_filter"] < 10:
        raise SingleCellError(
            "Configured QC thresholds retain fewer than 10 genes; relax min_cells or inspect the matrix."
        )
    if parameters["n_neighbors"] >= matrix["cells_after_filter"]:
        parameters["n_neighbors"] = max(2, matrix["cells_after_filter"] - 1)

    metadata_summary = matrix["metadata"]
    if parameters["run_scrublet"] and parameters["doublet_batch_key"]:
        batch_key = parameters["doublet_batch_key"]
        if batch_key not in metadata_summary["columns"]:
            raise SingleCellError(f"doublet_batch_key was not found in cell metadata: {batch_key}")
        batch_field = next(
            (
                field
                for field in metadata_summary["categorical_columns"]
                if field["column"] == batch_key
            ),
            None,
        )
        if batch_field is None:
            raise SingleCellError(
                "doublet_batch_key must identify a metadata field with 2 to 30 non-empty batches."
            )
        if batch_field.get("missing"):
            raise SingleCellError("doublet_batch_key cannot contain empty batch values.")

    warnings = list(matrix["warnings"])
    if metadata_summary["provided"] and not metadata_summary["categorical_columns"]:
        warnings.append("Metadata has no bounded categorical field suitable for coloring the embedding.")
    if parameters["run_scrublet"]:
        warnings.append(
            "Scrublet predictions depend on a simulated-doublet model and automatic threshold; review scores and threshold before interpreting or excluding cells."
        )
    return {
        "ready": True,
        "input_mode": "cell_by_gene_raw_counts",
        "input_format": matrix["input_format"],
        "input_files": count_input["input_files"],
        "count_matrix_path": count_input["relative"],
        "count_layer": matrix["count_layer"],
        "available_layers": matrix["available_layers"],
        "metadata_path": metadata_relative,
        "cell_id_column": cell_id_column,
        "cells": matrix["cells"],
        "genes": matrix["genes"],
        "entries": matrix["entries"],
        "nonzero_entries": matrix["nonzero_entries"],
        "sparsity_percent": matrix["sparsity_percent"],
        "mitochondrial_genes": matrix["mitochondrial_genes"],
        "cells_after_filter": matrix["cells_after_filter"],
        "cells_excluded": matrix["cells"] - matrix["cells_after_filter"],
        "genes_after_filter": matrix["genes_after_filter"],
        "genes_excluded": matrix["genes"] - matrix["genes_after_filter"],
        "qc_summary": matrix["qc_summary"],
        "metadata": metadata_summary,
        "parameters": parameters,
        "toolchain": toolchain,
        "warnings": warnings,
        "summary": (
            f"Validated {matrix['input_format']} raw counts with {matrix['cells']:,} cells by "
            f"{matrix['genes']:,} genes; configured QC retains {matrix['cells_after_filter']:,} cells "
            f"and {matrix['genes_after_filter']:,} genes."
        ),
    }


def run_single_cell_analysis(
    count_matrix_path: str,
    metadata_path: str = "",
    cell_id_column: str = "cell_id",
    count_layer: str = "",
    min_genes: int = 20,
    min_cells: int = 3,
    max_mito_percent: float = 20.0,
    n_top_genes: int = 2_000,
    n_neighbors: int = 15,
    leiden_resolution: float = 1.0,
    marker_genes: int = 10,
    run_scrublet: bool = False,
    doublet_batch_key: str = "",
    expected_doublet_rate: float = 0.05,
    exclude_predicted_doublets: bool = False,
) -> dict[str, Any]:
    preflight = preflight_single_cell(
        count_matrix_path=count_matrix_path,
        metadata_path=metadata_path,
        cell_id_column=cell_id_column,
        count_layer=count_layer,
        min_genes=min_genes,
        min_cells=min_cells,
        max_mito_percent=max_mito_percent,
        n_top_genes=n_top_genes,
        n_neighbors=n_neighbors,
        leiden_resolution=leiden_resolution,
        marker_genes=marker_genes,
        run_scrublet=run_scrublet,
        doublet_batch_key=doublet_batch_key,
        expected_doublet_rate=expected_doublet_rate,
        exclude_predicted_doublets=exclude_predicted_doublets,
    )
    python = find_scanpy_python()
    if python is None:
        raise SingleCellError(
            "Scanpy is not available. Install the project environment or set MOLEMO_SCANPY_PYTHON."
        )
    if not RUNNER_PATH.is_file():
        raise SingleCellError("The local Scanpy runner is missing.")

    count_path = resolve_workspace_path(preflight["count_matrix_path"])
    metadata_file = (
        resolve_workspace_path(preflight["metadata_path"]) if preflight["metadata_path"] else None
    )
    input_files = [resolve_workspace_path(path) for path in preflight["input_files"]]
    analysis_id = f"single-cell-{uuid.uuid4().hex[:12]}"
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / analysis_id
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    config = {
        "count_matrix": str(count_path),
        "input_format": preflight["input_format"],
        "count_layer": preflight["count_layer"] if preflight["count_layer"] != "X" else "",
        "metadata": str(metadata_file) if metadata_file else None,
        "count_delimiter": _delimiter(count_path),
        "metadata_delimiter": _delimiter(metadata_file) if metadata_file else None,
        "source_paths": {
            "count_matrix": preflight["count_matrix_path"],
            "metadata": preflight["metadata_path"],
            "input_files": preflight["input_files"],
        },
        "input_sha256": {
            "count_matrix": _sha256(count_path),
            "metadata": _sha256(metadata_file) if metadata_file else None,
            "input_files": {
                path.relative_to(WORKSPACE_ROOT).as_posix(): _sha256(path) for path in input_files
            },
        },
        "cell_id_column": preflight["cell_id_column"],
        "parameters": preflight["parameters"],
        "preflight_counts": {
            "cells": preflight["cells"],
            "genes": preflight["genes"],
            "cells_after_filter": preflight["cells_after_filter"],
            "genes_after_filter": preflight["genes_after_filter"],
        },
    }
    environment = {
        **os.environ,
        "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
    }
    with tempfile.TemporaryDirectory(prefix="single-cell-", dir=temp_root) as temporary:
        temporary_path = Path(temporary)
        runner_output = temporary_path / "output"
        config_path = temporary_path / "config.json"
        config_path.write_text(json.dumps(config, ensure_ascii=True, indent=2), encoding="utf-8")
        _run_process([str(python), str(RUNNER_PATH), str(config_path), str(runner_output)], environment)
        summary_path = runner_output / "summary.json"
        try:
            result = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SingleCellError("Scanpy did not return a valid analysis summary.") from exc
        if final_output.exists():
            raise SingleCellError(f"Analysis output already exists: {analysis_id}")
        shutil.move(str(runner_output), str(final_output))

    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result.update(
        {
            "analysis_id": analysis_id,
            "preflight": preflight,
            "output_root": relative_root,
            "outputs": {
                "cell_qc": f"{relative_root}/cell_qc.tsv",
                "embedding": f"{relative_root}/embedding.tsv",
                "markers": f"{relative_root}/markers.tsv",
                "gene_qc": f"{relative_root}/gene_qc.tsv",
                "cluster_summary": f"{relative_root}/cluster_summary.tsv",
                "anndata": f"{relative_root}/analysis.h5ad",
                "manifest": f"{relative_root}/run_manifest.json",
                "analysis_summary": f"{relative_root}/summary.json",
                "artifact_index": f"{relative_root}/artifact_index.json",
                "summary": f"{relative_root}/summary.md",
            },
        }
    )
    result["warnings"] = list(dict.fromkeys([*preflight["warnings"], *(result.get("warnings") or [])]))
    return result


def _inspect_count_matrix(
    path: Path,
    *,
    cell_id_column: str,
    min_genes: int,
    min_cells: int,
    max_mito_percent: float,
) -> dict[str, Any]:
    delimiter = _delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise SingleCellError("Single-cell count matrix is empty.") from exc
        if len(header) < 11:
            raise SingleCellError("Single-cell count matrix needs one cell ID column and at least 10 genes.")
        if header[0].strip() != cell_id_column:
            raise SingleCellError(
                f"The first count-matrix column must be {cell_id_column!r}; found {header[0].strip()!r}."
            )
        genes = [value.strip() for value in header[1:]]
        if any(not value for value in genes):
            raise SingleCellError("Gene identifiers cannot be empty.")
        duplicates = [name for name, count in Counter(genes).items() if count > 1]
        if duplicates:
            raise SingleCellError(f"Gene identifiers must be unique; duplicate: {duplicates[0]}")
        if len(genes) > MAX_GENES:
            raise SingleCellError(f"Count matrix exceeds the {MAX_GENES:,}-gene limit.")
        mitochondrial = [index for index, name in enumerate(genes) if name.upper().startswith("MT-")]
        detected_by_gene = [0] * len(genes)
        detected_by_gene_retained = [0] * len(genes)
        cell_ids: list[str] = []
        seen_cells: set[str] = set()
        library_sizes: list[int] = []
        detected_genes: list[int] = []
        mito_percents: list[float] = []
        nonzero_entries = 0
        retained_cells = 0

        for line_number, row in enumerate(reader, start=2):
            if not row or not any(value.strip() for value in row):
                continue
            if len(row) != len(header):
                raise SingleCellError(
                    f"Count-matrix row {line_number} has {len(row)} columns; expected {len(header)}."
                )
            cell_id = row[0].strip()
            if not cell_id:
                raise SingleCellError(f"Cell ID is empty at row {line_number}.")
            if cell_id in seen_cells:
                raise SingleCellError(f"Cell IDs must be unique; duplicate: {cell_id}")
            values: list[int] = []
            for column, raw in enumerate(row[1:], start=2):
                text = raw.strip()
                try:
                    value = int(text)
                except ValueError as exc:
                    raise SingleCellError(
                        f"Count at row {line_number}, column {column} must be a non-negative integer."
                    ) from exc
                if value < 0 or value > MAX_COUNT:
                    raise SingleCellError(
                        f"Count at row {line_number}, column {column} must be between 0 and {MAX_COUNT}."
                    )
                values.append(value)
            positive = [index for index, value in enumerate(values) if value > 0]
            library_size = sum(values)
            mito_count = sum(values[index] for index in mitochondrial)
            mito_percent = (mito_count / library_size * 100.0) if library_size else 0.0
            passes = len(positive) >= min_genes and mito_percent <= max_mito_percent
            for index in positive:
                detected_by_gene[index] += 1
                if passes:
                    detected_by_gene_retained[index] += 1
            if passes:
                retained_cells += 1
            nonzero_entries += len(positive)
            cell_ids.append(cell_id)
            seen_cells.add(cell_id)
            library_sizes.append(library_size)
            detected_genes.append(len(positive))
            mito_percents.append(mito_percent)
            if len(cell_ids) > MAX_CELLS:
                raise SingleCellError(f"Count matrix exceeds the {MAX_CELLS:,}-cell limit.")

    if not cell_ids:
        raise SingleCellError("Single-cell count matrix contains no cells.")
    entries = len(cell_ids) * len(genes)
    if entries > MAX_ENTRIES:
        raise SingleCellError(f"Count matrix exceeds the {MAX_ENTRIES:,}-entry limit.")
    genes_after_filter = sum(value >= min_cells for value in detected_by_gene_retained)
    warnings = []
    if not mitochondrial:
        warnings.append("No MT- prefixed genes were found; mitochondrial-percentage filtering is inactive.")
    if retained_cells < len(cell_ids) * 0.5:
        warnings.append("Configured cell QC excludes at least half of the input cells; inspect the thresholds.")
    if genes_after_filter < len(genes) * 0.25:
        warnings.append("Configured gene filtering excludes at least three quarters of the input genes.")
    return {
        "cell_ids": cell_ids,
        "cells": len(cell_ids),
        "genes": len(genes),
        "entries": entries,
        "nonzero_entries": nonzero_entries,
        "sparsity_percent": round((1.0 - nonzero_entries / entries) * 100.0, 2),
        "mitochondrial_genes": len(mitochondrial),
        "cells_after_filter": retained_cells,
        "genes_after_filter": genes_after_filter,
        "qc_summary": {
            "library_size": _distribution(library_sizes),
            "detected_genes": _distribution(detected_genes),
            "mitochondrial_percent": _distribution(mito_percents),
        },
        "warnings": warnings,
    }


def _inspect_metadata(path: Path, *, cell_id_column: str, expected_cells: list[str]) -> dict[str, Any]:
    delimiter = _delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        headers = [str(value or "").strip() for value in (reader.fieldnames or [])]
        if cell_id_column not in headers:
            raise SingleCellError(f"Cell metadata is missing the {cell_id_column!r} column.")
        if len(headers) > 21:
            raise SingleCellError("Cell metadata may contain at most 20 annotation columns plus the cell ID.")
        values: dict[str, Counter[str]] = {header: Counter() for header in headers if header != cell_id_column}
        seen: set[str] = set()
        for line_number, row in enumerate(reader, start=2):
            cell_id = str(row.get(cell_id_column) or "").strip()
            if not cell_id:
                raise SingleCellError(f"Cell metadata has an empty cell ID at row {line_number}.")
            if cell_id in seen:
                raise SingleCellError(f"Cell metadata IDs must be unique; duplicate: {cell_id}")
            seen.add(cell_id)
            for header in values:
                values[header][str(row.get(header) or "").strip()] += 1
    expected = set(expected_cells)
    missing = sorted(expected - seen)
    extra = sorted(seen - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {len(missing)} count-matrix cells")
        if extra:
            details.append(f"contains {len(extra)} extra cells")
        raise SingleCellError("Count matrix and cell metadata must match exactly: " + "; ".join(details) + ".")
    categorical = []
    for header, counts in values.items():
        nonempty = {key: value for key, value in counts.items() if key}
        if 1 < len(nonempty) <= 30:
            categorical.append(
                {
                    "column": header,
                    "levels": len(nonempty),
                    "counts": dict(sorted(nonempty.items())),
                }
            )
    return {
        "provided": True,
        "path": path.relative_to(WORKSPACE_ROOT).as_posix(),
        "columns": [header for header in headers if header != cell_id_column],
        "categorical_columns": categorical,
    }


def _normalize_parameters(**raw: Any) -> dict[str, Any]:
    try:
        values = {
            "min_genes": int(raw["min_genes"]),
            "min_cells": int(raw["min_cells"]),
            "max_mito_percent": float(raw["max_mito_percent"]),
            "n_top_genes": int(raw["n_top_genes"]),
            "n_neighbors": int(raw["n_neighbors"]),
            "leiden_resolution": float(raw["leiden_resolution"]),
            "marker_genes": int(raw["marker_genes"]),
            "expected_doublet_rate": float(raw["expected_doublet_rate"]),
        }
    except (TypeError, ValueError, KeyError) as exc:
        raise SingleCellError("Single-cell thresholds must be numeric.") from exc
    bounds = {
        "min_genes": (1, 10_000),
        "min_cells": (1, 5_000),
        "max_mito_percent": (0.0, 100.0),
        "n_top_genes": (10, 5_000),
        "n_neighbors": (2, 100),
        "leiden_resolution": (0.05, 5.0),
        "marker_genes": (1, 50),
        "expected_doublet_rate": (0.001, 0.3),
    }
    for key, (lower, upper) in bounds.items():
        value = values[key]
        if not math.isfinite(float(value)) or not lower <= value <= upper:
            raise SingleCellError(f"{key} must be between {lower} and {upper}.")
    values.update(
        {
            "run_scrublet": _boolean(raw.get("run_scrublet", False)),
            "doublet_batch_key": str(raw.get("doublet_batch_key") or "").strip(),
            "exclude_predicted_doublets": _boolean(
                raw.get("exclude_predicted_doublets", False)
            ),
        }
    )
    if values["exclude_predicted_doublets"] and not values["run_scrublet"]:
        raise SingleCellError("exclude_predicted_doublets requires run_scrublet=true.")
    if values["doublet_batch_key"] and not values["run_scrublet"]:
        raise SingleCellError("doublet_batch_key requires run_scrublet=true.")
    return values


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"", "0", "false", "no", "off"}:
        return False
    raise SingleCellError(f"Expected a boolean value; found {value!r}.")


def _resolve_table(value: str, label: str) -> tuple[Path, str]:
    try:
        path = resolve_workspace_path(str(value or "").strip())
    except Exception as exc:
        raise SingleCellError(str(exc)) from exc
    if not path.is_file():
        raise SingleCellError(f"{label.capitalize()} does not exist: {value}")
    if path.suffix.lower() not in TABLE_SUFFIXES:
        raise SingleCellError(f"{label.capitalize()} must be an uncompressed CSV or TSV file.")
    if path.stat().st_size > MAX_UPLOAD_BYTES:
        raise SingleCellError(f"{label.capitalize()} exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.")
    return path, path.relative_to(WORKSPACE_ROOT).as_posix()


def _resolve_count_input(value: str) -> dict[str, Any]:
    try:
        path = resolve_workspace_path(str(value or "").strip())
    except Exception as exc:
        raise SingleCellError(str(exc)) from exc
    if not path.is_file():
        raise SingleCellError(f"Single-cell count input does not exist: {value}")
    name = path.name.lower()
    if path.suffix.lower() in TABLE_SUFFIXES:
        input_format = path.suffix.lower().lstrip(".")
        files = [path]
    elif path.suffix.lower() == ".h5ad":
        input_format = "h5ad"
        files = [path]
    elif path.suffix.lower() in {".h5", ".hdf5"}:
        input_format = "10x_h5"
        files = [path]
    elif name in {"matrix.mtx", "matrix.mtx.gz"}:
        compressed = name.endswith(".gz")
        suffix = ".tsv.gz" if compressed else ".tsv"
        barcodes = path.parent / f"barcodes{suffix}"
        features = path.parent / f"features{suffix}"
        genes = path.parent / f"genes{suffix}"
        feature_file = features if features.is_file() else genes
        missing = []
        if not barcodes.is_file():
            missing.append(barcodes.name)
        if not feature_file.is_file():
            missing.append(f"features{suffix} or genes{suffix}")
        if missing:
            raise SingleCellError(
                "10x MTX input requires standard files in the same directory; missing "
                + ", ".join(missing)
                + "."
            )
        input_format = "10x_mtx_gz" if compressed else "10x_mtx"
        files = [path, barcodes, feature_file]
    else:
        raise SingleCellError(
            "Single-cell input must be CSV/TSV, AnnData .h5ad, 10x .h5/.hdf5, or a standard matrix.mtx[.gz] trio."
        )
    total = 0
    for item in files:
        size = item.stat().st_size
        if size > MAX_UPLOAD_BYTES:
            raise SingleCellError(
                f"Single-cell input file {item.name} exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
            )
        total += size
    if total > MAX_UPLOAD_BYTES:
        raise SingleCellError(
            f"Single-cell input files exceed the combined {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."
        )
    return {
        "path": path,
        "relative": path.relative_to(WORKSPACE_ROOT).as_posix(),
        "input_format": input_format,
        "input_files": [item.relative_to(WORKSPACE_ROOT).as_posix() for item in files],
    }


def _inspect_with_scanpy(python: Path, config: dict[str, Any]) -> dict[str, Any]:
    if not INSPECTOR_PATH.is_file():
        raise SingleCellError("The local single-cell input inspector is missing.")
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="single-cell-preflight-", dir=temp_root) as temporary:
        config_path = Path(temporary) / "config.json"
        output_path = Path(temporary) / "inspection.json"
        config_path.write_text(json.dumps(config, ensure_ascii=True), encoding="utf-8")
        environment = {
            **os.environ,
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
        try:
            _run_process(
                [str(python), str(INSPECTOR_PATH), str(config_path), str(output_path)],
                environment,
            )
        except SingleCellError as exc:
            detail = str(exc).removeprefix("Scanpy analysis failed: ")
            raise SingleCellError(f"Single-cell input inspection failed: {detail}") from exc
        try:
            return json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SingleCellError("Single-cell input inspection returned no valid result.") from exc


def _delimiter(path: Path | None) -> str:
    return "\t" if path and path.suffix.lower() == ".tsv" else ","


def _distribution(values: list[int] | list[float]) -> dict[str, float]:
    ordered = sorted(float(value) for value in values)
    return {
        "min": round(ordered[0], 3),
        "median": round(_quantile(ordered, 0.5), 3),
        "max": round(ordered[-1], 3),
    }


def _quantile(ordered: list[float], fraction: float) -> float:
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@functools.lru_cache(maxsize=4)
def _probe_scanpy(python: Path) -> dict[str, str] | None:
    try:
        completed = subprocess.run(
            [
                str(python),
                "-c",
                "import importlib.metadata as m, json, scanpy, leidenalg; "
                "v=lambda n: m.version(n) if n in {d.metadata['Name'] for d in m.distributions()} else None; "
                "print(json.dumps({'scanpy': m.version('scanpy'), 'leidenalg': m.version('leidenalg'), 'scikit_image': v('scikit-image')}))",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return None


def _run_process(command: list[str], environment: dict[str, str]) -> None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=PROCESS_TIMEOUT_SECONDS,
            env=environment,
            cwd=ROOT,
        )
    except subprocess.TimeoutExpired as exc:
        raise SingleCellError("Scanpy analysis exceeded the 15-minute runtime limit.") from exc
    except OSError as exc:
        raise SingleCellError(f"Could not start Scanpy: {exc}") from exc
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout or "").split())[-1200:]
        raise SingleCellError(f"Scanpy analysis failed: {detail or 'unknown error'}")
