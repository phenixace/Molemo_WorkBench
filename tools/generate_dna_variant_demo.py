"""Generate a deterministic paired-end DNA variant-calling demo dataset."""

from __future__ import annotations

import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "workspace" / "examples"
REFERENCE_LENGTH = 2_400
READ_LENGTH = 100
FRAGMENT_LENGTH = 260
VARIANT_POSITION = 1_201
READ_PAIRS = 80
SEED = 41


def reverse_complement(sequence: str) -> str:
    return sequence.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def write_fastq(path: Path, records: list[tuple[str, str]]) -> None:
    quality = "I" * READ_LENGTH
    path.write_text(
        "".join(f"@{name}\n{sequence}\n+\n{quality}\n" for name, sequence in records),
        encoding="ascii",
    )


def main() -> None:
    rng = random.Random(SEED)
    reference = "".join(rng.choice("ACGT") for _ in range(REFERENCE_LENGTH))
    ref_base = reference[VARIANT_POSITION - 1]
    alt_base = next(base for base in "ACGT" if base != ref_base)
    alt_haplotype = (
        reference[: VARIANT_POSITION - 1] + alt_base + reference[VARIANT_POSITION:]
    )

    read1: list[tuple[str, str]] = []
    read2: list[tuple[str, str]] = []
    for index in range(READ_PAIRS):
        start = 1_080 + (index * 13) % 90
        haplotype = alt_haplotype if index % 2 == 0 else reference
        fragment = haplotype[start : start + FRAGMENT_LENGTH]
        name = f"molemo_demo_{index + 1:03d}"
        read1.append((f"{name}/1", fragment[:READ_LENGTH]))
        read2.append((f"{name}/2", reverse_complement(fragment[-READ_LENGTH:])))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    wrapped = "\n".join(
        reference[index : index + 80] for index in range(0, len(reference), 80)
    )
    (OUTPUT / "dna_variant_reference.fa").write_text(
        f">molemo_demo_reference\n{wrapped}\n", encoding="ascii"
    )
    write_fastq(OUTPUT / "dna_variant_R1.fastq", read1)
    write_fastq(OUTPUT / "dna_variant_R2.fastq", read2)
    (OUTPUT / "dna_variant_truth.tsv").write_text(
        "chrom\tpos\tref\talt\tgenotype\n"
        f"molemo_demo_reference\t{VARIANT_POSITION}\t{ref_base}\t{alt_base}\t0/1\n",
        encoding="ascii",
    )
    print(
        f"Generated {READ_PAIRS} read pairs with {ref_base}>{alt_base} at "
        f"molemo_demo_reference:{VARIANT_POSITION}."
    )


if __name__ == "__main__":
    main()
