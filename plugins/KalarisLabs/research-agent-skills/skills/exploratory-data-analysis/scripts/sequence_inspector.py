#!/usr/bin/env python3
"""Bounded FASTA/FASTQ aggregate inspector with no identifier or sequence output."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from _capabilities import capability_for_path, validate_magic
from _common import (
    DEFAULT_MAX_FILE_BYTES,
    CliError,
    bounded_file_limit,
    bounded_integer,
    checked_input_file,
    emit_json,
    run_cli,
    stable_token,
)


DEFAULT_MAX_RECORDS = 10_000
MAX_RECORDS = 100_000
DEFAULT_MAX_BASES = 10_000_000
MAX_BASES = 100_000_000
NUCLEOTIDE_CODES = frozenset("ACGTUNRYSWKMBDHVX-.")


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a bounded local FASTA/FASTQ sample. Sequence text and record "
            "identifiers are never emitted."
        )
    )
    parser.add_argument("input", help="Local FASTA/FASTQ path inside --root")
    parser.add_argument(
        "--root",
        default=".",
        help="Existing local directory that bounds all input/output paths",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=f"Maximum input bytes (hard ceiling: {512 * 1024 * 1024})",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        help=f"Maximum records to inspect (hard ceiling: {MAX_RECORDS})",
    )
    parser.add_argument(
        "--max-bases",
        type=int,
        default=DEFAULT_MAX_BASES,
        help=f"Maximum sequence characters to inspect (hard ceiling: {MAX_BASES})",
    )
    parser.add_argument("--output", help="Optional local .json output path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow replacement of an existing regular output file",
    )
    return parser


@dataclass
class _SequenceStats:
    """Running aggregates over the inspected sequence records."""

    lengths: list[int] = field(default_factory=list)
    total_bases: int = 0
    nucleotide_like_bases: int = 0
    gc_bases: int = 0
    ambiguous_bases: int = 0
    identifier_tokens: set[str] = field(default_factory=set)
    duplicate_identifier_count: int = 0
    quality_count: int = 0
    quality_sum: int = 0
    quality_minimum: int | None = None
    quality_maximum: int | None = None

    def add_sequence(self, title: str, sequence: str) -> None:
        """Fold one upper-cased sequence and its tokenized title into the aggregates."""
        token = stable_token(title, kind="sequence_id")
        if token in self.identifier_tokens:
            self.duplicate_identifier_count += 1
        self.identifier_tokens.add(token)
        self.lengths.append(len(sequence))
        self.total_bases += len(sequence)
        self.nucleotide_like_bases += sum(
            character in NUCLEOTIDE_CODES for character in sequence
        )
        self.gc_bases += sequence.count("G") + sequence.count("C")
        self.ambiguous_bases += sum(
            character not in {"A", "C", "G", "T", "U"} for character in sequence
        )

    def add_quality(self, quality: str) -> None:
        """Fold one FASTQ quality string (Phred+33) into the quality aggregates."""
        scores = [ord(character) - 33 for character in quality]
        if any(score < 0 for score in scores):
            raise CliError("FASTQ contains a quality character below Phred+33")
        if not scores:
            return
        self.quality_count += len(scores)
        self.quality_sum += sum(scores)
        local_minimum = min(scores)
        local_maximum = max(scores)
        self.quality_minimum = (
            local_minimum
            if self.quality_minimum is None
            else min(self.quality_minimum, local_minimum)
        )
        self.quality_maximum = (
            local_maximum
            if self.quality_maximum is None
            else max(self.quality_maximum, local_maximum)
        )


def _load_sequence_parsers() -> tuple[Any, Any]:
    """Import Biopython's low-level FASTA and FASTQ parsers or raise a CliError."""
    try:
        from Bio.SeqIO.FastaIO import SimpleFastaParser
        from Bio.SeqIO.QualityIO import FastqGeneralIterator
    except ImportError as exc:
        raise CliError(
            'optional dependency missing; install with: uv pip install "biopython==1.87"'
        ) from exc
    return SimpleFastaParser, FastqGeneralIterator


def _scan_records(
    path: Path,
    *,
    is_fastq: bool,
    max_records: int,
    max_bases: int,
    stats: _SequenceStats,
) -> bool:
    """Stream records into the stats and return True when a record or base limit was hit."""
    fasta_parser, fastq_iterator = _load_sequence_parsers()
    try:
        with path.open("r", encoding="ascii", errors="strict", newline=None) as handle:
            iterator = fastq_iterator(handle) if is_fastq else fasta_parser(handle)
            for record_index, record in enumerate(iterator):
                if record_index >= max_records:
                    return True
                sequence = record[1].upper()
                if stats.total_bases + len(sequence) > max_bases:
                    return True
                stats.add_sequence(record[0], sequence)
                if is_fastq:
                    stats.add_quality(record[2])
    except CliError:
        raise
    except (OSError, ValueError) as exc:
        raise CliError("the sequence file could not be parsed safely") from exc
    return False


