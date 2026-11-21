#!/usr/bin/env python3
"""Inspect local model artifacts and checksums without deserialization."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from _common import (
    HARD_MAX_BYTES,
    HARD_MAX_FILES,
    SafetyError,
    add_path_mode_argument,
    display_path,
    fail_json,
    int_type,
    iter_text_lines,
    local_path,
    print_json,
    sha256_file,
    simple_yaml_mapping,
)


TOOL = "model-artifact-inspector"
_CONFIG_YAML = "config.yaml"
_HASH_LINE = re.compile(r"^([0-9a-fA-F]{64})[ \t]+[* ]?(.+)$")
_DESERIALIZATION_RISK = {
    ".pt",
    ".pth",
    ".ckpt",
    ".bin",
    ".pkl",
    ".pickle",
    ".joblib",
    ".model",
}
_NATIVE_RISK = {".so", ".dylib", ".dll", ".exe"}
_ARCHIVE_RISK = {".tar", ".zip", ".tgz", ".gz", ".bz2", ".xz"}
_METADATA_KEYS = {
    "architectures",
    "embedding_dim",
    "embedding_size",
    "model_type",
    "pooling_method",
    "vocab_size",
}


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inventory and hash a local Geniml model bundle without importing "
            "ML libraries, extracting archives, or deserializing model files."
        )
    )
    parser.add_argument("--model-dir", required=True)
    parser.add_argument(
        "--verify-manifest",
        help="Optional local SHA256SUMS-style manifest.",
    )
    parser.add_argument(
        "--max-files",
        type=int_type(minimum=1, maximum=HARD_MAX_FILES, label="max-files"),
        default=1_000,
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int_type(minimum=1, maximum=HARD_MAX_BYTES, label="max-file-bytes"),
        default=2 * 1024**3,
    )
    parser.add_argument(
        "--max-total-bytes",
        type=int_type(minimum=1, maximum=HARD_MAX_BYTES, label="max-total-bytes"),
        default=4 * 1024**3,
    )
    parser.add_argument(
        "--max-output-files",
        type=int_type(minimum=0, maximum=5_000, label="max-output-files"),
        default=200,
    )
    add_path_mode_argument(parser)
    return parser


def _walk_regular_files(root: Path, max_files: int) -> list[Path]:
    """Collect every regular file under root, rejecting symlinks and special entries."""
    files: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
        for entry in ordered:
            path = Path(entry.path)
            if entry.is_symlink():
                raise SafetyError("symlink is not allowed in model bundle")
            if entry.is_dir(follow_symlinks=False):
                pending.append(path)
            elif entry.is_file(follow_symlinks=False):
                files.append(path)
                if len(files) > max_files:
                    raise SafetyError("model bundle exceeds max-files")
            else:
                raise SafetyError("special filesystem entry is not allowed")
    return sorted(files)


def _risk_for(path: Path) -> str:
    """Classify a file by the load-time risk its extension implies."""
    suffix = path.suffix.lower()
    if suffix in _DESERIALIZATION_RISK:
        return "deserialization"
    if suffix in _NATIVE_RISK:
        return "native-executable"
    if suffix in _ARCHIVE_RISK:
        return "archive-expansion"
    if suffix == ".safetensors":
        return "bounded-format-still-untrusted"
    return "data-or-metadata"


def _safe_json(path: Path, max_bytes: int):
    """Parse a bounded JSON file, raising SafetyError when it is invalid."""
    lines = [
        line
        for _, line in iter_text_lines(
            path,
            max_bytes=max_bytes,
            max_records=100_000,
        )
    ]
    try:
        return json.loads("\n".join(lines))
    except json.JSONDecodeError as exc:
        raise SafetyError("invalid JSON metadata") from exc


def _read_checksum_manifest(
    path: Path,
    *,
    max_bytes: int,
    max_files: int,
) -> dict[str, str]:
    """Read a sha256sum-style manifest into a mapping of relative path to digest."""
    expected: dict[str, str] = {}
    for line_number, line in iter_text_lines(
        path,
        max_bytes=max_bytes,
        max_records=max_files + 100,
    ):
        if not line or line.startswith("#"):
            continue
        match = _HASH_LINE.fullmatch(line)
        if not match:
            raise SafetyError(f"invalid checksum manifest line {line_number}")
        digest, name = match.groups()
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not relative.parts
            or "://" in name
            or name.startswith("~")
        ):
            raise SafetyError(f"unsafe checksum path at line {line_number}")
        normalized = relative.as_posix()
        if normalized in expected:
            raise SafetyError(f"duplicate checksum entry at line {line_number}")
        expected[normalized] = digest.lower()
        if len(expected) > max_files:
            raise SafetyError("checksum manifest exceeds max-files")
    return expected


def _redacted_metadata(value) -> tuple[dict[str, object], int]:
    """Select the allow-listed config keys, redacting long strings and odd types."""
    if not isinstance(value, dict):
        raise SafetyError("config metadata must be a mapping")
    selected: dict[str, object] = {}
    for key in _METADATA_KEYS:
        if key not in value:
            continue
        item = value[key]
        if isinstance(item, (str, int, float, bool)) or item is None:
            if isinstance(item, str) and len(item) > 200:
                selected[key] = "<redacted-long-string>"
            else:
                selected[key] = item
        elif key == "architectures" and isinstance(item, list):
            selected[key] = [
                entry if isinstance(entry, str) and len(entry) <= 100 else "<redacted>"
                for entry in item[:20]
            ]
    return selected, max(0, len(value) - len(selected))


@dataclass
class _Inventory:
    """Mutable state accumulated while hashing the bundle's files."""

    errors: Counter = field(default_factory=Counter)
    warnings: Counter = field(default_factory=Counter)
    risk_counts: Counter = field(default_factory=Counter)
    computed: dict = field(default_factory=dict)
    summaries: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    total_bytes: int = 0


