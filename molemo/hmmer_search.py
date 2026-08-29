"""Bounded local HMMER profile search with domain-level provenance."""

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .workspace_utils import WORKSPACE_ROOT, WorkspaceError, resolve_workspace_path


ROOT = Path(__file__).resolve().parents[1]
TOOL_ENV_BIN = ROOT / ".molemo-tools" / "bin"
HMM_SUFFIXES = {".hmm"}
FASTA_SUFFIXES = {".fa", ".fasta", ".faa"}
PROTEIN_ALPHABET = set("ABCDEFGHIKLMNPQRSTVWXYZUOJ*")
MAX_HMM_BYTES = 20 * 1024 * 1024
MAX_FASTA_BYTES = 20 * 1024 * 1024
MAX_LINE_CHARS = 1024 * 1024
MAX_MODELS = 32
MAX_SEQUENCES = 5_000
MAX_RESIDUES = 2_000_000
MAX_HITS = 100
MAX_THREADS = 4
MAX_DOMAIN_ROWS = 20_000
MAX_OUTPUT_BYTES = 20 * 1024 * 1024
PROCESS_TIMEOUT_SECONDS = 120


class HmmerSearchError(ValueError):
    """Raised when a local HMMER search cannot be executed safely."""


def find_hmmer_executable(name: str = "hmmsearch") -> Path | None:
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


def hmmer_toolchain_status() -> dict[str, Any]:
    executable = find_hmmer_executable()
    return {
        "available": executable is not None,
        "path": str(executable) if executable else None,
        "version": _hmmer_version(executable) if executable else None,
    }


def preflight_hmmer_profile_search(
    hmm_path: str,
    database_path: str,
    evalue: float = 1e-5,
    domain_evalue: float = 1e-5,
    max_hits: int = 25,
    threads: int = 1,
) -> dict[str, Any]:
    inputs = normalize_hmmer_inputs(
        hmm_path,
        database_path,
        evalue,
        domain_evalue,
        max_hits,
        threads,
    )
    models = _read_hmm_models(resolve_workspace_path(inputs["hmm_path"]))
    sequences = _read_protein_fasta(resolve_workspace_path(inputs["database_path"]))
    toolchain = hmmer_toolchain_status()
    if not toolchain["available"]:
        raise HmmerSearchError(
            "HMMER hmmsearch is not available. Install the project environment or set "
            "MOLEMO_TOOL_BIN to a directory containing HMMER 3."
        )
    residue_count = sum(item["length"] for item in sequences)
    return {
        "ready": True,
        "engine": "HMMER hmmsearch",
        "version": toolchain["version"],
        "hmm_path": inputs["hmm_path"],
        "database_path": inputs["database_path"],
        "model_count": len(models),
        "models": models,
        "sequence_count": len(sequences),
        "residue_count": residue_count,
        "thresholds": {
            "sequence_evalue": inputs["evalue"],
            "domain_evalue": inputs["domain_evalue"],
            "max_hits": inputs["max_hits"],
            "threads": inputs["threads"],
        },
        "warnings": _caveats(),
        "summary": (
            f"Validated {len(models)} amino-acid profile HMM(s) against "
            f"{len(sequences)} protein sequence(s) totaling {residue_count:,} residues."
        ),
    }


