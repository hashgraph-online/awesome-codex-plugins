#!/usr/bin/env python3
"""Shared dependency-free safety helpers for local Gtars skill CLIs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import stat
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


HARD_MAX_BYTES = 8 * 1024**3
HARD_MAX_RECORDS = 10_000_000
HARD_MAX_FILES = 100_000
HARD_MAX_WORKERS = 256
HARD_MAX_LINE_BYTES = 1024 * 1024
MAX_COORDINATE = 2**32 - 1

_SCHEMES = (
    "http:",
    "https:",
    "ftp:",
    "file:",
    "s3:",
    "gs:",
    "hf:",
    "ssh:",
)
_INTEGER = re.compile(r"^(?:0|[1-9]\d*)$")
_VALID_STRANDS = {"+", "-", "."}


class SafetyError(ValueError):
    """Raised when a local-input safety contract is violated."""


def bounded_int(
    value: str,
    *,
    minimum: int = 0,
    maximum: int,
    label: str,
) -> int:
    """Parse an integer while enforcing an explicit hard bound."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise argparse.ArgumentTypeError(
            f"{label} must be between {minimum} and {maximum}"
        )
    return parsed


def int_type(*, minimum: int = 0, maximum: int, label: str):
    """Return an argparse-compatible bounded integer parser."""

    def parse(value: str) -> int:
        """Parse."""
        return bounded_int(
            value,
            minimum=minimum,
            maximum=maximum,
            label=label,
        )

    return parse


def _reject_unsafe_text_path(raw: str) -> None:
    """Handle reject unsafe text path."""
    if not raw or "\x00" in raw:
        raise SafetyError("path must be nonempty and contain no NUL byte")
    lowered = raw.strip().lower()
    if lowered.startswith(_SCHEMES) or "://" in lowered:
        raise SafetyError("URLs and URI-like paths are not allowed")
    if raw.startswith("~"):
        raise SafetyError("home expansion is not allowed; pass an explicit path")
    if ".." in Path(raw).parts:
        raise SafetyError("parent traversal ('..') is not allowed")


def _reject_symlink_components(path: Path) -> None:
    """Handle reject symlink components."""
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise SafetyError("symlink path component is not allowed")


def _check_missing_path(candidate: Path, *, must_exist: bool) -> None:
    """Require that a nonexistent path is allowed and sits in an existing directory."""
    if must_exist:
        raise SafetyError("required local path does not exist")
    try:
        parent_mode = candidate.parent.lstat().st_mode
    except FileNotFoundError as exc:
        raise SafetyError("output parent does not exist") from exc
    if not stat.S_ISDIR(parent_mode):
        raise SafetyError("output parent is not a directory")


def _check_existing_path(mode: int, kind: str) -> None:
    """Reject symlinks and entries that do not match the requested kind."""
    if stat.S_ISLNK(mode):
        raise SafetyError("symlinks are not allowed")
    if kind == "file" and not stat.S_ISREG(mode):
        raise SafetyError("expected a regular file")
    if kind == "dir" and not stat.S_ISDIR(mode):
        raise SafetyError("expected a directory")
    if kind == "any" and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
        raise SafetyError("only regular files and directories are allowed")


def local_path(
    raw: str,
    *,
    must_exist: bool = True,
    kind: str = "any",
) -> Path:
    """Resolve a strict local path without following symlinks."""
    _reject_unsafe_text_path(raw)
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = Path(os.path.abspath(candidate))
    _reject_symlink_components(candidate)

    try:
        mode = candidate.lstat().st_mode
    except FileNotFoundError:
        _check_missing_path(candidate, must_exist=must_exist)
    else:
        _check_existing_path(mode, kind)
    return candidate


