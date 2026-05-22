#!/usr/bin/env python3
"""Parsing and context-building utilities for consistency checks."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

from check_consistency_line_locator import LineLocator
from check_consistency_models import NEGATIVE_MARKERS, ScanContext, Violation, YamlBlock, YamlDocument


SUPPORTED_SCAN_SUFFIXES = {".md", ".yaml", ".yml"}


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if path.is_file():
            yield path


def iter_yaml_files(root: Path) -> Iterable[Path]:
    for pattern in ("*.yaml", "*.yml"):
        for path in sorted(root.rglob(pattern)):
            if path.is_file():
                yield path


def iter_supported_files(root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for path in [*iter_markdown_files(root), *iter_yaml_files(root)]:
        if path in seen:
            continue
        seen.add(path)
        yield path


def has_negative_markers(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in NEGATIVE_MARKERS)


def extract_yaml_blocks(path: Path, text: str) -> List[YamlBlock]:
    lines = text.splitlines()
    blocks: List[YamlBlock] = []

    in_block = False
    block_start = 0
    collected: List[str] = []
    block_skip_checks = False

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not in_block:
            if stripped.startswith("```"):
                lang = stripped[3:].strip().split(maxsplit=1)[0].lower() if stripped[3:].strip() else ""
                if lang in {"yaml", "yml"}:
                    in_block = True
                    block_start = index + 1
                    collected = []
                    context_lines = lines[max(0, index - 4): index]
                    block_skip_checks = has_negative_markers("\n".join(context_lines))
            continue

        if stripped.startswith("```"):
            source = "\n".join(collected).strip("\n")
            if source:
                skip_checks = block_skip_checks or has_negative_markers(source)
                blocks.append(
                    YamlBlock(path=path, start_line=block_start, source=source, skip_checks=skip_checks)
                )
            in_block = False
            block_start = 0
            collected = []
            block_skip_checks = False
            continue

        collected.append(line)

    return blocks


def split_yaml_documents(block: YamlBlock) -> List[Tuple[int, str]]:
    docs: List[Tuple[int, str]] = []
    lines = block.source.splitlines()

    current: List[str] = []
    doc_start = block.start_line

    for index, line in enumerate(lines, start=block.start_line):
        if re.match(r"^\s*---\s*$", line):
            text = "\n".join(current).strip()
            if text:
                docs.append((doc_start, text))
            current = []
            doc_start = index + 1
            continue
        current.append(line)

    tail = "\n".join(current).strip()
    if tail:
        docs.append((doc_start, tail))

    return docs


def should_ignore_yaml_parse_error(doc_text: str) -> bool:
    lines = [line.strip() for line in doc_text.splitlines()]
    if any(line == "..." for line in lines):
        return True

    template_control_prefixes = (
        "${{ if(",
        "${{ elif(",
        "${{ else() }}",
        "${{ endif() }}",
    )
    return any(line.startswith(template_prefix) for line in lines for template_prefix in template_control_prefixes)


def parse_yaml_documents(blocks: Sequence[YamlBlock]) -> Tuple[List[YamlDocument], List[Violation]]:
    documents: List[YamlDocument] = []
    violations: List[Violation] = []

    for block in blocks:
        for start_line, doc_text in split_yaml_documents(block):
            try:
                parsed = yaml.safe_load(doc_text)
            except yaml.YAMLError as exc:
                if block.skip_checks or should_ignore_yaml_parse_error(doc_text):
                    continue
                line = start_line
                mark = getattr(exc, "problem_mark", None)
                if mark is not None:
                    line += int(mark.line)
                violations.append(
                    Violation(
                        rule_id="R000",
                        path=block.path,
                        line=line,
                        message=f"invalid YAML snippet: {exc.__class__.__name__}",
                    )
                )
                continue

            if parsed is None:
                continue

            documents.append(
                YamlDocument(
                    path=block.path,
                    start_line=start_line,
                    source=doc_text,
                    data=parsed,
                    skip_checks=block.skip_checks,
                    line_locator=LineLocator(
                        start_line=start_line,
                        lines=tuple(doc_text.splitlines()),
                    ),
                )
            )

    return documents, violations


def find_line(doc: YamlDocument, pattern: str, default: Optional[int] = None) -> int:
    return doc.line_locator.find(pattern, default=default)


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base / path).resolve()


def build_scan_paths(skill_path: Path, references_dir: Path, include_paths: Sequence[str]) -> List[Path]:
    if not include_paths:
        return [skill_path, *iter_supported_files(references_dir)]

    skill_root = skill_path.parent
    resolved: List[Path] = []
    for rel in include_paths:
        p = resolve_path(rel, skill_root)
        if not p.exists():
            raise ValueError(f"included path does not exist: {p}")
        if p.is_dir():
            resolved.extend(list(iter_supported_files(p)))
        else:
            if p.suffix.lower() not in SUPPORTED_SCAN_SUFFIXES:
                allowed = ", ".join(sorted(SUPPORTED_SCAN_SUFFIXES))
                raise ValueError(f"unsupported included file type: {p} (allowed: {allowed})")
            resolved.append(p)

    unique: List[Path] = []
    seen: set[Path] = set()
    for path in resolved:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def build_context(skill_path: Path, references_dir: Path, include_paths: Sequence[str]) -> Tuple[ScanContext, List[Violation]]:
    scan_paths = build_scan_paths(skill_path, references_dir, include_paths)
    file_texts: Dict[Path, str] = {}
    blocks: List[YamlBlock] = []

    for path in scan_paths:
        text = path.read_text(encoding="utf-8")
        file_texts[path] = text
        if path.suffix.lower() == ".md":
            blocks.extend(extract_yaml_blocks(path, text))
            continue
        blocks.append(
            YamlBlock(
                path=path,
                start_line=1,
                source=text,
                skip_checks=False,
            )
        )

    yaml_documents, parse_violations = parse_yaml_documents(blocks)
    context = ScanContext(
        skill_path=skill_path,
        references_dir=references_dir,
        scanned_paths=scan_paths,
        file_texts=file_texts,
        yaml_documents=yaml_documents,
    )
    return context, parse_violations