def run_hmmer_profile_search(
    hmm_path: str,
    database_path: str,
    evalue: float = 1e-5,
    domain_evalue: float = 1e-5,
    max_hits: int = 25,
    threads: int = 1,
) -> dict[str, Any]:
    inputs = normalize_hmmer_inputs(
        hmm_path,
        database_path,
        evalue,
        domain_evalue,
        max_hits,
        threads,
    )
    hmm_target = resolve_workspace_path(inputs["hmm_path"])
    database_target = resolve_workspace_path(inputs["database_path"])
    models = _read_hmm_models(hmm_target)
    sequences = _read_protein_fasta(database_target)
    executable = find_hmmer_executable()
    if executable is None:
        raise HmmerSearchError(
            "HMMER hmmsearch is not available. Install the project environment or set "
            "MOLEMO_TOOL_BIN to a directory containing HMMER 3."
        )

    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hmmer-search-", dir=temp_root) as temporary:
        temporary_path = Path(temporary)
        domain_path = temporary_path / "domains.domtblout"
        _run_hmmsearch(
            executable,
            inputs,
            domain_path,
        )
        _validate_output_file(domain_path)
        raw_domtblout = domain_path.read_text(encoding="utf-8")
        domains = parse_hmmer_domtblout(raw_domtblout)
        stable_domtblout = _stable_domtblout(raw_domtblout)

    sequence_by_name = {item["name"]: item for item in sequences}
    hit_groups = _group_domain_hits(domains, inputs["max_hits"], sequence_by_name)
    selected_keys = {(item["query_name"], item["target_name"]) for item in hit_groups}
    selected_domains = [
        item for item in domains if (item["query_name"], item["target_name"]) in selected_keys
    ]
    analysis_id = f"hmmer-search-{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc).isoformat()
    result = {
        "analysis_id": analysis_id,
        "method": "HMMER 3 hmmsearch profile-to-sequence search",
        "engine": "HMMER hmmsearch",
        "version": _hmmer_version(executable),
        "retrieved_at": created_at,
        "inputs": inputs,
        "models": models,
        "model_count": len(models),
        "database_sequence_count": len(sequences),
        "database_residue_count": sum(item["length"] for item in sequences),
        "reported_hit_count": len(hit_groups),
        "reported_domain_count": len(selected_domains),
        "total_reported_domain_count": len(domains),
        "hits": hit_groups,
        "domains": selected_domains,
        "outputs": {},
        "caveats": _caveats(),
    }
    result["summary"] = (
        f"HMMER {result['version'] or '3'} reported {len(hit_groups)} profile-target hit(s) "
        f"and {len(selected_domains)} domain(s) from {len(models)} profile model(s) against "
        f"{len(sequences)} protein sequence(s). E-values are search-space dependent; "
        "no functional or mechanistic conclusion was generated."
    )
    _persist_hmmer_result(result, stable_domtblout, hmm_target, database_target)
    return result


def normalize_hmmer_inputs(
    hmm_path: str,
    database_path: str,
    evalue: float = 1e-5,
    domain_evalue: float = 1e-5,
    max_hits: int = 25,
    threads: int = 1,
) -> dict[str, Any]:
    hmm_relative = _workspace_file(hmm_path, HMM_SUFFIXES, MAX_HMM_BYTES, "Profile HMM")
    database_relative = _workspace_file(
        database_path,
        FASTA_SUFFIXES,
        MAX_FASTA_BYTES,
        "Protein FASTA database",
    )
    try:
        sequence_evalue = float(evalue)
        bounded_domain_evalue = float(domain_evalue)
        bounded_hits = int(max_hits)
        bounded_threads = int(threads)
    except (TypeError, ValueError) as exc:
        raise HmmerSearchError("HMMER thresholds, hit limit and threads must be numeric.") from exc
    if not math.isfinite(sequence_evalue) or not 1e-300 <= sequence_evalue <= 10:
        raise HmmerSearchError("evalue must be between 1e-300 and 10.")
    if not math.isfinite(bounded_domain_evalue) or not 1e-300 <= bounded_domain_evalue <= 10:
        raise HmmerSearchError("domain_evalue must be between 1e-300 and 10.")
    if not 1 <= bounded_hits <= MAX_HITS:
        raise HmmerSearchError(f"max_hits must be between 1 and {MAX_HITS}.")
    if not 1 <= bounded_threads <= MAX_THREADS:
        raise HmmerSearchError(f"threads must be between 1 and {MAX_THREADS}.")
    return {
        "hmm_path": hmm_relative,
        "database_path": database_relative,
        "evalue": sequence_evalue,
        "domain_evalue": bounded_domain_evalue,
        "max_hits": bounded_hits,
        "threads": bounded_threads,
    }


