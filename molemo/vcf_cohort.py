"""Bounded multi-sample VCF review with explicit call and provenance semantics."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import statistics
import tempfile
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .workspace_utils import WORKSPACE_ROOT, resolve_workspace_path


MAX_VCF_BYTES = 20 * 1024 * 1024
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_LINE_CHARS = 2 * 1024 * 1024
MAX_SAMPLES = 96
MAX_RECORDS = 20_000
MAX_ALLELES = 40_000
MAX_CALL_ROWS = 250_000
MAX_TEXT_CHARS = 2_000
LOW_FREQUENCY_VAF = 0.05

ANNOTATION_DEFAULTS = {
    "CSQ": [
        "Allele",
        "Consequence",
        "IMPACT",
        "SYMBOL",
        "Gene",
        "Feature_type",
        "Feature",
        "BIOTYPE",
        "EXON",
        "HGVSc",
        "HGVSp",
    ],
    "ANN": [
        "Allele",
        "Annotation",
        "Annotation_Impact",
        "Gene_Name",
        "Gene_ID",
        "Feature_Type",
        "Feature_ID",
        "Transcript_BioType",
        "Rank",
        "HGVS.c",
        "HGVS.p",
    ],
}


class VcfCohortError(ValueError):
    """Raised when a local VCF cohort cannot be reviewed safely."""


def preflight_vcf_cohort(
    vcf_path: str,
    metadata_path: str = "",
    sample_column: str = "sample",
    subject_column: str = "subject",
    timepoint_column: str = "timepoint",
    time_order_column: str = "time_order",
    min_vaf: float = 0.01,
    min_depth: int = 10,
    include_filtered: bool = False,
) -> dict[str, Any]:
    inputs = normalize_vcf_inputs(
        vcf_path,
        metadata_path,
        sample_column,
        subject_column,
        timepoint_column,
        time_order_column,
        min_vaf,
        min_depth,
        include_filtered,
    )
    analysis = _analyze_vcf(inputs)
    warnings = _caveats(inputs["metadata_path"] != "")[:4]
    return {
        "ready": True,
        "vcf_path": inputs["vcf_path"],
        "metadata_path": inputs["metadata_path"],
        "fileformat": analysis["header"]["fileformat"],
        "reference": analysis["header"]["reference"],
        "samples": analysis["samples"],
        "sample_count": analysis["sample_count"],
        "subject_count": analysis["subject_count"],
        "record_count": analysis["record_count"],
        "allele_count": analysis["allele_count"],
        "included_call_count": analysis["included_call_count"],
        "low_frequency_call_count": analysis["low_frequency_call_count"],
        "recurrent_variant_count": analysis["recurrent_variant_count"],
        "annotation_sources": analysis["header"]["annotation_sources"],
        "thresholds": analysis["thresholds"],
        "warnings": warnings,
        "summary": (
            f"Validated {analysis['header']['fileformat']} with {analysis['sample_count']} samples, "
            f"{analysis['record_count']} records and {analysis['allele_count']} alternate alleles; "
            f"{analysis['included_call_count']} sample-variant calls meet the proposed filters."
        ),
    }


def review_vcf_cohort(
    vcf_path: str,
    metadata_path: str = "",
    sample_column: str = "sample",
    subject_column: str = "subject",
    timepoint_column: str = "timepoint",
    time_order_column: str = "time_order",
    min_vaf: float = 0.01,
    min_depth: int = 10,
    include_filtered: bool = False,
) -> dict[str, Any]:
    inputs = normalize_vcf_inputs(
        vcf_path,
        metadata_path,
        sample_column,
        subject_column,
        timepoint_column,
        time_order_column,
        min_vaf,
        min_depth,
        include_filtered,
    )
    result = _analyze_vcf(inputs)
    result.update(
        {
            "analysis_id": f"vcf-cohort-{uuid.uuid4().hex[:12]}",
            "method": "Bounded VCF 4.x cohort review",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "source": "Local workspace VCF",
            "inputs": inputs,
            "outputs": {},
            "caveats": _caveats(inputs["metadata_path"] != ""),
        }
    )
    result["summary"] = (
        f"Reviewed {result['allele_count']} alternate alleles across {result['sample_count']} samples. "
        f"{result['included_call_count']} sample-variant calls met the explicit depth, VAF and FILTER rules; "
        f"{result['low_frequency_call_count']} were below {LOW_FREQUENCY_VAF:.0%} VAF and "
        f"{result['recurrent_variant_count']} variants appeared in at least two samples. "
        "No somatic, germline, driver, treatment or clinical-actionability conclusion was generated."
    )
    _persist_review(result)
    return result


def normalize_vcf_inputs(
    vcf_path: str,
    metadata_path: str = "",
    sample_column: str = "sample",
    subject_column: str = "subject",
    timepoint_column: str = "timepoint",
    time_order_column: str = "time_order",
    min_vaf: float = 0.01,
    min_depth: int = 10,
    include_filtered: bool = False,
) -> dict[str, Any]:
    vcf_relative = str(vcf_path or "").strip()
    if not vcf_relative:
        raise VcfCohortError("A workspace-relative VCF path is required.")
    target = resolve_workspace_path(vcf_relative)
    if target.suffix.casefold() != ".vcf":
        raise VcfCohortError("Use an uncompressed text .vcf file; VCF.gz and BCF are not supported yet.")
    _validate_file(target, MAX_VCF_BYTES, "VCF")

    metadata_relative = str(metadata_path or "").strip()
    if metadata_relative:
        metadata_target = resolve_workspace_path(metadata_relative)
        if metadata_target.suffix.casefold() not in {".csv", ".tsv"}:
            raise VcfCohortError("Sample metadata must be a workspace CSV or TSV file.")
        _validate_file(metadata_target, MAX_METADATA_BYTES, "Sample metadata")

    columns = {
        "sample_column": str(sample_column or "sample").strip(),
        "subject_column": str(subject_column or "subject").strip(),
        "timepoint_column": str(timepoint_column or "timepoint").strip(),
        "time_order_column": str(time_order_column or "time_order").strip(),
    }
    if any(not value for value in columns.values()):
        raise VcfCohortError("Sample, subject, timepoint and time-order column names are required.")
    try:
        normalized_vaf = float(min_vaf)
        normalized_depth = int(min_depth)
    except (TypeError, ValueError) as exc:
        raise VcfCohortError("VCF thresholds must be numeric.") from exc
    if not 0 <= normalized_vaf <= 1:
        raise VcfCohortError("min_vaf must be between 0 and 1.")
    if not 0 <= normalized_depth <= 100_000:
        raise VcfCohortError("min_depth must be between 0 and 100000.")
    include = include_filtered is True or str(include_filtered).strip().casefold() in {
        "1",
        "true",
        "yes",
    }
    return {
        "vcf_path": target.relative_to(WORKSPACE_ROOT.resolve()).as_posix(),
        "metadata_path": (
            resolve_workspace_path(metadata_relative).relative_to(WORKSPACE_ROOT.resolve()).as_posix()
            if metadata_relative
            else ""
        ),
        **columns,
        "min_vaf": normalized_vaf,
        "min_depth": normalized_depth,
        "include_filtered": include,
    }


def _analyze_vcf(inputs: dict[str, Any]) -> dict[str, Any]:
    target = resolve_workspace_path(inputs["vcf_path"])
    header, records = _read_vcf(target)
    metadata, metadata_provided = _read_metadata(inputs, header["samples"])
    metadata_by_sample = {item["sample"]: item for item in metadata}
    sample_stats = {
        sample: {
            "sample": sample,
            "subject": metadata_by_sample[sample]["subject"],
            "timepoint": metadata_by_sample[sample]["timepoint"],
            "time_order": metadata_by_sample[sample]["time_order"],
            "records_with_depth": 0,
            "depth_sum": 0,
            "observed_calls": 0,
            "included_calls": 0,
            "low_frequency_calls": 0,
            "excluded_low_depth": 0,
            "excluded_low_vaf": 0,
            "excluded_filter": 0,
        }
        for sample in header["samples"]
    }
    variants: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    calls_by_variant_sample: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        for alt_index, alt in enumerate(record["alts"], 1):
            annotation = _annotation_for_alt(record["info"], alt, header["annotation_formats"])
            variant_id = _variant_id(record["chrom"], record["pos"], record["ref"], alt)
            variant_calls = []
            for sample, raw_sample in zip(header["samples"], record["sample_values"]):
                call = _sample_call(
                    sample,
                    raw_sample,
                    record["format_keys"],
                    alt_index,
                    len(record["alts"]),
                    record["record_pass"],
                    inputs,
                )
                stats = sample_stats[sample]
                if alt_index == 1 and call["depth"] is not None:
                    stats["records_with_depth"] += 1
                    stats["depth_sum"] += call["depth"]
                if not call["observed"]:
                    continue
                stats["observed_calls"] += 1
                if call["included"]:
                    stats["included_calls"] += 1
                    if call["vaf"] is not None and call["vaf"] < LOW_FREQUENCY_VAF:
                        stats["low_frequency_calls"] += 1
                elif call["status"] in stats:
                    stats[call["status"]] += 1
                call.update(
                    {
                        "variant_id": variant_id,
                        "chrom": record["chrom"],
                        "pos": record["pos"],
                        "ref": record["ref"],
                        "alt": alt,
                        "gene": annotation["gene"],
                        "consequence": annotation["consequence"],
                        "subject": metadata_by_sample[sample]["subject"],
                        "timepoint": metadata_by_sample[sample]["timepoint"],
                        "time_order": metadata_by_sample[sample]["time_order"],
                    }
                )
                calls.append(call)
                variant_calls.append(call)
                calls_by_variant_sample[(variant_id, sample)] = call
                if len(calls) > MAX_CALL_ROWS:
                    raise VcfCohortError(
                        f"VCF produces more than {MAX_CALL_ROWS} observed sample-variant calls; filter or split it before review."
                    )
            included = [item for item in variant_calls if item["included"]]
            included_vafs = [item["vaf"] for item in included if item["vaf"] is not None]
            variants.append(
                {
                    "source_index": record["source_index"],
                    "variant_id": variant_id,
                    "chrom": record["chrom"],
                    "pos": record["pos"],
                    "id": record["id"],
                    "ref": record["ref"],
                    "alt": alt,
                    "type": _variant_type(record["ref"], alt),
                    "quality": record["quality"],
                    "filter": record["filter"],
                    "record_pass": record["record_pass"],
                    **annotation,
                    "observed_sample_count": len(variant_calls),
                    "included_sample_count": len({item["sample"] for item in included}),
                    "included_samples": [item["sample"] for item in included],
                    "max_vaf": max(included_vafs) if included_vafs else None,
                    "median_vaf": statistics.median(included_vafs) if included_vafs else None,
                    "low_frequency_call_count": sum(
                        item["vaf"] is not None and item["vaf"] < LOW_FREQUENCY_VAF
                        for item in included
                    ),
                }
            )
    sample_qc = []
    for item in sample_stats.values():
        item["mean_depth"] = (
            round(item["depth_sum"] / item["records_with_depth"], 2)
            if item["records_with_depth"]
            else None
        )
        item.pop("depth_sum")
        sample_qc.append(item)
    recurrent = sorted(
        [item for item in variants if item["included_sample_count"] > 0],
        key=lambda item: (
            -item["included_sample_count"],
            -(item["max_vaf"] if item["max_vaf"] is not None else -1),
            item["source_index"],
        ),
    )
    top_variants = recurrent[:30]
    mutation_matrix = {
        "samples": [item["sample"] for item in metadata],
        "variants": [
            {
                "variant_id": variant["variant_id"],
                "gene": variant["gene"],
                "consequence": variant["consequence"],
                "hgvsc": variant["hgvsc"],
                "hgvsp": variant["hgvsp"],
                "values": [
                    _matrix_value(calls_by_variant_sample.get((variant["variant_id"], sample)))
                    for sample in [item["sample"] for item in metadata]
                ],
            }
            for variant in top_variants
        ],
    }
    trajectories = _build_trajectories(
        top_variants,
        metadata,
        calls_by_variant_sample,
        metadata_provided,
    )
    included_calls = [item for item in calls if item["included"]]
    gene_counts = Counter(
        item["gene"] for item in variants if item["gene"] and item["included_sample_count"]
    )
    filter_counts = Counter(item["filter"] or "." for item in variants)
    return {
        "header": {
            key: value
            for key, value in header.items()
            if key not in {"samples", "annotation_formats"}
        },
        "samples": [item["sample"] for item in metadata],
        "sample_metadata": metadata,
        "metadata_provided": metadata_provided,
        "sample_count": len(metadata),
        "subject_count": len({item["subject"] for item in metadata}),
        "record_count": len(records),
        "allele_count": len(variants),
        "observed_call_count": len(calls),
        "included_call_count": len(included_calls),
        "low_frequency_call_count": sum(
            item["vaf"] is not None and item["vaf"] < LOW_FREQUENCY_VAF
            for item in included_calls
        ),
        "recurrent_variant_count": sum(item["included_sample_count"] >= 2 for item in variants),
        "gene_count": len(gene_counts),
        "thresholds": {
            "min_vaf": inputs["min_vaf"],
            "min_depth": inputs["min_depth"],
            "include_filtered": inputs["include_filtered"],
            "low_frequency_boundary": LOW_FREQUENCY_VAF,
        },
        "filter_counts": [
            {"label": label, "count": count}
            for label, count in sorted(filter_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "gene_counts": [
            {"label": label, "count": count}
            for label, count in sorted(gene_counts.items(), key=lambda item: (-item[1], item[0]))[:30]
        ],
        "sample_qc": sample_qc,
        "variants": variants,
        "calls": calls,
        "recurrent_variants": recurrent[:100],
        "mutation_matrix": mutation_matrix,
        "trajectories": trajectories,
    }


def _read_vcf(target: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fileformat = ""
    reference = ""
    source = ""
    annotation_formats: dict[str, list[str]] = {}
    annotation_sources = []
    samples: list[str] = []
    records = []
    header_seen = False
    try:
        with target.open("r", encoding="utf-8", newline="") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                if len(raw_line) > MAX_LINE_CHARS:
                    raise VcfCohortError(f"VCF line {line_number} exceeds the local line-size limit.")
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue
                if line.startswith("##"):
                    if line.startswith("##fileformat="):
                        fileformat = line.split("=", 1)[1].strip()
                    elif line.startswith("##reference="):
                        reference = _bounded_text(line.split("=", 1)[1])
                    elif line.startswith("##source="):
                        source = _bounded_text(line.split("=", 1)[1])
                    elif line.startswith("##INFO=<"):
                        definition = _meta_definition(line)
                        annotation_id = definition.get("ID", "")
                        if annotation_id in {"CSQ", "ANN"}:
                            fields = _annotation_fields(definition.get("Description", ""), annotation_id)
                            annotation_formats[annotation_id] = fields
                            annotation_sources.append(annotation_id)
                    continue
                if line.startswith("#CHROM"):
                    columns = line.split("\t")
                    if len(columns) < 8 or columns[:8] != [
                        "#CHROM",
                        "POS",
                        "ID",
                        "REF",
                        "ALT",
                        "QUAL",
                        "FILTER",
                        "INFO",
                    ]:
                        raise VcfCohortError("VCF header must use the standard tab-delimited fixed columns.")
                    if len(columns) > 8 and columns[8] != "FORMAT":
                        raise VcfCohortError("VCF sample columns require a FORMAT column.")
                    samples = columns[9:]
                    if not samples:
                        raise VcfCohortError("VCF cohort review requires at least one sample column.")
                    if len(samples) > MAX_SAMPLES:
                        raise VcfCohortError(f"VCF has more than the {MAX_SAMPLES}-sample limit.")
                    if len(set(samples)) != len(samples) or any(not sample.strip() for sample in samples):
                        raise VcfCohortError("VCF sample names must be non-empty and unique.")
                    header_seen = True
                    continue
                if line.startswith("#"):
                    continue
                if not header_seen:
                    raise VcfCohortError("VCF data appeared before the #CHROM header.")
                records.append(_parse_record(line, line_number, samples, len(records) + 1))
                if len(records) > MAX_RECORDS:
                    raise VcfCohortError(
                        f"VCF exceeds the {MAX_RECORDS}-record review limit; filter or split it first."
                    )
    except UnicodeDecodeError as exc:
        raise VcfCohortError("VCF must be UTF-8 text; compressed and binary inputs are unsupported.") from exc
    if not fileformat.startswith("VCFv4."):
        raise VcfCohortError("VCF must declare a supported VCFv4.x fileformat header.")
    if not header_seen:
        raise VcfCohortError("VCF is missing the #CHROM header.")
    if not records:
        raise VcfCohortError("VCF does not contain any variant records.")
    allele_count = sum(len(item["alts"]) for item in records)
    if allele_count > MAX_ALLELES:
        raise VcfCohortError(
            f"VCF exceeds the {MAX_ALLELES}-alternate-allele review limit; filter or split it first."
        )
    return (
        {
            "fileformat": fileformat,
            "reference": reference,
            "source": source,
            "samples": samples,
            "annotation_formats": annotation_formats,
            "annotation_sources": annotation_sources,
        },
        records,
    )


def _parse_record(
    line: str,
    line_number: int,
    samples: list[str],
    source_index: int,
) -> dict[str, Any]:
    columns = line.split("\t")
    expected = 9 + len(samples)
    if len(columns) != expected:
        raise VcfCohortError(
            f"VCF line {line_number} has {len(columns)} columns; expected {expected}."
        )
    chrom, pos_raw, identifier, ref, alt_raw, qual_raw, filter_raw, info_raw, format_raw = columns[:9]
    try:
        pos = int(pos_raw)
    except ValueError as exc:
        raise VcfCohortError(f"VCF line {line_number} has an invalid POS value.") from exc
    if pos < 1 or not chrom or not ref or not alt_raw:
        raise VcfCohortError(f"VCF line {line_number} has an invalid coordinate or allele.")
    alts = alt_raw.split(",")
    if any(not item or item == "." for item in alts):
        raise VcfCohortError(f"VCF line {line_number} has an unsupported missing ALT allele.")
    quality = _float_or_none(qual_raw)
    if qual_raw not in {"", "."} and quality is None:
        raise VcfCohortError(f"VCF line {line_number} has an invalid QUAL value.")
    format_keys = [] if format_raw in {"", "."} else format_raw.split(":")
    return {
        "source_index": source_index,
        "chrom": chrom,
        "pos": pos,
        "id": "" if identifier == "." else identifier,
        "ref": ref,
        "alts": alts,
        "quality": quality,
        "filter": filter_raw,
        "record_pass": filter_raw in {"", ".", "PASS"},
        "info": _parse_info(info_raw),
        "format_keys": format_keys,
        "sample_values": columns[9:],
    }


def _read_metadata(
    inputs: dict[str, Any],
    samples: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    if not inputs["metadata_path"]:
        return (
            [
                {
                    "sample": sample,
                    "subject": sample,
                    "timepoint": sample,
                    "time_order": index,
                }
                for index, sample in enumerate(samples)
            ],
            False,
        )
    target = resolve_workspace_path(inputs["metadata_path"])
    delimiter = "\t" if target.suffix.casefold() == ".tsv" else ","
    try:
        with target.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            required = {
                inputs["sample_column"],
                inputs["subject_column"],
                inputs["timepoint_column"],
                inputs["time_order_column"],
            }
            missing = sorted(required - set(reader.fieldnames or []))
            if missing:
                raise VcfCohortError("Sample metadata is missing columns: " + ", ".join(missing))
            rows = []
            for line_number, row in enumerate(reader, 2):
                sample = str(row.get(inputs["sample_column"]) or "").strip()
                subject = str(row.get(inputs["subject_column"]) or "").strip()
                timepoint = str(row.get(inputs["timepoint_column"]) or "").strip()
                order_raw = str(row.get(inputs["time_order_column"]) or "").strip()
                if not sample or not subject or not timepoint or not order_raw:
                    raise VcfCohortError(f"Sample metadata line {line_number} has missing required values.")
                try:
                    time_order = float(order_raw)
                except ValueError as exc:
                    raise VcfCohortError(
                        f"Sample metadata line {line_number} has a non-numeric time order."
                    ) from exc
                if not math.isfinite(time_order):
                    raise VcfCohortError(f"Sample metadata line {line_number} has an invalid time order.")
                rows.append(
                    {
                        "sample": sample,
                        "subject": subject,
                        "timepoint": timepoint,
                        "time_order": time_order,
                    }
                )
    except UnicodeDecodeError as exc:
        raise VcfCohortError("Sample metadata must be UTF-8 text.") from exc
    names = [item["sample"] for item in rows]
    if len(names) != len(set(names)):
        raise VcfCohortError("Sample metadata contains duplicate sample identifiers.")
    if set(names) != set(samples):
        missing = sorted(set(samples) - set(names))
        extra = sorted(set(names) - set(samples))
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing[:8]))
        if extra:
            detail.append("extra " + ", ".join(extra[:8]))
        raise VcfCohortError("Sample metadata must exactly match VCF samples: " + "; ".join(detail))
    duplicate_times = Counter((item["subject"], item["time_order"]) for item in rows)
    if any(count > 1 for count in duplicate_times.values()):
        raise VcfCohortError("Each subject must have unique time_order values.")
    order = {sample: index for index, sample in enumerate(samples)}
    rows.sort(key=lambda item: (item["subject"], item["time_order"], order[item["sample"]]))
    return rows, True


def _sample_call(
    sample: str,
    raw_sample: str,
    format_keys: list[str],
    alt_index: int,
    alt_count: int,
    record_pass: bool,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    values = raw_sample.split(":") if raw_sample not in {"", "."} else []
    fields = {
        key: values[index] if index < len(values) else "."
        for index, key in enumerate(format_keys)
    }
    genotype = fields.get("GT", "")
    genotype_alleles = [
        int(value)
        for value in re.split(r"[/|]", genotype)
        if value.isdigit()
    ]
    allele_depths = _number_list(fields.get("AD"))
    alt_depth = _list_value(allele_depths, alt_index)
    ref_depth = _list_value(allele_depths, 0)
    depth = _int_or_none(fields.get("DP"))
    if depth is None and allele_depths:
        depth = int(sum(value for value in allele_depths if value is not None))
    if alt_depth is None:
        ao = _number_list(fields.get("AO"))
        alt_depth = _list_value(ao, alt_index - 1)
        if depth is None:
            ro = _int_or_none(fields.get("RO"))
            if ro is not None and alt_depth is not None:
                depth = ro + int(alt_depth)
                ref_depth = ro
    vaf = None
    for key in ("AF", "VAF", "VF", "FA"):
        values_for_key = _fraction_list(fields.get(key))
        if values_for_key:
            vaf = _list_value(values_for_key, alt_index - 1)
            if vaf is None and len(values_for_key) == 1 and alt_count == 1:
                vaf = values_for_key[0]
            if vaf is not None:
                break
    if vaf is None and alt_depth is not None and depth and depth > 0:
        vaf = float(alt_depth) / depth
    observed = alt_index in genotype_alleles
    observed = observed or (alt_depth is not None and alt_depth > 0)
    observed = observed or (vaf is not None and vaf > 0)
    status = "included"
    if observed and not record_pass and not inputs["include_filtered"]:
        status = "excluded_filter"
    elif observed and inputs["min_depth"] > 0 and (depth is None or depth < inputs["min_depth"]):
        status = "excluded_low_depth"
    elif observed and inputs["min_vaf"] > 0 and (vaf is None or vaf < inputs["min_vaf"]):
        status = "excluded_low_vaf"
    elif not observed:
        status = "not_observed"
    return {
        "sample": sample,
        "genotype": genotype,
        "depth": depth,
        "ref_depth": int(ref_depth) if ref_depth is not None else None,
        "alt_depth": int(alt_depth) if alt_depth is not None else None,
        "vaf": round(vaf, 6) if vaf is not None else None,
        "observed": observed,
        "included": observed and status == "included",
        "status": status,
    }


def _annotation_for_alt(
    info: dict[str, Any],
    alt: str,
    formats: dict[str, list[str]],
) -> dict[str, Any]:
    annotations = []
    source = ""
    for annotation_id in ("CSQ", "ANN"):
        raw = info.get(annotation_id)
        if not isinstance(raw, str) or not raw:
            continue
        labels = formats.get(annotation_id) or ANNOTATION_DEFAULTS[annotation_id]
        for text in raw.split(","):
            values = text.split("|")
            item = {label: values[index] if index < len(values) else "" for index, label in enumerate(labels)}
            annotations.append(item)
        source = annotation_id
        break
    selected = next(
        (item for item in annotations if str(item.get("Allele") or "") == alt),
        {},
    )
    gene = _first_value(
        selected,
        ("SYMBOL", "Gene_Name", "Gene", "GENE"),
    ) or _first_info(info, ("SYMBOL", "GENE", "Gene", "Hugo_Symbol"))
    consequence = _first_value(selected, ("Consequence", "Annotation")) or _first_info(
        info, ("Consequence", "CONSEQUENCE")
    )
    impact = _first_value(selected, ("IMPACT", "Annotation_Impact")) or _first_info(
        info, ("IMPACT",)
    )
    hgvsc = _first_value(selected, ("HGVSc", "HGVS.c")) or _first_info(info, ("HGVSC",))
    hgvsp = _first_value(selected, ("HGVSp", "HGVS.p")) or _first_info(info, ("HGVSP",))
    return {
        "annotation_source": source,
        "annotation_count": len(annotations),
        "gene": _bounded_text(gene),
        "consequence": _bounded_text(consequence),
        "impact": _bounded_text(impact),
        "hgvsc": _bounded_text(hgvsc),
        "hgvsp": _bounded_text(hgvsp),
    }


def _build_trajectories(
    variants: list[dict[str, Any]],
    metadata: list[dict[str, Any]],
    calls: dict[tuple[str, str], dict[str, Any]],
    metadata_provided: bool,
) -> list[dict[str, Any]]:
    if not metadata_provided:
        return []
    by_subject: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in metadata:
        by_subject[item["subject"]].append(item)
    trajectories = []
    for subject, subject_samples in by_subject.items():
        if len(subject_samples) < 2:
            continue
        for variant in variants[:20]:
            points = []
            observed_count = 0
            for sample_metadata in subject_samples:
                call = calls.get((variant["variant_id"], sample_metadata["sample"]))
                if call:
                    observed_count += 1
                points.append(
                    {
                        "sample": sample_metadata["sample"],
                        "timepoint": sample_metadata["timepoint"],
                        "time_order": sample_metadata["time_order"],
                        "vaf": call["vaf"] if call else None,
                        "depth": call["depth"] if call else None,
                        "status": call["status"] if call else "not_observed",
                    }
                )
            if observed_count >= 2:
                trajectories.append(
                    {
                        "subject": subject,
                        "variant_id": variant["variant_id"],
                        "gene": variant["gene"],
                        "consequence": variant["consequence"],
                        "points": points,
                    }
                )
            if len(trajectories) >= 100:
                return trajectories
    return trajectories


def _matrix_value(call: dict[str, Any] | None) -> dict[str, Any]:
    if not call:
        return {"observed": False, "included": False, "vaf": None, "status": "not_observed"}
    return {
        "observed": call["observed"],
        "included": call["included"],
        "vaf": call["vaf"],
        "status": call["status"],
    }


def _persist_review(result: dict[str, Any]) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "variants": f"{relative_root}/variants.tsv",
        "calls": f"{relative_root}/calls.tsv",
        "sample_qc": f"{relative_root}/sample_qc.tsv",
        "trajectories": f"{relative_root}/trajectories.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="vcf-cohort-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_variants(output / "variants.tsv", result["variants"])
        _write_calls(output / "calls.tsv", result["calls"])
        _write_sample_qc(output / "sample_qc.tsv", result["sample_qc"])
        _write_trajectories(output / "trajectories.tsv", result["trajectories"])
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "created_at": result["retrieved_at"],
            "inputs": result["inputs"],
            "input_sha256": {
                "vcf": _sha256(resolve_workspace_path(result["inputs"]["vcf_path"])),
                "metadata": (
                    _sha256(resolve_workspace_path(result["inputs"]["metadata_path"]))
                    if result["inputs"]["metadata_path"]
                    else None
                ),
            },
            "bounds": {
                "max_vcf_bytes": MAX_VCF_BYTES,
                "max_samples": MAX_SAMPLES,
                "max_records": MAX_RECORDS,
                "max_alleles": MAX_ALLELES,
                "max_observed_calls": MAX_CALL_ROWS,
            },
            "files": [path.rsplit("/", 1)[-1] for path in result["outputs"].values()],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise VcfCohortError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_variants(path: Path, variants: list[dict[str, Any]]) -> None:
    fields = [
        "source_index",
        "variant_id",
        "chrom",
        "pos",
        "id",
        "ref",
        "alt",
        "type",
        "quality",
        "filter",
        "gene",
        "consequence",
        "impact",
        "hgvsc",
        "hgvsp",
        "annotation_source",
        "annotation_count",
        "observed_sample_count",
        "included_sample_count",
        "max_vaf",
        "median_vaf",
        "low_frequency_call_count",
    ]
    _write_tsv(path, fields, variants)


def _write_calls(path: Path, calls: list[dict[str, Any]]) -> None:
    fields = [
        "variant_id",
        "chrom",
        "pos",
        "ref",
        "alt",
        "gene",
        "consequence",
        "sample",
        "subject",
        "timepoint",
        "time_order",
        "genotype",
        "depth",
        "ref_depth",
        "alt_depth",
        "vaf",
        "observed",
        "included",
        "status",
    ]
    _write_tsv(path, fields, calls)


def _write_sample_qc(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "sample",
        "subject",
        "timepoint",
        "time_order",
        "records_with_depth",
        "mean_depth",
        "observed_calls",
        "included_calls",
        "low_frequency_calls",
        "excluded_low_depth",
        "excluded_low_vaf",
        "excluded_filter",
    ]
    _write_tsv(path, fields, rows)


def _write_trajectories(path: Path, trajectories: list[dict[str, Any]]) -> None:
    fields = [
        "subject",
        "variant_id",
        "gene",
        "consequence",
        "sample",
        "timepoint",
        "time_order",
        "vaf",
        "depth",
        "status",
    ]
    rows = []
    for trajectory in trajectories:
        for point in trajectory["points"]:
            rows.append(
                {
                    "subject": trajectory["subject"],
                    "variant_id": trajectory["variant_id"],
                    "gene": trajectory["gene"],
                    "consequence": trajectory["consequence"],
                    **point,
                }
            )
    _write_tsv(path, fields, rows)


def _write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Multi-sample VCF review",
        "",
        result["summary"],
        "",
        "## Input and filters",
        "",
        f"- VCF: {result['inputs']['vcf_path']}",
        f"- Metadata: {result['inputs']['metadata_path'] or 'not provided'}",
        f"- Samples: {result['sample_count']}; subjects: {result['subject_count']}",
        f"- Minimum depth: {result['thresholds']['min_depth']}",
        f"- Minimum VAF: {result['thresholds']['min_vaf']}",
        f"- Include non-PASS records: {result['thresholds']['include_filtered']}",
        "",
        "## Recurrent qualifying variants",
        "",
    ]
    for variant in result["recurrent_variants"][:20]:
        label = " ".join(
            value
            for value in (variant["gene"], variant["hgvsp"], variant["variant_id"])
            if value
        )
        lines.append(
            f"- {label}: {variant['included_sample_count']} samples; "
            f"maximum VAF {variant['max_vaf'] if variant['max_vaf'] is not None else 'n/a'}"
        )
    lines.extend(["", "## Interpretation limits", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _meta_definition(line: str) -> dict[str, str]:
    content = line.split("=<", 1)[1].rsplit(">", 1)[0]
    values: dict[str, str] = {}
    current = []
    quoted = False
    fields = []
    for character in content:
        if character == '"':
            quoted = not quoted
        if character == "," and not quoted:
            fields.append("".join(current))
            current = []
        else:
            current.append(character)
    fields.append("".join(current))
    for field in fields:
        if "=" not in field:
            continue
        key, value = field.split("=", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def _annotation_fields(description: str, annotation_id: str) -> list[str]:
    match = re.search(r"(?:Format|format)\s*[:=]\s*([^\"]+)", description)
    if not match:
        return ANNOTATION_DEFAULTS[annotation_id]
    fields = [item.strip() for item in match.group(1).strip(" '()[]").split("|")]
    return fields if len(fields) >= 2 else ANNOTATION_DEFAULTS[annotation_id]


def _parse_info(raw: str) -> dict[str, Any]:
    if raw in {"", "."}:
        return {}
    values: dict[str, Any] = {}
    for field in raw.split(";"):
        if not field:
            continue
        if "=" in field:
            key, value = field.split("=", 1)
            values[key] = value
        else:
            values[field] = True
    return values


def _variant_id(chrom: str, pos: int, ref: str, alt: str) -> str:
    return f"{chrom}:{pos}:{ref}>{alt}"


def _variant_type(ref: str, alt: str) -> str:
    if alt.startswith("<") or "[" in alt or "]" in alt:
        return "structural"
    if len(ref) == len(alt) == 1:
        return "SNV"
    if len(ref) == len(alt):
        return "MNV"
    return "deletion" if len(ref) > len(alt) else "insertion"


def _number_list(value: Any) -> list[float | None]:
    if value in {None, "", "."}:
        return []
    return [_float_or_none(item) for item in str(value).split(",")]


def _fraction_list(value: Any) -> list[float | None]:
    fractions = []
    for item in _string_list(value):
        percent = item.endswith("%")
        number = _float_or_none(item.rstrip("%"))
        if number is not None and percent:
            number /= 100
        fractions.append(number)
    return fractions


def _string_list(value: Any) -> list[str]:
    if value in {None, "", "."}:
        return []
    return str(value).split(",")


def _list_value(values: list[Any], index: int) -> Any:
    return values[index] if 0 <= index < len(values) else None


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _int_or_none(value: Any) -> int | None:
    number = _float_or_none(value)
    return int(number) if number is not None and number >= 0 else None


def _first_value(values: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = str(values.get(key) or "").strip()
        if value:
            return value
    return ""


def _first_info(info: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = info.get(key)
        if value not in {None, "", ".", True}:
            return str(value).split(",", 1)[0]
    return ""


def _bounded_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= MAX_TEXT_CHARS else text[:MAX_TEXT_CHARS].rsplit(" ", 1)[0] + "..."


def _validate_file(target: Path, maximum: int, label: str) -> None:
    if not target.is_file():
        raise VcfCohortError(f"{label} file was not found in the workspace.")
    size = target.stat().st_size
    if size <= 0:
        raise VcfCohortError(f"{label} file is empty.")
    if size > maximum:
        raise VcfCohortError(f"{label} exceeds the local {maximum}-byte limit.")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _caveats(metadata_provided: bool) -> list[str]:
    caveats = [
        "The review summarizes a processed VCF; variant detection, filtering and assay limits remain properties of the upstream caller and laboratory workflow.",
        "A sample call is included only when observed evidence meets the approved VAF, depth and record-FILTER rules. Missing or non-qualifying calls are not proof of biological absence.",
        "Variant allele fraction is not a direct estimate of tumor fraction, clonality, cell fraction or treatment response without purity, copy-number, assay and sampling context.",
        "Low-frequency calls near an assay's limit of detection require orthogonal review of read support, strand/orientation bias, background error, technical replicates and validation data.",
        "Gene and consequence labels are reproduced from VCF INFO annotations when available; this workflow does not independently reannotate transcripts or select a clinically preferred consequence.",
        "The workflow does not classify calls as somatic or germline, identify drivers, infer resistance, recommend treatment, or perform clinical variant interpretation.",
    ]
    if not metadata_provided:
        caveats.append(
            "No sample metadata was supplied, so subject-level longitudinal trajectories are not generated."
        )
    return caveats
