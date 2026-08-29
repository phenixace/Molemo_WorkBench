"""Bounded local NCBI BLAST+ execution for workspace FASTA databases."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .workspace_utils import MAX_UPLOAD_BYTES, WORKSPACE_ROOT, WorkspaceError, resolve_workspace_path


ROOT = Path(__file__).resolve().parents[1]
TOOL_ENV_BIN = ROOT / ".molemo-tools" / "bin"
FASTA_SUFFIXES = {".fa", ".fasta", ".faa", ".fna"}
PROTEIN_ALPHABET = set("ABCDEFGHIKLMNPQRSTVWXYZUOJ*")
NUCLEOTIDE_ALPHABET = set("ACGTURYKMSWBDHVN")
PROGRAMS = {"blastp": "prot", "blastn": "nucl"}
TASKS = {
    "blastp": {"blastp", "blastp-short"},
    "blastn": {"blastn", "blastn-short", "megablast", "dc-megablast"},
}
MAX_QUERY_LENGTH = 100_000
MAX_TARGETS = 100
MAX_THREADS = 4
PROCESS_TIMEOUT_SECONDS = 120


class SequenceSearchError(ValueError):
    """Raised when a local sequence search cannot be run safely."""


def find_executable(name: str) -> Path | None:
    configured = str(os.environ.get("MOLEMO_TOOL_BIN") or "").strip()
    candidates = []
    if configured:
        candidates.append(Path(configured).expanduser() / name)
    candidates.append(TOOL_ENV_BIN / name)
    discovered = shutil.which(name)
    if discovered:
        candidates.append(Path(discovered))
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
    return None


def toolchain_status() -> dict[str, Any]:
    tools: dict[str, dict[str, Any]] = {}
    for name in ("blastp", "blastn", "makeblastdb"):
        executable = find_executable(name)
        tools[name] = {
            "installed": executable is not None,
            "path": str(executable) if executable else None,
            "version": _tool_version(executable) if executable else None,
        }
    return {"available": all(item["installed"] for item in tools.values()), "tools": tools}


def clean_query(raw: str, program: str) -> str:
    lines = [line.strip() for line in str(raw).splitlines() if not line.lstrip().startswith(">")]
    sequence = re.sub(r"\s+", "", "".join(lines)).upper()
    if not sequence:
        raise SequenceSearchError("A query sequence is required.")
    if len(sequence) > MAX_QUERY_LENGTH:
        raise SequenceSearchError(f"Query sequences are limited to {MAX_QUERY_LENGTH:,} residues or bases.")
    alphabet = PROTEIN_ALPHABET if program == "blastp" else NUCLEOTIDE_ALPHABET
    invalid = sorted(set(sequence) - alphabet)
    if invalid:
        label = "amino-acid" if program == "blastp" else "nucleotide"
        raise SequenceSearchError(f"Unsupported {label} code(s): {', '.join(invalid)}")
    return sequence


def validate_fasta_database(relative_path: str, program: str) -> tuple[Path, str, int]:
    try:
        target = resolve_workspace_path(relative_path)
    except WorkspaceError as exc:
        raise SequenceSearchError(str(exc)) from exc
    if not target.is_file():
        raise SequenceSearchError(f"Workspace FASTA file not found: {relative_path}")
    if target.suffix.lower() not in FASTA_SUFFIXES:
        raise SequenceSearchError("The search database must be a workspace .fa, .fasta, .faa, or .fna file.")
    if target.stat().st_size > MAX_UPLOAD_BYTES:
        raise SequenceSearchError(f"Workspace FASTA databases are limited to {MAX_UPLOAD_BYTES:,} bytes.")

    alphabet = PROTEIN_ALPHABET if program == "blastp" else NUCLEOTIDE_ALPHABET
    record_count = 0
    has_sequence = False
    try:
        with target.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    if record_count and not has_sequence:
                        raise SequenceSearchError(f"FASTA record before line {line_number} has no sequence.")
                    record_count += 1
                    has_sequence = False
                    continue
                if record_count == 0:
                    raise SequenceSearchError("FASTA sequence data must follow a header beginning with >.")
                sequence_line = re.sub(r"\s+", "", line).upper()
                invalid = sorted(set(sequence_line) - alphabet)
                if invalid:
                    raise SequenceSearchError(
                        f"Unsupported sequence code(s) at FASTA line {line_number}: {', '.join(invalid)}"
                    )
                has_sequence = has_sequence or bool(sequence_line)
    except UnicodeDecodeError as exc:
        raise SequenceSearchError("The workspace FASTA database must be UTF-8 text.") from exc
    if record_count == 0:
        raise SequenceSearchError("The workspace FASTA database contains no records.")
    if not has_sequence:
        raise SequenceSearchError("The final FASTA record has no sequence.")
    relative = target.relative_to(WORKSPACE_ROOT.resolve()).as_posix()
    return target, relative, record_count


def run_local_blast(
    query: str,
    database_path: str,
    program: str = "blastp",
    evalue: float = 1e-5,
    max_hits: int = 10,
    task: str | None = None,
    threads: int = 1,
) -> dict[str, Any]:
    program = str(program or "blastp").strip().lower()
    if program not in PROGRAMS:
        raise SequenceSearchError("program must be blastp or blastn.")
    sequence = clean_query(query, program)
    database, relative_database, database_records = validate_fasta_database(database_path, program)
    try:
        bounded_evalue = float(evalue)
    except (TypeError, ValueError) as exc:
        raise SequenceSearchError("evalue must be numeric.") from exc
    if not 1e-200 <= bounded_evalue <= 1e6:
        raise SequenceSearchError("evalue must be between 1e-200 and 1e6.")
    try:
        bounded_hits = int(max_hits)
        bounded_threads = int(threads)
    except (TypeError, ValueError) as exc:
        raise SequenceSearchError("max_hits and threads must be integers.") from exc
    if not 1 <= bounded_hits <= MAX_TARGETS:
        raise SequenceSearchError(f"max_hits must be between 1 and {MAX_TARGETS}.")
    if not 1 <= bounded_threads <= MAX_THREADS:
        raise SequenceSearchError(f"threads must be between 1 and {MAX_THREADS}.")

    selected_task = str(task or _default_task(program, len(sequence))).strip().lower()
    if selected_task not in TASKS[program]:
        raise SequenceSearchError(f"Unsupported {program} task: {selected_task}")
    blast = find_executable(program)
    makeblastdb = find_executable("makeblastdb")
    if blast is None or makeblastdb is None:
        raise SequenceSearchError(
            "NCBI BLAST+ is not available. Install the project environment or set MOLEMO_TOOL_BIN to its bin directory."
        )

    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    process_env = {
        **os.environ,
        "BLAST_USAGE_REPORT": "false",
        "NCBI_DONT_USE_LOCAL_CONFIG": "true",
        "LC_ALL": "C",
    }
    with tempfile.TemporaryDirectory(prefix="blast-", dir=temp_root) as temporary:
        temporary_path = Path(temporary)
        query_path = temporary_path / "query.fa"
        database_prefix = temporary_path / "database"
        output_path = temporary_path / "result.json"
        query_path.write_text(f">molemo_query\n{sequence}\n", encoding="ascii")
        _run_process(
            [
                str(makeblastdb),
                "-in",
                str(database),
                "-dbtype",
                PROGRAMS[program],
                "-out",
                str(database_prefix),
            ],
            process_env,
        )
        _run_process(
            [
                str(blast),
                "-query",
                str(query_path),
                "-db",
                str(database_prefix),
                "-task",
                selected_task,
                "-evalue",
                str(bounded_evalue),
                "-max_target_seqs",
                str(bounded_hits),
                "-num_threads",
                str(bounded_threads),
                "-outfmt",
                "15",
                "-out",
                str(output_path),
            ],
            process_env,
        )
        try:
            payload = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SequenceSearchError("BLAST+ did not return valid JSON output.") from exc

    result = parse_blast_json(payload)
    result.update(
        {
            "engine": "NCBI BLAST+",
            "program": program,
            "version": _tool_version(blast),
            "task": selected_task,
            "database_path": relative_database,
            "database_sequences": database_records,
            "query_sequence": sequence,
            "max_hits": bounded_hits,
        }
    )
    return result


def parse_blast_json(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        report = payload["BlastOutput2"][0]["report"]
        search = report["results"]["search"]
    except (KeyError, IndexError, TypeError) as exc:
        raise SequenceSearchError("BLAST+ JSON output is missing the expected search report.") from exc
    query_length = int(search.get("query_len") or 0)
    parsed_hits = []
    for raw_hit in search.get("hits") or []:
        descriptions = raw_hit.get("description") or [{}]
        description = descriptions[0] if isinstance(descriptions[0], dict) else {}
        hsps = raw_hit.get("hsps") or []
        if not hsps:
            continue
        hsp = hsps[0]
        align_length = int(hsp.get("align_len") or 0)
        identities = int(hsp.get("identity") or 0)
        query_from = int(hsp.get("query_from") or 0)
        query_to = int(hsp.get("query_to") or 0)
        query_span = abs(query_to - query_from) + 1 if query_from and query_to else 0
        parsed_hits.append(
            {
                "id": str(description.get("id") or ""),
                "accession": str(description.get("accession") or ""),
                "title": str(description.get("title") or description.get("id") or "Untitled sequence"),
                "length": int(raw_hit.get("len") or 0),
                "bit_score": round(float(hsp.get("bit_score") or 0), 3),
                "score": int(hsp.get("score") or 0),
                "evalue": float(hsp.get("evalue") or 0),
                "identities": identities,
                "identity_percent": round(identities / align_length * 100, 2) if align_length else 0.0,
                "positives": int(hsp.get("positive") or identities),
                "gaps": int(hsp.get("gaps") or 0),
                "alignment_length": align_length,
                "query_coverage_percent": round(query_span / query_length * 100, 2) if query_length else 0.0,
                "query_from": query_from,
                "query_to": query_to,
                "hit_from": int(hsp.get("hit_from") or 0),
                "hit_to": int(hsp.get("hit_to") or 0),
                "query_alignment": str(hsp.get("qseq") or ""),
                "midline": str(hsp.get("midline") or ""),
                "hit_alignment": str(hsp.get("hseq") or ""),
            }
        )
    return {
        "query_id": str(search.get("query_id") or "molemo_query"),
        "query_length": query_length,
        "hits": parsed_hits,
        "hit_count": len(parsed_hits),
        "parameters": dict(search.get("params") or report.get("params") or {}),
        "statistics": dict(search.get("stat") or {}),
    }


def _default_task(program: str, query_length: int) -> str:
    if program == "blastp" and query_length < 30:
        return "blastp-short"
    if program == "blastn" and query_length < 50:
        return "blastn-short"
    return program


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
        raise SequenceSearchError(f"{Path(command[0]).name} exceeded the {PROCESS_TIMEOUT_SECONDS}s limit.") from exc
    except OSError as exc:
        raise SequenceSearchError(f"Could not start {Path(command[0]).name}: {exc}") from exc
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        detail = re.sub(r"\s+", " ", detail)[:800]
        raise SequenceSearchError(f"{Path(command[0]).name} failed: {detail}")


def _tool_version(executable: Path | None) -> str | None:
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [str(executable), "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env={**os.environ, "BLAST_USAGE_REPORT": "false", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    first_line = (completed.stdout or completed.stderr or "").splitlines()
    if not first_line:
        return None
    return first_line[0].split(":", 1)[-1].strip()
