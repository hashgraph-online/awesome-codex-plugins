#!/usr/bin/env python3
"""Bounded, redacted tabular profiling and EDA sensitivity calculations."""

from __future__ import annotations

import csv
import hashlib
import heapq
import math
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _common import (
    DEFAULT_MAX_ROWS,
    MAX_COLUMNS,
    MAX_FIELD_CHARS,
    MAX_ROWS,
    CliError,
    bounded_integer,
    display_identifier,
    finite_number,
    stable_token,
)


DEFAULT_MISSING_TOKENS = ("",)
PROFILE_SAMPLE_SIZE = 512
DISTRIBUTION_SAMPLE_SIZE = 4096
MAX_DISTRIBUTION_COLUMNS = 64
MAX_DISTINCT_GROUPS = 1000
MAX_TRACKED_LEAKAGE_KEYS = 200_000


@dataclass
class ScanSummary:
    """Scan summary."""
    rows_scanned: int
    truncated: bool
    column_count: int


def normalize_missing_tokens(tokens: Iterable[str] | None) -> frozenset[str]:
    """Build an explicit, case-insensitive missing-code set."""

    supplied = list(DEFAULT_MISSING_TOKENS if tokens is None else tokens)
    normalized = {item.strip().casefold() for item in supplied}
    normalized.add("")
    return frozenset(normalized)


def is_missing(value: str, missing_tokens: frozenset[str]) -> bool:
    """Return whether missing."""
    return value.strip().casefold() in missing_tokens


def delimiter_for_path(path: Path) -> str:
    """Handle delimiter for path."""
    name = path.name.casefold()
    if name.endswith(".csv"):
        return ","
    if name.endswith(".tsv"):
        return "\t"
    raise CliError("tabular tools accept only .csv and .tsv files")


def scan_table(
    path: Path,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    max_columns: int = MAX_COLUMNS,
    max_field_chars: int = MAX_FIELD_CHARS,
    on_header: Callable[[list[str]], None],
    on_row: Callable[[int, list[str]], None],
) -> ScanSummary:
    """Stream a rectangular UTF-8 table through bounded callbacks."""

    max_rows = bounded_integer(
        max_rows,
        name="max rows",
        minimum=1,
        maximum=MAX_ROWS,
    )
    max_columns = bounded_integer(
        max_columns,
        name="max columns",
        minimum=1,
        maximum=MAX_COLUMNS,
    )
    max_field_chars = bounded_integer(
        max_field_chars,
        name="max field characters",
        minimum=1,
        maximum=MAX_FIELD_CHARS,
    )
    delimiter = delimiter_for_path(path)
    previous_limit = csv.field_size_limit()
    rows_scanned = 0
    truncated = False
    column_count = 0
    try:
        csv.field_size_limit(max_field_chars)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(
                handle,
                delimiter=delimiter,
                strict=True,
            )
            try:
                header = next(reader)
            except StopIteration as exc:
                raise CliError("the table is empty") from exc
            if not header:
                raise CliError("the table header is empty")
            if len(header) > max_columns:
                raise CliError(
                    f"the table has more than the {max_columns}-column limit"
                )
            if any(not name.strip() for name in header):
                raise CliError("the table contains an empty column identifier")
            column_count = len(header)
            on_header(header)
            for row_index, row in enumerate(reader):
                if row_index >= max_rows:
                    truncated = True
                    break
                if len(row) != column_count:
                    raise CliError("the table contains a non-rectangular row")
                on_row(row_index, row)
                rows_scanned += 1
    except CliError:
        raise
    except (OSError, UnicodeError, csv.Error, OverflowError) as exc:
        raise CliError("the table could not be parsed safely as UTF-8") from exc
    finally:
        csv.field_size_limit(previous_limit)
    return ScanSummary(
        rows_scanned=rows_scanned,
        truncated=truncated,
        column_count=column_count,
    )


