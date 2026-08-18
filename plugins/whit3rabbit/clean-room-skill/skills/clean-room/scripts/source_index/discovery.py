"""Source root validation, file collection, and segmentation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from source_index.metrics import add_metrics, empty_metrics, metrics_for_text, metrics_for_text_fragment
from source_index.scanners import language_for_path, scan_file


DEFAULT_IGNORE_DIRS = (
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    ".next",
    "coverage",
    "__pycache__",
)
DEFAULT_MAX_FILES = 2000
DEFAULT_MAX_FILE_BYTES = 1_000_000
DEFAULT_MAX_TOTAL_BYTES = 50_000_000
DEFAULT_MAX_BATCH_TOKENS = 20_000
DEFAULT_LARGE_FILE_WORDS = 5_000
DEFAULT_LARGE_GROUP_WORDS = 15_000
DEFAULT_MAX_FILE_SEGMENTS = 200
MAX_SKIPPED_ENTRIES = 1000


def source_roots(values: list[str]) -> list[dict[str, str]]:
    roots: list[dict[str, str]] = []
    seen: set[Path] = set()
    for index, value in enumerate(values, start=1):
        path = Path(value).expanduser().resolve()
        if path in seen:
            raise SystemExit(f"duplicate --source-root: {path}")
        if not path.is_dir():
            raise SystemExit(f"source root is not a directory: {path}")
        for existing in seen:
            if paths_overlap(path, existing):
                raise SystemExit(f"source roots must not overlap: {path} overlaps {existing}")
        seen.add(path)
        roots.append({"root_id": f"root-{index:03d}", "path": str(path)})
    if not roots:
        raise SystemExit("at least one unique --source-root is required")
    return roots


def path_is_under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def paths_overlap(left: Path, right: Path) -> bool:
    return path_is_under(left, right) or path_is_under(right, left)


def contaminated_artifact_roots(args: argparse.Namespace) -> list[Path]:
    values = list(args.contaminated_artifact_root)
    values.extend(item for item in os.environ.get("CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS", "").split(os.pathsep) if item)
    roots: list[Path] = []
    seen: set[Path] = set()
    for value in values:
        root = Path(value).expanduser().resolve()
        if root in seen:
            continue
        seen.add(root)
        roots.append(root)
    return roots


def env_path_roots(name: str) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    for value in os.environ.get(name, "").split(os.pathsep):
        if not value:
            continue
        root = Path(value).expanduser().resolve()
        if root in seen:
            continue
        seen.add(root)
        roots.append(root)
    return roots


def clean_or_implementation_roots() -> list[tuple[str, Path]]:
    roots: list[tuple[str, Path]] = []
    for name in ("CLEAN_ROOM_CLEAN_ROOTS", "CLEAN_ROOM_IMPLEMENTATION_ROOTS"):
        roots.extend((name, root) for root in env_path_roots(name))
    return roots


def checked_output_path(args: argparse.Namespace, source_root_records: list[dict[str, str]]) -> Path:
    output = Path(args.output).expanduser().resolve()
    source_root_paths = [Path(root["path"]) for root in source_root_records]
    if any(path_is_under(output, root) for root in source_root_paths):
        raise SystemExit(f"--output must not be under a source root: {output}")
    roots = contaminated_artifact_roots(args)
    if not roots:
        raise SystemExit(
            "--output must be under CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS or an explicit --contaminated-artifact-root"
        )
    for source_root in source_root_paths:
        for contaminated_root in roots:
            if paths_overlap(source_root, contaminated_root):
                raise SystemExit(
                    f"source roots and contaminated artifact roots must be separate: "
                    f"{source_root} overlaps {contaminated_root}"
                )
        for env_name, clean_root in clean_or_implementation_roots():
            if paths_overlap(source_root, clean_root):
                raise SystemExit(
                    f"source roots and {env_name} roots must be separate: "
                    f"{source_root} overlaps {clean_root}"
                )
    if not any(path_is_under(output, root) for root in roots):
        allowed = ", ".join(root.as_posix() for root in roots)
        raise SystemExit(f"--output must be under a contaminated artifact root ({allowed}): {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output = output.resolve()
    resolved_roots = [root.resolve() for root in roots]
    resolved_source_roots = [root.resolve() for root in source_root_paths]
    if any(path_is_under(resolved_output, root) for root in resolved_source_roots):
        raise SystemExit(f"--output must not be under a source root: {resolved_output}")
    if not any(path_is_under(resolved_output, root) for root in resolved_roots):
        allowed = ", ".join(root.as_posix() for root in resolved_roots)
        raise SystemExit(f"--output must be under a contaminated artifact root ({allowed}): {resolved_output}")
    return resolved_output


def add_skipped(skipped_entries: list[dict[str, str]], counters: dict[str, int], path: str, reason: str, kind: str) -> None:
    counters["skipped_count"] += 1
    if len(skipped_entries) < MAX_SKIPPED_ENTRIES:
        skipped_entries.append({"path": path, "reason": reason, "kind": kind})


def normalized_relative(path: Path) -> str:
    return path.as_posix()


def stat_snapshot(stat: os.stat_result) -> tuple[int | None, int, int]:
    return (
        getattr(stat, "st_ino", None),
        stat.st_size,
        getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
    )


def build_file_segments(
    file_record: dict[str, Any],
    text: str,
    max_batch_tokens: int,
    large_file_words: int,
    max_file_segments: int,
) -> list[dict[str, Any]]:
    metrics = file_record["metrics"]
    if metrics["estimated_tokens"] <= max_batch_tokens and metrics["words"] <= large_file_words:
        return []

    reason = "large-file-word-count" if metrics["words"] > large_file_words else "large-file-token-count"
    lines = text.splitlines(keepends=True)
    if not lines and text:
        lines = [text]

    segments: list[dict[str, Any]] = []
    current_text: list[str] = []
    current_metrics = empty_metrics()
    start_line = 1
    current_line = 1

    def flush(end_line: int) -> None:
        nonlocal current_text, current_metrics, start_line
        if not current_text or len(segments) >= max_file_segments:
            return
        ordinal = len(segments) + 1
        segments.append(
            {
                "segment_id": f"segment-{file_record['file_id']}-{ordinal:04d}",
                "file_id": file_record["file_id"],
                "ordinal": ordinal,
                "start_line": start_line,
                "end_line": max(start_line, end_line),
                "metrics": dict(current_metrics),
                "reason": reason,
            }
        )
        current_text = []
        current_metrics = empty_metrics()
        start_line = end_line + 1

    for line in lines:
        line_metrics = metrics_for_text_fragment(line)
        if current_text and current_metrics["estimated_tokens"] + line_metrics["estimated_tokens"] > max_batch_tokens:
            flush(current_line - 1)
        if not current_text:
            start_line = current_line
        current_text.append(line)
        add_metrics(current_metrics, line_metrics)
        current_line += max(line_metrics["lines"], 1)
        if len(segments) >= max_file_segments:
            break
    if current_text and len(segments) < max_file_segments:
        flush(current_line - 1)

    return segments


def collect_files(
    args: argparse.Namespace, roots: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    ignore_dirs = set(DEFAULT_IGNORE_DIRS) | set(args.ignore_dir)
    files: list[dict[str, Any]] = []
    file_segments: list[dict[str, Any]] = []
    skipped_entries: list[dict[str, str]] = []
    counters = {"skipped_count": 0, "total_bytes": 0}
    next_file_id = 1

    for root in roots:
        root_path = Path(root["path"])
        limit_stop_recorded = False

        def limit_reached_reason() -> str | None:
            if len(files) >= args.max_files:
                return "file-count-limit"
            if counters["total_bytes"] >= args.max_total_bytes:
                return "total-byte-limit"
            return None

        def record_limit_stop(current: Path, reason: str) -> None:
            nonlocal limit_stop_recorded
            if limit_stop_recorded:
                return
            try:
                rel_path = current.relative_to(root_path)
                rel = normalized_relative(rel_path) if rel_path.as_posix() != "." else "."
            except ValueError:
                rel = normalized_relative(current)
            add_skipped(skipped_entries, counters, rel, f"remaining-files-skipped-after-limit:{reason}", "directory")
            limit_stop_recorded = True

        def record_walk_error(exc: OSError) -> None:
            raw_path = getattr(exc, "filename", None)
            rel = "."
            if raw_path:
                candidate = Path(raw_path)
                try:
                    rel = normalized_relative(candidate.relative_to(root_path))
                except ValueError:
                    try:
                        rel = normalized_relative(candidate.resolve().relative_to(root_path))
                    except (OSError, ValueError):
                        rel = candidate.name or "."
            add_skipped(skipped_entries, counters, rel, f"walk-error:{exc.__class__.__name__}", "directory")

        for current_dir, dirnames, filenames in os.walk(root_path, onerror=record_walk_error):
            current = Path(current_dir)
            limit_reason = limit_reached_reason()
            if limit_reason:
                dirnames[:] = []
                record_limit_stop(current, limit_reason)
                break

            kept_dirs: list[str] = []
            for dirname in sorted(dirnames):
                if dirname in ignore_dirs:
                    rel = normalized_relative((current / dirname).relative_to(root_path))
                    add_skipped(skipped_entries, counters, rel, "ignored-directory", "directory")
                    continue
                kept_dirs.append(dirname)
            dirnames[:] = kept_dirs

            for filename in sorted(filenames):
                limit_reason = limit_reached_reason()
                if limit_reason:
                    dirnames[:] = []
                    record_limit_stop(current, limit_reason)
                    break

                source_path = current / filename
                try:
                    resolved = source_path.resolve()
                    if not (resolved == root_path or root_path in resolved.parents):
                        rel = normalized_relative(source_path.relative_to(root_path))
                        add_skipped(skipped_entries, counters, rel, "symlink-outside-root", "file")
                        continue
                    stat = source_path.stat()
                except OSError as exc:
                    rel = normalized_relative(source_path.relative_to(root_path))
                    add_skipped(skipped_entries, counters, rel, f"stat-error:{exc.__class__.__name__}", "file")
                    continue

                rel_path = source_path.relative_to(root_path)
                rel = normalized_relative(rel_path)
                if len(files) >= args.max_files:
                    add_skipped(skipped_entries, counters, rel, "file-count-limit", "file")
                    continue
                if stat.st_size > args.max_file_bytes:
                    add_skipped(skipped_entries, counters, rel, "file-byte-limit", "file")
                    continue
                if counters["total_bytes"] + stat.st_size > args.max_total_bytes:
                    add_skipped(skipped_entries, counters, rel, "total-byte-limit", "file")
                    continue

                try:
                    data = source_path.read_bytes()
                except OSError as exc:
                    add_skipped(skipped_entries, counters, rel, f"read-error:{exc.__class__.__name__}", "file")
                    continue
                try:
                    post_read_stat = source_path.stat()
                except OSError as exc:
                    add_skipped(skipped_entries, counters, rel, f"post-read-stat-error:{exc.__class__.__name__}", "file")
                    continue
                if stat_snapshot(stat) != stat_snapshot(post_read_stat):
                    add_skipped(skipped_entries, counters, rel, "changed-during-read", "file")
                    continue
                if len(data) > args.max_file_bytes:
                    add_skipped(skipped_entries, counters, rel, "file-byte-limit-after-read", "file")
                    continue
                if counters["total_bytes"] + len(data) > args.max_total_bytes:
                    add_skipped(skipped_entries, counters, rel, "total-byte-limit-after-read", "file")
                    continue
                if b"\0" in data:
                    add_skipped(skipped_entries, counters, rel, "binary-file", "file")
                    continue

                text = data.decode("utf-8", errors="replace")
                language = language_for_path(source_path)
                scanner, imports, exports = scan_file(language, text)
                metrics = metrics_for_text(data, text)
                file_record = {
                    "file_id": f"file-{next_file_id:06d}",
                    "root_id": root["root_id"],
                    "path": rel,
                    "language": language,
                    "scanner": scanner,
                    "metrics": metrics,
                    "imports": imports,
                    "exports": exports,
                }
                files.append(file_record)
                file_segments.extend(
                    build_file_segments(
                        file_record,
                        text,
                        args.max_batch_tokens,
                        args.large_file_words,
                        args.max_file_segments,
                    )
                )
                next_file_id += 1
                counters["total_bytes"] += len(data)
    return files, file_segments, skipped_entries, counters
