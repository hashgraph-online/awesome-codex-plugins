#!/usr/bin/env python3
"""Validate one local BED file and emit a non-mutating normalization plan."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from _common import (
    HARD_MAX_BYTES,
    HARD_MAX_RECORDS,
    MAX_COORDINATE,
    SafetyError,
    add_path_mode_argument,
    display_path,
    fail_json,
    int_type,
    iter_text_lines,
    load_chrom_sizes,
    local_path,
    print_json,
    sha256_file,
)


TOOL = "bed-validator"
_DECIMAL = re.compile(r"^-?\d+$")
_VALID_STRANDS = {"+", "-", "."}


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate a local BED file as 0-based half-open intervals and emit "
            "a bounded normalization plan. The input is never rewritten."
        )
    )
    parser.add_argument("--input", required=True, help="Local BED or BED.GZ file.")
    parser.add_argument(
        "--assembly",
        required=True,
        help="Declared assembly/accession recorded in the report.",
    )
    parser.add_argument(
        "--chrom-sizes",
        help="Optional local two-column chromosome-sizes file for contig/bounds checks.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int_type(minimum=1, maximum=HARD_MAX_BYTES, label="max-bytes"),
        default=512 * 1024**2,
        help="Maximum compressed and expanded input bytes (default: 512 MiB).",
    )
    parser.add_argument(
        "--max-records",
        type=int_type(minimum=1, maximum=HARD_MAX_RECORDS, label="max-records"),
        default=1_000_000,
        help="Maximum text records, including headers (default: 1,000,000).",
    )
    parser.add_argument(
        "--max-examples",
        type=int_type(minimum=0, maximum=100, label="max-examples"),
        default=10,
        help="Maximum redacted issue examples (default: 10).",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Do not treat a BED with zero data records as an error.",
    )
    add_path_mode_argument(parser)
    return parser


def _record_issue(
    counter: Counter[str],
    examples: list[dict[str, int | str]],
    code: str,
    line_number: int,
    maximum: int,
) -> None:
    """Handle record issue."""
    counter[code] += 1
    if len(examples) < maximum:
        examples.append({"code": code, "line": line_number})


@dataclass
class _Scan:
    """Mutable state accumulated while scanning BED lines."""

    errors: Counter = field(default_factory=Counter)
    warnings: Counter = field(default_factory=Counter)
    examples: list = field(default_factory=list)
    records: int = 0
    skipped: int = 0
    min_columns: int | None = None
    max_columns: int = 0
    contigs: set = field(default_factory=set)
    seen: set = field(default_factory=set)
    duplicate_count: int = 0
    overlap_count: int = 0
    max_end_by_contig: dict = field(default_factory=dict)
    previous_sort_key: tuple | None = None
    unsorted_count: int = 0
    strand_rows: int = 0


def _load_chrom_info(args: argparse.Namespace):
    """Load optional chromosome sizes; return (sizes, order index, sha256 digest)."""
    if not args.chrom_sizes:
        return None, None, None
    chrom_path = local_path(args.chrom_sizes, kind="file")
    sizes, order = load_chrom_sizes(
        chrom_path,
        max_bytes=min(args.max_bytes, 128 * 1024**2),
        max_records=min(args.max_records, 1_000_000),
    )
    chrom_order = {chrom: index for index, chrom in enumerate(order)}
    digest, _ = sha256_file(
        chrom_path,
        max_bytes=min(args.max_bytes, 128 * 1024**2),
    )
    return sizes, chrom_order, digest


def _interval_error(fields: list[str], chrom_sizes: dict[str, int] | None):
    """Return (error code or None, start, end) for the first interval problem found."""
    chrom = fields[0]
    if not chrom or any(character.isspace() or ord(character) < 32 for character in chrom):
        return "invalid_contig", 0, 0
    start_text, end_text = fields[1], fields[2]
    if not _DECIMAL.fullmatch(start_text) or not _DECIMAL.fullmatch(end_text):
        return "non_decimal_coordinate", 0, 0
    start, end = int(start_text), int(end_text)
    if start < 0 or end < 0:
        return "negative_coordinate", start, end
    if start > MAX_COORDINATE or end > MAX_COORDINATE:
        return "coordinate_integer_overflow", start, end
    if end == start:
        return "zero_length_interval", start, end
    if end < start:
        return "end_before_start", start, end
    if chrom_sizes is not None:
        if chrom not in chrom_sizes:
            return "unknown_contig", start, end
        if end > chrom_sizes[chrom]:
            return "end_beyond_contig", start, end
    return None, start, end


def _track_interval(scan: _Scan, chrom: str, start: int, end: int,
                    chrom_order: dict[str, int] | None) -> None:
    """Update duplicate, overlap and ordering statistics for a valid interval."""
    scan.contigs.add(chrom)
    key = (chrom, start, end)
    if key in scan.seen:
        scan.duplicate_count += 1
    else:
        scan.seen.add(key)

    prior_end = scan.max_end_by_contig.get(chrom)
    if prior_end is not None and start < prior_end:
        scan.overlap_count += 1
    scan.max_end_by_contig[chrom] = max(end, prior_end or end)

    if chrom_order is None:
        sort_key: tuple[int | str, int, int] = (chrom, start, end)
    else:
        sort_key = (chrom_order[chrom], start, end)
    if scan.previous_sort_key is not None and sort_key < scan.previous_sort_key:
        scan.unsorted_count += 1
    scan.previous_sort_key = sort_key


def _scan_line(scan: _Scan, line_number: int, line: str, args: argparse.Namespace,
               chrom_sizes: dict[str, int] | None,
               chrom_order: dict[str, int] | None) -> None:
    """Classify one text line and fold it into the scan state."""
    if not line:
        scan.skipped += 1
        scan.warnings["blank_line"] += 1
        return
    if line.startswith("#") or line.startswith("track") or line.startswith("browser"):
        scan.skipped += 1
        return

    fields = line.split("\t")
    if len(fields) < 3:
        _record_issue(scan.errors, scan.examples, "fewer_than_three_columns",
                      line_number, args.max_examples)
        return
    scan.records += 1
    scan.min_columns = (
        len(fields) if scan.min_columns is None else min(scan.min_columns, len(fields))
    )
    scan.max_columns = max(scan.max_columns, len(fields))

    code, start, end = _interval_error(fields, chrom_sizes)
    if code is not None:
        _record_issue(scan.errors, scan.examples, code, line_number, args.max_examples)
        return

    if len(fields) >= 6:
        scan.strand_rows += 1
        if fields[5] not in _VALID_STRANDS:
            _record_issue(scan.errors, scan.examples, "invalid_bed6_strand",
                          line_number, args.max_examples)

    _track_interval(scan, fields[0], start, end, chrom_order)


def _summary_warnings(scan: _Scan, args: argparse.Namespace,
                      chrom_sizes: dict[str, int] | None) -> None:
    """Add the end-of-scan errors and warnings derived from the totals."""
    if scan.records == 0 and not args.allow_empty:
        scan.errors["no_data_records"] += 1
    if chrom_sizes is None:
        scan.warnings["bounds_not_checked_without_chrom_sizes"] += 1
    if scan.unsorted_count:
        scan.warnings["out_of_order_records"] = scan.unsorted_count
    if scan.duplicate_count:
        scan.warnings["duplicate_intervals"] = scan.duplicate_count
    if scan.overlap_count:
        scan.warnings["overlapping_intervals"] = scan.overlap_count


def _normalization_actions(scan: _Scan, chrom_sizes: dict[str, int] | None,
                           chrom_order: dict[str, int] | None) -> list[dict[str, str | int]]:
    """Build the non-mutating normalization plan from the scan results."""
    actions: list[dict[str, str | int]] = []
    if scan.errors:
        actions.append(
            {
                "action": "reject_or_quarantine_invalid_rows",
                "count": sum(scan.errors.values()),
            }
        )
    if scan.unsorted_count:
        actions.append(
            {
                "action": "stable_sort",
                "detail": (
                    "use chromosome-sizes order, then numeric start/end"
                    if chrom_order is not None
                    else "supply chromosome sizes before choosing contig order"
                ),
            }
        )
    if scan.duplicate_count:
        actions.append(
            {
                "action": "decide_duplicate_policy",
                "count": scan.duplicate_count,
            }
        )
    if chrom_sizes is None:
        actions.append(
            {
                "action": "supply_chromosome_sizes",
                "detail": "required before overflow/contig normalization",
            }
        )
    actions.append(
        {
            "action": "preserve_coordinate_semantics",
            "detail": "BED 0-based half-open; no implicit liftover or chr renaming",
        }
    )
    return actions


def validate(args: argparse.Namespace) -> tuple[dict, int]:
    """Validate the BED file and return the JSON report with its exit code."""
    if not args.assembly.strip() or len(args.assembly) > 200:
        raise SafetyError("assembly must be a nonempty value of at most 200 characters")

    bed_path = local_path(args.input, kind="file")
    chrom_sizes, chrom_order, chrom_sizes_digest = _load_chrom_info(args)

    scan = _Scan()
    for line_number, line in iter_text_lines(
        bed_path,
        max_bytes=args.max_bytes,
        max_records=args.max_records,
    ):
        _scan_line(scan, line_number, line, args, chrom_sizes, chrom_order)

    _summary_warnings(scan, args, chrom_sizes)

    digest, size = sha256_file(bed_path, max_bytes=args.max_bytes)
    actions = _normalization_actions(scan, chrom_sizes, chrom_order)
    errors = scan.errors

    report = {
        "ok": not errors,
        "tool": TOOL,
        "contract": {
            "assembly": args.assembly,
            "coordinate_system": "0-based-half-open",
            "input_mutated": False,
            "network_used": False,
        },
        "input": {
            "path": display_path(bed_path, 1, args.path_mode),
            "sha256": digest,
            "size_bytes": size,
        },
        "chromosome_sizes_sha256": chrom_sizes_digest,
        "summary": {
            "records": scan.records,
            "skipped_header_or_blank_lines": scan.skipped,
            "contig_count": len(scan.contigs),
            "minimum_columns": scan.min_columns,
            "maximum_columns": scan.max_columns if scan.records else None,
            "bed6_or_wider_rows": scan.strand_rows,
            "duplicate_intervals": scan.duplicate_count,
            "overlap_observations": scan.overlap_count,
            "out_of_order_records": scan.unsorted_count,
        },
        "errors": dict(sorted(errors.items())),
        "warnings": dict(sorted(scan.warnings.items())),
        "issue_examples": scan.examples,
        "normalization_plan": actions,
    }
    return report, 0 if not errors else 2


def main() -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        report, exit_code = validate(args)
        print_json(report)
        return exit_code
    except (OSError, SafetyError, UnicodeError) as exc:
        return fail_json(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
