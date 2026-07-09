#!/usr/bin/env python3
"""Build a bounded contaminated-side source index for clean-room planning."""

from __future__ import annotations

import argparse
import platform
from datetime import datetime, timezone

import clean_room_tooling
from source_index.batching import aggregate_metrics, build_batches, build_large_items
from source_index.discovery import (
    DEFAULT_IGNORE_DIRS,
    DEFAULT_LARGE_FILE_WORDS,
    DEFAULT_LARGE_GROUP_WORDS,
    DEFAULT_MAX_BATCH_TOKENS,
    DEFAULT_MAX_FILE_BYTES,
    DEFAULT_MAX_FILE_SEGMENTS,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_TOTAL_BYTES,
    checked_output_path,
    collect_files,
    source_roots,
)
from source_index.relationships import build_groups, resolve_relationships
from source_index.scanners import SCANNER_MODES
from source_index.writer import atomic_write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a bounded contaminated-side source-index.json for clean-room controller preflight."
    )
    parser.add_argument("--source-root", action="append", required=True, help="Authorized source root to index.")
    parser.add_argument("--output", required=True, help="Path to write source-index.json.")
    parser.add_argument(
        "--contaminated-artifact-root",
        action="append",
        default=[],
        help="Approved contaminated artifact root. Defaults to CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS.",
    )
    parser.add_argument("--task-id", required=True, help="Clean-room task id associated with this index.")
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    parser.add_argument("--max-file-bytes", type=int, default=DEFAULT_MAX_FILE_BYTES)
    parser.add_argument("--max-total-bytes", type=int, default=DEFAULT_MAX_TOTAL_BYTES)
    parser.add_argument("--max-batch-tokens", type=int, default=DEFAULT_MAX_BATCH_TOKENS)
    parser.add_argument("--large-file-words", type=int, default=DEFAULT_LARGE_FILE_WORDS)
    parser.add_argument("--large-group-words", type=int, default=DEFAULT_LARGE_GROUP_WORDS)
    parser.add_argument("--max-file-segments", type=int, default=DEFAULT_MAX_FILE_SEGMENTS)
    parser.add_argument("--ignore-dir", action="append", default=[], help="Directory basename to skip.")
    parser.add_argument(
        "--skip-tool-detection",
        action="store_true",
        help="Do not record optional AST/indexing tool status in source-index.json.",
    )
    parser.add_argument(
        "--probe-tools",
        action="store_true",
        help="Execute optional helper tools with version commands in dependency_report. Default is stat-only.",
    )
    parser.add_argument(
        "--allow-user-toolchain-probes",
        action="store_true",
        help="With --probe-tools, execute version commands for tools found under /opt/homebrew or /usr/local.",
    )
    parser.add_argument(
        "--allow-working-project-tools",
        action="store_true",
        help="Allow dependency detection to consider .local/bin, .bin, node_modules/.bin, and npm prefix/global tools.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_limits(args: argparse.Namespace) -> None:
    if args.max_files < 1:
        raise SystemExit("--max-files must be at least 1")
    if args.max_file_bytes < 1:
        raise SystemExit("--max-file-bytes must be at least 1")
    if args.max_total_bytes < 1:
        raise SystemExit("--max-total-bytes must be at least 1")
    if args.max_batch_tokens < 1:
        raise SystemExit("--max-batch-tokens must be at least 1")
    if args.large_file_words < 1:
        raise SystemExit("--large-file-words must be at least 1")
    if args.large_group_words < 1:
        raise SystemExit("--large-group-words must be at least 1")
    if args.max_file_segments < 1:
        raise SystemExit("--max-file-segments must be at least 1")


def main() -> int:
    args = parse_args()
    validate_limits(args)

    roots = source_roots(args.source_root)
    output_path = checked_output_path(args, roots)
    files, file_segments, skipped_entries, counters = collect_files(args, roots)
    relationships = resolve_relationships(files)
    groups = build_groups(files, relationships)
    batches = build_batches(files, file_segments, groups, args.max_batch_tokens)
    large_items = build_large_items(
        files,
        groups,
        batches,
        args.large_file_words,
        args.large_group_words,
        args.max_batch_tokens,
    )
    now = utc_now()
    output = {
        "index_id": f"source-index-{args.task_id}",
        "task_id": args.task_id,
        "created_at": now,
        "created_by_role": "controller-preflight",
        "domain": "contaminated",
        "generator": {
            "name": "build_source_index.py",
            "version": "1",
            "python_version": platform.python_version(),
            "scanner_modes": SCANNER_MODES,
        },
        "limits": {
            "max_files": args.max_files,
            "max_file_bytes": args.max_file_bytes,
            "max_total_bytes": args.max_total_bytes,
            "max_batch_tokens": args.max_batch_tokens,
            "large_file_words": args.large_file_words,
            "large_group_words": args.large_group_words,
            "max_file_segments": args.max_file_segments,
            "ignore_dirs": sorted(set(DEFAULT_IGNORE_DIRS) | set(args.ignore_dir)),
        },
        "dependency_report": (
            None
            if args.skip_tool_detection
            else clean_room_tooling.dependency_report(
                args.allow_working_project_tools,
                args.probe_tools,
                args.allow_user_toolchain_probes,
            )
        ),
        "source_roots": roots,
        "files": files,
        "file_segments": file_segments,
        "relationships": relationships,
        "groups": groups,
        "recommended_batches": batches,
        "large_items": large_items,
        "skipped_entries": skipped_entries,
        "aggregate_metrics": aggregate_metrics(
            files,
            file_segments,
            relationships,
            groups,
            batches,
            large_items,
            counters["skipped_count"],
            skipped_entries,
        ),
    }
    atomic_write_json(output_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
