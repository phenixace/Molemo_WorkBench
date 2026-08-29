"""Approval-gated import and bounded inspection of NCBI GEO Series Matrix files."""

from __future__ import annotations

import csv
import gzip
import hashlib
import html
import io
import json
import math
import random
import re
import shutil
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

from bio_clients import ExternalDataError, get_binary, get_head_metadata, get_text
from workspace_utils import WORKSPACE_ROOT


GEO_FTP_ROOT = "https://ftp.ncbi.nlm.nih.gov/geo/series"
MAX_COMPRESSED_BYTES = 32 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 160 * 1024 * 1024
MAX_LINE_BYTES = 2 * 1024 * 1024
MAX_SAMPLES = 500
MAX_FEATURES = 100_000
MAX_MATRIX_CELLS = 12_000_000
MAX_METADATA_FIELDS = 60
RESERVOIR_SIZE = 2048
GLOBAL_RESERVOIR_SIZE = 20_000
MISSING_VALUES = {"", "na", "nan", "null", "n/a"}
EXCLUDED_SAMPLE_METADATA_PREFIXES = ("contact_",)


class GeoSeriesMatrixError(ValueError):
    """Raised when a Series Matrix source or payload is invalid."""


def normalize_geo_series_matrix_inputs(accession: str, matrix_file: str = "") -> dict[str, str]:
    normalized_accession = str(accession or "").strip().upper()
    if not re.fullmatch(r"GSE[1-9][0-9]{0,8}", normalized_accession):
        raise GeoSeriesMatrixError("GEO Series accession must use the exact GSE<number> form.")
    normalized_file = str(matrix_file or "").strip()
    if normalized_file:
        if Path(normalized_file).name != normalized_file or not re.fullmatch(
            rf"{re.escape(normalized_accession)}(?:-GPL[1-9][0-9]*)?_series_matrix\.txt\.gz",
            normalized_file,
            re.I,
        ):
            raise GeoSeriesMatrixError(
                "matrix_file must be an exact Series Matrix filename for the requested GSE accession."
            )
    directory_url = _matrix_directory_url(normalized_accession)
    return {
        "accession": normalized_accession,
        "matrix_file": normalized_file,
        "directory_url": directory_url,
    }


def preflight_geo_series_matrix(accession: str, matrix_file: str = "") -> dict[str, Any]:
    normalized = normalize_geo_series_matrix_inputs(accession, matrix_file)
    try:
        listing = get_text(normalized["directory_url"])
    except ExternalDataError as exc:
        raise GeoSeriesMatrixError(str(exc)) from exc
    available_files = parse_matrix_directory_listing(listing, normalized["accession"])
    if not available_files:
        raise GeoSeriesMatrixError(
            f"{normalized['accession']} does not expose a GEO Series Matrix file in its official matrix directory."
        )

    selected = normalized["matrix_file"]
    if selected and selected not in available_files:
        raise GeoSeriesMatrixError(
            f"matrix_file was not found for {normalized['accession']}; available files: "
            + ", ".join(available_files)
        )
    if not selected and len(available_files) == 1:
        selected = available_files[0]

    download_url = urljoin(normalized["directory_url"], quote(selected, safe="-_.")) if selected else ""
    response_metadata: dict[str, Any] = {}
    if download_url:
        try:
            response_metadata = get_head_metadata(download_url)
        except ExternalDataError as exc:
            raise GeoSeriesMatrixError(str(exc)) from exc
        content_length = response_metadata.get("content_length")
        if content_length is not None and int(content_length) > MAX_COMPRESSED_BYTES:
            raise GeoSeriesMatrixError(
                f"Series Matrix is {int(content_length):,} compressed bytes; the local limit is "
                f"{MAX_COMPRESSED_BYTES:,} bytes."
            )

    ready = bool(selected)
    warnings = [
        "GEO Series Matrix values are submitter-processed measurements, not established raw counts.",
        "Sample titles and characteristics are submitter metadata; experimental groups and independent replicates require researcher review.",
        "The importer does not infer normalization, batch correction, platform annotation, or a differential-expression design.",
    ]
    if not ready:
        warnings.insert(0, "Multiple platform-specific matrices are available; choose one exact matrix_file before approval.")
    if ready and response_metadata.get("content_length") is None:
        warnings.insert(0, "The source did not report a compressed size; execution remains bounded by the local download limit.")
    return {
        "ready": ready,
        "source": "NCBI GEO Series Matrix",
        "source_url": normalized["directory_url"],
        "accession": normalized["accession"],
        "matrix_file": selected,
        "available_files": available_files,
        "download_url": download_url,
        "compressed_bytes": response_metadata.get("content_length"),
        "content_type": response_metadata.get("content_type", ""),
        "last_modified": response_metadata.get("last_modified", ""),
        "limits": {
            "compressed_bytes": MAX_COMPRESSED_BYTES,
            "uncompressed_bytes": MAX_UNCOMPRESSED_BYTES,
            "samples": MAX_SAMPLES,
            "features": MAX_FEATURES,
            "matrix_cells": MAX_MATRIX_CELLS,
        },
        "warnings": warnings,
        "summary": (
            f"Validated official Series Matrix source {selected} for {normalized['accession']}."
            if ready
            else f"Found {len(available_files)} Series Matrix files for {normalized['accession']}; choose one before approval."
        ),
    }


