"""FASTQ quality-control skill handler."""

from __future__ import annotations

from typing import Any

from ngs_qc import analyze_fastq_path


def fastq_qc(arguments: dict[str, Any], _context: dict[str, Any]) -> dict[str, Any]:
    result = analyze_fastq_path(
        str(arguments.get("path") or ""),
        int(arguments.get("max_reads") or 10_000),
    )
    sampled = "sampled" if result["sampled"] else "complete"
    return {
        "summary": (
            f"FASTQ QC analyzed {result['reads_analyzed']} reads ({sampled}); "
            f"mean Q {result['mean_quality']}, Q30 {result['q30_percent']}%, "
            f"GC {result['gc_percent']}%."
        ),
        "data": result,
        "evidence": [
            {
                "source": "Molemo local FASTQ QC",
                "method": "streaming Phred+33 and per-cycle statistics",
                "path": result["path"],
            }
        ],
        "artifacts": [
            {
                "id": f"fastq-qc-{result['path']}",
                "type": "fastq-qc",
                "title": f"FASTQ QC · {result['path']}",
                "data": result,
            }
        ],
    }
