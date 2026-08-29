"""Small deterministic Needleman-Wunsch sequence aligner."""

from __future__ import annotations

import re
from typing import Any


VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def clean_sequence(raw: str) -> str:
    lines = [line.strip() for line in str(raw).splitlines() if not line.strip().startswith(">")]
    sequence = re.sub(r"[^A-Za-z]", "", "".join(lines)).upper()
    invalid = sorted(set(sequence) - VALID_AA)
    if not sequence:
        raise ValueError("Both sequences are required")
    if invalid:
        raise ValueError(f"Unsupported amino-acid code(s): {', '.join(invalid)}")
    return sequence


def align_sequences(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    seq_a = clean_sequence(str(arguments.get("sequence_a") or ""))
    seq_b = clean_sequence(str(arguments.get("sequence_b") or ""))
    aligned_a, aligned_b, score = needleman_wunsch(seq_a, seq_b)
    markers = "".join("|" if a == b else " " for a, b in zip(aligned_a, aligned_b))
    matches = markers.count("|")
    aligned_positions = max(1, sum(1 for a, b in zip(aligned_a, aligned_b) if a != "-" and b != "-"))
    identity = matches / aligned_positions * 100
    data = {
        "labelA": str(arguments.get("label_a") or "Sequence A"),
        "labelB": str(arguments.get("label_b") or "Sequence B"),
        "sequenceA": aligned_a,
        "sequenceB": aligned_b,
        "markers": markers,
        "score": score,
        "identity": round(identity, 2),
        "matches": matches,
        "alignmentLength": len(aligned_a),
    }
    return {
        "summary": f"Global alignment identity {identity:.1f}% across {len(aligned_a)} columns (score {score}).",
        "data": data,
        "artifacts": [
            {
                "id": "latest-sequence-alignment",
                "type": "sequence-alignment",
                "title": f"{data['labelA']} vs {data['labelB']}",
                "data": data,
            }
        ],
    }


def needleman_wunsch(seq_a: str, seq_b: str) -> tuple[str, str, int]:
    match_score, mismatch_score, gap_score = 2, -1, -2
    rows, cols = len(seq_a) + 1, len(seq_b) + 1
    scores = [[0] * cols for _ in range(rows)]
    trace = [[""] * cols for _ in range(rows)]
    for i in range(1, rows):
        scores[i][0] = i * gap_score
        trace[i][0] = "up"
    for j in range(1, cols):
        scores[0][j] = j * gap_score
        trace[0][j] = "left"
    for i in range(1, rows):
        for j in range(1, cols):
            diagonal = scores[i - 1][j - 1] + (match_score if seq_a[i - 1] == seq_b[j - 1] else mismatch_score)
            up = scores[i - 1][j] + gap_score
            left = scores[i][j - 1] + gap_score
            best = max(diagonal, up, left)
            scores[i][j] = best
            trace[i][j] = "diag" if best == diagonal else "up" if best == up else "left"
    aligned_a, aligned_b = [], []
    i, j = len(seq_a), len(seq_b)
    while i > 0 or j > 0:
        direction = trace[i][j]
        if direction == "diag":
            aligned_a.append(seq_a[i - 1])
            aligned_b.append(seq_b[j - 1])
            i -= 1
            j -= 1
        elif direction == "up":
            aligned_a.append(seq_a[i - 1])
            aligned_b.append("-")
            i -= 1
        else:
            aligned_a.append("-")
            aligned_b.append(seq_b[j - 1])
            j -= 1
    return "".join(reversed(aligned_a)), "".join(reversed(aligned_b)), scores[-1][-1]