def import_geo_series_matrix(accession: str, matrix_file: str = "") -> dict[str, Any]:
    preflight = preflight_geo_series_matrix(accession, matrix_file)
    if not preflight["ready"]:
        raise GeoSeriesMatrixError(
            "Multiple Series Matrix files are available; provide one of: "
            + ", ".join(preflight["available_files"])
        )
    try:
        compressed = get_binary(preflight["download_url"], MAX_COMPRESSED_BYTES)
    except ExternalDataError as exc:
        raise GeoSeriesMatrixError(str(exc)) from exc
    if not compressed.startswith(b"\x1f\x8b"):
        raise GeoSeriesMatrixError("The official Series Matrix download is not a gzip payload.")

    analysis_id = f"geo-series-matrix-{uuid.uuid4().hex[:12]}"
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / analysis_id
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()

    with tempfile.TemporaryDirectory(prefix="geo-series-matrix-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        source_path = output / preflight["matrix_file"]
        source_path.write_bytes(compressed)
        parsed = parse_geo_series_matrix(compressed, output / "expression_matrix.tsv")
        _write_sample_metadata(output / "sample_metadata.tsv", parsed["sample_metadata"], parsed["sample_metadata_fields"])

        outputs = {
            "expression_matrix": f"{relative_root}/expression_matrix.tsv",
            "sample_metadata": f"{relative_root}/sample_metadata.tsv",
            "source_matrix": f"{relative_root}/{preflight['matrix_file']}",
            "report": f"{relative_root}/matrix_summary.json",
            "manifest": f"{relative_root}/run_manifest.json",
            "summary": f"{relative_root}/summary.md",
        }
        result = {
            "analysis_id": analysis_id,
            "method": "NCBI GEO Series Matrix bounded import",
            "source": "NCBI GEO Series Matrix",
            "source_url": preflight["download_url"],
            "retrieved_at": retrieved_at,
            "accession": preflight["accession"],
            "matrix_file": preflight["matrix_file"],
            "compressed_bytes": len(compressed),
            "source_sha256": hashlib.sha256(compressed).hexdigest(),
            "preflight": preflight,
            **parsed,
            "raw_count_compatible": False,
            "contact_metadata_omitted": True,
            "value_semantics": (
                "Submitter-processed GEO Series Matrix values; confirm transformation, normalization, feature annotation, "
                "and analysis design in the GEO record and associated publication."
            ),
            "analysis_handoff": (
                "Use the imported matrix for descriptive inspection only until sample groups, biological replication, "
                "platform annotation, normalization and batch structure are confirmed. The existing PyDESeq2 workflow "
                "requires raw non-negative integer counts and must not consume this matrix directly."
            ),
            "output_root": relative_root,
            "outputs": outputs,
            "caveats": [
                "Series Matrix values are submitter-processed and cannot be assumed to be raw counts, TPM, CPM, log2 values, or cross-study comparable.",
                "Sample characteristics are free-text metadata; inferred groups, paired samples, repeated measures and batches require manual confirmation.",
                "Probe or feature identifiers are preserved as submitted and are not automatically mapped to current genes or transcripts.",
                "This import performs structural and descriptive QC only; it does not fit a statistical model or support a biological conclusion.",
                "Submitter contact fields are intentionally omitted from the local sample metadata because they are not required for analysis.",
            ],
        }
        result["summary"] = (
            f"Imported {result['accession']} Series Matrix with {result['feature_count']:,} features and "
            f"{result['sample_count']:,} samples; {result['matrix_metrics']['missing_fraction']:.2%} values are missing."
        )
        (output / "matrix_summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": analysis_id,
            "method": result["method"],
            "source": result["source"],
            "source_url": result["source_url"],
            "retrieved_at": retrieved_at,
            "accession": result["accession"],
            "matrix_file": result["matrix_file"],
            "compressed_bytes": len(compressed),
            "uncompressed_bytes": result["uncompressed_bytes"],
            "source_sha256": result["source_sha256"],
            "dimensions": {"features": result["feature_count"], "samples": result["sample_count"]},
            "limits": preflight["limits"],
            "value_semantics": result["value_semantics"],
            "raw_count_compatible": False,
            "contact_metadata_omitted": True,
            "files": [Path(value).name for value in outputs.values()],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise GeoSeriesMatrixError(f"Analysis output already exists: {analysis_id}")
        shutil.move(str(output), str(final_output))
    return result


def parse_matrix_directory_listing(listing: str, accession: str) -> list[str]:
    normalized_accession = normalize_geo_series_matrix_inputs(accession)["accession"]
    pattern = re.compile(
        rf"^{re.escape(normalized_accession)}(?:-GPL[1-9][0-9]*)?_series_matrix\.txt\.gz$",
        re.I,
    )
    found: list[str] = []
    for href in re.findall(r"href=[\"']([^\"']+)[\"']", str(listing or ""), re.I):
        name = html.unescape(href).split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1]
        if pattern.fullmatch(name) and name not in found:
            found.append(name)
    return sorted(found)


def parse_geo_series_matrix(compressed: bytes, expression_output: Path) -> dict[str, Any]:
    series_metadata: dict[str, list[str]] = defaultdict(list)
    sample_metadata_rows: dict[str, list[list[str]]] = defaultdict(list)
    samples: list[str] = []
    sample_stats: list[dict[str, Any]] = []
    sample_reservoirs: list[list[float]] = []
    sample_rngs: list[random.Random] = []
    feature_ids: set[str] = set()
    feature_preview: list[dict[str, Any]] = []
    global_reservoir: list[float] = []
    global_rng = random.Random(1701)
    numeric_count = 0
    missing_count = 0
    integer_count = 0
    nonnegative_count = 0
    uncompressed_bytes = 0
    feature_count = 0
    table_started = False
    table_header_seen = False
    table_finished = False

    expression_output.parent.mkdir(parents=True, exist_ok=True)
    try:
        gzip_stream = gzip.GzipFile(fileobj=io.BytesIO(bytes(compressed)), mode="rb")
        with gzip_stream, expression_output.open("w", encoding="utf-8", newline="") as expression_handle:
            writer = csv.writer(expression_handle, delimiter="\t", lineterminator="\n")
            while True:
                raw_line = gzip_stream.readline(MAX_LINE_BYTES + 1)
                if not raw_line:
                    break
                if len(raw_line) > MAX_LINE_BYTES:
                    raise GeoSeriesMatrixError("Series Matrix contains a line above the local size limit.")
                uncompressed_bytes += len(raw_line)
                if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                    raise GeoSeriesMatrixError("Series Matrix exceeded the local uncompressed size limit.")
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == "!series_matrix_table_begin":
                    table_started = True
                    continue
                if line == "!series_matrix_table_end":
                    table_finished = True
                    break
                if not table_started:
                    _collect_matrix_metadata(line, series_metadata, sample_metadata_rows)
                    continue
                if not line:
                    continue
                fields = next(csv.reader([line], delimiter="\t", quotechar='"'))
                if not table_header_seen:
                    if len(fields) < 2 or fields[0].strip().upper() not in {"ID_REF", "IDENTIFIER"}:
                        raise GeoSeriesMatrixError("Series Matrix table header must start with ID_REF.")
                    samples = [value.strip() for value in fields[1:]]
                    if not samples or len(samples) > MAX_SAMPLES:
                        raise GeoSeriesMatrixError(f"Series Matrix must contain 1 to {MAX_SAMPLES} samples.")
                    if len(set(samples)) != len(samples) or any(not re.fullmatch(r"GSM[1-9][0-9]*", value, re.I) for value in samples):
                        raise GeoSeriesMatrixError("Series Matrix sample columns must be unique GSM accessions.")
                    sample_stats = [
                        {"sample": sample, "numeric": 0, "missing": 0, "min": None, "max": None, "sum": 0.0, "sum_sq": 0.0}
                        for sample in samples
                    ]
                    sample_reservoirs = [[] for _ in samples]
                    sample_rngs = [random.Random(2300 + index) for index in range(len(samples))]
                    writer.writerow(["feature_id", *samples])
                    table_header_seen = True
                    continue

                if len(fields) != len(samples) + 1:
                    raise GeoSeriesMatrixError(
                        f"Series Matrix row {feature_count + 1} has {len(fields) - 1} values for {len(samples)} samples."
                    )
                feature_id = fields[0].strip()
                if not feature_id:
                    raise GeoSeriesMatrixError(f"Series Matrix row {feature_count + 1} has an empty feature identifier.")
                if feature_id in feature_ids:
                    raise GeoSeriesMatrixError(f"Series Matrix contains duplicate feature identifier: {feature_id}")
                feature_ids.add(feature_id)
                feature_count += 1
                if feature_count > MAX_FEATURES or feature_count * len(samples) > MAX_MATRIX_CELLS:
                    raise GeoSeriesMatrixError("Series Matrix dimensions exceed the local feature or cell limit.")

                output_values: list[str] = []
                preview_values: list[str] = []
                for index, raw_value in enumerate(fields[1:]):
                    token = raw_value.strip()
                    if token.casefold() in MISSING_VALUES:
                        output_values.append("")
                        sample_stats[index]["missing"] += 1
                        missing_count += 1
                        if index < 8:
                            preview_values.append("")
                        continue
                    try:
                        value = float(token)
                    except ValueError as exc:
                        raise GeoSeriesMatrixError(
                            f"Series Matrix contains non-numeric value at feature {feature_id}, sample {samples[index]}."
                        ) from exc
                    if not math.isfinite(value):
                        raise GeoSeriesMatrixError(
                            f"Series Matrix contains a non-finite value at feature {feature_id}, sample {samples[index]}."
                        )
                    output_values.append(token)
                    if index < 8:
                        preview_values.append(token)
                    stats = sample_stats[index]
                    stats["numeric"] += 1
                    stats["sum"] += value
                    stats["sum_sq"] += value * value
                    stats["min"] = value if stats["min"] is None else min(stats["min"], value)
                    stats["max"] = value if stats["max"] is None else max(stats["max"], value)
                    numeric_count += 1
                    integer_count += int(abs(value - round(value)) <= 1e-9)
                    nonnegative_count += int(value >= 0)
                    _reservoir_add(sample_reservoirs[index], value, stats["numeric"], sample_rngs[index], RESERVOIR_SIZE)
                    _reservoir_add(global_reservoir, value, numeric_count, global_rng, GLOBAL_RESERVOIR_SIZE)
                writer.writerow([feature_id, *output_values])
                if len(feature_preview) < 12:
                    feature_preview.append({"feature_id": feature_id, "values": preview_values})
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise GeoSeriesMatrixError(f"Could not decompress the Series Matrix: {exc}") from exc

    if not table_header_seen or not table_finished or feature_count == 0:
        raise GeoSeriesMatrixError("Series Matrix did not contain one complete non-empty expression table.")
    if numeric_count == 0:
        raise GeoSeriesMatrixError("Series Matrix did not contain numeric measurements.")

    sample_metadata, metadata_fields = _build_sample_metadata(samples, sample_metadata_rows)
    metadata_summaries = _metadata_summaries(sample_metadata, metadata_fields)
    sample_summaries = []
    for index, stats in enumerate(sample_stats):
        values = sorted(sample_reservoirs[index])
        count = int(stats["numeric"])
        mean = stats["sum"] / count if count else None
        variance = max(0.0, stats["sum_sq"] / count - mean * mean) if count and mean is not None else None
        metadata = sample_metadata[index]
        sample_summaries.append(
            {
                "sample": stats["sample"],
                "title": metadata.get("title", ""),
                "source": metadata.get("source_name_ch1", ""),
                "organism": metadata.get("organism_ch1", ""),
                "numeric": count,
                "missing": int(stats["missing"]),
                "missing_fraction": int(stats["missing"]) / feature_count,
                "min": stats["min"],
                "q1": _quantile(values, 0.25),
                "median": _quantile(values, 0.5),
                "q3": _quantile(values, 0.75),
                "max": stats["max"],
                "mean": mean,
                "standard_deviation": math.sqrt(variance) if variance is not None else None,
                "quantiles_approximate": count > len(values),
            }
        )

    total_cells = feature_count * len(samples)
    global_values = sorted(global_reservoir)
    matrix_metrics = {
        "total_cells": total_cells,
        "numeric_values": numeric_count,
        "missing_values": missing_count,
        "missing_fraction": missing_count / total_cells,
        "integer_fraction": integer_count / numeric_count,
        "nonnegative_fraction": nonnegative_count / numeric_count,
        "min": min(item["min"] for item in sample_stats if item["min"] is not None),
        "q1": _quantile(global_values, 0.25),
        "median": _quantile(global_values, 0.5),
        "q3": _quantile(global_values, 0.75),
        "max": max(item["max"] for item in sample_stats if item["max"] is not None),
        "quantiles_approximate": numeric_count > len(global_values),
    }
    return {
        "series_title": _first_series_value(series_metadata, "title"),
        "series_type": series_metadata.get("type", []),
        "series_summary": _first_series_value(series_metadata, "summary")[:2000],
        "feature_count": feature_count,
        "sample_count": len(samples),
        "samples": samples,
        "uncompressed_bytes": uncompressed_bytes,
        "matrix_metrics": matrix_metrics,
        "sample_summaries": sample_summaries,
        "sample_metadata": sample_metadata,
        "sample_metadata_fields": metadata_fields,
        "metadata_summaries": metadata_summaries,
        "feature_preview": feature_preview,
        "preview_samples": samples[:8],
    }


def _collect_matrix_metadata(
    line: str,
    series_metadata: dict[str, list[str]],
    sample_metadata_rows: dict[str, list[list[str]]],
) -> None:
    if not line.startswith("!") or "\t" not in line:
        return
    fields = next(csv.reader([line], delimiter="\t", quotechar='"'))
    key = fields[0].strip()
    values = [value.strip() for value in fields[1:]]
    if key.startswith("!Series_"):
        series_metadata[key.removeprefix("!Series_").casefold()].extend(value for value in values if value)
    elif key.startswith("!Sample_"):
        sample_metadata_rows[key.removeprefix("!Sample_").casefold()].append(values)


def _build_sample_metadata(
    samples: list[str], sample_rows: dict[str, list[list[str]]]
) -> tuple[list[dict[str, str]], list[str]]:
    priority = [
        "title", "geo_accession", "source_name_ch1", "organism_ch1", "characteristics_ch1",
        "molecule_ch1", "label_ch1", "extract_protocol_ch1", "data_processing", "platform_id",
    ]
    populated = [
        key for key, rows in sample_rows.items()
        if not key.startswith(EXCLUDED_SAMPLE_METADATA_PREFIXES)
        and any(any(value.strip() for value in row) for row in rows)
    ]
    ordered = [key for key in priority if key in populated]
    ordered.extend(sorted(key for key in populated if key not in ordered))
    ordered = ordered[:MAX_METADATA_FIELDS]
    metadata: list[dict[str, str]] = []
    for sample_index, sample in enumerate(samples):
        record = {"sample": sample}
        for key in ordered:
            values = []
            for row in sample_rows[key]:
                value = row[sample_index].strip() if sample_index < len(row) else ""
                if value and value not in values:
                    values.append(value)
            record[key] = "; ".join(values)
        metadata.append(record)
    return metadata, ["sample", *ordered]


def _metadata_summaries(metadata: list[dict[str, str]], fields: list[str]) -> list[dict[str, Any]]:
    summaries = []
    for field in fields:
        if field == "sample":
            continue
        values = [row.get(field, "") for row in metadata if row.get(field, "")]
        unique = list(dict.fromkeys(values))
        summaries.append(
            {
                "field": field,
                "populated": len(values),
                "missing": len(metadata) - len(values),
                "unique_count": len(unique),
                "example_values": unique[:8],
            }
        )
    return summaries


def _write_sample_metadata(path: Path, metadata: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(metadata)


def _summary_markdown(result: dict[str, Any]) -> str:
    metrics = result["matrix_metrics"]
    lines = [
        f"# {result['accession']} Series Matrix import",
        "",
        result["series_title"] or "Untitled GEO Series",
        "",
        f"- Source: [{result['matrix_file']}]({result['source_url']})",
        f"- Dimensions: {result['feature_count']:,} features x {result['sample_count']:,} samples",
        f"- Missing values: {metrics['missing_fraction']:.2%}",
        f"- Integer-valued observations: {metrics['integer_fraction']:.2%}",
        f"- Source SHA-256: `{result['source_sha256']}`",
        "",
        "## Interpretation boundary",
        "",
        result["analysis_handoff"],
        "",
        "The imported values and free-text sample annotations must be checked against the GEO record and associated publication before analysis.",
    ]
    return "\n".join(lines) + "\n"


def _matrix_directory_url(accession: str) -> str:
    digits = accession[3:]
    range_name = f"GSE{digits[:-3]}nnn" if len(digits) > 3 else "GSEnnn"
    return f"{GEO_FTP_ROOT}/{range_name}/{accession}/matrix/"


def _reservoir_add(
    reservoir: list[float], value: float, seen: int, rng: random.Random, limit: int
) -> None:
    if len(reservoir) < limit:
        reservoir.append(value)
        return
    replacement = rng.randrange(seen)
    if replacement < limit:
        reservoir[replacement] = value


def _quantile(sorted_values: list[float], fraction: float) -> float | None:
    if not sorted_values:
        return None
    position = (len(sorted_values) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _first_series_value(metadata: dict[str, list[str]], key: str) -> str:
    values = metadata.get(key, [])
    return values[0] if values else ""
