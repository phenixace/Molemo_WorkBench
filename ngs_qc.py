"""Streaming FASTQ quality control for files in the constrained workspace."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable, TextIO

from workspace_utils import WorkspaceError, ensure_workspace, resolve_workspace_path


MAX_FASTQ_READS = 100_000


class FastqError(ValueError):
    """Raised when a FASTQ file is malformed or unsupported."""


def analyze_fastq_path(relative_path: str, max_reads: int = 10_000) -> dict[str, Any]:
    target = resolve_workspace_path(relative_path)
    if not target.is_file():
        raise WorkspaceError(f"Workspace file not found: {relative_path}")
    if target.suffix.lower() not in {".fastq", ".fq"}:
        raise FastqError("FASTQ QC accepts .fastq or .fq files inside the workspace.")
    bounded_reads = max(1, min(int(max_reads or 10_000), MAX_FASTQ_READS))
    with target.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        result = analyze_fastq_stream(handle, bounded_reads)
    result["path"] = target.relative_to(ensure_workspace().resolve()).as_posix()
    result["file_size"] = target.stat().st_size
    return result


def analyze_fastq_text(text: str, max_reads: int = 10_000) -> dict[str, Any]:
    from io import StringIO

    return analyze_fastq_stream(StringIO(str(text or "")), max_reads)


def analyze_fastq_stream(handle: TextIO, max_reads: int = 10_000) -> dict[str, Any]:
    bounded_reads = max(1, min(int(max_reads or 10_000), MAX_FASTQ_READS))
    read_count = 0
    total_bases = 0
    gc_count = 0
    n_count = 0
    quality_sum = 0
    q20_count = 0
    q30_count = 0
    min_length = None
    max_length = 0
    cycle_quality_sum: list[int] = []
    cycle_quality_count: list[int] = []
    cycle_q20: list[int] = []
    cycle_bases: list[Counter[str]] = []
    length_counts: Counter[int] = Counter()
    exhausted = True

    for record_number, record in enumerate(_fastq_records(handle), start=1):
        if read_count >= bounded_reads:
            exhausted = False
            break
        header, sequence, plus, quality = record
        if not header.startswith("@"):
            raise FastqError(f"FASTQ record {record_number} does not start with '@'.")
        if not plus.startswith("+"):
            raise FastqError(f"FASTQ record {record_number} is missing the '+' separator.")
        if len(sequence) != len(quality):
            raise FastqError(f"FASTQ record {record_number} has unequal sequence and quality lengths.")
        if not sequence:
            raise FastqError(f"FASTQ record {record_number} has an empty sequence.")
        scores = [ord(char) - 33 for char in quality]
        if any(score < 0 or score > 93 for score in scores):
            raise FastqError(f"FASTQ record {record_number} contains invalid Phred+33 quality characters.")

        read_count += 1
        length = len(sequence)
        total_bases += length
        min_length = length if min_length is None else min(min_length, length)
        max_length = max(max_length, length)
        length_counts[length] += 1
        upper = sequence.upper()
        gc_count += upper.count("G") + upper.count("C")
        n_count += upper.count("N")
        quality_sum += sum(scores)
        q20_count += sum(score >= 20 for score in scores)
        q30_count += sum(score >= 30 for score in scores)

        _grow(cycle_quality_sum, length, 0)
        _grow(cycle_quality_count, length, 0)
        _grow(cycle_q20, length, 0)
        _grow(cycle_bases, length, Counter)
        for index, (base, score) in enumerate(zip(upper, scores)):
            cycle_quality_sum[index] += score
            cycle_quality_count[index] += 1
            cycle_q20[index] += int(score >= 20)
            cycle_bases[index][base if base in "ACGTN" else "N"] += 1

    if read_count == 0:
        raise FastqError("No complete FASTQ records were found.")

    per_cycle_quality = [round(total / count, 2) for total, count in zip(cycle_quality_sum, cycle_quality_count)]
    per_cycle_q20 = [round(passing / count * 100, 2) for passing, count in zip(cycle_q20, cycle_quality_count)]
    base_composition = {
        base: [round(counts.get(base, 0) / max(1, total) * 100, 2) for counts, total in zip(cycle_bases, cycle_quality_count)]
        for base in "ACGTN"
    }
    lengths = sorted(length_counts)
    return {
        "reads_analyzed": read_count,
        "sample_limit": bounded_reads,
        "sampled": not exhausted,
        "total_bases": total_bases,
        "mean_read_length": round(total_bases / read_count, 2),
        "min_read_length": min_length or 0,
        "max_read_length": max_length,
        "mean_quality": round(quality_sum / total_bases, 2),
        "q20_percent": round(q20_count / total_bases * 100, 2),
        "q30_percent": round(q30_count / total_bases * 100, 2),
        "gc_percent": round(gc_count / total_bases * 100, 2),
        "n_percent": round(n_count / total_bases * 100, 3),
        "per_cycle_quality": per_cycle_quality,
        "per_cycle_q20": per_cycle_q20,
        "base_composition": base_composition,
        "length_distribution": {
            "lengths": lengths[:250],
            "counts": [length_counts[length] for length in lengths[:250]],
            "truncated": len(lengths) > 250,
        },
        "quality_encoding": "Phred+33",
    }


def _fastq_records(handle: TextIO) -> Iterable[tuple[str, str, str, str]]:
    record: list[str] = []
    for line in handle:
        record.append(line.rstrip("\r\n"))
        if len(record) == 4:
            yield record[0], record[1], record[2], record[3]
            record = []
    if record:
        raise FastqError("FASTQ file ends with an incomplete four-line record.")


def _grow(values: list[Any], length: int, default: Any) -> None:
    while len(values) < length:
        values.append(default() if callable(default) else default)
