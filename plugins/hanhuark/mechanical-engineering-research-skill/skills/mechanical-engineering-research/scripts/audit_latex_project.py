#!/usr/bin/env python3
"""Audit a LaTeX project without modifying it.

Checks recursive TeX inputs, citations, bibliography keys, references, graphics,
placeholders, and stale alternate source files. Semantic claim verification and
visual PDF inspection remain manual tasks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


TEX_EXTENSIONS = (".tex",)
GRAPHICS_EXTENSIONS = ("", ".pdf", ".png", ".jpg", ".jpeg", ".eps")
PLACEHOLDER_PATTERNS = {
    "TODO": re.compile(r"\bTODO\b", re.IGNORECASE),
    "TBD": re.compile(r"\bTBD\b", re.IGNORECASE),
    "XXX": re.compile(r"\bXXX\b"),
    "question marks": re.compile(r"(?<!\\)\?\?+"),
    "placeholder": re.compile(r"\bplaceholder\b", re.IGNORECASE),
    "insert here": re.compile(r"\binsert\s+here\b", re.IGNORECASE),
    "prompt artifact": re.compile(r"\b(?:ChatGPT|Codex|feel free|no need to)\b", re.IGNORECASE),
}


def strip_comments(text: str) -> str:
    cleaned = []
    for line in text.splitlines():
        match = re.search(r"(?<!\\)%", line)
        cleaned.append(line[: match.start()] if match else line)
    return "\n".join(cleaned)


def resolve_tex_target(parent: Path, raw: str) -> Path:
    target = (parent / raw.strip()).resolve()
    if target.suffix:
        return target
    return target.with_suffix(".tex")


def collect_tex_files(main_file: Path) -> tuple[list[Path], list[str]]:
    found: list[Path] = []
    missing: list[str] = []
    pending = [main_file.resolve()]
    seen: set[Path] = set()
    input_re = re.compile(r"\\(?:input|include|subfile)\s*\{([^}]+)\}")

    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if not current.is_file():
            missing.append(str(current))
            continue
        found.append(current)
        text = strip_comments(current.read_text(encoding="utf-8", errors="replace"))
        for raw in input_re.findall(text):
            pending.append(resolve_tex_target(current.parent, raw))
    return found, missing


def find_graphic(parent: Path, raw: str) -> Path | None:
    target = (parent / raw.strip()).resolve()
    for suffix in GRAPHICS_EXTENSIONS:
        candidate = target if suffix == "" else Path(f"{target}{suffix}")
        if candidate.is_file():
            return candidate
    return None


def parse_bib_keys(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return re.findall(r"(?im)^\s*@\w+\s*\{\s*([^,\s]+)\s*,", text)


def audit(project: Path, main_file: Path) -> dict[str, object]:
    tex_files, missing_inputs = collect_tex_files(main_file)
    errors: list[str] = []
    warnings: list[str] = []
    if missing_inputs:
        errors.extend(f"missing TeX input: {item}" for item in missing_inputs)

    citation_order: list[str] = []
    labels: set[str] = set()
    refs: set[str] = set()
    bib_files: set[Path] = set()

    cite_re = re.compile(
        r"\\(?:[A-Za-z]*cite[A-Za-z]*|nocite)(?:\s*\[[^\]]*\]){0,2}\s*\{([^}]*)\}"
    )
    label_re = re.compile(r"\\label\s*\{([^}]+)\}")
    ref_re = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref)\s*\{([^}]+)\}")
    graphics_re = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}")
    bibliography_re = re.compile(r"\\bibliography\s*\{([^}]+)\}")
    bibresource_re = re.compile(r"\\addbibresource(?:\s*\[[^\]]*\])?\s*\{([^}]+)\}")

    for tex_file in tex_files:
        raw_text = tex_file.read_text(encoding="utf-8", errors="replace")
        text = strip_comments(raw_text)
        labels.update(label_re.findall(text))
        refs.update(ref_re.findall(text))

        for group in cite_re.findall(text):
            for key in (item.strip() for item in group.split(",")):
                if key and key != "*" and key not in citation_order:
                    citation_order.append(key)

        for group in bibliography_re.findall(text):
            for raw in group.split(","):
                candidate = (tex_file.parent / raw.strip()).resolve()
                bib_files.add(candidate if candidate.suffix else candidate.with_suffix(".bib"))
        for raw in bibresource_re.findall(text):
            candidate = (tex_file.parent / raw.strip()).resolve()
            bib_files.add(candidate if candidate.suffix else candidate.with_suffix(".bib"))

        for raw in graphics_re.findall(text):
            if find_graphic(tex_file.parent, raw) is None:
                errors.append(f"missing graphic from {tex_file.name}: {raw}")

        for label, pattern in PLACEHOLDER_PATTERNS.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                warnings.append(f"{label} in {tex_file.name}:{line}")

    missing_refs = sorted(refs - labels)
    errors.extend(f"undefined reference label: {item}" for item in missing_refs)

    bib_key_sources: dict[str, list[str]] = {}
    for bib_file in sorted(bib_files):
        if not bib_file.is_file():
            errors.append(f"missing bibliography file: {bib_file}")
            continue
        for key in parse_bib_keys(bib_file):
            bib_key_sources.setdefault(key, []).append(str(bib_file))

    duplicate_bib_keys = sorted(key for key, sources in bib_key_sources.items() if len(sources) > 1)
    errors.extend(f"duplicate bibliography key: {key}" for key in duplicate_bib_keys)
    missing_citations = sorted(set(citation_order) - set(bib_key_sources))
    errors.extend(f"citation key missing from bibliography: {key}" for key in missing_citations)
    uncited_bib_keys = sorted(set(bib_key_sources) - set(citation_order))

    alternate_sources = sorted(
        str(path.relative_to(project))
        for path in project.rglob("*.tex")
        if path.resolve() not in set(tex_files)
        and re.search(r"(?:autocite|old|backup|copy|draft|marked|highlight)", path.name, re.IGNORECASE)
    )
    warnings.extend(f"possible stale alternate source: {item}" for item in alternate_sources)

    duplicate_labels = [
        label for label, count in Counter(
            match
            for tex_file in tex_files
            for match in label_re.findall(strip_comments(tex_file.read_text(encoding="utf-8", errors="replace")))
        ).items()
        if count > 1
    ]
    errors.extend(f"duplicate LaTeX label: {label}" for label in sorted(duplicate_labels))

    return {
        "project": str(project),
        "main": str(main_file),
        "tex_files": [str(path) for path in tex_files],
        "bibliography_files": [str(path) for path in sorted(bib_files)],
        "citation_order": citation_order,
        "uncited_bibliography_keys": uncited_bib_keys,
        "warnings": warnings,
        "errors": errors,
        "manual_checks": [
            "Verify that each citation supports the exact claim and regime.",
            "Compile with the intended engine and inspect the log.",
            "Render and visually inspect the final PDF.",
        ],
    }


def choose_main(project: Path, requested: str | None) -> Path:
    if requested:
        candidate = (project / requested).resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"main file not found: {candidate}")
        return candidate
    default = project / "main.tex"
    if default.is_file():
        return default.resolve()
    candidates = sorted(project.glob("*.tex"))
    if len(candidates) == 1:
        return candidates[0].resolve()
    raise FileNotFoundError("specify --main because no unique main TeX file was found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default=".", help="LaTeX project directory")
    parser.add_argument("--main", help="main TeX file relative to the project directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"ERROR: project directory not found: {project}", file=sys.stderr)
        return 2
    try:
        main_file = choose_main(project, args.main)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = audit(project, main_file)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Main: {report['main']}")
        print(f"TeX files: {len(report['tex_files'])}")
        print(f"Citation keys: {len(report['citation_order'])}")
        for index, key in enumerate(report["citation_order"], start=1):
            print(f"  {index}: {key}")
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")
        if report["uncited_bibliography_keys"]:
            print(f"INFO: uncited bibliography keys: {len(report['uncited_bibliography_keys'])}")
        for item in report["manual_checks"]:
            print(f"MANUAL: {item}")

    return 1 if report["errors"] or (args.strict and report["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
