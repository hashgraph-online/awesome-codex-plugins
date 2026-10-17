#!/usr/bin/env python3
"""Build a bounded contaminated-side visual index for clean-room planning."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import struct
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from source_index.writer import atomic_write_json


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
DEFAULT_MAX_FILE_BYTES = 10_000_000
DEFAULT_MAX_TOTAL_BYTES = 100_000_000
DEFAULT_MAX_BATCH_ITEMS = 20
MAX_SKIPPED_ENTRIES = 1000
SUPPORTED_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a bounded contaminated-side visual-index.json for clean-room controller preflight."
    )
    parser.add_argument("--visual-root", action="append", required=True, help="Authorized screenshot/image root.")
    parser.add_argument("--output", required=True, help="Path to write visual-index.json.")
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
    parser.add_argument("--max-batch-items", type=int, default=DEFAULT_MAX_BATCH_ITEMS)
    parser.add_argument("--ignore-dir", action="append", default=[], help="Directory basename to skip.")
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
    if args.max_batch_items < 1:
        raise SystemExit("--max-batch-items must be at least 1")


def path_is_under(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def paths_overlap(left: Path, right: Path) -> bool:
    return path_is_under(left, right) or path_is_under(right, left)


def visual_roots(values: list[str]) -> list[dict[str, str]]:
    roots: list[dict[str, str]] = []
    seen: set[Path] = set()
    for index, value in enumerate(values, start=1):
        path = Path(value).expanduser().resolve()
        if path in seen:
            raise SystemExit(f"duplicate --visual-root: {path}")
        if not path.is_dir():
            raise SystemExit(f"visual root is not a directory: {path}")
        for existing in seen:
            if paths_overlap(path, existing):
                raise SystemExit(f"visual roots must not overlap: {path} overlaps {existing}")
        seen.add(path)
        roots.append({"root_id": f"root-{index:03d}", "path": str(path)})
    if not roots:
        raise SystemExit("at least one unique --visual-root is required")
    return roots


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


def checked_output_path(args: argparse.Namespace, visual_root_records: list[dict[str, str]]) -> Path:
    output = Path(args.output).expanduser().resolve()
    visual_root_paths = [Path(root["path"]) for root in visual_root_records]
    if any(path_is_under(output, root) for root in visual_root_paths):
        raise SystemExit(f"--output must not be under a visual root: {output}")
    roots = contaminated_artifact_roots(args)
    if not roots:
        raise SystemExit(
            "--output must be under CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS or an explicit --contaminated-artifact-root"
        )
    for visual_root in visual_root_paths:
        for contaminated_root in roots:
            if paths_overlap(visual_root, contaminated_root):
                raise SystemExit(
                    f"visual roots and contaminated artifact roots must be separate: "
                    f"{visual_root} overlaps {contaminated_root}"
                )
    if not any(path_is_under(output, root) for root in roots):
        allowed = ", ".join(root.as_posix() for root in roots)
        raise SystemExit(f"--output must be under a contaminated artifact root ({allowed}): {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output = output.resolve()
    resolved_roots = [root.resolve() for root in roots]
    resolved_visual_roots = [root.resolve() for root in visual_root_paths]
    if any(path_is_under(resolved_output, root) for root in resolved_visual_roots):
        raise SystemExit(f"--output must not be under a visual root: {resolved_output}")
    if not any(path_is_under(resolved_output, root) for root in resolved_roots):
        allowed = ", ".join(root.as_posix() for root in resolved_roots)
        raise SystemExit(f"--output must be under a contaminated artifact root ({allowed}): {resolved_output}")
    return resolved_output


def normalized_relative(path: Path) -> str:
    return path.as_posix()


def stat_snapshot(stat: os.stat_result) -> tuple[int | None, int, int]:
    return (
        getattr(stat, "st_ino", None),
        stat.st_size,
        getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
    )


def add_skipped(skipped_entries: list[dict[str, str]], counters: dict[str, int], path: str, reason: str, kind: str) -> None:
    counters["skipped_count"] += 1
    if len(skipped_entries) < MAX_SKIPPED_ENTRIES:
        skipped_entries.append({"path": path, "reason": reason, "kind": kind})


def parse_png(data: bytes) -> tuple[str, int, int] | None:
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return ("image/png", width, height)


def parse_gif(data: bytes) -> tuple[str, int, int] | None:
    if len(data) < 10 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        return None
    width, height = struct.unpack("<HH", data[6:10])
    return ("image/gif", width, height)


def parse_jpeg(data: bytes) -> tuple[str, int, int] | None:
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
    while index + 4 <= len(data):
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            return None
        marker = data[index]
        index += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xDA or index + 2 > len(data):
            return None
        segment_length = struct.unpack(">H", data[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > len(data):
            return None
        if marker in sof_markers and segment_length >= 7:
            height, width = struct.unpack(">HH", data[index + 3 : index + 7])
            return ("image/jpeg", width, height)
        index += segment_length
    return None


def parse_webp(data: bytes) -> tuple[str, int, int] | None:
    if len(data) < 20 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return ("image/webp", width, height)
    if chunk == b"VP8 " and len(data) >= 30:
        if data[23:26] != b"\x9d\x01\x2a":
            return None
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return ("image/webp", width, height)
    if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        width = 1 + (bits & 0x3FFF)
        height = 1 + ((bits >> 14) & 0x3FFF)
        return ("image/webp", width, height)
    return None


def image_metadata(data: bytes, suffix: str) -> tuple[str, int, int] | None:
    if suffix == ".png":
        return parse_png(data)
    if suffix in {".jpg", ".jpeg"}:
        return parse_jpeg(data)
    if suffix == ".gif":
        return parse_gif(data)
    if suffix == ".webp":
        return parse_webp(data)
    return None


def build_batches(images: list[dict[str, Any]], max_batch_items: int) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    for start in range(0, len(images), max_batch_items):
        batch_images = images[start : start + max_batch_items]
        ordinal = len(batches) + 1
        batches.append(
            {
                "batch_id": f"batch-{ordinal:04d}",
                "image_ids": [image["image_id"] for image in batch_images],
                "image_count": len(batch_images),
                "total_bytes": sum(int(image["bytes"]) for image in batch_images),
                "notes": "Visual evidence batch for contaminated-side review.",
            }
        )
    return batches


def collect_images(
    args: argparse.Namespace, roots: list[dict[str, str]]
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    ignore_dirs = set(DEFAULT_IGNORE_DIRS) | set(args.ignore_dir)
    images: list[dict[str, Any]] = []
    skipped_entries: list[dict[str, str]] = []
    counters = {"skipped_count": 0, "total_bytes": 0, "attempted_total_bytes": 0}
    next_image_id = 1

    for root in roots:
        root_path = Path(root["path"])
        limit_stop_recorded = False

        def limit_reached_reason() -> str | None:
            if len(images) >= args.max_files:
                return "file-count-limit"
            if counters["attempted_total_bytes"] >= args.max_total_bytes:
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
                rel = normalized_relative(source_path.relative_to(root_path))
                suffix = source_path.suffix.lower()
                if suffix not in SUPPORTED_EXTENSIONS:
                    add_skipped(skipped_entries, counters, rel, "unsupported-format", "file")
                    continue

                try:
                    resolved = source_path.resolve()
                    if not (resolved == root_path or root_path in resolved.parents):
                        add_skipped(skipped_entries, counters, rel, "symlink-outside-root", "file")
                        continue
                    stat = source_path.stat()
                except OSError as exc:
                    add_skipped(skipped_entries, counters, rel, f"stat-error:{exc.__class__.__name__}", "file")
                    continue

                if len(images) >= args.max_files:
                    add_skipped(skipped_entries, counters, rel, "file-count-limit", "file")
                    continue
                if stat.st_size > args.max_file_bytes:
                    add_skipped(skipped_entries, counters, rel, "file-byte-limit", "file")
                    continue
                if counters["attempted_total_bytes"] + stat.st_size > args.max_total_bytes:
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
                counters["attempted_total_bytes"] += len(data)
                if counters["attempted_total_bytes"] > args.max_total_bytes:
                    add_skipped(skipped_entries, counters, rel, "total-byte-limit-after-read", "file")
                    break

                metadata = image_metadata(data, suffix)
                if metadata is None:
                    add_skipped(skipped_entries, counters, rel, "image-header-unsupported-or-invalid", "file")
                    continue
                media_type, width, height = metadata
                image_record = {
                    "image_id": f"image-{next_image_id:06d}",
                    "root_id": root["root_id"],
                    "path": rel,
                    "media_type": media_type,
                    "width": width,
                    "height": height,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
                images.append(image_record)
                counters["total_bytes"] += len(data)
                next_image_id += 1
    return images, skipped_entries, counters


def aggregate_metrics(
    images: list[dict[str, Any]], batches: list[dict[str, Any]], counters: dict[str, int], skipped_entries: list[dict[str, str]]
) -> dict[str, Any]:
    media_type_counts: dict[str, int] = defaultdict(int)
    for image in images:
        media_type_counts[str(image["media_type"])] += 1
    return {
        "image_count": len(images),
        "total_bytes": counters["total_bytes"],
        "batch_count": len(batches),
        "skipped_count": counters["skipped_count"],
        "skipped_entries_truncated": counters["skipped_count"] > len(skipped_entries),
        "media_type_counts": dict(sorted(media_type_counts.items())),
    }


def main() -> int:
    args = parse_args()
    validate_limits(args)

    roots = visual_roots(args.visual_root)
    output_path = checked_output_path(args, roots)
    images, skipped_entries, counters = collect_images(args, roots)
    batches = build_batches(images, args.max_batch_items)
    now = utc_now()
    output = {
        "index_id": f"visual-index-{args.task_id}",
        "task_id": args.task_id,
        "created_at": now,
        "created_by_role": "controller-preflight",
        "domain": "contaminated",
        "generator": {
            "name": "build_visual_index.py",
            "version": "1",
            "python_version": platform.python_version(),
        },
        "limits": {
            "max_files": args.max_files,
            "max_file_bytes": args.max_file_bytes,
            "max_total_bytes": args.max_total_bytes,
            "max_batch_items": args.max_batch_items,
            "ignore_dirs": sorted(set(DEFAULT_IGNORE_DIRS) | set(args.ignore_dir)),
        },
        "visual_roots": roots,
        "images": images,
        "recommended_batches": batches,
        "skipped_entries": skipped_entries,
        "aggregate_metrics": aggregate_metrics(images, batches, counters, skipped_entries),
    }
    atomic_write_json(output_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