def resolve_column(header: Sequence[str], requested: str | None) -> int | None:
    """Resolve an exact identifier, rejecting absent or duplicate columns."""

    if requested is None:
        return None
    matches = [index for index, name in enumerate(header) if name == requested]
    if not matches:
        raise CliError("a requested role column was not found")
    if len(matches) > 1:
        raise CliError("a requested role column is duplicated")
    return matches[0]


class PrioritySample:
    """Keep a deterministic bounded sample selected by content and position hash."""

    def __init__(self, limit: int) -> None:
        """Initialise the instance."""
        self.limit = limit
        self._heap: list[tuple[int, float]] = []

    def add(self, value: float, *, row_index: int, column_index: int) -> None:
        """Add."""
        material = f"{row_index}\0{column_index}\0{value!r}".encode("ascii")
        priority = int.from_bytes(
            hashlib.blake2s(material, digest_size=8).digest(),
            "big",
        )
        item = (-priority, value)
        if len(self._heap) < self.limit:
            heapq.heappush(self._heap, item)
        elif priority < -self._heap[0][0]:
            heapq.heapreplace(self._heap, item)

    def values(self) -> list[float]:
        """Handle values."""
        return [value for _, value in self._heap]


def _quantile(sorted_values: Sequence[float], probability: float) -> float | None:
    """Handle quantile."""
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = probability * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(
        sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight
    )


@dataclass
class ColumnAccumulator:
    """Column accumulator."""
    column_index: int
    sample_limit: int = PROFILE_SAMPLE_SIZE
    total: int = 0
    missing: int = 0
    numeric: int = 0
    integer_like: int = 0
    boolean_like: int = 0
    text: int = 0
    mean: float = 0.0
    m2: float = 0.0
    minimum: float | None = None
    maximum: float | None = None
    text_length_total: int = 0
    maximum_text_length: int = 0
    unique_tokens: set[str] = field(default_factory=set)
    unique_truncated: bool = False
    frequent_tokens: Counter[str] = field(default_factory=Counter)
    sample: PrioritySample = field(init=False)

    def __post_init__(self) -> None:
        """Validate and normalise fields after initialisation."""
        self.sample = PrioritySample(self.sample_limit)

    def add(
        self,
        value: str,
        *,
        row_index: int,
        missing_tokens: frozenset[str],
    ) -> None:
        """Add."""
        self.total += 1
        if is_missing(value, missing_tokens):
            self.missing += 1
            return
        token = stable_token(value, kind="value")
        if len(self.unique_tokens) < 4096:
            self.unique_tokens.add(token)
        elif token not in self.unique_tokens:
            self.unique_truncated = True
        if len(self.frequent_tokens) < 4096 or token in self.frequent_tokens:
            self.frequent_tokens[token] += 1
        stripped = value.strip()
        lowered = stripped.casefold()
        if lowered in {"true", "false"}:
            self.boolean_like += 1
        number = finite_number(stripped)
        if number is None:
            self.text += 1
            length = len(value)
            self.text_length_total += length
            self.maximum_text_length = max(self.maximum_text_length, length)
            return
        self.numeric += 1
        if number.is_integer():
            self.integer_like += 1
        delta = number - self.mean
        self.mean += delta / self.numeric
        self.m2 += delta * (number - self.mean)
        self.minimum = number if self.minimum is None else min(self.minimum, number)
        self.maximum = number if self.maximum is None else max(self.maximum, number)
        self.sample.add(
            number,
            row_index=row_index,
            column_index=self.column_index,
        )

    def as_report(self, *, column_id: str) -> dict[str, Any]:
        """Handle as report."""
        observed = self.total - self.missing
        if observed == 0:
            inferred = "all_missing_in_scanned_rows"
        elif self.numeric == observed:
            inferred = "integer" if self.integer_like == observed else "numeric"
        elif self.boolean_like == observed:
            inferred = "boolean"
        elif self.text == observed:
            inferred = "text"
        else:
            inferred = "mixed"
        report: dict[str, Any] = {
            "column_id": column_id,
            "column_index": self.column_index,
            "inferred_kind": inferred,
            "missing_count": self.missing,
            "missing_fraction": self.missing / self.total if self.total else None,
            "non_missing_count": observed,
            "numeric_parse_count": self.numeric,
            "text_parse_count": self.text,
            "distinct_value_count_or_lower_bound": len(self.unique_tokens),
            "distinct_count_is_lower_bound": self.unique_truncated,
        }
        if self.numeric:
            sample = sorted(self.sample.values())
            report["numeric_aggregates"] = {
                "count": self.numeric,
                "mean": self.mean,
                "sample_standard_deviation": (
                    math.sqrt(self.m2 / (self.numeric - 1))
                    if self.numeric > 1
                    else None
                ),
                "minimum": self.minimum,
                "q1": _quantile(sample, 0.25),
                "median": _quantile(sample, 0.5),
                "q3": _quantile(sample, 0.75),
                "maximum": self.maximum,
                "quantiles_from_bounded_sample": len(sample) < self.numeric,
                "quantile_sample_count": len(sample),
            }
        if self.text:
            report["text_aggregates"] = {
                "count": self.text,
                "mean_character_count": self.text_length_total / self.text,
                "maximum_character_count": self.maximum_text_length,
            }
        if self.frequent_tokens:
            report["most_frequent_value_tokens"] = [
                {"value_token": token, "count": count}
                for token, count in sorted(
                    self.frequent_tokens.items(),
                    key=lambda item: (-item[1], item[0]),
                )[:5]
            ]
        return report


