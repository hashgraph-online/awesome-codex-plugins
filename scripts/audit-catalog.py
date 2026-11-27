#!/usr/bin/env python3
"""Audit existing Community Plugins entries and committed plugin bundles."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts/validate-plugin-pr.py"
H2_RE = re.compile(r"^##\s+(.+?)\s*$")
H3_RE = re.compile(r"^###\s+(.+?)\s*$")
GUARD_RE = re.compile(
    r"\bsystem of record\b|\bwrite.{0,40}\bverif|\bverif.{0,40}\bwrite|"
    r"\breceipts?\b|\breconcil(?:e|iation|ing|es)\b|\bapproval gate\b|"
    r"\bdrift detection\b|\baudit trail\b|\bprovenance\b", re.I
)


@dataclass(frozen=True)
class Entry:
    name: str
    url: str
    owner: str
    repo: str
    description: str
    subsection: str
    line: int


@dataclass(frozen=True)
class Result:
    name: str
    url: str
    owner: str
    repo: str
    subsection: str
    line: int
    status: str
    evidence: tuple[str, ...] = ()
    error: str | None = None
    guard_candidate: bool = False


def load_validator() -> Any:
    spec = importlib.util.spec_from_file_location("validate_plugin_pr", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_entries(readme: str, validator: Any) -> list[Entry]:
    entries: list[Entry] = []
    section = ""
    subsection = ""
    for line_number, line in enumerate(readme.splitlines(), start=1):
        heading = H2_RE.match(line)
        if heading:
            section = heading.group(1).strip()
            subsection = ""
            continue
        subheading = H3_RE.match(line)
        if subheading:
            subsection = subheading.group(1).strip()
            continue
        if section.casefold() != "community plugins":
            continue
        match = validator.README_ENTRY_RE.match(line.strip())
        if match:
            description_group = 6 if match.lastindex and match.lastindex >= 6 else match.lastindex
            if description_group is None:
                continue
            entries.append(Entry(
                match.group(1).strip(), match.group(2).strip(), match.group(3),
                match.group(4), match.group(description_group).strip(), subsection, line_number,
            ))
    return entries


def local_bundle(repo: str, owner: str) -> Path | None:
    owner_dir = ROOT / "plugins" / owner
    if not owner_dir.is_dir():
        return None
    for candidate in owner_dir.iterdir():
        if candidate.name.casefold() == repo.casefold() and candidate.is_dir():
            return candidate
    return None


def source_repo_url(url: str) -> str:
    return url.rstrip("/").split("/tree/", 1)[0]


def source_reachable(url: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", source_repo_url(url), "HEAD"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    return result.returncode == 0


def audit_entry(entry: Entry, validator: Any) -> Result:
    bundle = local_bundle(entry.repo, entry.owner)
    guard_candidate = bool(GUARD_RE.search(entry.description))
    if bundle is not None:
        errors, _warnings = validator.validate_local_bundle(bundle)
        if errors:
            return Result(
                entry.name, entry.url, entry.owner, entry.repo, entry.subsection,
                entry.line, "invalid-bundle", ("local-bundle",), "; ".join(errors), guard_candidate,
            )
        return Result(
            entry.name, entry.url, entry.owner, entry.repo, entry.subsection,
            entry.line, "eligible", ("local-bundle",), guard_candidate=guard_candidate,
        )
    try:
        reachable = source_reachable(entry.url)
    except (OSError, subprocess.SubprocessError):
        reachable = False
    if reachable:
        return Result(
            entry.name, entry.url, entry.owner, entry.repo, entry.subsection,
            entry.line, "source-only", ("reachable-source",),
            "No committed bundle is available for local validation", guard_candidate,
        )
    return Result(
        entry.name, entry.url, entry.owner, entry.repo, entry.subsection,
        entry.line, "dead-source", error="Source repository is unreachable", guard_candidate=guard_candidate,
    )


def report(results: list[Result]) -> str:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    lines = ["# Codex Community Plugins catalog audit", "", f"Entries audited: {len(results)}", "", "## Summary", ""]
    lines.extend(f"- {status}: {count}" for status, count in sorted(counts.items()))
    lines.append(f"- HOL Guard candidates: {sum(result.guard_candidate for result in results)}")
    findings = [result for result in results if result.status in ("dead-source", "invalid-bundle")]
    if findings:
        lines += ["", "## Confirmed findings", "", "| Entry | Section | Line | Status | Reason |", "| --- | --- | ---: | --- | --- |"]
        lines.extend(
            f"| [{result.name}]({result.url}) | {result.subsection} | {result.line} | {result.status} | {(result.error or '').replace('|', '/')} |"
            for result in findings
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=12)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validator = load_validator()
    entries = read_entries((ROOT / "README.md").read_text(encoding="utf-8"), validator)
    if args.limit is not None:
        entries = entries[:args.limit]
    if args.workers < 1:
        raise SystemExit("--workers must be positive")
    results: list[Result] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(audit_entry, entry, validator) for entry in entries]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda result: result.line)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps([asdict(result) for result in results], indent=2) + "\n", encoding="utf-8")
    args.output_markdown.write_text(report(results), encoding="utf-8")
    print(report(results), end="")
    return 1 if any(result.status in ("dead-source", "invalid-bundle") for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
