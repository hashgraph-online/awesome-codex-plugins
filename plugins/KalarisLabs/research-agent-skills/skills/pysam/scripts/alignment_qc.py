#!/usr/bin/env python3
"""Stream a local SAM/BAM/CRAM file and write aggregate QC counts as JSON.

Counts are alignment-record counts, not unique templates. A whole-file scan
uses fetch(until_eof=True) and needs no index. --region is a 1-based inclusive
samtools region string and requires an index. CRAM requires --reference.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pysam
from _common import (
    alignment_format,
    nonnegative_int,
    optional_local_file,
    positive_int,
    region_coordinate_system,
    reject_output_overwriting_input,
    require_local_file,
    run_report_cli,
    selected_reads,
    write_report,
)

# Boolean pysam read properties counted one-for-one into the named count.
_FLAG_COUNTS = (
    ("secondary_records", "is_secondary"),
    ("supplementary_records", "is_supplementary"),
    ("duplicate_records", "is_duplicate"),
    ("qc_fail_records", "is_qcfail"),
    ("paired_records", "is_paired"),
    ("proper_pair_records", "is_proper_pair"),
    ("read1_records", "is_read1"),
    ("read2_records", "is_read2"),
    ("reverse_records", "is_reverse"),
    ("mate_unmapped_records", "mate_is_unmapped"),
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="local SAM/BAM/CRAM file")
    parser.add_argument(
        "--reference",
        type=Path,
        help="local indexed reference FASTA; required for CRAM",
    )
    parser.add_argument(
        "--index",
        type=Path,
        help="explicit local BAI/CSI/CRAI index",
    )
    parser.add_argument(
        "--region",
        help="1-based inclusive samtools region, for example chr1:1-1000000",
    )
    parser.add_argument(
        "--threads",
        type=positive_int,
        default=1,
        help="HTSlib decompression threads",
    )
    parser.add_argument(
        "--max-records",
        type=nonnegative_int,
        default=0,
        help="stop after this many records; 0 scans the complete selection",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write JSON to a new file instead of stdout; refuses overwrite",
    )
    return parser


def alignment_mode(path: Path) -> str:
    """Map the input suffix to the pysam AlignmentFile read mode."""
    name = path.name.lower()
    if name.endswith(".sam"):
        return "r"
    if name.endswith(".cram"):
        return "rc"
    if name.endswith(".bam"):
        return "rb"
    raise ValueError("input suffix must be .sam, .bam, or .cram")


def ratio(numerator: int, denominator: int) -> Optional[float]:
    """Divide, returning None when the denominator is zero."""
    return numerator / denominator if denominator else None


def average(total: int, count: int) -> Optional[float]:
    """Average a running total, returning None when nothing was counted."""
    return total / count if count else None


def empty_counts() -> dict[str, int]:
    """Return the zeroed per-record count table in report order."""
    return {
        "total_records": 0,
        "primary_records": 0,
        "mapped_records": 0,
        "unmapped_records": 0,
        "secondary_records": 0,
        "supplementary_records": 0,
        "duplicate_records": 0,
        "qc_fail_records": 0,
        "paired_records": 0,
        "proper_pair_records": 0,
        "read1_records": 0,
        "read2_records": 0,
        "reverse_records": 0,
        "mate_unmapped_records": 0,
        "cigar_missing_records": 0,
        "sequence_missing_records": 0,
        "mapq_255_records": 0,
    }


@dataclass
class QcTally:
    """Running totals accumulated while streaming alignment records."""

    counts: dict[str, int] = field(default_factory=empty_counts)
    query_length_sum: int = 0
    query_length_count: int = 0
    aligned_query_bases: int = 0
    mapq_sum: int = 0
    mapq_count: int = 0
    record_limit_reached: bool = False


def _tally_mapping(read: Any, tally: QcTally) -> None:
    """Count mapped/unmapped status and accumulate MAPQ (255 is reported as unavailable)."""
    counts = tally.counts
    if read.is_unmapped:
        counts["unmapped_records"] += 1
        return
    counts["mapped_records"] += 1
    if read.mapping_quality == 255:
        counts["mapq_255_records"] += 1
    else:
        tally.mapq_sum += int(read.mapping_quality)
        tally.mapq_count += 1


def _tally_read(read: Any, tally: QcTally) -> None:
    """Add one alignment record to the running totals."""
    counts = tally.counts
    counts["total_records"] += 1
    if not read.is_secondary and not read.is_supplementary:
        counts["primary_records"] += 1
    _tally_mapping(read, tally)
    for name, attribute in _FLAG_COUNTS:
        if getattr(read, attribute):
            counts[name] += 1
    if read.cigartuples is None:
        counts["cigar_missing_records"] += 1
    if read.query_sequence is None:
        counts["sequence_missing_records"] += 1
    if read.query_length is not None:
        tally.query_length_sum += int(read.query_length)
        tally.query_length_count += 1
    if read.query_alignment_length is not None:
        tally.aligned_query_bases += int(read.query_alignment_length)


def _scan_reads(
    alignments: pysam.AlignmentFile, region: Optional[str], max_records: int
) -> QcTally:
    """Stream the selected records into a tally, stopping at --max-records when set."""
    tally = QcTally()
    for read in selected_reads(alignments, region):
        if max_records and tally.counts["total_records"] >= max_records:
            tally.record_limit_reached = True
            break
        _tally_read(read, tally)
    return tally


def _open_kwargs(
    args: argparse.Namespace, reference: Optional[Path], index: Optional[Path]
) -> dict[str, Any]:
    """Build the keyword arguments for pysam.AlignmentFile."""
    kwargs: dict[str, Any] = {
        "threads": args.threads,
        "require_index": args.region is not None,
    }
    if reference is not None:
        kwargs["reference_filename"] = str(reference)
    if index is not None:
        kwargs["index_filename"] = str(index)
    return kwargs


def _has_index(alignments: pysam.AlignmentFile) -> bool:
    """Report whether an index is loaded, treating lookup failures as no index."""
    try:
        return bool(alignments.has_index())
    except (AttributeError, OSError, ValueError):
        return False


def _derived_metrics(tally: QcTally) -> dict[str, Any]:
    """Compute the rate and mean metrics reported beside the raw counts."""
    counts = tally.counts
    return {
        "mapping_rate_all_records": ratio(
            counts["mapped_records"],
            counts["total_records"],
        ),
        "duplicate_rate_all_records": ratio(
            counts["duplicate_records"],
            counts["total_records"],
        ),
        "proper_pair_rate_paired_records": ratio(
            counts["proper_pair_records"],
            counts["paired_records"],
        ),
        "mean_query_length": average(
            tally.query_length_sum,
            tally.query_length_count,
        ),
        "mean_mapping_quality": average(tally.mapq_sum, tally.mapq_count),
        "aligned_query_bases": tally.aligned_query_bases,
    }


def _build_report(
    alignments: pysam.AlignmentFile,
    path: Path,
    args: argparse.Namespace,
    tally: QcTally,
) -> dict[str, Any]:
    """Assemble the JSON report from the open file, the arguments and the tally."""
    header = alignments.header.to_dict()
    return {
        "schema_version": "1.0",
        "pysam_version": pysam.__version__,
        "samtools_version": getattr(pysam, "__samtools_version__", None),
        "file_name": path.name,
        "format": alignment_format(alignments),
        "sort_order": header.get("HD", {}).get("SO"),
        "has_index": _has_index(alignments),
        "selection": {
            "region": args.region,
            "region_coordinate_system": region_coordinate_system(args.region),
            "whole_file_order": args.region is None,
            "max_records": args.max_records,
            "record_limit_reached": tally.record_limit_reached,
        },
        "semantics": (
            "Counts are alignment records, not unique query names, "
            "templates, or fragments. MAPQ 255 is reported as unavailable "
            "and excluded from mean_mapping_quality."
        ),
        "counts": tally.counts,
        "derived": _derived_metrics(tally),
    }


def inspect_alignments(args: argparse.Namespace) -> dict[str, Any]:
    """Stream the selected alignments and return the QC report."""
    path = require_local_file(args.input, "input")
    reference = optional_local_file(args.reference, "reference")
    index = optional_local_file(args.index, "index")
    mode = alignment_mode(path)

    if mode == "rc" and reference is None:
        raise ValueError("CRAM QC requires --reference")

    kwargs = _open_kwargs(args, reference, index)
    with pysam.AlignmentFile(str(path), mode, **kwargs) as alignments:
        tally = _scan_reads(alignments, args.region, args.max_records)
        return _build_report(alignments, path, args, tally)


def main(argv: Optional[list[str]] = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    reject_output_overwriting_input(parser, args)
    return run_report_cli("alignment_qc", args, inspect_alignments, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
