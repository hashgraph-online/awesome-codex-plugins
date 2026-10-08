#!/usr/bin/env python3
"""Build a bounded, reproducible packet for an external ChatGPT agent."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import pathlib
import os
import subprocess
import zipfile
from dataclasses import dataclass
from typing import Iterable

import sys
# Also support the legacy runpy launcher without importing from the workspace.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from access_policy import (checked_path, denied, ignore_patterns as shared_ignore_patterns,
                           read_regular, relative_path)


DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".chatgpt-agent",
    ".chatgpt-review",
}
DEFAULT_DENY_GLOBS = {
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.kdbx",
    ".env",
    ".env.*",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service-account*.json",
    "*secret*.json",
}
ALLOW_GLOBS = {".env.example", ".env.sample", ".env.template"}
DEFAULT_INCLUDES = [
    "*.py",
    "*.js",
    "*.ts",
    "*.tsx",
    "*.jsx",
    "*.md",
    "*.txt",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.toml",
    "*.html",
    "*.css",
    "*.sh",
    "*.cmd",
    "*.ps1",
]


@dataclass(frozen=True)
class IncludedFile:
    relative: str
    original: bytes
    included: bytes

    @property
    def truncated(self) -> bool:
        return len(self.included) < len(self.original)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_path(raw: str) -> pathlib.Path:
    root = pathlib.Path(raw).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Repository directory not found: {raw}")
    return root


def load_ignore_patterns(root: pathlib.Path) -> list[str]:
    return shared_ignore_patterns(root)


def is_denied(relative: pathlib.PurePosixPath, extra_patterns: Iterable[str]) -> bool:
    return (any(part.casefold() in DEFAULT_EXCLUDES for part in relative.parts)
            or denied(relative, extra_patterns))


def safe_child(root: pathlib.Path, raw: str, ignore_patterns: list[str]) -> pathlib.Path:
    try:
        rel = relative_path(raw)
        if is_denied(rel, ignore_patterns):
            raise ValueError("sensitive or ignored path")
        path = checked_path(root, raw, patterns=ignore_patterns)
        if not path.is_file():
            raise ValueError("not a regular file")
        return path
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Refusing sensitive, ignored path, or unsafe file: {raw}: {exc}") from None


def safe_dir(root: pathlib.Path, raw: str) -> pathlib.Path:
    try:
        path = checked_path(root, raw, allow_root=True, patterns=load_ignore_patterns(root))
        if not path.is_dir():
            raise ValueError("not a directory")
        return path
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Refusing unsafe directory: {raw}: {exc}") from None


def iter_dir_files(root: pathlib.Path, raw: str, includes: list[str],
                   ignore_patterns: list[str]) -> list[pathlib.Path]:
    base = safe_dir(root, raw)
    found = []
    visited = 0
    for directory, dirs, names in os.walk(base, followlinks=False):
        kept = []
        for name in dirs:
            rel = (pathlib.Path(directory) / name).relative_to(root).as_posix()
            try:
                if is_denied(pathlib.PurePosixPath(rel), ignore_patterns):
                    continue
                checked_path(root, rel, patterns=ignore_patterns)
            except (ValueError, OSError):
                continue
            kept.append(name)
        dirs[:] = sorted(kept)
        for name in sorted(names):
            visited += 1
            if visited > 20000:
                raise SystemExit("Directory scan budget exceeded; select narrower evidence.")
            rel = (pathlib.Path(directory) / name).relative_to(root).as_posix()
            if not any(fnmatch.fnmatchcase(name, pat) or fnmatch.fnmatchcase(rel, pat) for pat in includes):
                continue
            try:
                if is_denied(pathlib.PurePosixPath(rel), ignore_patterns):
                    continue
                path = checked_path(root, rel, patterns=ignore_patterns)
                if not path.is_file():
                    continue
            except (ValueError, OSError):
                continue
            found.append(path)
    return sorted(found)


def reject_binary(data: bytes, relative: str) -> None:
    if b"\x00" in data[:8192]:
        raise SystemExit(
            f"Binary files are not supported in text packets: {relative}"
        )


def include_file(
    root: pathlib.Path, path: pathlib.Path, max_bytes: int
) -> IncludedFile:
    relative = path.relative_to(root).as_posix()
    original = read_regular(root, relative, limit=16_000_000, patterns=load_ignore_patterns(root))
    reject_binary(original, relative)
    included = original[:max_bytes]
    return IncludedFile(relative, original, included)


def git_metadata(root: pathlib.Path) -> dict[str, object]:
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    probe = run(["rev-parse", "--is-inside-work-tree"])
    if probe.returncode != 0:
        return {
            "is_repo": False,
            "commit": None,
            "branch": None,
            "dirty": None,
        }
    commit = run(["rev-parse", "HEAD"]).stdout.strip() or None
    branch = run(["branch", "--show-current"]).stdout.strip() or None
    dirty = bool(run(["status", "--porcelain"]).stdout)
    return {
        "is_repo": True,
        "commit": commit,
        "branch": branch,
        "dirty": dirty,
    }


def numbered_text(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    width = len(str(len(lines) or 1))
    return "\n".join(
        f"{index:>{width}}: {line}"
        for index, line in enumerate(lines, 1)
    )


def fence_for(path: pathlib.PurePosixPath) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "jsx",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".sh": "bash",
        ".ps1": "powershell",
        ".cmd": "batch",
    }.get(path.suffix.lower(), "text")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", required=True)
    parser.add_argument("--zip")
    parser.add_argument("--manifest")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--role", default="reviewer")
    parser.add_argument("--route", default="packet.inspect")
    parser.add_argument("--source-kind", default="local_workspace")
    parser.add_argument("--repo-alias", default="workspace:/")
    parser.add_argument("--claim", action="append", default=[])
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--dir", action="append", default=[])
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--max-files", type=int, default=80)
    parser.add_argument("--max-bytes-per-file", type=int, default=30_000)
    parser.add_argument("--max-total-bytes", type=int, default=5_000_000)
    args = parser.parse_args()
    if (not 1 <= args.max_files <= 1000 or not 1 <= args.max_bytes_per_file <= 16_000_000
            or not 1 <= args.max_total_bytes <= 64_000_000):
        raise SystemExit("Packet limits must be positive and within documented bounds.")

    root = repo_path(args.repo)
    out = pathlib.Path(os.path.abspath(pathlib.Path(args.out).expanduser()))
    manifest_path = (pathlib.Path(os.path.abspath(pathlib.Path(args.manifest).expanduser()))
                     if args.manifest else out.with_name("manifest.json"))
    destinations = [out, manifest_path]
    if args.zip:
        destinations.append(pathlib.Path(os.path.abspath(pathlib.Path(args.zip).expanduser())))
    for dest in destinations:
        # Output paths are host-selected, but may not follow links or overwrite
        # hard-linked source data, even outside the evidence root.
        for component in [dest, *dest.parents]:
            if component.is_symlink() or getattr(component, "is_junction", lambda: False)():
                raise SystemExit("Linked packet output paths are denied.")
        if dest.exists() and (not dest.is_file() or dest.stat().st_nlink != 1):
            raise SystemExit("Unsafe packet output path.")
    # Validate raw components before resolving: resolution must not erase a
    # forbidden symlink/junction. Then compare identities, not 8.3/long-path
    # spellings, both between outputs and against canonical selected evidence.
    destinations = [dest.resolve() for dest in destinations]
    if len(set(destinations)) != len(destinations):
        raise SystemExit("Packet output paths must be distinct.")
    out, manifest_path = destinations[:2]
    ignore_patterns = load_ignore_patterns(root)
    includes = args.include or list(DEFAULT_INCLUDES)
    selected: dict[str, pathlib.Path] = {}
    for raw in args.file:
        path = safe_child(root, raw, ignore_patterns)
        if path in destinations:
            raise SystemExit("Packet output cannot overwrite selected evidence.")
        selected[path.relative_to(root).as_posix()] = path
    for raw_dir in args.dir:
        for path in iter_dir_files(
            root, raw_dir, includes, ignore_patterns
        ):
            if path not in destinations:
                selected[path.relative_to(root).as_posix()] = path
    paths = [selected[key] for key in sorted(selected)]
    if not paths:
        raise SystemExit("No files selected. Use --file or --dir.")
    if len(paths) > args.max_files:
        raise SystemExit(
            f"Too many files ({len(paths)}). Narrow --dir/--include or "
            "raise --max-files."
        )

    files = []
    total = original_total = 0
    for path in paths:
        # Admit original read cost, not merely the truncated output size.
        original_total += path.stat().st_size
        if original_total > 64_000_000:
            raise SystemExit("Packet original-input budget exceeded.")
        item = include_file(root, path, args.max_bytes_per_file)
        files.append(item)
        total += len(item.included)
        if total > args.max_total_bytes:
            raise SystemExit("Packet content exceeds total byte limit.")
    if total > args.max_total_bytes:
        raise SystemExit(
            f"Packet content is too large ({total} bytes); limit is "
            f"{args.max_total_bytes}."
        )

    generated = dt.datetime.now(dt.timezone.utc).isoformat()
    git = git_metadata(root)
    manifest = {
        "packet_version": 2,
        "generated_at": generated,
        "route": args.route,
        "role": args.role,
        "source_kind": args.source_kind,
        "repository": {"alias": args.repo_alias, "git": git},
        "goal": args.goal,
        "claims": args.claim,
        "limits": {
            "max_files": args.max_files,
            "max_bytes_per_file": args.max_bytes_per_file,
            "max_total_bytes": args.max_total_bytes,
        },
        "files": [
            {
                "path": item.relative,
                "original_bytes": len(item.original),
                "included_bytes": len(item.included),
                "truncated": item.truncated,
                "sha256_original": sha256(item.original),
                "sha256_included": sha256(item.included),
            }
            for item in files
        ],
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        "# ChatGPT Agent Packet",
        "",
        f"- Generated: {generated}",
        f"- Route: `{args.route}`",
        f"- Role: `{args.role}`",
        f"- Source: `{args.source_kind}`",
        f"- Repository: `{args.repo_alias}`",
        f"- Commit: `{git.get('commit') or 'not-a-git-repository'}`",
        f"- Dirty: `{git.get('dirty')}`",
        "",
        "## Goal",
        "",
        args.goal,
        "",
    ]
    if args.claim:
        parts.extend(["## Claims To Verify", ""])
        parts.extend(f"- {claim}" for claim in args.claim)
        parts.append("")
    parts.extend(
        [
            "## Evidence Boundary",
            "",
            "Only the files listed in `manifest.json` are in scope. A "
            "truncated file is also truncated inside the ZIP; the full "
            "original is not silently included.",
            "",
            "## Evidence",
            "",
        ]
    )
    for item in files:
        path = pathlib.PurePosixPath(item.relative)
        suffix = " (truncated)" if item.truncated else ""
        parts.extend(
            [
                f"### {item.relative}{suffix}",
                "",
                f"```{fence_for(path)}",
                numbered_text(item.included),
                "```",
                "",
            ]
        )
    out.write_text("\n".join(parts), encoding="utf-8")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if args.zip:
        zip_path = destinations[2]
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(
            zip_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.write(out, "agent-packet.md")
            archive.write(manifest_path, "manifest.json")
            for item in files:
                archive.writestr(f"files/{item.relative}", item.included)

    print(out)
    print(manifest_path)
    if args.zip:
        print(destinations[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