def profile_table(
    path: Path,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    missing_tokens: Iterable[str] | None = None,
    reveal_identifiers: bool = False,
) -> dict[str, Any]:
    """Build a bounded aggregate profile without emitting cell values."""

    missing = normalize_missing_tokens(missing_tokens)
    header: list[str] = []
    accumulators: list[ColumnAccumulator] = []
    duplicate_rows = 0
    row_hashes: set[bytes] = set()
    duplicate_tracking_truncated = False

    def on_header(names: list[str]) -> None:
        """Handle on header."""
        nonlocal header, accumulators
        header = names
        accumulators = [
            ColumnAccumulator(column_index=index) for index in range(len(names))
        ]

    def on_row(row_index: int, row: list[str]) -> None:
        """Handle on row."""
        nonlocal duplicate_rows, duplicate_tracking_truncated
        for accumulator, value in zip(accumulators, row, strict=True):
            accumulator.add(
                value,
                row_index=row_index,
                missing_tokens=missing,
            )
        fingerprint = hashlib.blake2s(
            "\0".join(row).encode("utf-8", errors="surrogatepass"),
            digest_size=16,
        ).digest()
        if len(row_hashes) < MAX_TRACKED_LEAKAGE_KEYS:
            if fingerprint in row_hashes:
                duplicate_rows += 1
            row_hashes.add(fingerprint)
        else:
            duplicate_tracking_truncated = True

    summary = scan_table(
        path,
        max_rows=max_rows,
        on_header=on_header,
        on_row=on_row,
    )
    columns = [
        accumulator.as_report(
            column_id=display_identifier(
                header[index],
                kind="column",
                reveal_identifiers=reveal_identifiers,
            )
        )
        for index, accumulator in enumerate(accumulators)
    ]
    return {
        "profile_type": "tabular_schema_and_aggregate_profile",
        "rows_scanned": summary.rows_scanned,
        "row_limit_reached": summary.truncated,
        "column_count": summary.column_count,
        "columns": columns,
        "duplicate_row_count_in_scanned_rows": duplicate_rows,
        "duplicate_tracking_truncated": duplicate_tracking_truncated,
        "missing_code_policy": {
            "empty_or_whitespace_is_missing": True,
            "additional_token_count": max(len(missing) - 1, 0),
            "tokens_are_not_emitted": True,
        },
        "raw_values_emitted": False,
        "identifier_redaction": "sanitized opt-in" if reveal_identifiers else "tokenized",
        "limitations": [
            "Dtypes are inferred from scanned text and are not a data dictionary.",
            "Quantiles use a deterministic bounded sample when numeric counts exceed the sample limit.",
            "Duplicate counts use exact hashes only until the documented tracking cap.",
        ],
    }