def _record_config_metadata(path: Path, args: argparse.Namespace, inv: _Inventory) -> None:
    """Parse a recognised config file and record its redacted metadata."""
    max_bytes = min(args.max_file_bytes, 16 * 1024**2)
    if path.name in {_CONFIG_YAML, "config.yml"}:
        parsed = simple_yaml_mapping(path, max_bytes=max_bytes)
    elif path.name in {"config.json", "tokenizer_config.json"}:
        parsed = _safe_json(path, max_bytes=max_bytes)
    else:
        return
    selected, omitted = _redacted_metadata(parsed)
    inv.metadata[path.name] = selected
    if omitted:
        inv.warnings["config_metadata_fields_redacted"] += omitted


def _shown_path(path: Path, index: int, mode: str) -> str:
    """Render an artifact path according to the path disclosure mode."""
    if mode == "redacted":
        return f"artifact_{index:04d}"
    if mode == "basename":
        return path.name
    return str(path)


def _inspect_file(args: argparse.Namespace, model_dir: Path, index: int, path: Path,
                  inv: _Inventory) -> None:
    """Hash and classify one bundle file, updating the inventory."""
    relative = path.relative_to(model_dir).as_posix()
    size = path.lstat().st_size
    if size > args.max_file_bytes:
        inv.errors["file_exceeds_byte_limit"] += 1
        return
    inv.total_bytes += size
    if inv.total_bytes > args.max_total_bytes:
        raise SafetyError("model bundle exceeds max-total-bytes")
    digest, hashed_size = sha256_file(path, max_bytes=args.max_file_bytes)
    inv.computed[relative] = digest
    risk = _risk_for(path)
    inv.risk_counts[risk] += 1
    if risk in {"deserialization", "native-executable", "archive-expansion"}:
        inv.warnings[f"risky_artifact:{risk}"] += 1

    _record_config_metadata(path, args, inv)

    if len(inv.summaries) < args.max_output_files:
        inv.summaries.append(
            {
                "path": _shown_path(path, index, args.path_mode),
                "sha256": digest,
                "size_bytes": hashed_size,
                "risk_class": risk,
                "deserialized": False,
            }
        )