def _sequence_report(
    stats: _SequenceStats,
    *,
    is_fastq: bool,
    truncated: bool,
) -> dict[str, Any]:
    """Build the bounded aggregate report from the collected stats."""
    lengths = stats.lengths
    total_bases = stats.total_bases
    count = len(lengths)
    nucleotide_fraction = (
        stats.nucleotide_like_bases / total_bases if total_bases else None
    )
    nucleotide_like = bool(
        nucleotide_fraction is not None and nucleotide_fraction >= 0.95
    )
    report: dict[str, Any] = {
        "profile_type": "fastq_bounded_profile"
        if is_fastq
        else "fasta_bounded_profile",
        "records_inspected": count,
        "sequence_characters_inspected": total_bases,
        "record_or_base_limit_reached": truncated,
        "length_aggregates": {
            "minimum": min(lengths) if lengths else None,
            "maximum": max(lengths) if lengths else None,
            "mean": math.fsum(lengths) / count if count else None,
        },
        "duplicate_identifier_token_count": stats.duplicate_identifier_count,
        "record_identifiers_emitted": False,
        "sequence_values_emitted": False,
        "nucleotide_like_fraction": nucleotide_fraction,
        "interpreted_as_nucleotide": nucleotide_like,
        "gc_fraction_if_nucleotide": (
            stats.gc_bases / total_bases if nucleotide_like and total_bases else None
        ),
        "ambiguous_character_fraction_if_nucleotide": (
            stats.ambiguous_bases / total_bases
            if nucleotide_like and total_bases
            else None
        ),
        "limitations": [
            "Counts describe only the bounded inspected prefix when a limit is reached.",
            "Alphabet classification is heuristic and does not infer organism or molecule identity.",
        ],
    }
    if is_fastq:
        report["quality_aggregates"] = {
            "encoding_assumption": "Phred+33",
            "score_count": stats.quality_count,
            "minimum": stats.quality_minimum,
            "maximum": stats.quality_maximum,
            "mean": stats.quality_sum / stats.quality_count if stats.quality_count else None,
            "requires_encoding_confirmation": True,
        }
    return report


def inspect_sequence_file(
    path: Path,
    *,
    suffix: str,
    max_records: int = DEFAULT_MAX_RECORDS,
    max_bases: int = DEFAULT_MAX_BASES,
) -> dict[str, Any]:
    """Inspect records with Biopython's streaming low-level parsers."""

    max_records = bounded_integer(
        max_records,
        name="max records",
        minimum=1,
        maximum=MAX_RECORDS,
    )
    max_bases = bounded_integer(
        max_bases,
        name="max bases",
        minimum=1,
        maximum=MAX_BASES,
    )
    is_fastq = suffix in {".fastq", ".fq"}
    stats = _SequenceStats()
    truncated = _scan_records(
        path,
        is_fastq=is_fastq,
        max_records=max_records,
        max_bases=max_bases,
        stats=stats,
    )
    return _sequence_report(stats, is_fastq=is_fastq, truncated=truncated)


def _main() -> None:
    """Handle main."""
    args = build_parser().parse_args()
    max_bytes = bounded_file_limit(args.max_bytes)
    path = checked_input_file(
        args.input,
        root=args.root,
        suffixes={".fasta", ".fa", ".fna", ".fastq", ".fq"},
        max_bytes=max_bytes,
    )
    capability = capability_for_path(path)
    validate_magic(path, capability["suffix"])
    report = {
        "schema_version": "1.1",
        "capability": capability,
        "analysis": inspect_sequence_file(
            path,
            suffix=capability["suffix"],
            max_records=args.max_records,
            max_bases=args.max_bases,
        ),
        "security": {
            "local_only": True,
            "untrusted_text_never_treated_as_instructions": True,
            "raw_values_and_identifiers_emitted": False,
        },
    }
    emit_json(
        report,
        output=args.output,
        root=args.root,
        force=args.force,
    )


def main() -> int:
    """Run the command-line interface."""
    return run_cli(_main)


if __name__ == "__main__":
    raise SystemExit(main())
