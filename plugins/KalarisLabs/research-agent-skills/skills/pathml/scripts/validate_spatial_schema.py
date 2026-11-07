#!/usr/bin/env python3
"""Validate bounded graph JSON and multiplex cell-table CSV schemas."""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from _common import (
    CliError,
    MAX_CSV_BYTES,
    MAX_JSON_BYTES,
    checked_input_file,
    checked_root,
    emit_json,
    finite_float,
    load_json_object,
    parse_name_list,
    run_cli,
    validate_keys,
)


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
COORDINATE_UNITS = {"level_pixels", "level0_pixels", "um"}


def _identifier(value: Any, *, context: str) -> str:
    """Handle identifier."""
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise CliError(
            f"{context} must use 1-128 letters, digits, dots, underscores, "
            "colons, or hyphens"
        )
    return value


_GRAPH_ALLOWED_KEYS = {
    "schema_version",
    "slide_id",
    "coordinate_unit",
    "level",
    "nodes",
    "edges",
    "metadata",
}
_GRAPH_REQUIRED_KEYS = {"schema_version", "slide_id", "coordinate_unit", "nodes", "edges"}


def _validate_graph_header(document: dict[str, Any]) -> str:
    """Validate the graph document's top-level fields and return its coordinate unit."""
    validate_keys(
        document,
        allowed=_GRAPH_ALLOWED_KEYS,
        required=_GRAPH_REQUIRED_KEYS,
        context="graph",
    )
    if document["schema_version"] != "1.0":
        raise CliError("graph schema_version must be '1.0'")
    _identifier(document["slide_id"], context="slide_id")
    coordinate_unit = document["coordinate_unit"]
    if coordinate_unit not in COORDINATE_UNITS:
        raise CliError(
            "coordinate_unit must be one of: "
            + ", ".join(sorted(COORDINATE_UNITS))
        )
    if "level" in document:
        level = document["level"]
        if isinstance(level, bool) or not isinstance(level, int) or level < 0:
            raise CliError("level must be a nonnegative integer")
    return coordinate_unit


def _validate_graph_features(
    index: int,
    features: Any,
    feature_length: int | None,
    max_features: int,
) -> int:
    """Validate one node's feature array and return the (possibly newly set) shared length."""
    if not isinstance(features, list):
        raise CliError(f"node {index} features must be an array")
    if len(features) > max_features:
        raise CliError(f"node {index} has more than {max_features} features")
    if feature_length is None:
        feature_length = len(features)
    elif len(features) != feature_length:
        raise CliError("all feature arrays must have the same length")
    for feature_index, value in enumerate(features):
        finite_float(
            value,
            name=f"node {index} feature {feature_index}",
            minimum=-1e15,
            maximum=1e15,
        )
    return feature_length


def _validate_graph_node(
    index: int,
    node: Any,
    node_ids: set[str],
    feature_length: int | None,
    max_features: int,
) -> int | None:
    """Validate one graph node, register its id, and return the shared feature length."""
    if not isinstance(node, dict):
        raise CliError(f"node {index} must be an object")
    validate_keys(
        node,
        allowed={"id", "x", "y", "features", "label"},
        required={"id", "x", "y"},
        context=f"node {index}",
    )
    node_id = _identifier(node["id"], context=f"node {index} id")
    if node_id in node_ids:
        raise CliError(f"duplicate node id: {node_id!r}")
    node_ids.add(node_id)
    finite_float(node["x"], name=f"node {index} x", minimum=0, maximum=1e12)
    finite_float(node["y"], name=f"node {index} y", minimum=0, maximum=1e12)
    if "features" in node:
        return _validate_graph_features(index, node["features"], feature_length, max_features)
    return feature_length