def _verify_checksums(args: argparse.Namespace, inv: _Inventory) -> dict:
    """Compare the computed digests with the expected checksum manifest."""
    manifest = local_path(args.verify_manifest, kind="file")
    expected = _read_checksum_manifest(
        manifest,
        max_bytes=min(args.max_file_bytes, 64 * 1024**2),
        max_files=args.max_files,
    )
    computed = inv.computed
    missing = sorted(set(expected) - set(computed))
    unlisted = sorted(set(computed) - set(expected))
    mismatched = sorted(
        name
        for name in set(expected) & set(computed)
        if expected[name] != computed[name]
    )
    if missing:
        inv.errors["checksum_manifest_missing_files"] = len(missing)
    if mismatched:
        inv.errors["checksum_mismatches"] = len(mismatched)
    if unlisted:
        inv.warnings["files_not_listed_in_checksum_manifest"] = len(unlisted)
    return {
        "manifest": display_path(manifest, 2, args.path_mode),
        "expected_entries": len(expected),
        "missing_count": len(missing),
        "mismatch_count": len(mismatched),
        "unlisted_count": len(unlisted),
        "verified": not missing and not mismatched,
    }


def _check_config_values(inv: _Inventory) -> None:
    """Flag invalid or deprecated values in the parsed config.yaml metadata."""
    config = inv.metadata.get(_CONFIG_YAML)
    if not isinstance(config, dict):
        return
    vocab_size = config.get("vocab_size")
    embedding_dim = config.get("embedding_dim", config.get("embedding_size"))
    if not isinstance(vocab_size, int) or vocab_size <= 0:
        inv.errors["config:invalid_vocab_size"] += 1
    if not isinstance(embedding_dim, int) or embedding_dim <= 0:
        inv.errors["config:invalid_embedding_dim"] += 1
    if "embedding_size" in config and "embedding_dim" not in config:
        inv.warnings["config:deprecated_embedding_size_key"] += 1


def inspect(args: argparse.Namespace) -> tuple[dict, int]:
    """Inspect the model bundle and return the JSON report with its exit code."""
    model_dir = local_path(args.model_dir, kind="dir")
    files = _walk_regular_files(model_dir, args.max_files)
    if not files:
        raise SafetyError("model directory is empty")

    inv = _Inventory()
    for index, path in enumerate(files, start=1):
        _inspect_file(args, model_dir, index, path, inv)

    standard = {
        name: name in inv.computed for name in ("checkpoint.pt", _CONFIG_YAML, "universe.bed")
    }
    for name, present in standard.items():
        if not present:
            inv.errors[f"missing_standard_artifact:{name}"] += 1

    verification = _verify_checksums(args, inv) if args.verify_manifest else None
    _check_config_values(inv)

    errors = inv.errors
    report = {
        "ok": not errors,
        "tool": TOOL,
        "contract": {
            "network_used": False,
            "model_deserialized": False,
            "archives_extracted": False,
            "dynamic_imports_used": False,
            "symlinks_allowed": False,
        },
        "model_dir": display_path(model_dir, 1, args.path_mode),
        "summary": {
            "file_count": len(files),
            "hashed_file_count": len(inv.computed),
            "total_bytes": inv.total_bytes,
            "output_file_summaries": len(inv.summaries),
            "omitted_file_summaries": max(0, len(files) - len(inv.summaries)),
            "risk_classes": dict(sorted(inv.risk_counts.items())),
            "standard_artifacts": standard,
        },
        "metadata": inv.metadata,
        "checksum_verification": verification,
        "errors": dict(sorted(errors.items())),
        "warnings": dict(sorted(inv.warnings.items())),
        "files": inv.summaries,
        "loading_policy": [
            "verify provenance and checksums before loading",
            "never inspect .pt/.model/pickle/joblib by deserializing it",
            "load only in an isolated environment with CPU, RAM, disk, and time bounds",
            "compare universe bytes/order, tokenizer special IDs, vocab size, and assembly",
            "treat native binaries and archives as independently untrusted",
        ],
    }
    return report, 0 if not errors else 2


def main() -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    try:
        report, exit_code = inspect(args)
        print_json(report)
        return exit_code
    except (OSError, SafetyError, UnicodeError) as exc:
        return fail_json(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
