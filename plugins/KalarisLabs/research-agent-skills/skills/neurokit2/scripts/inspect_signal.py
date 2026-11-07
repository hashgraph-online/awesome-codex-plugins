#!/usr/bin/env python3
"""Inspect bounded local biosignal CSV structure without exposing row values."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path
from typing import Any

from _common import (
    MAX_CELL_CHARS,
    MAX_CHANNELS,
    MAX_CSV_BYTES,
    MAX_ROWS,
    MISSING_TOKENS,
    CliError,
    checked_input_file,
    emit_json,
    finite_float,
    parse_name_list,
    require_deidentified,
    run_cli,
)


class OnlineStats:
    """Online stats."""
    def __init__(self) -> None:
        """Initialise the instance."""
        self.numeric = 0
        self.missing = 0
        self.nonfinite = 0
        self.nonnumeric = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.minimum = math.inf
        self.maximum = -math.inf
        self.previous: float | None = None
        self.transitions = 0
        self.flat_transitions = 0
        self.flat_run = 0
        self.max_flat_run = 0
        self.gap_run = 0
        self.max_gap_run = 0

    def add_cell(self, cell: str) -> float | None:
        """Add cell."""
        normalized = cell.strip()
        if normalized.lower() in MISSING_TOKENS:
            self.missing += 1
            self.gap_run += 1
            self.max_gap_run = max(self.max_gap_run, self.gap_run)
            self.previous = None
            self.flat_run = 0
            return None
        try:
            value = float(normalized)
        except ValueError:
            self.nonnumeric += 1
            self.gap_run += 1
            self.max_gap_run = max(self.max_gap_run, self.gap_run)
            self.previous = None
            self.flat_run = 0
            return None
        if not math.isfinite(value):
            self.nonfinite += 1
            self.gap_run += 1
            self.max_gap_run = max(self.max_gap_run, self.gap_run)
            self.previous = None
            self.flat_run = 0
            return None

        self.gap_run = 0
        self.numeric += 1
        delta = value - self.mean
        self.mean += delta / self.numeric
        self.m2 += delta * (value - self.mean)
        self.minimum = min(self.minimum, value)
        self.maximum = max(self.maximum, value)
        if self.previous is not None:
            self.transitions += 1
            if value == self.previous:
                self.flat_transitions += 1
                self.flat_run += 1
            else:
                self.flat_run = 0
            self.max_flat_run = max(self.max_flat_run, self.flat_run)
        self.previous = value
        return value

    def report(self, unit: str | None) -> dict[str, Any]:
        """Handle report."""
        variance = self.m2 / (self.numeric - 1) if self.numeric > 1 else None
        return {
            "flat_transition_fraction": (
                self.flat_transitions / self.transitions if self.transitions else None
            ),
            "maximum": self.maximum if self.numeric else None,
            "max_flat_run_samples": self.max_flat_run + 1 if self.max_flat_run else 0,
            "max_gap_run_samples": self.max_gap_run,
            "mean": self.mean if self.numeric else None,
            "minimum": self.minimum if self.numeric else None,
            "missing_count": self.missing,
            "nonfinite_count": self.nonfinite,
            "nonnumeric_count": self.nonnumeric,
            "numeric_count": self.numeric,
            "sample_sd": math.sqrt(variance) if variance is not None else None,
            "unit": unit or "unspecified",
        }


def _check_unit_text(unit: str) -> None:
    """Require a unit label to be short and printable."""
    if len(unit) > 32 or any(ord(character) < 32 for character in unit):
        raise CliError("units must be short printable strings")


def _parse_units(value: str | None, selected: list[str]) -> dict[str, str]:
    """Parse units."""
    if value is None:
        return {}
    result: dict[str, str] = {}
    for item in value.split(","):
        if "=" not in item:
            raise CliError("--units entries must use COLUMN=UNIT")
        column, unit = (part.strip() for part in item.split("=", 1))
        if not column or not unit:
            raise CliError("--units entries must have nonempty column and unit")
        if column in result:
            raise CliError(f"duplicate unit declaration for {column!r}")
        if column not in selected:
            raise CliError(f"unit declared for unselected column {column!r}")
        _check_unit_text(unit)
        result[column] = unit
    return result


class _TimeTracker:
    """Track timestamp spacing, duplicates and backward steps across rows."""

    def __init__(self) -> None:
        """Start with no previous timestamp and empty counters."""
        self.positive_deltas: list[float] = []
        self.previous: float | None = None
        self.duplicates = 0
        self.backward = 0

    def update(self, time_value: float | None) -> None:
        """Fold one parsed timestamp (or None when unusable) into the running totals."""
        if time_value is None:
            return
        if self.previous is not None:
            delta = time_value - self.previous
            if delta > 0:
                self.positive_deltas.append(delta)
            elif delta == 0:
                self.duplicates += 1
            else:
                self.backward += 1
        self.previous = time_value


def _read_header(reader: Any, max_channels: int, time_column: str | None) -> list[str]:
    """Read and validate the CSV header row."""
    try:
        header = [name.strip() for name in next(reader)]
    except StopIteration as exc:
        raise CliError("CSV is empty") from exc
    if not header or any(not name for name in header):
        raise CliError("CSV header names must be nonempty")
    if len(header) != len(set(header)):
        raise CliError("CSV header names must be unique")
    if len(header) > max_channels:
        raise CliError(
            f"CSV has {len(header)} columns; --max-channels is {max_channels}"
        )
    if time_column is not None and time_column not in header:
        raise CliError(f"time column {time_column!r} is absent")
    return header


def _check_selection(
    selected_names: list[str] | None,
    header: list[str],
    time_column: str | None,
    max_channels: int,
) -> list[str]:
    """Validate the selected signal columns against the header and return them."""
    selected = selected_names or []
    if not selected:
        raise CliError("no signal columns selected")
    if len(selected) > max_channels:
        raise CliError(
            f"selected {len(selected)} columns; --max-channels is {max_channels}"
        )
    missing = [name for name in selected if name not in header]
    if missing:
        raise CliError(f"CSV is missing selected columns: {', '.join(missing)}")
    if time_column in selected:
        raise CliError("--time-column must not also be a signal column")
    return selected


def _check_row_shape(row: list[str], row_count: int, width: int) -> None:
    """Require a data row to have the header width and bounded cell lengths."""
    if len(row) != width:
        raise CliError(
            f"CSV row {row_count + 1} has {len(row)} cells; expected {width}"
        )
    for cell in row:
        if len(cell) > MAX_CELL_CHARS:
            raise CliError(
                f"CSV row {row_count + 1} contains a cell longer than "
                f"{MAX_CELL_CHARS} characters"
            )


def _scan_rows(
    reader: Any,
    header: list[str],
    positions: dict[str, int],
    stats: dict[str, OnlineStats],
    time_position: int | None,
    time_stats: OnlineStats | None,
    tracker: _TimeTracker,
    max_rows: int,
) -> int:
    """Stream the data rows into the per-column statistics and return the row count."""
    row_count = 0
    try:
        for row_count, row in enumerate(reader, start=1):
            if row_count > max_rows:
                raise CliError(f"CSV exceeds --max-rows={max_rows}")
            _check_row_shape(row, row_count, len(header))
            for name, position in positions.items():
                stats[name].add_cell(row[position])
            if time_position is not None and time_stats is not None:
                tracker.update(time_stats.add_cell(row[time_position]))
    except csv.Error as exc:
        raise CliError(f"cannot parse CSV: {exc}") from exc
    return row_count


def _sampling_summary(
    positive_deltas: list[float],
) -> tuple[float | None, float | None, float | None]:
    """Return the median interval, observed sampling rate and maximum relative jitter."""
    observed_sampling_rate: float | None = None
    median_delta: float | None = None
    maximum_relative_jitter: float | None = None
    if positive_deltas:
        median_delta = statistics.median(positive_deltas)
        if median_delta > 0:
            observed_sampling_rate = 1.0 / median_delta
            maximum_relative_jitter = max(
                abs(delta - median_delta) / median_delta for delta in positive_deltas
            )
    return median_delta, observed_sampling_rate, maximum_relative_jitter


def _channel_warnings(channel_reports: dict[str, dict[str, Any]]) -> list[str]:
    """Warn about invalid or suspiciously flat samples in each channel."""
    warnings: list[str] = []
    for name, report in channel_reports.items():
        invalid = (
            report["missing_count"]
            + report["nonfinite_count"]
            + report["nonnumeric_count"]
        )
        if invalid:
            warnings.append(
                f"{name}: {invalid} missing, non-finite, or non-numeric samples"
            )
        flat_fraction = report["flat_transition_fraction"]
        if isinstance(flat_fraction, float) and flat_fraction > 0.20:
            warnings.append(
                f"{name}: more than 20% of adjacent finite samples are identical"
            )
    return warnings


def _time_warnings(
    tracker: _TimeTracker,
    declared_sampling_rate: float | None,
    observed_sampling_rate: float | None,
    maximum_relative_jitter: float | None,
) -> list[str]:
    """Warn about timestamp order, rate mismatch and interval jitter."""
    warnings: list[str] = []
    if tracker.duplicates:
        warnings.append("time column contains duplicate timestamps")
    if tracker.backward:
        warnings.append("time column contains backward timestamps")
    if (
        declared_sampling_rate
        and observed_sampling_rate
        and abs(observed_sampling_rate - declared_sampling_rate)
        / declared_sampling_rate
        > 0.01
    ):
        warnings.append(
            "observed timestamp rate differs from declared sampling rate by more than 1%"
        )
    if maximum_relative_jitter is not None and maximum_relative_jitter > 0.01:
        warnings.append("timestamp intervals vary by more than 1% from the median")
    return warnings


def inspect_csv(
    path: Path,
    *,
    selected_names: list[str] | None,
    time_column: str | None,
    declared_sampling_rate: float | None,
    units_value: str | None,
    max_rows: int,
    max_channels: int,
) -> dict[str, Any]:
    """Handle inspect csv."""
    if not 1 <= max_rows <= MAX_ROWS:
        raise CliError(f"--max-rows must be between 1 and {MAX_ROWS}")
    if not 1 <= max_channels <= MAX_CHANNELS:
        raise CliError(f"--max-channels must be between 1 and {MAX_CHANNELS}")

    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except (OSError, UnicodeError) as exc:
        raise CliError(f"cannot open CSV: {exc}") from exc
    with handle:
        reader = csv.reader(handle)
        header = _read_header(reader, max_channels, time_column)
        selected = _check_selection(selected_names, header, time_column, max_channels)
        units = _parse_units(units_value, selected)
        positions = {name: header.index(name) for name in selected}
        time_position = header.index(time_column) if time_column else None
        stats = {name: OnlineStats() for name in selected}
        time_stats = OnlineStats() if time_column else None
        tracker = _TimeTracker()
        row_count = _scan_rows(
            reader, header, positions, stats, time_position, time_stats, tracker, max_rows
        )

    if row_count == 0:
        raise CliError("CSV has a header but no data rows")

    median_delta, observed_sampling_rate, maximum_relative_jitter = _sampling_summary(
        tracker.positive_deltas
    )

    duration_s: float | None = None
    effective_rate = observed_sampling_rate or declared_sampling_rate
    if effective_rate and row_count > 1:
        duration_s = (row_count - 1) / effective_rate

    channel_reports = {name: stats[name].report(units.get(name)) for name in selected}
    warnings = _channel_warnings(channel_reports) + _time_warnings(
        tracker, declared_sampling_rate, observed_sampling_rate, maximum_relative_jitter
    )

    return {
        "channel_count_in_file": len(header),
        "channels": channel_reports,
        "declared_sampling_rate_hz": declared_sampling_rate,
        "duration_s_estimate": duration_s,
        "observed_sampling_rate_hz": observed_sampling_rate,
        "path_redacted": True,
        "research_use_only": True,
        "row_count": row_count,
        "selected_columns": selected,
        "time": {
            "backward_step_count": tracker.backward,
            "duplicate_count": tracker.duplicates,
            "maximum_relative_interval_jitter": maximum_relative_jitter,
            "median_interval_s": median_delta,
            "name": time_column,
            "stats": time_stats.report("s") if time_stats else None,
        },
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a bounded local CSV for numeric coverage, gaps, flat runs, "
            "timestamp order, and sampling-rate consistency. Row values and paths "
            "are never emitted."
        )
    )
    parser.add_argument("--input", required=True, help="local .csv input")
    parser.add_argument("--root", default=".", help="existing local I/O boundary")
    parser.add_argument(
        "--columns",
        required=True,
        help="explicit comma-separated signal columns",
    )
    parser.add_argument("--time-column", help="numeric time column in seconds")
    parser.add_argument(
        "--sampling-rate", type=float, help="declared sampling rate in Hz"
    )
    parser.add_argument(
        "--units", help="comma-separated COLUMN=UNIT declarations, e.g. ECG=mV,EDA=uS"
    )
    parser.add_argument("--max-rows", type=int, default=MAX_ROWS)
    parser.add_argument("--max-channels", type=int, default=32)
    parser.add_argument(
        "--deidentified",
        action="store_true",
        help="confirm direct and reviewed quasi-identifiers were removed",
    )
    parser.add_argument("--output", help="optional local .json report")
    parser.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    require_deidentified(args.deidentified)
    declared_rate = (
        finite_float(
            args.sampling_rate,
            name="--sampling-rate",
            minimum=0.01,
            maximum=1_000_000.0,
        )
        if args.sampling_rate is not None
        else None
    )
    path = checked_input_file(
        args.input,
        root=args.root,
        suffixes={".csv"},
        max_bytes=MAX_CSV_BYTES,
    )
    report = inspect_csv(
        path,
        selected_names=parse_name_list(args.columns, name="--columns"),
        time_column=args.time_column,
        declared_sampling_rate=declared_rate,
        units_value=args.units,
        max_rows=args.max_rows,
        max_channels=args.max_channels,
    )
    emit_json(report, output=args.output, root=args.root, force=args.force)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