def _validate_graph_edge(
    index: int,
    edge: Any,
    node_ids: set[str],
    seen_edges: set[tuple[str, str]],
    args: argparse.Namespace,
) -> bool:
    """Validate one graph edge, register it, and return whether it is a self-loop."""
    if not isinstance(edge, dict):
        raise CliError(f"edge {index} must be an object")
    validate_keys(
        edge,
        allowed={"source", "target", "weight", "edge_type"},
        required={"source", "target"},
        context=f"edge {index}",
    )
    source = _identifier(edge["source"], context=f"edge {index} source")
    target = _identifier(edge["target"], context=f"edge {index} target")
    if source not in node_ids or target not in node_ids:
        raise CliError(f"edge {index} references an unknown node")
    is_self_loop = source == target
    if is_self_loop and not args.allow_self_loops:
        raise CliError(f"edge {index} is a self-loop")
    key = tuple(sorted((source, target))) if args.undirected else (source, target)
    if key in seen_edges:
        raise CliError(f"edge {index} duplicates an existing edge")
    seen_edges.add(key)
    if "weight" in edge:
        finite_float(
            edge["weight"],
            name=f"edge {index} weight",
            minimum=-1e15,
            maximum=1e15,
        )
    return is_self_loop


def validate_graph(args: argparse.Namespace) -> dict[str, Any]:
    """Validate a bounded graph JSON document and return its validation report."""
    root = checked_root(args.root)
    document = load_json_object(
        args.input,
        root=root,
        max_bytes=args.max_input_bytes,
    )
    coordinate_unit = _validate_graph_header(document)
    nodes = document["nodes"]
    edges = document["edges"]
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise CliError("nodes and edges must be arrays")
    if not 1 <= len(nodes) <= args.max_nodes:
        raise CliError(f"node count must be in [1, {args.max_nodes}]")
    if len(edges) > args.max_edges:
        raise CliError(f"edge count exceeds --max-edges={args.max_edges}")

    node_ids: set[str] = set()
    feature_length: int | None = None
    for index, node in enumerate(nodes):
        feature_length = _validate_graph_node(
            index, node, node_ids, feature_length, args.max_features
        )

    seen_edges: set[tuple[str, str]] = set()
    self_loops = 0
    for index, edge in enumerate(edges):
        if _validate_graph_edge(index, edge, node_ids, seen_edges, args):
            self_loops += 1

    return {
        "command": "graph",
        "valid": True,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "feature_count": feature_length or 0,
        "coordinate_unit": coordinate_unit,
        "directed_edge_keys": not args.undirected,
        "self_loop_count": self_loops,
        "checks": {
            "strict_json": True,
            "bounded": True,
            "unique_node_ids": True,
            "finite_coordinates": True,
            "uniform_feature_shape": True,
            "valid_edge_endpoints": True,
            "unique_edges": True,
        },
        "path_redacted": True,
    }


def _parse_csv_float(
    raw: str,
    *,
    name: str,
    minimum: float | None = None,
) -> float:
    """Parse csv float."""
    try:
        value = float(raw)
    except ValueError as exc:
        raise CliError(f"{name} must be numeric") from exc
    if not math.isfinite(value):
        raise CliError(f"{name} must be finite")
    if minimum is not None and value < minimum:
        raise CliError(f"{name} must be at least {minimum}")
    return value


@dataclass
class _MultiplexState:
    """Accumulated cross-row state while validating a multiplex cell table."""

    keys: set[tuple[str, str]] = field(default_factory=set)
    slide_units: dict[str, str] = field(default_factory=dict)
    slide_levels: dict[str, int] = field(default_factory=dict)
    patient_splits: dict[str, str] = field(default_factory=dict)
    unit_counts: Counter[str] = field(default_factory=Counter)
    marker_missing: Counter[str] = field(default_factory=Counter)
    slide_ids: set[str] = field(default_factory=set)
    patient_ids: set[str] = field(default_factory=set)


def _read_multiplex_markers(
    reader: csv.DictReader, requested_markers: list[str]
) -> list[str]:
    """Validate the CSV header and return the marker columns to check."""
    headers = reader.fieldnames
    if headers is None:
        raise CliError("multiplex CSV has no header")
    headers = [header.strip() for header in headers]
    if len(headers) != len(set(headers)):
        raise CliError("multiplex CSV header contains duplicates")
    required = {"cell_id", "slide_id", "x", "y", "coordinate_unit"}
    missing = sorted(required - set(headers))
    if missing:
        raise CliError(
            "multiplex CSV is missing required columns: "
            + ", ".join(missing)
        )
    marker_columns = requested_markers or [
        header for header in headers if header.startswith("marker:")
    ]
    if not marker_columns:
        raise CliError(
            "provide --marker-columns or use at least one marker:* column"
        )
    missing_markers = sorted(set(marker_columns) - set(headers))
    if missing_markers:
        raise CliError(
            "requested marker columns are absent: "
            + ", ".join(missing_markers)
        )
    return marker_columns


