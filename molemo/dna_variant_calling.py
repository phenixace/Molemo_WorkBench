"""Approval-gated paired-end DNA alignment and candidate variant calling."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Iterator

from .workspace_utils import WORKSPACE_ROOT, resolve_workspace_path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_NGS_BIN = ROOT / ".molemo-ngs-tools" / "bin"
PROJECT_TOOL_BIN = ROOT / ".molemo-tools" / "bin"
FASTQ_SUFFIXES = (".fastq", ".fq", ".fastq.gz", ".fq.gz")
FASTA_SUFFIXES = (".fa", ".fasta", ".fna")
DNA_ALPHABET = set("ACGTNRYKMSWBDHV")
MAX_FASTQ_BYTES = 32 * 1024 * 1024
MAX_FASTQ_UNCOMPRESSED_BYTES = 160 * 1024 * 1024
MAX_REFERENCE_BYTES = 64 * 1024 * 1024
MAX_REFERENCE_BASES = 50_000_000
MAX_REFERENCE_CONTIGS = 5_000
MAX_READ_PAIRS = 500_000
MIN_READ_LENGTH = 35
MAX_READ_LENGTH = 1_000
MAX_FASTQ_LINE_BYTES = 2 * 1024 * 1024
MAX_OUTPUT_BYTES = 256 * 1024 * 1024
MAX_VCF_BYTES = 24 * 1024 * 1024
MAX_VARIANTS = 20_000
MAX_THREADS = 4
PROCESS_TIMEOUT_SECONDS = 300
MAX_PROCESS_LOG_BYTES = 2 * 1024 * 1024


class DnaVariantCallingError(ValueError):
    """Raised when the bounded DNA variant-calling workflow cannot run safely."""


def find_ngs_executable(name: str) -> Path | None:
    configured = str(os.environ.get("MOLEMO_NGS_TOOL_BIN") or "").strip()
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured).expanduser() / name)
    candidates.extend([PROJECT_NGS_BIN / name, PROJECT_TOOL_BIN / name])
    discovered = shutil.which(name)
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def ngs_toolchain_status() -> dict[str, Any]:
    tools = {}
    for name in ("bwa", "samtools", "bcftools"):
        executable = find_ngs_executable(name)
        tools[name] = {
            "available": executable is not None,
            "path": str(executable) if executable else None,
            "version": _tool_version(name, executable) if executable else None,
        }
    return {
        "available": all(item["available"] for item in tools.values()),
        "tools": tools,
    }


def normalize_dna_variant_inputs(
    read1_path: str,
    read2_path: str,
    reference_path: str,
    sample_id: str,
    ploidy: int = 2,
    min_base_quality: int = 13,
    min_mapping_quality: int = 20,
    max_depth: int = 10_000,
    threads: int = 1,
) -> dict[str, Any]:
    read1 = _workspace_file(read1_path, FASTQ_SUFFIXES, MAX_FASTQ_BYTES, "Read 1 FASTQ")
    read2 = _workspace_file(read2_path, FASTQ_SUFFIXES, MAX_FASTQ_BYTES, "Read 2 FASTQ")
    reference = _workspace_file(reference_path, FASTA_SUFFIXES, MAX_REFERENCE_BYTES, "Reference FASTA")
    if read1 == read2:
        raise DnaVariantCallingError("Read 1 and Read 2 must be different FASTQ files.")
    sample = str(sample_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", sample):
        raise DnaVariantCallingError(
            "sample_id must contain 1 to 64 letters, numbers, periods, underscores, or hyphens."
        )
    try:
        normalized_ploidy = int(ploidy)
        normalized_base_quality = int(min_base_quality)
        normalized_mapping_quality = int(min_mapping_quality)
        normalized_depth = int(max_depth)
        normalized_threads = int(threads)
    except (TypeError, ValueError) as exc:
        raise DnaVariantCallingError("Ploidy, quality, depth, and thread settings must be integers.") from exc
    if normalized_ploidy not in {1, 2}:
        raise DnaVariantCallingError("ploidy must be 1 or 2.")
    if not 0 <= normalized_base_quality <= 60:
        raise DnaVariantCallingError("min_base_quality must be between 0 and 60.")
    if not 0 <= normalized_mapping_quality <= 60:
        raise DnaVariantCallingError("min_mapping_quality must be between 0 and 60.")
    if not 50 <= normalized_depth <= 100_000:
        raise DnaVariantCallingError("max_depth must be between 50 and 100000.")
    if not 1 <= normalized_threads <= MAX_THREADS:
        raise DnaVariantCallingError(f"threads must be between 1 and {MAX_THREADS}.")
    return {
        "read1_path": read1,
        "read2_path": read2,
        "reference_path": reference,
        "sample_id": sample,
        "ploidy": normalized_ploidy,
        "min_base_quality": normalized_base_quality,
        "min_mapping_quality": normalized_mapping_quality,
        "max_depth": normalized_depth,
        "threads": normalized_threads,
    }


def preflight_dna_variant_calling(**arguments: Any) -> dict[str, Any]:
    inputs = normalize_dna_variant_inputs(**arguments)
    reference = inspect_reference_fasta(resolve_workspace_path(inputs["reference_path"]))
    reads = inspect_fastq_pair(
        resolve_workspace_path(inputs["read1_path"]),
        resolve_workspace_path(inputs["read2_path"]),
    )
    toolchain = ngs_toolchain_status()
    if not toolchain["available"]:
        missing = [name for name, item in toolchain["tools"].items() if not item["available"]]
        raise DnaVariantCallingError(
            "Missing local NGS tools: "
            + ", ".join(missing)
            + ". Install the project environment or set MOLEMO_NGS_TOOL_BIN."
        )
    warnings = _caveats()
    if min(reads["read1"]["mean_read_length"], reads["read2"]["mean_read_length"]) < 70:
        warnings = [
            "Mean read length is below 70 bases; BWA-MEM behavior should be reviewed for this library.",
            *warnings,
        ]
    return {
        "ready": True,
        "method": "BWA-MEM paired-end alignment with bcftools candidate variant calling",
        "inputs": inputs,
        "reference": reference,
        "reads": reads,
        "toolchain": toolchain,
        "limits": {
            "read_pairs": MAX_READ_PAIRS,
            "fastq_uncompressed_bytes_per_file": MAX_FASTQ_UNCOMPRESSED_BYTES,
            "reference_bases": MAX_REFERENCE_BASES,
            "output_bytes": MAX_OUTPUT_BYTES,
            "variants": MAX_VARIANTS,
            "process_timeout_seconds": PROCESS_TIMEOUT_SECONDS,
        },
        "warnings": warnings,
        "summary": (
            f"Validated {reads['read_pairs']:,} synchronized read pairs for sample {inputs['sample_id']} "
            f"against {reference['contig_count']:,} reference contig(s) totaling "
            f"{reference['total_bases']:,} bases."
        ),
    }


def run_dna_variant_calling(**arguments: Any) -> dict[str, Any]:
    preflight = preflight_dna_variant_calling(**arguments)
    inputs = preflight["inputs"]
    tool_paths = {
        name: Path(item["path"])
        for name, item in preflight["toolchain"]["tools"].items()
    }
    analysis_id = f"dna-variant-calling-{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / analysis_id
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="dna-variant-calling-", dir=temp_root) as temporary:
        temporary_path = Path(temporary)
        work = temporary_path / "work"
        output = temporary_path / "output"
        work.mkdir()
        output.mkdir()
        reference_copy = work / "reference.fa"
        shutil.copy2(resolve_workspace_path(inputs["reference_path"]), reference_copy)
        bam_path = output / "aligned.bam"
        bai_path = output / "aligned.bam.bai"
        vcf_path = output / "candidate_variants.vcf"
        pileup_path = work / "pileup.bcf"
        calls_path = work / "calls.bcf"
        env = _process_env(inputs["threads"], work)

        stages: list[dict[str, Any]] = []
        _timed_stage(
            stages,
            "Reference indexing",
            "bwa index",
            lambda: _run_command([tool_paths["bwa"], "index", reference_copy], work, env),
        )
        _timed_stage(
            stages,
            "Paired-end alignment and coordinate sort",
            "bwa mem | samtools sort",
            lambda: _run_alignment_pipeline(tool_paths, inputs, reference_copy, bam_path, work, env),
        )
        _validate_output_file(bam_path, MAX_OUTPUT_BYTES, "Aligned BAM")
        _timed_stage(
            stages,
            "BAM indexing",
            "samtools index",
            lambda: _run_command(
                [tool_paths["samtools"], "index", "-o", bai_path, bam_path], work, env
            ),
        )
        flagstat_text = _run_command(
            [tool_paths["samtools"], "flagstat", bam_path], work, env
        )
        coverage_text = _run_command(
            [tool_paths["samtools"], "coverage", bam_path], work, env
        )
        _timed_stage(
            stages,
            "Genotype likelihoods",
            "bcftools mpileup",
            lambda: _run_command(
                [
                    tool_paths["bcftools"],
                    "mpileup",
                    "-Ou",
                    "-f",
                    reference_copy,
                    "-a",
                    "FORMAT/AD,FORMAT/DP",
                    "-q",
                    str(inputs["min_mapping_quality"]),
                    "-Q",
                    str(inputs["min_base_quality"]),
                    "-d",
                    str(inputs["max_depth"]),
                    "-o",
                    pileup_path,
                    bam_path,
                ],
                work,
                env,
            ),
        )
        _timed_stage(
            stages,
            "Candidate variant calling",
            "bcftools call",
            lambda: _run_command(
                [
                    tool_paths["bcftools"],
                    "call",
                    "-m",
                    "-v",
                    "--ploidy",
                    str(inputs["ploidy"]),
                    "-Ob",
                    "-o",
                    calls_path,
                    pileup_path,
                ],
                work,
                env,
            ),
        )
        _timed_stage(
            stages,
            "Variant normalization",
            "bcftools norm",
            lambda: _run_command(
                [
                    tool_paths["bcftools"],
                    "norm",
                    "-f",
                    reference_copy,
                    "-m",
                    "-both",
                    "-Ov",
                    "-o",
                    vcf_path,
                    calls_path,
                ],
                work,
                env,
            ),
        )
        _validate_output_file(vcf_path, MAX_VCF_BYTES, "Candidate VCF", allow_empty=False)
        _stabilize_vcf(vcf_path, temporary_path)

        alignment = parse_flagstat(flagstat_text)
        coverage = parse_samtools_coverage(coverage_text)
        variants = parse_candidate_vcf(vcf_path, inputs["sample_id"])
        variant_summary = summarize_variants(variants)
        coverage_path = output / "contig_coverage.tsv"
        variants_path = output / "variant_calls.tsv"
        _write_coverage(coverage_path, coverage["contigs"])
        _write_variants(variants_path, variants)

        outputs = {
            "bam": f"{relative_root}/aligned.bam",
            "bam_index": f"{relative_root}/aligned.bam.bai",
            "vcf": f"{relative_root}/candidate_variants.vcf",
            "variant_table": f"{relative_root}/variant_calls.tsv",
            "coverage_table": f"{relative_root}/contig_coverage.tsv",
            "report": f"{relative_root}/analysis_report.json",
            "manifest": f"{relative_root}/run_manifest.json",
            "summary": f"{relative_root}/summary.md",
        }
        input_sha256 = {
            "read1": _sha256(resolve_workspace_path(inputs["read1_path"])),
            "read2": _sha256(resolve_workspace_path(inputs["read2_path"])),
            "reference": _sha256(resolve_workspace_path(inputs["reference_path"])),
        }
        output_sha256 = {
            "bam": _sha256(bam_path),
            "bam_index": _sha256(bai_path),
            "vcf": _sha256(vcf_path),
            "variant_table": _sha256(variants_path),
            "coverage_table": _sha256(coverage_path),
        }
        result = {
            "analysis_id": analysis_id,
            "method": "BWA-MEM paired-end alignment with samtools QC and bcftools candidate variant calling",
            "created_at": created_at,
            "inputs": inputs,
            "input_sha256": input_sha256,
            "toolchain": preflight["toolchain"],
            "reference": preflight["reference"],
            "reads": preflight["reads"],
            "alignment": alignment,
            "coverage": coverage,
            **variant_summary,
            "variants": variants[:500],
            "variants_truncated": len(variants) > 500,
            "stages": stages,
            "output_root": relative_root,
            "outputs": outputs,
            "output_sha256": output_sha256,
            "clinical_interpretation": False,
            "analysis_handoff": (
                "Review read quality, mapping rate, depth and uncovered reference regions before using the candidate VCF. "
                "Variant annotation, cohort comparison, orthogonal validation and assay-specific filtering remain separate steps."
            ),
            "caveats": _caveats(),
        }
        result["summary"] = (
            f"Aligned {preflight['reads']['read_pairs']:,} read pairs for {inputs['sample_id']}; "
            f"{alignment['mapped_percent']:.1f}% of records mapped, mean reference depth was "
            f"{coverage['mean_depth']:.2f}x, and bcftools emitted {len(variants):,} unfiltered candidate variant(s)."
        )
        (output / "analysis_report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": analysis_id,
            "method": result["method"],
            "created_at": created_at,
            "inputs": inputs,
            "input_sha256": input_sha256,
            "tool_versions": {
                name: item["version"] for name, item in preflight["toolchain"]["tools"].items()
            },
            "parameters": {
                key: inputs[key]
                for key in ("sample_id", "ploidy", "min_base_quality", "min_mapping_quality", "max_depth", "threads")
            },
            "pipeline": _logical_pipeline(inputs),
            "stages": stages,
            "output_sha256": output_sha256,
            "clinical_interpretation": False,
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise DnaVariantCallingError(f"Analysis output already exists: {analysis_id}")
        shutil.move(str(output), str(final_output))
    return result


def inspect_reference_fasta(path: Path) -> dict[str, Any]:
    contigs: list[dict[str, Any]] = []
    identifier = ""
    length = 0
    ambiguous = 0
    total_bases = 0
    seen: set[str] = set()

    def finish() -> None:
        nonlocal identifier, length, ambiguous
        if not identifier:
            return
        if length == 0:
            raise DnaVariantCallingError(f"Reference contig {identifier} has no sequence.")
        contigs.append({"name": identifier, "length": length, "ambiguous_bases": ambiguous})
        identifier = ""
        length = 0
        ambiguous = 0

    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                if len(raw_line) > MAX_FASTQ_LINE_BYTES:
                    raise DnaVariantCallingError(f"Reference FASTA line {line_number} exceeds the local line limit.")
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    finish()
                    identifier = line[1:].split(None, 1)[0].strip()
                    if not identifier or len(identifier) > 200 or identifier in seen:
                        raise DnaVariantCallingError("Reference FASTA contig identifiers must be unique and non-empty.")
                    seen.add(identifier)
                    if len(seen) > MAX_REFERENCE_CONTIGS:
                        raise DnaVariantCallingError(
                            f"Reference FASTA exceeds the {MAX_REFERENCE_CONTIGS:,}-contig limit."
                        )
                    continue
                if not identifier:
                    raise DnaVariantCallingError("Reference FASTA sequence appeared before the first header.")
                sequence = "".join(line.split()).upper()
                invalid = sorted(set(sequence) - DNA_ALPHABET)
                if invalid:
                    raise DnaVariantCallingError(
                        f"Reference FASTA contains unsupported DNA symbols: {''.join(invalid[:12])}."
                    )
                length += len(sequence)
                total_bases += len(sequence)
                ambiguous += sum(base not in "ACGT" for base in sequence)
                if total_bases > MAX_REFERENCE_BASES:
                    raise DnaVariantCallingError(
                        f"Reference FASTA exceeds the {MAX_REFERENCE_BASES:,}-base local limit."
                    )
        finish()
    except UnicodeDecodeError as exc:
        raise DnaVariantCallingError("Reference FASTA must be UTF-8 text.") from exc
    if not contigs:
        raise DnaVariantCallingError("Reference FASTA does not contain any sequence records.")
    return {
        "path": path.relative_to(WORKSPACE_ROOT.resolve()).as_posix(),
        "file_size": path.stat().st_size,
        "sha256": _sha256(path),
        "contig_count": len(contigs),
        "total_bases": total_bases,
        "ambiguous_fraction": sum(item["ambiguous_bases"] for item in contigs) / total_bases,
        "contigs": contigs[:100],
        "contigs_truncated": len(contigs) > 100,
    }


def inspect_fastq_pair(read1: Path, read2: Path) -> dict[str, Any]:
    stats = [_empty_read_stats(read1), _empty_read_stats(read2)]
    states = [{"bytes": 0}, {"bytes": 0}]
    pairs = 0
    try:
        with _open_fastq_binary(read1) as stream1, _open_fastq_binary(read2) as stream2:
            while True:
                record1 = _read_fastq_record(stream1, states[0], "Read 1", pairs + 1)
                record2 = _read_fastq_record(stream2, states[1], "Read 2", pairs + 1)
                if record1 is None and record2 is None:
                    break
                if record1 is None or record2 is None:
                    raise DnaVariantCallingError("Read 1 and Read 2 contain different numbers of records.")
                name1 = _update_read_stats(stats[0], record1, "Read 1", pairs + 1)
                name2 = _update_read_stats(stats[1], record2, "Read 2", pairs + 1)
                if name1 != name2:
                    raise DnaVariantCallingError(
                        f"FASTQ pair {pairs + 1} has different read identifiers: {name1} vs {name2}."
                    )
                pairs += 1
                if pairs > MAX_READ_PAIRS:
                    raise DnaVariantCallingError(
                        f"FASTQ inputs exceed the {MAX_READ_PAIRS:,}-pair local limit."
                    )
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise DnaVariantCallingError(f"Could not read the FASTQ inputs: {exc}") from exc
    if pairs == 0:
        raise DnaVariantCallingError("FASTQ inputs do not contain any complete read pairs.")
    return {
        "read_pairs": pairs,
        "read1": _finish_read_stats(stats[0], states[0]["bytes"]),
        "read2": _finish_read_stats(stats[1], states[1]["bytes"]),
        "pair_identifiers_synchronized": True,
    }


@contextmanager
def _open_fastq_binary(path: Path) -> Iterator[BinaryIO]:
    with path.open("rb") as raw:
        if path.name.casefold().endswith(".gz"):
            with gzip.GzipFile(fileobj=raw, mode="rb") as decoded:
                yield decoded
        else:
            yield raw


def _read_fastq_record(
    stream: BinaryIO,
    state: dict[str, int],
    label: str,
    record_number: int,
) -> tuple[str, str, str, str] | None:
    lines: list[str] = []
    for line_index in range(4):
        raw = stream.readline(MAX_FASTQ_LINE_BYTES + 1)
        if not raw:
            if line_index == 0:
                return None
            raise DnaVariantCallingError(f"{label} ends with an incomplete record {record_number}.")
        if len(raw) > MAX_FASTQ_LINE_BYTES:
            raise DnaVariantCallingError(f"{label} record {record_number} exceeds the local line limit.")
        state["bytes"] += len(raw)
        if state["bytes"] > MAX_FASTQ_UNCOMPRESSED_BYTES:
            raise DnaVariantCallingError(
                f"{label} exceeds the {MAX_FASTQ_UNCOMPRESSED_BYTES:,}-byte uncompressed limit."
            )
        try:
            lines.append(raw.rstrip(b"\r\n").decode("ascii"))
        except UnicodeDecodeError as exc:
            raise DnaVariantCallingError(f"{label} must contain ASCII FASTQ text.") from exc
    return lines[0], lines[1], lines[2], lines[3]


def _empty_read_stats(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(WORKSPACE_ROOT.resolve()).as_posix(),
        "file_size": path.stat().st_size,
        "sha256": _sha256(path),
        "reads": 0,
        "bases": 0,
        "gc": 0,
        "n": 0,
        "quality_sum": 0,
        "q20": 0,
        "q30": 0,
        "min_length": None,
        "max_length": 0,
    }


def _update_read_stats(
    stats: dict[str, Any],
    record: tuple[str, str, str, str],
    label: str,
    record_number: int,
) -> str:
    header, sequence, plus, quality = record
    if not header.startswith("@") or not plus.startswith("+"):
        raise DnaVariantCallingError(f"{label} record {record_number} is not valid four-line FASTQ.")
    if not sequence or len(sequence) != len(quality):
        raise DnaVariantCallingError(
            f"{label} record {record_number} has empty or unequal sequence and quality lengths."
        )
    if not MIN_READ_LENGTH <= len(sequence) <= MAX_READ_LENGTH:
        raise DnaVariantCallingError(
            f"{label} record {record_number} length must be between {MIN_READ_LENGTH} and {MAX_READ_LENGTH} bases."
        )
    upper = sequence.upper()
    invalid = set(upper) - DNA_ALPHABET
    if invalid:
        raise DnaVariantCallingError(
            f"{label} record {record_number} contains unsupported DNA symbols."
        )
    scores = [ord(char) - 33 for char in quality]
    if any(score < 0 or score > 93 for score in scores):
        raise DnaVariantCallingError(f"{label} record {record_number} has invalid Phred+33 qualities.")
    stats["reads"] += 1
    stats["bases"] += len(upper)
    stats["gc"] += upper.count("G") + upper.count("C")
    stats["n"] += upper.count("N")
    stats["quality_sum"] += sum(scores)
    stats["q20"] += sum(score >= 20 for score in scores)
    stats["q30"] += sum(score >= 30 for score in scores)
    stats["min_length"] = len(upper) if stats["min_length"] is None else min(stats["min_length"], len(upper))
    stats["max_length"] = max(stats["max_length"], len(upper))
    token = header[1:].split(None, 1)[0]
    return re.sub(r"/[12]$", "", token)


def _finish_read_stats(stats: dict[str, Any], uncompressed_bytes: int) -> dict[str, Any]:
    bases = stats["bases"]
    reads = stats["reads"]
    return {
        "path": stats["path"],
        "file_size": stats["file_size"],
        "uncompressed_bytes": uncompressed_bytes,
        "sha256": stats["sha256"],
        "reads": reads,
        "total_bases": bases,
        "mean_read_length": round(bases / reads, 2),
        "min_read_length": stats["min_length"],
        "max_read_length": stats["max_length"],
        "mean_quality": round(stats["quality_sum"] / bases, 2),
        "q20_percent": round(stats["q20"] / bases * 100, 2),
        "q30_percent": round(stats["q30"] / bases * 100, 2),
        "gc_percent": round(stats["gc"] / bases * 100, 2),
        "n_percent": round(stats["n"] / bases * 100, 3),
        "quality_encoding": "Phred+33",
    }


def parse_flagstat(text: str) -> dict[str, Any]:
    metrics: dict[str, int] = {}
    for line in str(text or "").splitlines():
        match = re.match(r"^(\d+) \+ (\d+) (.+)$", line.strip())
        if not match:
            continue
        passed, failed, label = match.groups()
        value = int(passed) + int(failed)
        if label.startswith("in total "):
            metrics["total_records"] = value
        elif label.startswith("primary mapped "):
            metrics["primary_mapped"] = value
        elif label.startswith("mapped "):
            metrics["mapped_records"] = value
        elif label.startswith("properly paired "):
            metrics["properly_paired"] = value
        elif label.startswith("duplicates "):
            metrics["duplicate_records"] = value
        elif label == "primary":
            metrics["primary_records"] = value
    total = metrics.get("total_records", 0)
    if total <= 0:
        raise DnaVariantCallingError("samtools flagstat did not report any alignment records.")
    mapped = metrics.get("mapped_records", metrics.get("primary_mapped", 0))
    properly_paired = metrics.get("properly_paired", 0)
    return {
        **metrics,
        "mapped_percent": mapped / total * 100,
        "properly_paired_percent": properly_paired / total * 100,
        "duplicate_percent": metrics.get("duplicate_records", 0) / total * 100,
    }


def parse_samtools_coverage(text: str) -> dict[str, Any]:
    contigs = []
    for line_number, raw_line in enumerate(str(text or "").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 9:
            raise DnaVariantCallingError(f"samtools coverage line {line_number} has an unexpected format.")
        name, start, end, reads, covered, coverage, depth, baseq, mapq = fields
        try:
            item = {
                "contig": name,
                "start": int(start),
                "end": int(end),
                "reads": int(reads),
                "covered_bases": int(covered),
                "coverage_percent": float(coverage),
                "mean_depth": float(depth),
                "mean_base_quality": float(baseq),
                "mean_mapping_quality": float(mapq),
            }
        except ValueError as exc:
            raise DnaVariantCallingError(f"samtools coverage line {line_number} is not numeric.") from exc
        contigs.append(item)
        if len(contigs) > MAX_REFERENCE_CONTIGS:
            raise DnaVariantCallingError("samtools coverage returned too many contigs.")
    if not contigs:
        raise DnaVariantCallingError("samtools coverage did not return reference contigs.")
    total_bases = sum(item["end"] - item["start"] + 1 for item in contigs)
    covered_bases = sum(item["covered_bases"] for item in contigs)
    mean_depth = sum(
        item["mean_depth"] * (item["end"] - item["start"] + 1) for item in contigs
    ) / total_bases
    return {
        "reference_bases": total_bases,
        "covered_bases": covered_bases,
        "covered_percent": covered_bases / total_bases * 100,
        "mean_depth": mean_depth,
        "contigs": contigs[:500],
        "contigs_truncated": len(contigs) > 500,
    }


def parse_candidate_vcf(path: Path, expected_sample: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    samples: list[str] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                if len(raw_line) > MAX_FASTQ_LINE_BYTES:
                    raise DnaVariantCallingError(f"VCF line {line_number} exceeds the local line limit.")
                line = raw_line.rstrip("\r\n")
                if line.startswith("#CHROM"):
                    columns = line.split("\t")
                    samples = columns[9:]
                    if samples != [expected_sample]:
                        raise DnaVariantCallingError(
                            "Candidate VCF sample header does not match the approved sample_id."
                        )
                    continue
                if not line or line.startswith("#"):
                    continue
                fields = line.split("\t")
                if len(fields) != 10 or not samples:
                    raise DnaVariantCallingError(f"VCF line {line_number} has an unexpected column count.")
                chrom, pos, identifier, ref, alt, quality, filter_value, info, format_text, sample_text = fields
                if "," in alt:
                    raise DnaVariantCallingError("Normalized candidate VCF still contains a multiallelic row.")
                format_keys = format_text.split(":")
                sample_values = sample_text.split(":")
                values = dict(zip(format_keys, sample_values))
                dp = _int_or_none(values.get("DP"))
                ad_values = [
                    _int_or_none(value) for value in str(values.get("AD") or "").split(",")
                ]
                ref_depth = ad_values[0] if ad_values and ad_values[0] is not None else None
                alt_depth = ad_values[1] if len(ad_values) > 1 and ad_values[1] is not None else None
                denominator = dp if dp not in {None, 0} else (
                    sum(value for value in ad_values if value is not None) if ad_values else 0
                )
                vaf = alt_depth / denominator if alt_depth is not None and denominator else None
                variants.append(
                    {
                        "chrom": chrom,
                        "pos": int(pos),
                        "id": "" if identifier == "." else identifier,
                        "ref": ref,
                        "alt": alt,
                        "type": _variant_type(ref, alt),
                        "quality": None if quality == "." else float(quality),
                        "filter": filter_value,
                        "genotype": values.get("GT", ""),
                        "depth": dp,
                        "ref_depth": ref_depth,
                        "alt_depth": alt_depth,
                        "vaf": vaf,
                        "info_depth": _info_depth(info),
                    }
                )
                if len(variants) > MAX_VARIANTS:
                    raise DnaVariantCallingError(
                        f"Candidate VCF exceeds the {MAX_VARIANTS:,}-variant local limit."
                    )
    except (UnicodeDecodeError, ValueError) as exc:
        if isinstance(exc, DnaVariantCallingError):
            raise
        raise DnaVariantCallingError(f"Candidate VCF could not be parsed: {exc}") from exc
    if not samples:
        raise DnaVariantCallingError("Candidate VCF is missing the #CHROM sample header.")
    return variants


def summarize_variants(variants: list[dict[str, Any]]) -> dict[str, Any]:
    type_counts = Counter(item["type"] for item in variants)
    genotype_counts = Counter(item["genotype"] for item in variants)
    transitions = 0
    transversions = 0
    transition_pairs = {("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")}
    for item in variants:
        if item["type"] != "SNV":
            continue
        if (item["ref"].upper(), item["alt"].upper()) in transition_pairs:
            transitions += 1
        else:
            transversions += 1
    return {
        "variant_count": len(variants),
        "variant_type_counts": [
            {"label": label, "count": count}
            for label, count in sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "genotype_counts": [
            {"label": label or "missing", "count": count}
            for label, count in sorted(genotype_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "transition_count": transitions,
        "transversion_count": transversions,
        "transition_transversion_ratio": transitions / transversions if transversions else None,
    }


def _run_alignment_pipeline(
    tools: dict[str, Path],
    inputs: dict[str, Any],
    reference: Path,
    bam_path: Path,
    work: Path,
    env: dict[str, str],
) -> None:
    read_group = (
        f"@RG\\tID:{inputs['sample_id']}\\tSM:{inputs['sample_id']}"
        f"\\tPL:ILLUMINA\\tLB:{inputs['sample_id']}"
    )
    bwa_args = [
        str(tools["bwa"]),
        "mem",
        "-t",
        str(inputs["threads"]),
        "-R",
        read_group,
        str(reference),
        str(resolve_workspace_path(inputs["read1_path"])),
        str(resolve_workspace_path(inputs["read2_path"])),
    ]
    sort_args = [
        str(tools["samtools"]),
        "sort",
        "-@",
        str(inputs["threads"]),
        "-m",
        "256M",
        "-T",
        str(work / "sort"),
        "-o",
        str(bam_path),
        "-",
    ]
    bwa_log = work / "bwa.stderr"
    sort_log = work / "samtools-sort.stderr"
    with bwa_log.open("wb") as bwa_stderr, sort_log.open("wb") as sort_stderr:
        bwa_process = subprocess.Popen(
            bwa_args,
            cwd=work,
            env=env,
            stdout=subprocess.PIPE,
            stderr=bwa_stderr,
            start_new_session=True,
        )
        assert bwa_process.stdout is not None
        sort_process = subprocess.Popen(
            sort_args,
            cwd=work,
            env=env,
            stdin=bwa_process.stdout,
            stdout=subprocess.DEVNULL,
            stderr=sort_stderr,
            start_new_session=True,
        )
        bwa_process.stdout.close()
        started = time.monotonic()
        try:
            sort_code = sort_process.wait(timeout=PROCESS_TIMEOUT_SECONDS)
            remaining = max(1, PROCESS_TIMEOUT_SECONDS - int(time.monotonic() - started))
            bwa_code = bwa_process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            bwa_process.kill()
            sort_process.kill()
            bwa_process.wait()
            sort_process.wait()
            raise DnaVariantCallingError("BWA-MEM alignment exceeded the local time limit.") from exc
    bwa_error = _bounded_log(bwa_log)
    sort_error = _bounded_log(sort_log)
    if bwa_code != 0 or sort_code != 0:
        detail = _scrub_paths((bwa_error + "\n" + sort_error).strip())[-1200:]
        raise DnaVariantCallingError(
            f"BWA-MEM or samtools sort failed ({bwa_code}/{sort_code}): {detail or 'no diagnostic output'}"
        )


def _run_command(
    arguments: list[Any],
    cwd: Path,
    env: dict[str, str],
) -> str:
    command = [str(item) for item in arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=PROCESS_TIMEOUT_SECONDS,
            check=False,
            start_new_session=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise DnaVariantCallingError(
            f"{Path(command[0]).name} exceeded the {PROCESS_TIMEOUT_SECONDS}-second local time limit."
        ) from exc
    if len(completed.stdout) > MAX_PROCESS_LOG_BYTES or len(completed.stderr) > MAX_PROCESS_LOG_BYTES:
        raise DnaVariantCallingError(f"{Path(command[0]).name} emitted an oversized process log.")
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode != 0:
        detail = _scrub_paths((stderr or stdout).strip())[-1200:]
        raise DnaVariantCallingError(
            f"{Path(command[0]).name} failed with exit code {completed.returncode}: "
            f"{detail or 'no diagnostic output'}"
        )
    return stdout


def _timed_stage(
    stages: list[dict[str, Any]],
    name: str,
    engine: str,
    action,
) -> None:
    started = time.monotonic()
    action()
    stages.append(
        {
            "name": name,
            "engine": engine,
            "status": "completed",
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
        }
    )


def _tool_version(name: str, executable: Path) -> str:
    command = [str(executable), "--version"] if name != "bwa" else [str(executable)]
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    text = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
    if name == "bwa":
        match = re.search(r"Version:\s*([^\s]+)", text)
    else:
        match = re.search(rf"{re.escape(name)}\s+([0-9][^\s]*)", text, re.I)
    return match.group(1) if match else "unknown"


def _workspace_file(path: str, suffixes: tuple[str, ...], max_bytes: int, label: str) -> str:
    relative = str(path or "").strip()
    if not relative:
        raise DnaVariantCallingError(f"{label} path is required.")
    target = resolve_workspace_path(relative)
    if not target.is_file():
        raise DnaVariantCallingError(f"{label} was not found in the workspace: {relative}")
    if not target.name.casefold().endswith(suffixes):
        raise DnaVariantCallingError(f"{label} has an unsupported file extension.")
    size = target.stat().st_size
    if size <= 0 or size > max_bytes:
        raise DnaVariantCallingError(f"{label} must contain 1 to {max_bytes:,} bytes.")
    return target.relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def _validate_output_file(path: Path, max_bytes: int, label: str, allow_empty: bool = False) -> None:
    if not path.is_file():
        raise DnaVariantCallingError(f"{label} was not produced.")
    size = path.stat().st_size
    if (not allow_empty and size <= 0) or size > max_bytes:
        raise DnaVariantCallingError(f"{label} is empty or exceeds the local output limit.")


def _process_env(threads: int, temporary: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "LC_ALL": "C",
            "LANG": "C",
            "OMP_NUM_THREADS": str(threads),
            "OPENBLAS_NUM_THREADS": "1",
            "TMPDIR": str(temporary),
        }
    )
    return env


def _stabilize_vcf(path: Path, temporary_root: Path) -> None:
    stable_lines = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.replace(str(temporary_root), "<temporary-workdir>")
        line = line.replace(str(WORKSPACE_ROOT.resolve()), "workspace")
        if line.startswith("##reference=file://"):
            line = "##reference=workspace reference FASTA recorded in run_manifest.json"
        stable_lines.append(line)
    path.write_text("\n".join(stable_lines) + "\n", encoding="utf-8")


def _write_coverage(path: Path, contigs: list[dict[str, Any]]) -> None:
    fields = [
        "contig", "start", "end", "reads", "covered_bases", "coverage_percent",
        "mean_depth", "mean_base_quality", "mean_mapping_quality",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(contigs)


def _write_variants(path: Path, variants: list[dict[str, Any]]) -> None:
    fields = [
        "chrom", "pos", "id", "ref", "alt", "type", "quality", "filter", "genotype",
        "depth", "ref_depth", "alt_depth", "vaf", "info_depth",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(variants)


def _logical_pipeline(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"stage": "reference_index", "tool": "bwa index", "reference": inputs["reference_path"]},
        {
            "stage": "alignment",
            "tool": "bwa mem",
            "threads": inputs["threads"],
            "read_group_sample": inputs["sample_id"],
        },
        {"stage": "sort_and_index", "tool": "samtools sort/index"},
        {"stage": "alignment_qc", "tool": "samtools flagstat/coverage"},
        {
            "stage": "candidate_calling",
            "tool": "bcftools mpileup/call/norm",
            "ploidy": inputs["ploidy"],
            "min_base_quality": inputs["min_base_quality"],
            "min_mapping_quality": inputs["min_mapping_quality"],
            "max_depth": inputs["max_depth"],
        },
    ]


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['inputs']['sample_id']} paired-end DNA variant calling",
        "",
        result["summary"],
        "",
        f"- Read pairs: {result['reads']['read_pairs']:,}",
        f"- Mapped records: {result['alignment']['mapped_percent']:.2f}%",
        f"- Covered reference: {result['coverage']['covered_percent']:.2f}%",
        f"- Mean depth: {result['coverage']['mean_depth']:.2f}x",
        f"- Candidate variants: {result['variant_count']:,}",
        "",
        "## Interpretation boundary",
        "",
        result["analysis_handoff"],
        "",
        "The VCF is an unfiltered research-use candidate set, not a germline, somatic, pathogenic, or clinically actionable classification.",
    ]
    return "\n".join(lines) + "\n"


def _variant_type(ref: str, alt: str) -> str:
    if len(ref) == len(alt) == 1:
        return "SNV"
    if len(ref) < len(alt):
        return "insertion"
    if len(ref) > len(alt):
        return "deletion"
    return "MNV/complex"


def _int_or_none(value: Any) -> int | None:
    text = str(value or "").strip()
    if text in {"", "."}:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _info_depth(info: str) -> int | None:
    for field in str(info or "").split(";"):
        if field.startswith("DP="):
            return _int_or_none(field.split("=", 1)[1])
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bounded_log(path: Path) -> str:
    if path.stat().st_size > MAX_PROCESS_LOG_BYTES:
        raise DnaVariantCallingError("A local NGS process emitted an oversized diagnostic log.")
    return path.read_text(encoding="utf-8", errors="replace")


def _scrub_paths(text: str) -> str:
    return str(text or "").replace(str(WORKSPACE_ROOT.resolve()), "workspace")


def _caveats() -> list[str]:
    return [
        "This bounded BWA-MEM workflow is intended for short paired-end DNA reads and a small local reference, not production human WGS/WES or clinical diagnostics.",
        "The pipeline does not trim adapters, mark PCR duplicates, recalibrate base qualities, jointly genotype samples, or apply assay-specific variant filters.",
        "bcftools output is an unfiltered candidate set; a call is not automatically germline, somatic, pathogenic, causal, or clinically actionable.",
        "Reference build, sample identity, library construction, contamination, expected ploidy, target design, coverage gaps, and orthogonal validation require researcher review.",
    ]
