#!/usr/bin/env python3
"""Score an AgentOps skill against the local product-grade skill rubric."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


CATEGORIES = [
    "trigger_quality",
    "kernel_clarity",
    "progressive_disclosure",
    "helper_scripts",
    "validation",
    "self_test",
    "assets_templates",
    "subagents_roles",
    "safety_boundaries",
    "packaging",
]


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    data: dict[str, str] = {}
    if not match:
        return data
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("'\"")
    return data


def count_files(path: Path, *parts: str) -> int:
    target = path.joinpath(*parts)
    if not target.exists():
        return 0
    return sum(1 for p in target.rglob("*") if p.is_file())


def has_named_script(path: Path, patterns: tuple[str, ...]) -> bool:
    scripts = path / "scripts"
    if not scripts.exists():
        return False
    for script in scripts.rglob("*"):
        if not script.is_file():
            continue
        name = script.name.lower()
        if any(pattern in name for pattern in patterns):
            return True
    return False


def collect_metrics(path: Path, text: str) -> dict:
    lines = text.splitlines()
    scripts_dir = path / "scripts"
    executable_scripts = 0
    if scripts_dir.exists():
        executable_scripts = sum(
            1 for p in scripts_dir.rglob("*") if p.is_file() and os.access(p, os.X_OK)
        )

    return {
        "total_files": sum(1 for p in path.rglob("*") if p.is_file()),
        "skill_md_lines": len(lines),
        "headings": len([line for line in lines if line.startswith("#")]),
        "reference_links": len(re.findall(r"references/", text)),
        "reference_files": count_files(path, "references"),
        "script_files": count_files(path, "scripts"),
        "asset_files": count_files(path, "assets"),
        "subagent_files": count_files(path, "subagents"),
        "self_test_exists": (path / "SELF-TEST.md").exists(),
        "symlinks": sum(1 for p in path.rglob("*") if p.is_symlink()),
        "executable_scripts": executable_scripts,
    }


def score_trigger(description: str) -> tuple[int, str]:
    trigger_signals = sum(
        signal in description.lower()
        for signal in ("use when", "when", "audit", "upgrade", "validate", "create")
    )
    return min(3, int(bool(description)) + trigger_signals), "Description length and trigger phrases."


def score_kernel(metrics: dict) -> tuple[int, str]:
    lines = metrics["skill_md_lines"]
    headings = metrics["headings"]
    if lines <= 220 and headings >= 3:
        score = 3
    elif lines <= 500 and headings >= 2:
        score = 2
    elif lines <= 800:
        score = 1
    else:
        score = 0
    return score, f"SKILL.md has {lines} lines and {headings} headings."


def score_progressive_disclosure(metrics: dict) -> tuple[int, str]:
    reference_files = metrics["reference_files"]
    reference_links = metrics["reference_links"]
    score = min(3, (1 if reference_files else 0) + min(2, reference_links))
    return score, f"{reference_files} reference files, {reference_links} direct reference links."


def score_helper_scripts(path: Path, metrics: dict) -> tuple[int, str]:
    script_files = metrics["script_files"]
    score = 0
    if script_files:
        score = 1
    if has_named_script(path, ("validate", "check", "audit", "score", "doctor")):
        score = 2
    if script_files >= 2 and score == 2:
        score = 3
    return score, f"{script_files} script files."


def score_validation(path: Path, body: str, metrics: dict) -> tuple[int, str]:
    validation_terms = ("validate", "test", "check", "lint", "verify", "heal-skill")
    score = int(any(term in body.lower() for term in validation_terms))
    score += int(has_named_script(path, ("validate", "check", "test", "audit")))
    score += int(metrics["self_test_exists"])
    return min(3, score), "Validation commands, scripts, and self-test presence."


def score_self_test(path: Path, metrics: dict) -> tuple[int, str]:
    if not metrics["self_test_exists"]:
        return 0, "SELF-TEST.md missing."
    self_test = (path / "SELF-TEST.md").read_text(encoding="utf-8").lower()
    score = min(
        3,
        1
        + int("trigger" in self_test)
        + int("non-trigger" in self_test or "failure" in self_test),
    )
    return score, "SELF-TEST.md present."


def score_assets(path: Path, metrics: dict) -> tuple[int, str]:
    asset_files = metrics["asset_files"]
    score = 0
    if asset_files:
        score = 2
        if any("template" in p.name.lower() for p in (path / "assets").rglob("*") if p.is_file()):
            score = 3
    return score, f"{asset_files} asset files."


def score_subagents(metrics: dict) -> tuple[int, str]:
    subagent_files = metrics["subagent_files"]
    score = 0
    if subagent_files:
        score = 2 if subagent_files < 3 else 3
    return score, f"{subagent_files} subagent files."


def score_safety(body: str) -> tuple[int, str]:
    safety_terms = ("do not", "never", "forbidden", "non-goal", "scope", "clean-room", "auth")
    safety_hits = sum(term in body.lower() for term in safety_terms)
    return min(3, safety_hits), f"{safety_hits} safety boundary signals."


def score_packaging(metrics: dict) -> tuple[int, str]:
    score = 0
    if metrics["total_files"] <= 50 and metrics["symlinks"] == 0:
        score += 1
    if metrics["executable_scripts"] == 0:
        score += 1
    if metrics["self_test_exists"]:
        score += 1
    note = (
        f"{metrics['total_files']} files, {metrics['symlinks']} symlinks, "
        f"{metrics['executable_scripts']} executable scripts."
    )
    return min(3, score), note


def add_score(
    scores: dict[str, int],
    notes: dict[str, str],
    category: str,
    result: tuple[int, str],
) -> None:
    scores[category], notes[category] = result


def score_skill(path: Path) -> dict:
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        raise SystemExit(f"SKILL.md not found: {skill_md}")

    text = skill_md.read_text(encoding="utf-8")
    fm = frontmatter(text)
    body = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.S)
    metrics = collect_metrics(path, text)

    scores: dict[str, int] = {}
    notes: dict[str, str] = {}

    add_score(scores, notes, "trigger_quality", score_trigger(fm.get("description", "")))
    add_score(scores, notes, "kernel_clarity", score_kernel(metrics))
    add_score(scores, notes, "progressive_disclosure", score_progressive_disclosure(metrics))
    add_score(scores, notes, "helper_scripts", score_helper_scripts(path, metrics))
    add_score(scores, notes, "validation", score_validation(path, body, metrics))
    add_score(scores, notes, "self_test", score_self_test(path, metrics))
    add_score(scores, notes, "assets_templates", score_assets(path, metrics))
    add_score(scores, notes, "subagents_roles", score_subagents(metrics))
    add_score(scores, notes, "safety_boundaries", score_safety(body))
    add_score(scores, notes, "packaging", score_packaging(metrics))

    total = sum(scores.values())
    if total >= 27:
        rating = "S"
    elif total >= 21:
        rating = "A"
    elif total >= 11:
        rating = "B"
    else:
        rating = "C"

    gaps = [
        {"category": category, "score": scores[category], "note": notes[category]}
        for category in CATEGORIES
        if scores[category] < 2
    ]

    return {
        "skill": str(path),
        "name": path.name,
        "total_score": total,
        "max_score": 30,
        "rating": rating,
        "scores": scores,
        "notes": notes,
        "categories": [
            {"category": category, "score": scores[category], "reason": notes[category]}
            for category in CATEGORIES
        ],
        "gaps": gaps,
        "metrics": {
            "total_files": metrics["total_files"],
            "skill_md_lines": metrics["skill_md_lines"],
            "reference_files": metrics["reference_files"],
            "script_files": metrics["script_files"],
            "asset_files": metrics["asset_files"],
            "subagent_files": metrics["subagent_files"],
            "self_test_exists": metrics["self_test_exists"],
            "symlinks": metrics["symlinks"],
            "executable_scripts": metrics["executable_scripts"],
        },
    }


def audit_block(report: dict) -> dict:
    """Compact rubric object for embedding in skill-auditor's audit-report.json (Pass 3).

    Mirrors the rubric schema block: per-category 0-3 score plus an explainable
    reason, the 0-30 total, max, and the C/B/A/S rating band. Deterministic —
    derived only from the skill directory contents.
    """
    return {
        "total_score": report["total_score"],
        "max_score": report["max_score"],
        "rating": report["rating"],
        "advisory": True,
        "categories": report["categories"],
    }


def markdown_report(report: dict) -> str:
    lines = [
        f"# Skill Quality Score: {report['name']}",
        "",
        f"Score: {report['total_score']}/{report['max_score']} ({report['rating']})",
        "",
        "## Category Scores",
        "",
        "| Category | Score | Note |",
        "|---|---:|---|",
    ]
    for category in CATEGORIES:
        lines.append(
            f"| `{category}` | {report['scores'][category]} | {report['notes'][category]} |"
        )
    lines.extend(["", "## Highest Leverage Gaps", ""])
    if report["gaps"]:
        for gap in report["gaps"]:
            lines.append(f"- `{gap['category']}` ({gap['score']}): {gap['note']}")
    else:
        lines.append("- No category scored below 2.")
    lines.extend(["", "## Metrics", "", "```json", json.dumps(report["metrics"], indent=2), "```"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_path")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--markdown", action="store_true", help="Emit a markdown report.")
    group.add_argument(
        "--audit-block",
        action="store_true",
        help="Emit the compact rubric block consumed by skill-auditor Pass 3.",
    )
    args = parser.parse_args()

    report = score_skill(Path(args.skill_path).expanduser().resolve())
    if args.markdown:
        print(markdown_report(report))
    elif args.audit_block:
        print(json.dumps(audit_block(report), indent=2))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