def _check_multiplex_identity_and_unit(
    row_number: int, row: Mapping[str, str], state: _MultiplexState
) -> str:
    """Validate ids, coordinates and the per-slide unit of a row; return its slide id."""
    slide_id = _identifier(row["slide_id"], context=f"row {row_number} slide_id")
    cell_id = _identifier(row["cell_id"], context=f"row {row_number} cell_id")
    key = (slide_id, cell_id)
    if key in state.keys:
        raise CliError(f"row {row_number}: duplicate (slide_id, cell_id)")
    state.keys.add(key)
    state.slide_ids.add(slide_id)
    _parse_csv_float(row["x"], name=f"row {row_number} x", minimum=0)
    _parse_csv_float(row["y"], name=f"row {row_number} y", minimum=0)
    unit = row["coordinate_unit"]
    if unit not in COORDINATE_UNITS:
        raise CliError(
            f"row {row_number}: coordinate_unit must be one of "
            + ", ".join(sorted(COORDINATE_UNITS))
        )
    previous_unit = state.slide_units.setdefault(slide_id, unit)
    if previous_unit != unit:
        raise CliError(f"row {row_number}: slide has inconsistent coordinate units")
    state.unit_counts[unit] += 1
    return slide_id


def _check_multiplex_level(
    row_number: int, row: Mapping[str, str], slide_id: str, state: _MultiplexState
) -> None:
    """Validate the optional pyramid level of a row and its per-slide consistency."""
    level_raw = row.get("level", "")
    if not level_raw:
        return
    try:
        level = int(level_raw)
    except ValueError as exc:
        raise CliError(f"row {row_number}: level must be an integer") from exc
    if level < 0:
        raise CliError(f"row {row_number}: level must be nonnegative")
    previous_level = state.slide_levels.setdefault(slide_id, level)
    if previous_level != level:
        raise CliError(f"row {row_number}: slide has inconsistent levels")


def _check_multiplex_patient(
    row_number: int, row: Mapping[str, str], state: _MultiplexState
) -> None:
    """Validate the optional patient id and ensure each patient stays in one split."""
    patient_id = row.get("patient_id", "")
    split = row.get("split", "")
    if patient_id:
        patient_id = _identifier(patient_id, context=f"row {row_number} patient_id")
        state.patient_ids.add(patient_id)
    if split and patient_id:
        previous_split = state.patient_splits.setdefault(patient_id, split)
        if previous_split != split:
            raise CliError(f"row {row_number}: patient appears in multiple splits")


def _check_multiplex_markers(
    row_number: int,
    row: Mapping[str, str],
    marker_columns: list[str],
    allow_missing: bool,
    state: _MultiplexState,
) -> None:
    """Validate the marker values of a row, counting missing values when allowed."""
    for marker in marker_columns:
        raw_value = row.get(marker, "")
        if raw_value == "":
            state.marker_missing[marker] += 1
            if not allow_missing:
                raise CliError(f"row {row_number}: marker {marker!r} is missing")
            continue
        _parse_csv_float(raw_value, name=f"row {row_number} marker {marker}")


def _validate_multiplex_rows(
    reader: csv.DictReader,
    marker_columns: list[str],
    args: argparse.Namespace,
    state: _MultiplexState,
) -> None:
    """Validate every data row of the multiplex CSV, accumulating state."""
    row_count = 0
    for row_count, raw_row in enumerate(reader, start=1):
        if row_count > args.max_rows:
            raise CliError(f"CSV exceeds --max-rows={args.max_rows}")
        row_number = row_count + 1
        row = {
            key.strip(): (value or "").strip()
            for key, value in raw_row.items()
            if key is not None
        }
        slide_id = _check_multiplex_identity_and_unit(row_number, row, state)
        _check_multiplex_level(row_number, row, slide_id, state)
        _check_multiplex_patient(row_number, row, state)
        _check_multiplex_markers(
            row_number, row, marker_columns, args.allow_missing_markers, state
        )
    if row_count == 0:
        raise CliError("multiplex CSV contains no rows")