def profile_json_structure(
    document: Any,
    *,
    reveal_identifiers: bool = False,
    max_nodes: int = 100_000,
) -> dict[str, Any]:
    """Summarize a parsed JSON value without emitting scalar values."""

    stack: list[tuple[Any, int]] = [(document, 0)]
    type_counts: Counter[str] = Counter()
    top_level_fields: list[str] = []
    maximum_depth = 0
    array_lengths: list[int] = []
    object_sizes: list[int] = []
    nodes = 0
    truncated = False
    if isinstance(document, dict):
        top_level_fields = [
            display_identifier(
                str(key),
                kind="field",
                reveal_identifiers=reveal_identifiers,
            )
            for key in list(document)[:MAX_COLUMNS]
        ]
    while stack:
        value, depth = stack.pop()
        if nodes >= max_nodes:
            truncated = True
            break
        nodes += 1
        maximum_depth = max(maximum_depth, depth)
        if value is None:
            type_counts["null"] += 1
        elif isinstance(value, bool):
            type_counts["boolean"] += 1
        elif isinstance(value, (int, float)):
            type_counts["number"] += 1
        elif isinstance(value, str):
            type_counts["string"] += 1
        elif isinstance(value, list):
            type_counts["array"] += 1
            array_lengths.append(len(value))
            stack.extend((item, depth + 1) for item in reversed(value))
        elif isinstance(value, dict):
            type_counts["object"] += 1
            object_sizes.append(len(value))
            stack.extend((item, depth + 1) for item in reversed(list(value.values())))
        else:
            raise CliError("the JSON parser produced an unsupported value type")
    if isinstance(document, dict):
        root_type = "object"
    elif isinstance(document, list):
        root_type = "array"
    else:
        root_type = "scalar"
    return {
        "profile_type": "json_structural_profile",
        "root_type": root_type,
        "nodes_visited": nodes,
        "node_limit_reached": truncated,
        "maximum_depth_visited": maximum_depth,
        "type_counts": dict(sorted(type_counts.items())),
        "top_level_field_ids": top_level_fields,
        "top_level_fields_truncated": (
            isinstance(document, dict) and len(document) > len(top_level_fields)
        ),
        "array_count": len(array_lengths),
        "array_length_minimum": min(array_lengths) if array_lengths else None,
        "array_length_maximum": max(array_lengths) if array_lengths else None,
        "object_count": len(object_sizes),
        "object_field_count_maximum": max(object_sizes) if object_sizes else None,
        "raw_values_emitted": False,
        "identifier_redaction": "sanitized opt-in" if reveal_identifiers else "tokenized",
    }


def _moment_skew(values: Sequence[float]) -> float | None:
    """Handle moment skew."""
    if len(values) < 3:
        return None
    mean = statistics.fmean(values)
    variance = statistics.fmean((value - mean) ** 2 for value in values)
    if variance <= 0:
        return 0.0
    third = statistics.fmean((value - mean) ** 3 for value in values)
    return third / (variance ** 1.5)


