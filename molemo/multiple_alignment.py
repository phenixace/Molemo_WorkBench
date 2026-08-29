"""Researcher-approved MAFFT protein alignment and site conservation review."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .workspace_utils import WORKSPACE_ROOT, WorkspaceError, resolve_workspace_path


ROOT = Path(__file__).resolve().parents[1]
TOOL_ENV_BIN = ROOT / ".molemo-tools" / "bin"
FASTA_SUFFIXES = {".fa", ".fasta", ".faa", ".afa"}
PROTEIN_ALPHABET = set("ACDEFGHIKLMNPQRSTVWYX")
CANONICAL_AA = set("ACDEFGHIKLMNPQRSTVWY")
MAX_FASTA_BYTES = 2 * 1024 * 1024
MAX_SEQUENCES = 100
MIN_SEQUENCES = 3
MAX_SEQUENCE_LENGTH = 5_000
MAX_TOTAL_RESIDUES = 200_000
MAX_ALIGNMENT_COLUMNS = 10_000
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
PROCESS_TIMEOUT_SECONDS = 120
DISPLAY_FLANK_COLUMNS = 35
MAX_TRACK_BINS = 300


class MultipleAlignmentError(ValueError):
    """Raised when an alignment review cannot be executed or interpreted safely."""


def find_mafft_executable() -> Path | None:
    configured = str(os.environ.get("MOLEMO_TOOL_BIN") or "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser() / "mafft")
    candidates.append(TOOL_ENV_BIN / "mafft")
    discovered = shutil.which("mafft")
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def mafft_toolchain_status() -> dict[str, Any]:
    executable = find_mafft_executable()
    return {
        "available": executable is not None,
        "path": str(executable) if executable else None,
        "version": _mafft_version(executable) if executable else None,
    }


def normalize_alignment_inputs(
    fasta_path: str,
    reference_id: str,
    site: str | int,
) -> dict[str, Any]:
    relative = _workspace_fasta(fasta_path)
    reference = str(reference_id or "").strip()
    if not reference or len(reference) > 200 or any(char.isspace() for char in reference):
        raise MultipleAlignmentError("Reference ID must be one exact FASTA identifier without whitespace.")
    site_text = str(site or "").strip().upper().replace("P.", "")
    expected_residue = ""
    alternate_residue = ""
    if site_text.isdigit():
        position = int(site_text)
        site_label = str(position)
    else:
        match = re.fullmatch(r"([ACDEFGHIKLMNPQRSTVWY])([1-9][0-9]*)([ACDEFGHIKLMNPQRSTVWY])", site_text)
        if not match:
            raise MultipleAlignmentError("Site must be a positive reference position or substitution such as G12C.")
        expected_residue, raw_position, alternate_residue = match.groups()
        if expected_residue == alternate_residue:
            raise MultipleAlignmentError("Variant reference and alternate amino acids must differ.")
        position = int(raw_position)
        site_label = f"{expected_residue}{position}{alternate_residue}"
    if position < 1 or position > MAX_SEQUENCE_LENGTH:
        raise MultipleAlignmentError(
            f"Reference position must be between 1 and {MAX_SEQUENCE_LENGTH:,}."
        )
    return {
        "fasta_path": relative,
        "reference_id": reference,
        "site": site_label,
        "reference_position": position,
        "expected_residue": expected_residue,
        "alternate_residue": alternate_residue,
    }


def preflight_multiple_alignment(**arguments: Any) -> dict[str, Any]:
    inputs = normalize_alignment_inputs(**arguments)
    target = resolve_workspace_path(inputs["fasta_path"])
    records = read_protein_fasta(target)
    reference = _validate_reference(records, inputs)
    toolchain = mafft_toolchain_status()
    if not toolchain["available"]:
        raise MultipleAlignmentError(
            "MAFFT is not available. Install the project environment or set MOLEMO_TOOL_BIN."
        )
    return {
        "ready": True,
        "preview": True,
        "engine": "MAFFT",
        "version": toolchain["version"],
        "inputs": inputs,
        "sequence_count": len(records),
        "total_residues": sum(item["length"] for item in records),
        "records": [
            {key: item[key] for key in ("id", "description", "length")}
            for item in records
        ],
        "reference": {
            "id": reference["id"],
            "length": reference["length"],
            "position": inputs["reference_position"],
            "residue": reference["sequence"][inputs["reference_position"] - 1],
            "site": inputs["site"],
            "alternate_residue": inputs["alternate_residue"],
        },
        "warnings": _caveats(),
        "summary": (
            f"Validated {len(records)} protein sequences and reference {reference['id']} "
            f"position {inputs['reference_position']} for a bounded MAFFT alignment."
        ),
    }


def run_multiple_alignment(**arguments: Any) -> dict[str, Any]:
    inputs = normalize_alignment_inputs(**arguments)
    target = resolve_workspace_path(inputs["fasta_path"])
    records = read_protein_fasta(target)
    reference = _validate_reference(records, inputs)
    executable = find_mafft_executable()
    if executable is None:
        raise MultipleAlignmentError(
            "MAFFT is not available. Install the project environment or set MOLEMO_TOOL_BIN."
        )
    aligned_records = _run_mafft(executable, records)
    columns = calculate_conservation(aligned_records)
    if len(columns) > MAX_ALIGNMENT_COLUMNS:
        raise MultipleAlignmentError(
            f"MAFFT alignment exceeds the {MAX_ALIGNMENT_COLUMNS:,}-column output limit."
        )
    site_summary = map_reference_site(aligned_records, columns, inputs)
    reference_alignment = next(item["sequence"] for item in aligned_records if item["id"] == reference["id"])
    sequence_summaries = _sequence_summaries(aligned_records, reference_alignment, site_summary)
    display = _display_window(aligned_records, columns, sequence_summaries, site_summary)
    analysis_id = f"protein-conservation-{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    fully_conserved = sum(item["fully_conserved"] for item in columns)
    high_conservation = sum(
        item["consensus_support"] >= 0.8 and item["occupancy"] >= 0.8 for item in columns
    )
    result = {
        "analysis_id": analysis_id,
        "method": "MAFFT protein multiple-sequence alignment with unweighted column conservation",
        "engine": "MAFFT",
        "version": _mafft_version(executable),
        "created_at": created_at,
        "inputs": inputs,
        "sequence_count": len(records),
        "total_input_residues": sum(item["length"] for item in records),
        "alignment_length": len(columns),
        "fully_conserved_columns": fully_conserved,
        "high_conservation_columns": high_conservation,
        "mean_consensus_support": round(
            sum(item["consensus_support"] for item in columns) / max(1, len(columns)), 4
        ),
        "site": site_summary,
        "sequences": sequence_summaries,
        "display": display,
        "conservation_track": _conservation_track(columns, site_summary["alignment_column"]),
        "outputs": {},
        "caveats": _caveats(),
    }
    site_text = (
        f"{site_summary['reference_residue']}{site_summary['reference_position']}"
        + (site_summary["alternate_residue"] if site_summary["alternate_residue"] else "")
    )
    result["summary"] = (
        f"MAFFT {result['version'] or '7'} aligned {len(records)} protein sequences across "
        f"{len(columns)} columns. Reference site {site_text} maps to column "
        f"{site_summary['alignment_column']} with consensus {site_summary['consensus_residue']} "
        f"in {site_summary['matching_sequence_count']}/{len(records)} approved input sequences."
    )
    _persist_alignment(result, aligned_records, columns, target)
    return result


def read_protein_fasta(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    identifier = ""
    description = ""
    parts: list[str] = []

    def finish() -> None:
        if not identifier:
            return
        sequence = "".join(parts)
        if not sequence:
            raise MultipleAlignmentError(f"Protein FASTA record {identifier} has no sequence.")
        if len(sequence) > MAX_SEQUENCE_LENGTH:
            raise MultipleAlignmentError(
                f"Protein FASTA record {identifier} exceeds {MAX_SEQUENCE_LENGTH:,} residues."
            )
        records.append(
            {
                "id": identifier,
                "description": description,
                "sequence": sequence,
                "length": len(sequence),
            }
        )

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    finish()
                    header = line[1:].strip()
                    if not header:
                        raise MultipleAlignmentError(f"Protein FASTA line {line_number} has an empty header.")
                    identifier, _, description = header.partition(" ")
                    parts = []
                    continue
                if not identifier:
                    raise MultipleAlignmentError("Protein FASTA sequence data must follow a > header.")
                sequence_line = re.sub(r"\s+", "", line).upper()
                invalid = sorted(set(sequence_line) - PROTEIN_ALPHABET)
                if invalid:
                    raise MultipleAlignmentError(
                        f"Unsupported amino-acid code(s) at FASTA line {line_number}: "
                        + ", ".join(invalid)
                    )
                parts.append(sequence_line)
        finish()
    except UnicodeDecodeError as exc:
        raise MultipleAlignmentError("Protein FASTA must be UTF-8 text.") from exc
    if not MIN_SEQUENCES <= len(records) <= MAX_SEQUENCES:
        raise MultipleAlignmentError(
            f"Protein FASTA must contain between {MIN_SEQUENCES} and {MAX_SEQUENCES} sequences."
        )
    identifiers = [item["id"] for item in records]
    if len(identifiers) != len(set(identifiers)):
        raise MultipleAlignmentError("Protein FASTA identifiers must be unique.")
    total = sum(item["length"] for item in records)
    if total > MAX_TOTAL_RESIDUES:
        raise MultipleAlignmentError(
            f"Protein FASTA exceeds the {MAX_TOTAL_RESIDUES:,}-residue alignment limit."
        )
    return records


def parse_aligned_fasta(raw: str) -> list[dict[str, Any]]:
    records = []
    identifier = ""
    parts: list[str] = []

    def finish() -> None:
        if identifier:
            records.append({"id": identifier, "sequence": "".join(parts)})

    for line_number, raw_line in enumerate(str(raw or "").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            finish()
            identifier = line[1:].strip().split(maxsplit=1)[0]
            if not identifier:
                raise MultipleAlignmentError(f"Aligned FASTA line {line_number} has an empty header.")
            parts = []
            continue
        if not identifier:
            raise MultipleAlignmentError("Aligned FASTA sequence data must follow a > header.")
        sequence = re.sub(r"\s+", "", line).upper()
        invalid = sorted(set(sequence) - (PROTEIN_ALPHABET | {"-"}))
        if invalid:
            raise MultipleAlignmentError(
                f"MAFFT output contains unsupported character(s): {', '.join(invalid)}."
            )
        parts.append(sequence)
    finish()
    if not records:
        raise MultipleAlignmentError("MAFFT did not return aligned FASTA records.")
    lengths = {len(item["sequence"]) for item in records}
    if len(lengths) != 1:
        raise MultipleAlignmentError("MAFFT output sequences do not share one alignment length.")
    return records


def calculate_conservation(aligned_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not aligned_records:
        raise MultipleAlignmentError("At least one aligned sequence is required.")
    width = len(aligned_records[0]["sequence"])
    count = len(aligned_records)
    columns = []
    for index in range(width):
        symbols = [item["sequence"][index] for item in aligned_records]
        observed = [symbol for symbol in symbols if symbol != "-"]
        canonical = [symbol for symbol in observed if symbol in CANONICAL_AA]
        counts = Counter(canonical)
        consensus, support_count = (sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0] if counts else ("X", 0))
        entropy = 0.0
        if canonical:
            for value in counts.values():
                probability = value / len(canonical)
                entropy -= probability * math.log2(probability)
        columns.append(
            {
                "column": index + 1,
                "consensus": consensus,
                "consensus_support": round(support_count / count, 4),
                "residue_identity": round(support_count / max(1, len(canonical)), 4),
                "occupancy": round(len(observed) / count, 4),
                "gap_fraction": round(symbols.count("-") / count, 4),
                "unknown_fraction": round(symbols.count("X") / count, 4),
                "shannon_entropy_bits": round(entropy, 4),
                "fully_conserved": len(canonical) == count and len(counts) == 1,
                "counts": ";".join(f"{key}:{counts[key]}" for key in sorted(counts)),
            }
        )
    return columns


def map_reference_site(
    aligned_records: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    inputs: dict[str, Any],
) -> dict[str, Any]:
    reference = next(
        (item for item in aligned_records if item["id"] == inputs["reference_id"]),
        None,
    )
    if reference is None:
        raise MultipleAlignmentError("Reference ID was not retained by MAFFT.")
    residue_position = 0
    alignment_index = None
    for index, residue in enumerate(reference["sequence"]):
        if residue != "-":
            residue_position += 1
        if residue_position == inputs["reference_position"] and residue != "-":
            alignment_index = index
            break
    if alignment_index is None:
        raise MultipleAlignmentError("Reference site could not be mapped into the MAFFT alignment.")
    reference_residue = reference["sequence"][alignment_index]
    expected = inputs["expected_residue"]
    if expected and reference_residue != expected:
        raise MultipleAlignmentError(
            f"Reference {reference['id']} contains {reference_residue} at position "
            f"{inputs['reference_position']}; site {inputs['site']} expects {expected}."
        )
    observations = []
    for item in aligned_records:
        residue = item["sequence"][alignment_index]
        observations.append(
            {
                "sequence_id": item["id"],
                "residue": residue,
                "matches_reference": residue == reference_residue,
                "status": "gap" if residue == "-" else "unknown" if residue == "X" else "match" if residue == reference_residue else "substitution",
            }
        )
    column = columns[alignment_index]
    return {
        "label": inputs["site"],
        "reference_id": reference["id"],
        "reference_position": inputs["reference_position"],
        "reference_residue": reference_residue,
        "alternate_residue": inputs["alternate_residue"],
        "alignment_column": alignment_index + 1,
        "consensus_residue": column["consensus"],
        "consensus_support": column["consensus_support"],
        "residue_identity": column["residue_identity"],
        "occupancy": column["occupancy"],
        "fully_conserved": column["fully_conserved"],
        "matching_sequence_count": sum(item["matches_reference"] for item in observations),
        "observations": observations,
    }


def _validate_reference(
    records: list[dict[str, Any]], inputs: dict[str, Any]
) -> dict[str, Any]:
    matches = [item for item in records if item["id"] == inputs["reference_id"]]
    if len(matches) != 1:
        raise MultipleAlignmentError(
            f"Reference ID {inputs['reference_id']} was not found exactly once in the FASTA input."
        )
    reference = matches[0]
    position = inputs["reference_position"]
    if position > reference["length"]:
        raise MultipleAlignmentError(
            f"Reference position {position} exceeds {reference['id']} length {reference['length']}."
        )
    observed = reference["sequence"][position - 1]
    expected = inputs["expected_residue"]
    if expected and observed != expected:
        raise MultipleAlignmentError(
            f"Reference {reference['id']} contains {observed} at position {position}; "
            f"site {inputs['site']} expects {expected}."
        )
    return reference


def _run_mafft(
    executable: Path, records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mafft-alignment-", dir=temp_root) as temporary:
        input_path = Path(temporary) / "input.faa"
        input_path.write_text(_render_fasta(records), encoding="utf-8")
        command = [
            str(executable),
            "--auto",
            "--amino",
            "--quiet",
            "--thread",
            "1",
            str(input_path),
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
                check=False,
                cwd=Path(temporary),
                env={
                    **os.environ,
                    "LC_ALL": "C",
                    "PATH": str(executable.parent) + os.pathsep + os.environ.get("PATH", ""),
                },
            )
        except subprocess.TimeoutExpired as exc:
            raise MultipleAlignmentError(
                f"MAFFT exceeded the {PROCESS_TIMEOUT_SECONDS}s local runtime limit."
            ) from exc
        except OSError as exc:
            raise MultipleAlignmentError(f"Could not start MAFFT: {exc}") from exc
    if completed.returncode:
        detail = re.sub(
            r"\s+", " ", (completed.stderr or completed.stdout or "unknown error").strip()
        )[:800]
        raise MultipleAlignmentError(f"MAFFT failed: {detail}")
    if len(completed.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise MultipleAlignmentError(
            f"MAFFT output exceeds the {MAX_OUTPUT_BYTES:,}-byte local limit."
        )
    aligned = parse_aligned_fasta(completed.stdout)
    expected_ids = [item["id"] for item in records]
    if [item["id"] for item in aligned] != expected_ids:
        raise MultipleAlignmentError("MAFFT output did not preserve the approved input sequence order.")
    original = {item["id"]: item["sequence"] for item in records}
    for item in aligned:
        if item["sequence"].replace("-", "") != original[item["id"]]:
            raise MultipleAlignmentError(f"MAFFT output changed residues for {item['id']}.")
    return aligned


def _sequence_summaries(
    aligned_records: list[dict[str, Any]],
    reference_alignment: str,
    site: dict[str, Any],
) -> list[dict[str, Any]]:
    site_by_id = {item["sequence_id"]: item for item in site["observations"]}
    rows = []
    for item in aligned_records:
        compared = [
            (reference, residue)
            for reference, residue in zip(reference_alignment, item["sequence"])
            if reference != "-" and residue != "-"
        ]
        identity = sum(reference == residue for reference, residue in compared) / max(1, len(compared))
        rows.append(
            {
                "id": item["id"],
                "ungapped_length": len(item["sequence"].replace("-", "")),
                "identity_to_reference": round(identity, 4),
                "site_residue": site_by_id[item["id"]]["residue"],
                "site_status": site_by_id[item["id"]]["status"],
            }
        )
    return rows


def _display_window(
    aligned_records: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    site: dict[str, Any],
) -> dict[str, Any]:
    center = site["alignment_column"]
    start = max(1, center - DISPLAY_FLANK_COLUMNS)
    end = min(len(columns), center + DISPLAY_FLANK_COLUMNS)
    summary_by_id = {item["id"]: item for item in summaries}
    return {
        "start_column": start,
        "end_column": end,
        "site_column": center,
        "site_offset": center - start,
        "consensus": "".join(item["consensus"] if item["occupancy"] else "-" for item in columns[start - 1 : end]),
        "conservation": [item["consensus_support"] for item in columns[start - 1 : end]],
        "sequences": [
            {
                **summary_by_id[item["id"]],
                "aligned_sequence": item["sequence"][start - 1 : end],
            }
            for item in aligned_records
        ],
    }


def _conservation_track(
    columns: list[dict[str, Any]], site_column: int
) -> dict[str, Any]:
    bin_size = max(1, math.ceil(len(columns) / MAX_TRACK_BINS))
    bins = []
    for start in range(0, len(columns), bin_size):
        chunk = columns[start : start + bin_size]
        end = start + len(chunk)
        bins.append(
            {
                "start_column": start + 1,
                "end_column": end,
                "mean_consensus_support": round(
                    sum(item["consensus_support"] for item in chunk) / len(chunk), 4
                ),
                "mean_occupancy": round(
                    sum(item["occupancy"] for item in chunk) / len(chunk), 4
                ),
                "contains_site": start < site_column <= end,
            }
        )
    return {"bin_size": bin_size, "bins": bins}


def _persist_alignment(
    result: dict[str, Any],
    aligned_records: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    input_path: Path,
) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.relative_to(WORKSPACE_ROOT).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "alignment": f"{relative_root}/alignment.fasta",
        "conservation": f"{relative_root}/conservation.tsv",
        "site_observations": f"{relative_root}/site_observations.tsv",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="mafft-publish-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        (output / "alignment.fasta").write_text(_render_fasta(aligned_records), encoding="utf-8")
        _write_tsv(output / "conservation.tsv", columns)
        _write_tsv(output / "site_observations.tsv", result["site"]["observations"])
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "created_at": result["created_at"],
            "engine": {"name": result["engine"], "version": result["version"]},
            "command": ["mafft", "--auto", "--amino", "--quiet", "--thread", "1", "<sanitized-input.faa>"],
            "inputs": result["inputs"],
            "input_sha256": _sha256(input_path),
            "bounds": {
                "max_fasta_bytes": MAX_FASTA_BYTES,
                "min_sequences": MIN_SEQUENCES,
                "max_sequences": MAX_SEQUENCES,
                "max_sequence_length": MAX_SEQUENCE_LENGTH,
                "max_total_residues": MAX_TOTAL_RESIDUES,
                "max_alignment_columns": MAX_ALIGNMENT_COLUMNS,
                "process_timeout_seconds": PROCESS_TIMEOUT_SECONDS,
                "threads": 1,
            },
            "files": [path.rsplit("/", 1)[-1] for path in result["outputs"].values()],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise MultipleAlignmentError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _render_fasta(records: Iterable[dict[str, Any]]) -> str:
    lines = []
    for item in records:
        lines.append(f">{item['id']}")
        sequence = str(item["sequence"])
        lines.extend(sequence[index : index + 80] for index in range(0, len(sequence), 80))
    return "\n".join(lines) + "\n"


def _write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _workspace_fasta(value: str) -> str:
    relative = str(value or "").strip()
    if not relative:
        raise MultipleAlignmentError("A workspace-relative protein FASTA path is required.")
    try:
        target = resolve_workspace_path(relative)
    except WorkspaceError as exc:
        raise MultipleAlignmentError(str(exc)) from exc
    if target.suffix.casefold() not in FASTA_SUFFIXES:
        raise MultipleAlignmentError("Protein FASTA must use .fa, .fasta, .faa, or .afa.")
    if not target.is_file():
        raise MultipleAlignmentError("Protein FASTA file was not found in the workspace.")
    size = target.stat().st_size
    if size <= 0:
        raise MultipleAlignmentError("Protein FASTA file is empty.")
    if size > MAX_FASTA_BYTES:
        raise MultipleAlignmentError(
            f"Protein FASTA exceeds the {MAX_FASTA_BYTES:,}-byte local limit."
        )
    return target.relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def _mafft_version(executable: Path | None) -> str | None:
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = completed.stdout or completed.stderr or ""
    match = re.search(r"v?([0-9]+(?:\.[0-9]+)+)", text)
    return match.group(1) if match else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _summary_markdown(result: dict[str, Any]) -> str:
    site = result["site"]
    lines = [
        "# Protein family conservation review",
        "",
        result["summary"],
        "",
        "## Reference site",
        "",
        f"- Reference: {site['reference_id']}",
        f"- Position: {site['reference_position']} ({site['reference_residue']})",
        f"- Alignment column: {site['alignment_column']}",
        f"- Consensus: {site['consensus_residue']}",
        f"- Matching approved input sequences: {site['matching_sequence_count']}/{result['sequence_count']}",
        "",
        "## Interpretation boundary",
        "",
    ]
    lines.extend(f"- {item}" for item in result["caveats"])
    return "\n".join(lines) + "\n"


def _caveats() -> list[str]:
    return [
        "Conservation is calculated only across the approved input sequences; the workflow does not establish that they are orthologs, a complete protein family, or an unbiased evolutionary sample.",
        "Each sequence has equal weight. Closely related or redundant sequences can inflate consensus support, and no phylogenetic correction or evolutionary-rate model is applied.",
        "MAFFT produces a heuristic alignment. Gap-rich, low-complexity, disordered, or weakly homologous regions require manual review and may not support residue-level comparison.",
        "Consensus support and sequence identity are descriptive alignment statistics, not probabilities of functional importance, pathogenicity, structural equivalence, or mutational effect.",
    ]
