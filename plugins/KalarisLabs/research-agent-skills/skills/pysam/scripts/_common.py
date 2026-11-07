#!/usr/bin/env python3
"""Helpers shared by the pysam command-line scripts in this directory.

This module never imports pysam so it can be imported (and tested) without it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

REPORT_ERRORS: tuple[type[BaseException], ...] = (
    IndexError,
    KeyError,
    OSError,
    TypeError,
    ValueError,
)
REGION_COORDINATE_SYSTEM = "1-based inclusive samtools string"


def positive_int(value: str) -> int:
    """Parse an argparse integer that must be greater than zero."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value: str) -> int:
    """Parse an argparse integer that must be zero or greater."""
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def require_local_file(path: Path, label: str) -> Path:
    """Expand a user path and require that it names an existing regular file."""
    resolved = path.expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"{label} is not a regular file: {resolved}")
    return resolved


def optional_local_file(path: Optional[Path], label: str) -> Optional[Path]:
    """Return the validated local file for an optional argument, or None when it is unset."""
    if path is None:
        return None
    return require_local_file(path, label)


def region_coordinate_system(region: Optional[str]) -> Optional[str]:
    """Describe the coordinate system of a region string, or None when no region is used."""
    return REGION_COORDINATE_SYSTEM if region is not None else None


def selected_reads(alignments: Any, region: Optional[str]) -> Iterator[Any]:
    """Iterate the whole file in order, or only the records overlapping the region."""
    if region is None:
        return alignments.fetch(until_eof=True)
    return alignments.fetch(region=region)


def alignment_format(alignments: Any) -> str:
    """Name the container format (CRAM, BAM or SAM) of an open AlignmentFile."""
    if alignments.is_cram:
        return "CRAM"
    if alignments.is_bam:
        return "BAM"
    return "SAM"


def write_report(report: dict[str, Any], output: Optional[Path]) -> None:
    """Write the report as JSON to stdout, or to a new file that must not already exist."""
    text = json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    )
    if output is None:
        sys.stdout.write(text + "\n")
        return

    destination = output.expanduser()
    with destination.open("x", encoding="utf-8") as handle:
        handle.write(text + "\n")


def reject_output_overwriting_input(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    """Exit through the parser if --output resolves to the same file as the input."""
    if args.output is None:
        return
    try:
        if args.output.expanduser().resolve() == args.input.expanduser().resolve():
            parser.error("--output must not overwrite the input file")
    except OSError:
        pass


def run_report_cli(
    prog: str,
    args: argparse.Namespace,
    produce: Callable[[argparse.Namespace], dict[str, Any]],
    destination: Optional[Path],
    extra_errors: tuple[type[BaseException], ...] = (),
) -> int:
    """Build and write a report, printing a prefixed error and returning 2 on failure."""
    try:
        report = produce(args)
        write_report(report, destination)
    except REPORT_ERRORS + extra_errors as error:
        print(f"{prog}: {error}", file=sys.stderr)
        return 2
    return 0