def _distribution_report(
    values: Sequence[float],
    *,
    numeric_count: int,
    nonnumeric_count: int,
    missing_count: int,
) -> dict[str, Any]:
    """Handle distribution report."""
    ordered = sorted(values)
    if not ordered:
        return {
            "numeric_count": numeric_count,
            "nonnumeric_count": nonnumeric_count,
            "missing_count": missing_count,
            "status": "no_finite_numeric_values_sampled",
        }
    q1 = _quantile(ordered, 0.25)
    median = _quantile(ordered, 0.5)
    q3 = _quantile(ordered, 0.75)
    assert q1 is not None and median is not None and q3 is not None
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    inliers = [value for value in ordered if lower_fence <= value <= upper_fence]
    absolute_deviations = sorted(abs(value - median) for value in ordered)
    mad = _quantile(absolute_deviations, 0.5)
    trim = int(len(ordered) * 0.1)
    trimmed = ordered[trim : len(ordered) - trim] if trim and len(ordered) > 2 * trim else ordered
    winsorized = list(ordered)
    if trim and len(ordered) > 2 * trim:
        low = ordered[trim]
        high = ordered[-trim - 1]
        winsorized = [min(max(value, low), high) for value in ordered]
    raw_mean = statistics.fmean(ordered)
    transformed: dict[str, Any] = {
        "raw_skewness_moment": _moment_skew(ordered),
    }
    if ordered[0] >= 0:
        transformed["log1p_skewness_moment"] = _moment_skew(
            [math.log1p(value) for value in ordered]
        )
        transformed["candidate"] = "log1p"
    else:
        transformed["signed_log1p_skewness_moment"] = _moment_skew(
            [math.copysign(math.log1p(abs(value)), value) for value in ordered]
        )
        transformed["candidate"] = "signed_log1p"
    return {
        "numeric_count": numeric_count,
        "nonnumeric_count": nonnumeric_count,
        "missing_count": missing_count,
        "bounded_numeric_sample_count": len(ordered),
        "sample_is_bounded": len(ordered) < numeric_count,
        "location_and_scale": {
            "mean": raw_mean,
            "sample_standard_deviation": (
                statistics.stdev(ordered) if len(ordered) > 1 else None
            ),
            "median": median,
            "median_absolute_deviation": mad,
            "q1": q1,
            "q3": q3,
            "interquartile_range": iqr,
        },
        "outlier_sensitivity": {
            "iqr_fence_low": lower_fence,
            "iqr_fence_high": upper_fence,
            "outside_iqr_fence_count_in_sample": len(ordered) - len(inliers),
            "mean_without_iqr_fence_values": (
                statistics.fmean(inliers) if inliers else None
            ),
            "ten_percent_trimmed_mean": statistics.fmean(trimmed),
            "ten_percent_winsorized_mean": statistics.fmean(winsorized),
            "raw_minus_trimmed_mean": raw_mean - statistics.fmean(trimmed),
            "values_were_not_deleted_or_modified": True,
        },
        "transformation_sensitivity": {
            **transformed,
            "diagnostic_only": True,
            "fit_on_training_data_only_if_later_adopted": True,
        },
    }


def audit_distributions(
    path: Path,
    *,
    columns: Sequence[str] | None = None,
    max_rows: int = DEFAULT_MAX_ROWS,
    missing_tokens: Iterable[str] | None = None,
    reveal_identifiers: bool = False,
) -> dict[str, Any]:
    """Compare robust/classical summaries without deleting or transforming data."""

    missing = normalize_missing_tokens(missing_tokens)
    header: list[str] = []
    selected_indices: list[int] = []
    selected_ids: list[str] = []
    accumulators: dict[int, ColumnAccumulator] = {}
    skipped_columns = 0

    def on_header(names: list[str]) -> None:
        """Handle on header."""
        nonlocal header, selected_indices, selected_ids, accumulators, skipped_columns
        header = names
        if columns:
            selected_indices = []
            for requested in columns:
                index = resolve_column(names, requested)
                assert index is not None
                if index in selected_indices:
                    raise CliError("distribution columns must not be duplicated")
                selected_indices.append(index)
        else:
            selected_indices = list(range(min(len(names), MAX_DISTRIBUTION_COLUMNS)))
            skipped_columns = max(len(names) - len(selected_indices), 0)
        selected_ids = [
            display_identifier(
                names[index],
                kind="column",
                reveal_identifiers=reveal_identifiers,
            )
            for index in selected_indices
        ]
        accumulators = {
            index: ColumnAccumulator(
                column_index=index,
                sample_limit=DISTRIBUTION_SAMPLE_SIZE,
            )
            for index in selected_indices
        }

    def on_row(row_index: int, row: list[str]) -> None:
        """Handle on row."""
        for index in selected_indices:
            accumulators[index].add(
                row[index],
                row_index=row_index,
                missing_tokens=missing,
            )

    summary = scan_table(
        path,
        max_rows=max_rows,
        on_header=on_header,
        on_row=on_row,
    )
    reports: list[dict[str, Any]] = []
    for index, column_id in zip(selected_indices, selected_ids, strict=True):
        accumulator = accumulators[index]
        report = _distribution_report(
            accumulator.sample.values(),
            numeric_count=accumulator.numeric,
            nonnumeric_count=accumulator.text,
            missing_count=accumulator.missing,
        )
        if accumulator.numeric:
            reports.append({"column_id": column_id, **report})
    return {
        "audit_type": "distribution_and_outlier_sensitivity",
        "rows_scanned": summary.rows_scanned,
        "row_limit_reached": summary.truncated,
        "numeric_columns_reported": len(reports),
        "columns_skipped_by_default_limit": skipped_columns,
        "columns": reports,
        "interpretation": [
            "IQR fences are descriptive flags, not deletion rules.",
            "Transformation comparisons are exploratory diagnostics, not automatic recommendations.",
            "No hypothesis tests, p-values, imputations, or causal claims are produced.",
            "If later tests are run, define the hypothesis family and multiplicity procedure first.",
        ],
        "raw_values_emitted": False,
    }