def _open_binary_nofollow(path: Path):
    """Open binary nofollow."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    mode = os.fstat(descriptor).st_mode
    if not stat.S_ISREG(mode):
        os.close(descriptor)
        raise SafetyError("expected a regular file")
    return os.fdopen(descriptor, "rb")


def iter_text_lines(
    path: Path,
    *,
    max_bytes: int,
    max_records: int,
    max_line_bytes: int = HARD_MAX_LINE_BYTES,
) -> Iterator[tuple[int, str]]:
    """Yield bounded UTF-8 lines from a local plain-text or gzip file."""
    if not 1 <= max_bytes <= HARD_MAX_BYTES:
        raise SafetyError("max_bytes is outside the hard safety bound")
    if not 1 <= max_records <= HARD_MAX_RECORDS:
        raise SafetyError("max_records is outside the hard safety bound")
    if not 1 <= max_line_bytes <= HARD_MAX_LINE_BYTES:
        raise SafetyError("max_line_bytes is outside the hard safety bound")
    if path.stat().st_size > max_bytes:
        raise SafetyError("compressed/input file exceeds byte limit")

    expanded = 0
    with _open_binary_nofollow(path) as raw_handle:
        stream = (
            gzip.GzipFile(fileobj=raw_handle, mode="rb")
            if path.name.lower().endswith(".gz")
            else raw_handle
        )
        try:
            for line_number, raw_line in enumerate(stream, start=1):
                if line_number > max_records:
                    raise SafetyError("record limit exceeded")
                if len(raw_line) > max_line_bytes:
                    raise SafetyError(f"line {line_number} exceeds line-size limit")
                expanded += len(raw_line)
                if expanded > max_bytes:
                    raise SafetyError("expanded text exceeds byte limit")
                if b"\x00" in raw_line:
                    raise SafetyError(f"NUL byte found at line {line_number}")
                try:
                    line = raw_line.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise SafetyError(
                        f"input is not UTF-8 near line {line_number}"
                    ) from exc
                yield line_number, line.rstrip("\r\n")
        finally:
            if stream is not raw_handle:
                stream.close()


def sha256_file(path: Path, *, max_bytes: int) -> tuple[str, int]:
    """Hash a bounded regular file without following symlinks."""
    if not 1 <= max_bytes <= HARD_MAX_BYTES:
        raise SafetyError("max_bytes is outside the hard safety bound")
    digest = hashlib.sha256()
    total = 0
    with _open_binary_nofollow(path) as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise SafetyError("file exceeds hash byte limit")
            digest.update(chunk)
    return digest.hexdigest(), total


def load_json(path: Path, *, max_bytes: int) -> Any:
    """Load strict bounded JSON, rejecting duplicate keys and non-finite values."""
    text = "\n".join(
        line
        for _, line in iter_text_lines(
            path,
            max_bytes=max_bytes,
            max_records=min(HARD_MAX_RECORDS, 1_000_000),
        )
    )

    def object_pairs(pairs):
        """Handle object pairs."""
        result = {}
        for key, value in pairs:
            if key in result:
                raise SafetyError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_constant(value: str):
        """Handle invalid constant."""
        raise SafetyError(f"non-finite JSON number is not allowed: {value}")

    try:
        return json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=invalid_constant,
        )
    except json.JSONDecodeError as exc:
        raise SafetyError("invalid JSON") from exc


def load_chrom_sizes(
    path: Path,
    *,
    max_bytes: int,
    max_records: int,
) -> tuple[dict[str, int], list[str]]:
    """Load a strict two-column chromosome-sizes file."""
    sizes: dict[str, int] = {}
    order: list[str] = []
    for line_number, line in iter_text_lines(
        path,
        max_bytes=max_bytes,
        max_records=max_records,
    ):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2:
            raise SafetyError(
                f"chromosome-sizes line {line_number} must have two tab fields"
            )
        chrom, size_text = fields
        if (
            not chrom
            or any(character.isspace() or ord(character) < 32 for character in chrom)
            or chrom in sizes
        ):
            raise SafetyError(f"invalid or duplicate contig at line {line_number}")
        if not _INTEGER.fullmatch(size_text):
            raise SafetyError(f"invalid contig size at line {line_number}")
        size = int(size_text)
        if not 1 <= size <= MAX_COORDINATE:
            raise SafetyError(f"contig size out of bounds at line {line_number}")
        sizes[chrom] = size
        order.append(chrom)
    if not sizes:
        raise SafetyError("chromosome-sizes file contains no records")
    return sizes, order


def _valid_contig_name(chrom: str) -> bool:
    """Return True for a nonempty contig name without whitespace or control characters."""
    return bool(chrom) and not any(
        character.isspace() or ord(character) < 32 for character in chrom
    )


class _BedScan:
    """Accumulator for BED-like record statistics and bounded issue examples."""

    def __init__(
        self,
        *,
        chrom_sizes: dict[str, int] | None,
        chrom_order: list[str] | None,
        max_examples: int,
    ) -> None:
        """Create empty counters for one BED scan."""
        self.chrom_sizes = chrom_sizes
        self.max_examples = max_examples
        self.errors: Counter[str] = Counter()
        self.warnings: Counter[str] = Counter()
        self.examples: list[dict[str, int | str]] = []
        self.seen: set[tuple[str, int, int]] = set()
        self.max_end: dict[str, int] = {}
        self.records = 0
        self.skipped = 0
        self.contigs: set[str] = set()
        self.min_columns: int | None = None
        self.max_columns = 0
        self.unsorted = 0
        self.duplicates = 0
        self.overlap_observations = 0
        self.bed6_rows = 0
        self.previous_key: tuple[int | str, int, int] | None = None
        self.order_map = (
            {chrom: index for index, chrom in enumerate(chrom_order)}
            if chrom_order is not None
            else None
        )

    def issue(self, kind: str, code: str, line_number: int) -> None:
        """Count an error or warning and keep a bounded number of examples."""
        target = self.errors if kind == "error" else self.warnings
        target[code] += 1
        if len(self.examples) < self.max_examples:
            self.examples.append({"severity": kind, "code": code, "line": line_number})

    def _parse_interval(
        self, fields: list[str], line_number: int
    ) -> tuple[str, int, int] | None:
        """Return (chrom, start, end) for a well-formed interval, else record an issue."""
        chrom = fields[0]
        if not _valid_contig_name(chrom):
            self.issue("error", "invalid_contig", line_number)
            return None
        if not _INTEGER.fullmatch(fields[1]) or not _INTEGER.fullmatch(fields[2]):
            self.issue("error", "non_unsigned_decimal_coordinate", line_number)
            return None
        start, end = int(fields[1]), int(fields[2])
        if start > MAX_COORDINATE or end > MAX_COORDINATE:
            self.issue("error", "coordinate_exceeds_gtars_u32", line_number)
            return None
        if end <= start:
            self.issue(
                "error",
                "zero_length_interval" if end == start else "end_before_start",
                line_number,
            )
            return None
        return chrom, start, end

    def _within_contig(self, chrom: str, end: int, line_number: int) -> bool:
        """Check the interval against the supplied chromosome sizes, if any."""
        if self.chrom_sizes is None:
            return True
        if chrom not in self.chrom_sizes:
            self.issue("error", "unknown_contig", line_number)
            return False
        if end > self.chrom_sizes[chrom]:
            self.issue("error", "end_beyond_contig", line_number)
            return False
        return True

    def _track_interval(self, chrom: str, start: int, end: int) -> None:
        """Update duplicate, overlap and sort-order counters for a valid interval."""
        self.contigs.add(chrom)
        key = (chrom, start, end)
        if key in self.seen:
            self.duplicates += 1
        else:
            self.seen.add(key)
        prior_end = self.max_end.get(chrom)
        if prior_end is not None and start < prior_end:
            self.overlap_observations += 1
        self.max_end[chrom] = max(end, prior_end or end)

        sort_key: tuple[int | str, int, int]
        if self.order_map is None:
            sort_key = (chrom, start, end)
        else:
            sort_key = (self.order_map[chrom], start, end)
        if self.previous_key is not None and sort_key < self.previous_key:
            self.unsorted += 1
        self.previous_key = sort_key

    def process_line(self, line_number: int, line: str) -> None:
        """Fold one input line into the scan statistics."""
        if not line:
            self.skipped += 1
            self.warnings["blank_line"] += 1
            return
        if line.startswith(("#", "track", "browser")):
            self.skipped += 1
            return
        fields = line.split("\t")
        if len(fields) < 3:
            self.issue("error", "fewer_than_three_columns", line_number)
            return
        self.records += 1
        self.min_columns = (
            len(fields) if self.min_columns is None else min(self.min_columns, len(fields))
        )
        self.max_columns = max(self.max_columns, len(fields))
        interval = self._parse_interval(fields, line_number)
        if interval is None:
            return
        chrom, start, end = interval
        if not self._within_contig(chrom, end, line_number):
            return
        if len(fields) >= 6:
            self.bed6_rows += 1
            if fields[5] not in _VALID_STRANDS:
                self.issue("error", "invalid_bed6_strand", line_number)
        self._track_interval(chrom, start, end)

    def finalize_warnings(self) -> None:
        """Add the aggregate duplicate, overlap, order and bounds warnings."""
        if self.duplicates:
            self.warnings["duplicate_intervals"] = self.duplicates
        if self.overlap_observations:
            self.warnings["overlapping_intervals"] = self.overlap_observations
        if self.unsorted:
            self.warnings["out_of_order_records"] = self.unsorted
        if self.chrom_sizes is None:
            self.warnings["bounds_not_checked_without_chrom_sizes"] += 1


def inspect_bed(
    path: Path,
    *,
    max_bytes: int,
    max_records: int,
    chrom_sizes: dict[str, int] | None = None,
    chrom_order: list[str] | None = None,
    max_examples: int = 10,
) -> dict[str, Any]:
    """Inspect BED-like records without returning genomic coordinates."""
    scan = _BedScan(
        chrom_sizes=chrom_sizes,
        chrom_order=chrom_order,
        max_examples=max_examples,
    )
    for line_number, line in iter_text_lines(
        path,
        max_bytes=max_bytes,
        max_records=max_records,
    ):
        scan.process_line(line_number, line)
    scan.finalize_warnings()

    digest, size = sha256_file(path, max_bytes=max_bytes)
    return {
        "sha256": digest,
        "size_bytes": size,
        "records": scan.records,
        "skipped_records": scan.skipped,
        "contig_count": len(scan.contigs),
        "minimum_columns": scan.min_columns,
        "maximum_columns": scan.max_columns if scan.records else None,
        "bed6_or_wider_rows": scan.bed6_rows,
        "duplicate_intervals": scan.duplicates,
        "overlap_observations": scan.overlap_observations,
        "out_of_order_records": scan.unsorted,
        "errors": dict(sorted(scan.errors.items())),
        "warnings": dict(sorted(scan.warnings.items())),
        "issue_examples": scan.examples,
    }


def add_path_mode_argument(parser: argparse.ArgumentParser) -> None:
    """Add path mode argument."""
    parser.add_argument(
        "--path-mode",
        choices=("redacted", "basename", "full"),
        default="redacted",
        help="Path disclosure in output (default: redacted).",
    )


def display_path(path: Path, index: int, mode: str) -> str:
    """Render a path using the requested disclosure level."""
    if mode == "redacted":
        return f"file_{index:04d}"
    if mode == "basename":
        return path.name
    if mode == "full":
        return str(path)
    raise SafetyError(f"unknown path mode: {mode}")


def print_json(payload: dict[str, Any]) -> None:
    """Print deterministic JSON with no non-finite values."""
    json.dump(payload, sys.stdout, indent=2, sort_keys=True, allow_nan=False)
    sys.stdout.write("\n")


def fail_json(tool: str, exc: Exception) -> int:
    """Emit a bounded machine-readable error."""
    print_json(
        {
            "ok": False,
            "tool": tool,
            "error": type(exc).__name__,
            "message": str(exc)[:500],
        }
    )
    return 2