def parse_hmmer_domtblout(raw: str) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(str(raw or "").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split(maxsplit=22)
        if len(fields) < 22:
            raise HmmerSearchError(
                f"HMMER domtblout line {line_number} has {len(fields)} fields; expected at least 22."
            )
        try:
            row = {
                "target_name": fields[0],
                "target_accession": "" if fields[1] == "-" else fields[1],
                "target_length": int(fields[2]),
                "query_name": fields[3],
                "query_accession": "" if fields[4] == "-" else fields[4],
                "query_length": int(fields[5]),
                "full_evalue": float(fields[6]),
                "full_score": float(fields[7]),
                "full_bias": float(fields[8]),
                "domain_number": int(fields[9]),
                "domain_total": int(fields[10]),
                "conditional_evalue": float(fields[11]),
                "independent_evalue": float(fields[12]),
                "domain_score": float(fields[13]),
                "domain_bias": float(fields[14]),
                "hmm_from": int(fields[15]),
                "hmm_to": int(fields[16]),
                "alignment_from": int(fields[17]),
                "alignment_to": int(fields[18]),
                "envelope_from": int(fields[19]),
                "envelope_to": int(fields[20]),
                "accuracy": float(fields[21]),
                "description": fields[22] if len(fields) > 22 else "",
            }
        except ValueError as exc:
            raise HmmerSearchError(
                f"HMMER domtblout line {line_number} contains an invalid numeric field."
            ) from exc
        if not (
            1 <= row["alignment_from"] <= row["alignment_to"] <= row["target_length"]
            and 1 <= row["hmm_from"] <= row["hmm_to"] <= row["query_length"]
        ):
            raise HmmerSearchError(
                f"HMMER domtblout line {line_number} contains inconsistent domain coordinates."
            )
        rows.append(row)
        if len(rows) > MAX_DOMAIN_ROWS:
            raise HmmerSearchError(
                f"HMMER reported more than {MAX_DOMAIN_ROWS:,} domains; use a stricter threshold "
                "or smaller database."
            )
    return rows


def _read_hmm_models(path: Path) -> list[dict[str, Any]]:
    models = []
    current: dict[str, Any] = {}
    header_seen = False
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                if len(raw_line) > MAX_LINE_CHARS:
                    raise HmmerSearchError(f"Profile HMM line {line_number} exceeds the line-size limit.")
                line = raw_line.rstrip("\r\n")
                if line.startswith("HMMER3/"):
                    if current:
                        raise HmmerSearchError("Profile HMM model is missing its // terminator.")
                    header_seen = True
                    current = {"format": line.strip()}
                    continue
                if not current:
                    if line.strip():
                        raise HmmerSearchError("Profile HMM must be an HMMER3 text file.")
                    continue
                if line == "//":
                    _finish_hmm_model(current, models)
                    current = {}
                    if len(models) > MAX_MODELS:
                        raise HmmerSearchError(
                            f"Profile HMM contains more than the {MAX_MODELS}-model limit."
                        )
                    continue
                match = re.match(r"^(NAME|ACC|DESC|LENG|ALPH)\s+(.+?)\s*$", line)
                if match:
                    current[match.group(1).casefold()] = match.group(2).strip()
    except UnicodeDecodeError as exc:
        raise HmmerSearchError("Profile HMM must be an uncompressed UTF-8 HMMER3 text file.") from exc
    if current:
        raise HmmerSearchError("Profile HMM model is missing its // terminator.")
    if not header_seen or not models:
        raise HmmerSearchError("Profile HMM does not contain an HMMER3 model.")
    names = [item["name"] for item in models]
    if len(names) != len(set(names)):
        raise HmmerSearchError("Profile HMM model names must be unique for traceable results.")
    return models


def _finish_hmm_model(current: dict[str, Any], models: list[dict[str, Any]]) -> None:
    name = str(current.get("name") or "").strip()
    alphabet = str(current.get("alph") or "").strip().casefold()
    try:
        length = int(current.get("leng") or 0)
    except ValueError as exc:
        raise HmmerSearchError("Profile HMM contains an invalid model length.") from exc
    if not name or length < 1:
        raise HmmerSearchError("Each profile HMM model requires NAME and positive LENG fields.")
    if alphabet != "amino":
        raise HmmerSearchError("Only amino-acid profile HMMs are supported in this workflow.")
    models.append(
        {
            "name": name,
            "accession": str(current.get("acc") or ""),
            "description": str(current.get("desc") or ""),
            "length": length,
            "alphabet": alphabet,
            "format": current["format"],
        }
    )


def _read_protein_fasta(path: Path) -> list[dict[str, Any]]:
    sequences = []
    name = ""
    description = ""
    parts: list[str] = []
    residue_count = 0

    def finish_record() -> None:
        nonlocal residue_count
        if not name:
            return
        sequence = "".join(parts)
        if not sequence:
            raise HmmerSearchError(f"Protein FASTA record {name} has no sequence.")
        residue_count += len(sequence)
        if residue_count > MAX_RESIDUES:
            raise HmmerSearchError(
                f"Protein FASTA exceeds the {MAX_RESIDUES:,}-residue search limit."
            )
        sequences.append(
            {
                "name": name,
                "description": description,
                "length": len(sequence),
            }
        )
        if len(sequences) > MAX_SEQUENCES:
            raise HmmerSearchError(
                f"Protein FASTA contains more than the {MAX_SEQUENCES:,}-sequence limit."
            )

    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                if len(raw_line) > MAX_LINE_CHARS:
                    raise HmmerSearchError(f"Protein FASTA line {line_number} exceeds the line-size limit.")
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    finish_record()
                    header = line[1:].strip()
                    if not header:
                        raise HmmerSearchError(f"Protein FASTA line {line_number} has an empty header.")
                    name, _, description = header.partition(" ")
                    parts = []
                    continue
                if not name:
                    raise HmmerSearchError("Protein FASTA sequence data must follow a > header.")
                sequence_line = re.sub(r"\s+", "", line).upper()
                invalid = sorted(set(sequence_line) - PROTEIN_ALPHABET)
                if invalid:
                    raise HmmerSearchError(
                        f"Unsupported amino-acid code(s) at FASTA line {line_number}: "
                        + ", ".join(invalid)
                    )
                parts.append(sequence_line)
        finish_record()
    except UnicodeDecodeError as exc:
        raise HmmerSearchError("Protein FASTA must be UTF-8 text.") from exc
    if not sequences:
        raise HmmerSearchError("Protein FASTA does not contain any records.")
    names = [item["name"] for item in sequences]
    if len(names) != len(set(names)):
        raise HmmerSearchError("Protein FASTA identifiers must be unique for domain coordinates.")
    return sequences


def _group_domain_hits(
    domains: list[dict[str, Any]],
    max_hits: int,
    sequences: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for domain in domains:
        grouped.setdefault((domain["query_name"], domain["target_name"]), []).append(domain)
    ordered = sorted(
        grouped.items(),
        key=lambda item: (
            min(domain["full_evalue"] for domain in item[1]),
            -max(domain["full_score"] for domain in item[1]),
            item[0],
        ),
    )[:max_hits]
    hits = []
    for (query_name, target_name), rows in ordered:
        rows.sort(key=lambda item: (item["alignment_from"], item["domain_number"]))
        representative = rows[0]
        sequence = sequences.get(target_name) or {}
        hits.append(
            {
                "query_name": query_name,
                "query_accession": representative["query_accession"],
                "query_length": representative["query_length"],
                "target_name": target_name,
                "target_accession": representative["target_accession"],
                "target_length": representative["target_length"],
                "target_description": sequence.get("description") or representative["description"],
                "full_evalue": representative["full_evalue"],
                "full_score": representative["full_score"],
                "full_bias": representative["full_bias"],
                "domain_count": len(rows),
                "domains": rows,
            }
        )
    return hits


def _run_hmmsearch(
    executable: Path,
    inputs: dict[str, Any],
    domain_path: Path,
) -> None:
    command = [
        str(executable),
        "--cpu",
        str(inputs["threads"]),
        "--noali",
        "-E",
        str(inputs["evalue"]),
        "--domE",
        str(inputs["domain_evalue"]),
        "--domtblout",
        str(domain_path),
        "-o",
        os.devnull,
        inputs["hmm_path"],
        inputs["database_path"],
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PROCESS_TIMEOUT_SECONDS,
            env={**os.environ, "LC_ALL": "C"},
            cwd=WORKSPACE_ROOT.resolve(),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HmmerSearchError(
            f"hmmsearch exceeded the {PROCESS_TIMEOUT_SECONDS}s local runtime limit."
        ) from exc
    except OSError as exc:
        raise HmmerSearchError(f"Could not start hmmsearch: {exc}") from exc
    if completed.returncode:
        detail = re.sub(
            r"\s+",
            " ",
            (completed.stderr or completed.stdout or "unknown error").strip(),
        )[:800]
        raise HmmerSearchError(f"hmmsearch failed: {detail}")


def _stable_domtblout(raw: str) -> str:
    omitted = ("# Option settings:", "# Current dir:", "# Date:")
    lines = [line for line in raw.splitlines() if not line.startswith(omitted)]
    return "\n".join(lines) + "\n"


def _persist_hmmer_result(
    result: dict[str, Any],
    raw_domtblout: str,
    hmm_path: Path,
    database_path: Path,
) -> None:
    analyses_root = WORKSPACE_ROOT / "analyses"
    analyses_root.mkdir(parents=True, exist_ok=True)
    final_output = analyses_root / result["analysis_id"]
    temp_root = WORKSPACE_ROOT / ".molemo" / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    relative_root = final_output.resolve().relative_to(WORKSPACE_ROOT.resolve()).as_posix()
    result["output_root"] = relative_root
    result["outputs"] = {
        "hits": f"{relative_root}/hits.tsv",
        "domains": f"{relative_root}/domains.tsv",
        "domtblout": f"{relative_root}/hmmsearch.domtblout",
        "report": f"{relative_root}/report.json",
        "manifest": f"{relative_root}/run_manifest.json",
        "summary": f"{relative_root}/summary.md",
    }
    with tempfile.TemporaryDirectory(prefix="hmmer-publish-", dir=temp_root) as temporary:
        output = Path(temporary) / "output"
        output.mkdir()
        _write_hits(output / "hits.tsv", result["hits"])
        _write_domains(output / "domains.tsv", result["domains"])
        (output / "hmmsearch.domtblout").write_text(raw_domtblout, encoding="utf-8")
        (output / "report.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        manifest = {
            "analysis_id": result["analysis_id"],
            "method": result["method"],
            "created_at": result["retrieved_at"],
            "engine": {"name": result["engine"], "version": result["version"]},
            "inputs": result["inputs"],
            "input_sha256": {
                "hmm": _sha256(hmm_path),
                "database": _sha256(database_path),
            },
            "bounds": {
                "max_hmm_bytes": MAX_HMM_BYTES,
                "max_fasta_bytes": MAX_FASTA_BYTES,
                "max_models": MAX_MODELS,
                "max_sequences": MAX_SEQUENCES,
                "max_residues": MAX_RESIDUES,
                "max_domain_rows": MAX_DOMAIN_ROWS,
                "process_timeout_seconds": PROCESS_TIMEOUT_SECONDS,
            },
            "files": [path.rsplit("/", 1)[-1] for path in result["outputs"].values()],
        }
        (output / "run_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (output / "summary.md").write_text(_summary_markdown(result), encoding="utf-8")
        if final_output.exists():
            raise HmmerSearchError(f"Analysis output already exists: {result['analysis_id']}")
        shutil.move(str(output), str(final_output))


def _write_hits(path: Path, hits: list[dict[str, Any]]) -> None:
    fields = [
        "query_name",
        "query_accession",
        "query_length",
        "target_name",
        "target_accession",
        "target_length",
        "target_description",
        "full_evalue",
        "full_score",
        "full_bias",
        "domain_count",
    ]
    _write_tsv(path, fields, hits)


def _write_domains(path: Path, domains: list[dict[str, Any]]) -> None:
    fields = [
        "query_name",
        "query_accession",
        "query_length",
        "target_name",
        "target_accession",
        "target_length",
        "domain_number",
        "domain_total",
        "full_evalue",
        "full_score",
        "conditional_evalue",
        "independent_evalue",
        "domain_score",
        "domain_bias",
        "hmm_from",
        "hmm_to",
        "alignment_from",
        "alignment_to",
        "envelope_from",
        "envelope_to",
        "accuracy",
        "description",
    ]
    _write_tsv(path, fields, domains)


def _write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _summary_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# HMMER profile search",
        "",
        result["summary"],
        "",
        "## Inputs",
        "",
        f"- Profile HMM: {result['inputs']['hmm_path']}",
        f"- Protein FASTA: {result['inputs']['database_path']}",
        f"- Sequence E-value threshold: {result['inputs']['evalue']}",
        f"- Domain E-value threshold: {result['inputs']['domain_evalue']}",
        f"- Engine: HMMER {result['version'] or 'unknown'}",
        "",
        "## Reported hits",
        "",
    ]
    if result["hits"]:
        lines.extend(
            f"- {hit['query_name']} -> {hit['target_name']}: E={hit['full_evalue']:.3g}, "
            f"score={hit['full_score']:.2f}, domains={hit['domain_count']}"
            for hit in result["hits"][:25]
        )
    else:
        lines.append("- No hits met the approved reporting thresholds.")
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {item}" for item in result["caveats"])
    lines.append("")
    return "\n".join(lines)


def _workspace_file(
    value: str,
    suffixes: set[str],
    maximum_bytes: int,
    label: str,
) -> str:
    relative = str(value or "").strip()
    if not relative:
        raise HmmerSearchError(f"A workspace-relative {label} path is required.")
    try:
        target = resolve_workspace_path(relative)
    except WorkspaceError as exc:
        raise HmmerSearchError(str(exc)) from exc
    if target.suffix.casefold() not in suffixes:
        allowed = ", ".join(sorted(suffixes))
        raise HmmerSearchError(f"{label} must use one of these suffixes: {allowed}.")
    if not target.is_file():
        raise HmmerSearchError(f"{label} file was not found in the workspace.")
    size = target.stat().st_size
    if size <= 0:
        raise HmmerSearchError(f"{label} file is empty.")
    if size > maximum_bytes:
        raise HmmerSearchError(f"{label} exceeds the local {maximum_bytes:,}-byte limit.")
    return target.relative_to(WORKSPACE_ROOT.resolve()).as_posix()


def _validate_output_file(path: Path) -> None:
    if not path.is_file():
        raise HmmerSearchError("hmmsearch did not produce a domain table.")
    if path.stat().st_size > MAX_OUTPUT_BYTES:
        raise HmmerSearchError(
            f"hmmsearch domain output exceeds the {MAX_OUTPUT_BYTES:,}-byte limit; "
            "use a stricter threshold or smaller database."
        )


def _hmmer_version(executable: Path | None) -> str | None:
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [str(executable), "-h"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = completed.stdout or completed.stderr or ""
    match = re.search(r"# HMMER\s+([^;\r\n]+)", text)
    return match.group(1).strip() if match else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _caveats() -> list[str]:
    return [
        "HMMER sequence E-values depend on target database size; domain conditional E-values also depend on the number of targets passing the sequence reporting threshold. Values from different search spaces are not directly interchangeable.",
        "A profile match supports sequence-family or domain relatedness, not a complete functional, mechanistic, localization or activity assignment.",
        "Domain boundaries are model-based alignment coordinates and should be reviewed with profile coverage, score, bias, architecture and independent evidence.",
        "The profile HMM and target FASTA are user-supplied local inputs. This workflow does not download, version or validate Pfam or other external profile databases.",
    ]