def _parse_time(value: str) -> datetime | None:
    """Parse time."""
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


PartitionMap = dict[str, tuple[int, list[int]]]


def _track_split(
    mapping: dict[Any, set[str]],
    key: Any,
    split_token: str,
) -> bool:
    """Record a key's split membership; return True when the tracking cap dropped it."""
    if len(mapping) < MAX_TRACKED_LEAKAGE_KEYS:
        mapping.setdefault(key, set()).add(split_token)
        return False
    return key not in mapping


class _LeakageScan:
    """Streaming accumulator for missingness and split-leakage statistics."""

    def __init__(
        self,
        missing: frozenset[str],
        *,
        group_column: str | None,
        entity_column: str | None,
        split_column: str | None,
        time_column: str | None,
    ) -> None:
        """Remember the missing-code set and the requested role columns."""
        self.missing = missing
        self.columns = (group_column, entity_column, split_column, time_column)
        self.header: list[str] = []
        self.group_index: int | None = None
        self.entity_index: int | None = None
        self.split_index: int | None = None
        self.time_index: int | None = None
        self.overall_missing: list[int] = []
        self.by_group: PartitionMap = {}
        self.by_split: PartitionMap = {}
        self.entity_splits: dict[str, set[str]] = {}
        self.group_splits: dict[str, set[str]] = {}
        self.row_splits: dict[bytes, set[str]] = {}
        self.time_intervals: dict[str, tuple[datetime, datetime]] = {}
        self.time_parse_failures = 0
        self.missing_split_rows = 0
        self.tracking_truncated = False

    def on_header(self, names: list[str]) -> None:
        """Resolve the role columns against the header and size the counters."""
        self.header = names
        group_column, entity_column, split_column, time_column = self.columns
        self.group_index = resolve_column(names, group_column)
        self.entity_index = resolve_column(names, entity_column)
        self.split_index = resolve_column(names, split_column)
        self.time_index = resolve_column(names, time_column)
        self.overall_missing = [0] * len(names)

    def _is_missing_at(self, row: list[str], index: int) -> bool:
        """Return whether the cell at an index is a missing code."""
        return is_missing(row[index], self.missing)

    def _update_partition(self, mapping: PartitionMap, key: str, row: list[str]) -> None:
        """Count one row and its missing cells under a group or split key."""
        if key not in mapping:
            if len(mapping) >= MAX_DISTINCT_GROUPS:
                raise CliError("too many distinct group or split values")
            mapping[key] = (0, [0] * len(row))
        count, counts = mapping[key]
        for index, value in enumerate(row):
            if is_missing(value, self.missing):
                counts[index] += 1
        mapping[key] = (count + 1, counts)

    def _partition_tokens(self, row: list[str]) -> tuple[str | None, str | None]:
        """Update the group and split partitions and return their tokens."""
        group_token: str | None = None
        split_token: str | None = None
        if self.group_index is not None and not self._is_missing_at(row, self.group_index):
            group_token = stable_token(row[self.group_index], kind="group")
            self._update_partition(self.by_group, group_token, row)
        if self.split_index is not None:
            if self._is_missing_at(row, self.split_index):
                self.missing_split_rows += 1
            else:
                split_token = stable_token(row[self.split_index], kind="split")
                self._update_partition(self.by_split, split_token, row)
        return group_token, split_token

    def _track_overlap(
        self,
        row: list[str],
        group_token: str | None,
        split_token: str,
    ) -> None:
        """Track entity, group and identical-row membership across splits."""
        truncated = False
        if self.entity_index is not None and not self._is_missing_at(row, self.entity_index):
            entity_token = stable_token(row[self.entity_index], kind="entity")
            truncated |= _track_split(self.entity_splits, entity_token, split_token)
        if group_token is not None:
            truncated |= _track_split(self.group_splits, group_token, split_token)
        row_without_split = [
            value for index, value in enumerate(row) if index != self.split_index
        ]
        fingerprint = hashlib.blake2s(
            "\0".join(row_without_split).encode(
                "utf-8",
                errors="surrogatepass",
            ),
            digest_size=16,
        ).digest()
        truncated |= _track_split(self.row_splits, fingerprint, split_token)
        if truncated:
            self.tracking_truncated = True

    def _track_time(self, row: list[str], split_token: str) -> None:
        """Extend the observed time interval of a split with this row's timestamp."""
        if self.time_index is None:
            return
        parsed = _parse_time(row[self.time_index])
        if parsed is None:
            if not self._is_missing_at(row, self.time_index):
                self.time_parse_failures += 1
        elif split_token not in self.time_intervals:
            self.time_intervals[split_token] = (parsed, parsed)
        else:
            low, high = self.time_intervals[split_token]
            self.time_intervals[split_token] = (min(low, parsed), max(high, parsed))

    def on_row(self, _row_index: int, row: list[str]) -> None:
        """Fold one table row into the missingness and leakage counters."""
        for index, value in enumerate(row):
            if is_missing(value, self.missing):
                self.overall_missing[index] += 1
        group_token, split_token = self._partition_tokens(row)
        if split_token is None:
            return
        self._track_overlap(row, group_token, split_token)
        self._track_time(row, split_token)

    def temporal_overlap_pairs(self) -> int:
        """Count pairs of splits whose observed time intervals overlap."""
        pairs = 0
        interval_items = sorted(self.time_intervals.items())
        for left_index, (_, (left_low, left_high)) in enumerate(interval_items):
            for _, (right_low, right_high) in interval_items[left_index + 1 :]:
                if max(left_low, right_low) <= min(left_high, right_high):
                    pairs += 1
        return pairs

    def leakage_flags(self) -> dict[str, int]:
        """Return the counts of tokens and intervals that straddle multiple splits."""
        return {
            "entity_tokens_in_multiple_splits": sum(
                len(splits) > 1 for splits in self.entity_splits.values()
            ),
            "group_tokens_in_multiple_splits": sum(
                len(splits) > 1 for splits in self.group_splits.values()
            ),
            "identical_row_hashes_in_multiple_splits": sum(
                len(splits) > 1 for splits in self.row_splits.values()
            ),
            "overlapping_split_time_interval_pairs": self.temporal_overlap_pairs(),
        }