def validate_multiplex(args: argparse.Namespace) -> dict[str, Any]:
    """Validate a multiplex cell-by-marker CSV and return its validation report."""
    root = checked_root(args.root)
    path = checked_input_file(
        args.input,
        root=root,
        suffixes={".csv"},
        max_bytes=args.max_input_bytes,
    )
    requested_markers = parse_name_list(
        args.marker_columns, name="--marker-columns"
    )
    state = _MultiplexState()

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            marker_columns = _read_multiplex_markers(reader, requested_markers)
            _validate_multiplex_rows(reader, marker_columns, args, state)
    except CliError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise CliError(f"cannot parse multiplex CSV: {exc}") from exc

    return {
        "command": "multiplex",
        "valid": True,
        "row_count": len(state.keys),
        "slide_count": len(state.slide_ids),
        "patient_count": len(state.patient_ids),
        "marker_columns": marker_columns,
        "missing_marker_values": dict(sorted(state.marker_missing.items())),
        "coordinate_unit_counts": dict(sorted(state.unit_counts.items())),
        "checks": {
            "bounded": True,
            "unique_slide_cell_ids": True,
            "finite_nonnegative_coordinates": True,
            "per_slide_coordinate_units": True,
            "per_slide_levels": True,
            "finite_marker_values": True,
            "patient_split_isolation_when_present": True,
        },
        "path_redacted": True,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate bounded local graph JSON or multiplex cell CSV without "
            "loading PathML, Torch, models, or checkpoints."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    graph = subparsers.add_parser("graph", help="validate graph JSON")
    graph.add_argument("--input", required=True)
    graph.add_argument("--root", default=".")
    graph.add_argument("--max-input-bytes", type=int, default=MAX_JSON_BYTES)
    graph.add_argument("--max-nodes", type=int, default=100_000)
    graph.add_argument("--max-edges", type=int, default=1_000_000)
    graph.add_argument("--max-features", type=int, default=4096)
    graph.add_argument("--undirected", action="store_true")
    graph.add_argument("--allow-self-loops", action="store_true")
    graph.add_argument("--output")
    graph.add_argument("--force", action="store_true")

    multiplex = subparsers.add_parser(
        "multiplex", help="validate a cell-by-marker CSV"
    )
    multiplex.add_argument("--input", required=True)
    multiplex.add_argument("--root", default=".")
    multiplex.add_argument("--max-input-bytes", type=int, default=MAX_CSV_BYTES)
    multiplex.add_argument("--max-rows", type=int, default=100_000)
    multiplex.add_argument("--marker-columns")
    multiplex.add_argument("--allow-missing-markers", action="store_true")
    multiplex.add_argument("--output")
    multiplex.add_argument("--force", action="store_true")
    return parser


def main() -> None:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    if args.command == "graph":
        if not 1 <= args.max_input_bytes <= MAX_JSON_BYTES:
            raise CliError(
                f"--max-input-bytes must be between 1 and {MAX_JSON_BYTES}"
            )
        if not 1 <= args.max_nodes <= 10_000_000:
            raise CliError("--max-nodes must be between 1 and 10000000")
        if not 0 <= args.max_edges <= 100_000_000:
            raise CliError("--max-edges must be between 0 and 100000000")
        if not 0 <= args.max_features <= 100_000:
            raise CliError("--max-features must be between 0 and 100000")
        report = validate_graph(args)
    else:
        if not 1 <= args.max_input_bytes <= MAX_CSV_BYTES:
            raise CliError(
                f"--max-input-bytes must be between 1 and {MAX_CSV_BYTES}"
            )
        if not 1 <= args.max_rows <= 1_000_000:
            raise CliError("--max-rows must be between 1 and 1000000")
        report = validate_multiplex(args)
    emit_json(report, output=args.output, root=args.root, force=args.force)


if __name__ == "__main__":
    raise SystemExit(run_cli(main))
