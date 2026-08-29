"""Generate the deterministic synthetic single-cell example tracked by Molemo."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "workspace" / "examples"
RNG = np.random.default_rng(17)
MARKERS = {
    "T_like": ["CD3D", "CD3E", "TRAC", "LCK", "IL7R", "LTB", "MALAT1", "B2M"],
    "B_like": ["MS4A1", "CD79A", "CD74", "HLA-DRA", "CD37", "CD22", "CD79B", "CD83"],
    "Mono_like": ["LST1", "S100A8", "S100A9", "FCN1", "CTSS", "TYMP", "LGALS3", "SAT1"],
}
HOUSEKEEPING = [
    "ACTB", "GAPDH", "RPL3", "RPL5", "RPL7", "RPL11", "RPL13", "RPL18", "RPL23", "RPL27",
    "RPS3", "RPS5", "RPS8", "RPS12", "RPS14", "RPS18", "RPS24", "EEF1A1", "TMSB10", "FTL",
    "FTH1", "UBC", "HSP90AA1", "HSPA8", "VIM", "PFN1", "CFL1", "LGALS1", "YWHAZ", "PPIA",
]
MITO = ["MT-CO1", "MT-ND1", "MT-CYB"]


def main() -> None:
    genes = [gene for marker_set in MARKERS.values() for gene in marker_set] + HOUSEKEEPING + MITO
    count_path = EXAMPLES / "single_cell_counts.csv"
    metadata_path = EXAMPLES / "single_cell_metadata.csv"
    with count_path.open("w", encoding="utf-8", newline="") as count_handle, metadata_path.open(
        "w", encoding="utf-8", newline=""
    ) as metadata_handle:
        count_writer = csv.writer(count_handle)
        metadata_writer = csv.writer(metadata_handle)
        count_writer.writerow(["cell_id", *genes])
        metadata_writer.writerow(["cell_id", "donor", "condition", "synthetic_truth"])
        for group_index, (group, marker_genes) in enumerate(MARKERS.items()):
            for cell_index in range(30):
                cell_id = f"demo_{group_index + 1}_{cell_index + 1:02d}"
                donor = f"D{cell_index % 3 + 1}"
                condition = "stimulated" if cell_index % 2 else "control"
                values = []
                for gene in genes:
                    rate = 0.25
                    if gene in HOUSEKEEPING:
                        rate = 2.5
                    if gene in MITO:
                        rate = 0.25
                    if gene in marker_genes:
                        rate = 14.0
                    elif gene in {item for name, items in MARKERS.items() if name != group for item in items}:
                        rate = 0.15
                    if donor == "D3" and gene in {"VIM", "FTL", "FTH1"}:
                        rate += 1.0
                    values.append(int(RNG.poisson(rate)))
                count_writer.writerow([cell_id, *values])
                metadata_writer.writerow([cell_id, donor, condition, group])


if __name__ == "__main__":
    main()