def _partition_report(
    mapping: PartitionMap,
    *,
    key_name: str,
    column_ids: list[str],
) -> list[dict[str, Any]]:
    """Build the per-key row counts and column missingness for one partitioning."""
    reports: list[dict[str, Any]] = []
    for key in sorted(mapping):
        count, counts = mapping[key]
        reports.append(
            {
                key_name: key,
                "row_count": count,
                "column_missingness": [
                    {
                        "column_id": column_ids[index],
                        "missing_count": value,
                        "missing_fraction": value / count if count else None,
                    }
                    for index, value in enumerate(counts)
                ],
            }
        )
    return reports


def _maximum_group_gaps(by_group: PartitionMap, column_ids: list[str]) -> list[dict[str, Any]]:
    """Report the largest between-group missingness-rate gap per column."""
    gaps: list[dict[str, Any]] = []
    if len(by_group) < 2:
        return gaps
    for index, column_id in enumerate(column_ids):
        rates = [
            counts[index] / count
            for count, counts in by_group.values()
            if count
        ]
        if rates:
            gaps.append(
                {
                    "column_id": column_id,
                    "maximum_group_missingness_gap": max(rates) - min(rates),
                }
            )
    return gaps


def _leakage_status(leakage_assessed: bool, any_flag: bool) -> str:
    """Name the leakage-audit outcome from whether it ran and whether it flagged anything."""
    if not leakage_assessed:
        return "not_assessed_without_split_column"
    if any_flag:
        return "potential_leakage_detected"
    return "not_detected_in_scanned_rows"


def audit_missingness_and_leakage(
    path: Path,
    *,
    max_rows: int = DEFAULT_MAX_ROWS,
    missing_tokens: Iterable[str] | None = None,
    group_column: str | None = None,
    entity_column: str | None = None,
    split_column: str | None = None,
    time_column: str | None = None,
    reveal_identifiers: bool = False,
) -> dict[str, Any]:
    """Audit missingness and common split leakage without exposing identifiers."""

    missing = normalize_missing_tokens(missing_tokens)
    scan = _LeakageScan(
        missing,
        group_column=group_column,
        entity_column=entity_column,
        split_column=split_column,
        time_column=time_column,
    )
    summary = scan_table(
        path,
        max_rows=max_rows,
        on_header=scan.on_header,
        on_row=scan.on_row,
    )
    column_ids = [
        display_identifier(
            name,
            kind="column",
            reveal_identifiers=reveal_identifiers,
        )
        for name in scan.header
    ]
    overall = [
        {
            "column_id": column_ids[index],
            "missing_count": count,
            "missing_fraction": count / summary.rows_scanned
            if summary.rows_scanned
            else None,
        }
        for index, count in enumerate(scan.overall_missing)
    ]
    leakage_flags = scan.leakage_flags()
    # resolve_column returns an index exactly when a split column was requested.
    leakage_assessed = split_column is not None
    return {
        "audit_type": "missingness_group_and_split_leakage",
        "rows_scanned": summary.rows_scanned,
        "row_limit_reached": summary.truncated,
        "overall_missingness": overall,
        "missingness_by_group": _partition_report(
            scan.by_group, key_name="group_token", column_ids=column_ids
        ),
        "missingness_by_split": _partition_report(
            scan.by_split, key_name="split_token", column_ids=column_ids
        ),
        "maximum_group_missingness_gaps": _maximum_group_gaps(scan.by_group, column_ids),
        "leakage_audit": {
            "status": _leakage_status(leakage_assessed, any(leakage_flags.values())),
            **leakage_flags,
            "rows_with_missing_split": scan.missing_split_rows,
            "unparseable_nonmissing_time_values": scan.time_parse_failures,
            "tracking_truncated": scan.tracking_truncated,
            "scope_warning": (
                "No finding is not proof of no leakage, especially for truncated scans "
                "or unprovided entity/group/time roles."
            ),
        },
        "missing_code_policy": {
            "empty_or_whitespace_is_missing": True,
            "additional_token_count": max(len(missing) - 1, 0),
            "tokens_are_not_emitted": True,
        },
        "raw_values_emitted": False,
        "automatic_imputation_or_deletion": False,
    }
