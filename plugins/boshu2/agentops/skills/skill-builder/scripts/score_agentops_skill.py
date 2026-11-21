#!/usr/bin/env python3
"""Score static package readiness for an AgentOps skill."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import yaml


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


def frontmatter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


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
    if not description:
        return 0, "Description missing."
    lowered = description.lower()
    if any(term in lowered for term in ("not for", "do not use", "not when", "only when")):
        return 3, "Description contains a literal false-positive boundary phrase."
    if "triggers:" in lowered or "use when" in lowered:
        return 2, "Description contains a literal trigger marker."
    return 1, "Description is present without a literal trigger or boundary marker."


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
    if not reference_files and metrics["skill_md_lines"] <= 100:
        return 2, "SKILL.md is at most 100 lines with no reference files; loading semantics are not evaluated."
    score = min(3, (1 if reference_files else 0) + min(2, reference_links))
    return score, f"{reference_files} reference files, {reference_links} direct reference links."


def score_helper_scripts(path: Path, metrics: dict) -> tuple[int, str]:
    script_files = metrics["script_files"]
    if not script_files:
        return 1, "No helper scripts are visible; necessity is not inferred."
    recognized_helper = has_named_script(path, ("validate", "check", "audit", "score", "doctor"))
    score = 2 if recognized_helper else 1
    if script_files >= 2 and score == 2:
        score = 3
    return score, f"{script_files} script files; recognized helper name={int(recognized_helper)}."


def score_validation(path: Path, body: str, metrics: dict) -> tuple[int, str]:
    validation_terms = ("validate", "test", "check", "lint", "verify", "heal.sh")
    keyword_signal = int(any(term in body.lower() for term in validation_terms))
    named_helper = int(has_named_script(path, ("validate", "check", "test", "audit")))
    self_test = int(metrics["self_test_exists"])
    score = keyword_signal + named_helper + self_test
    note = (
        f"keyword signal={keyword_signal}, recognized helper={named_helper}, "
        f"SELF-TEST.md={self_test}."
    )
    return min(3, score), note


def score_self_test(path: Path, metrics: dict) -> tuple[int, str]:
    if not metrics["self_test_exists"]:
        if any(path.rglob("*.feature")):
            return 2, "At least one .feature file is present."
        return 1, "No focused self-test or feature artifact is visible."
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
    if not asset_files:
        return 1, "No asset files are visible; necessity is not inferred."
    template_named = any(
        "template" in p.name.lower() for p in (path / "assets").rglob("*") if p.is_file()
    )
    score = 3 if template_named else 2
    return score, f"{asset_files} asset files; template-named file={int(template_named)}."


def score_subagents(metrics: dict) -> tuple[int, str]:
    subagent_files = metrics["subagent_files"]
    if not subagent_files:
        return 1, "No subagent files are visible; necessity is not inferred."
    score = 2 if subagent_files < 3 else 3
    return score, f"{subagent_files} subagent files."


def score_safety(body: str) -> tuple[int, str]:
    safety_terms = ("do not", "never", "forbidden", "non-goal", "scope", "clean-room", "auth")
    safety_hits = sum(term in body.lower() for term in safety_terms)
    return min(3, safety_hits), f"{safety_hits} safety boundary signals."


def score_packaging(metrics: dict) -> tuple[int, str]:
    score = 0
    if metrics["total_files"] <= 50 and metrics["symlinks"] == 0:
        score += 2
    if metrics["script_files"] == 0 or metrics["executable_scripts"] > 0:
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


def readiness_rating(total: int) -> str:
    """Map a 0-30 static package-readiness score to its advisory band."""
    if total >= 27:
        return "S"
    if total >= 21:
        return "A"
    if total >= 11:
        return "B"
    return "C"


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
    rating = readiness_rating(total)

    gaps = [
        {"category": category, "score": scores[category], "note": notes[category]}
        for category in CATEGORIES
        if scores[category] < 2
    ]

    return {
        "skill": str(path),
        "name": path.name,
        "scope": "static-package-readiness",
        "safety_gate_evaluated": False,
        "effectiveness_evaluated": False,
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
    """Compact static-readiness object for the deep audit report (Pass 3).

    Mirrors the rubric schema block: per-category 0-3 score plus an explainable
    reason, the 0-30 total, max, and the C/B/A/S readiness band. It is derived
    only from directory contents and cannot evaluate safety or effectiveness.
    """
    return {
        "scope": report["scope"],
        "safety_gate_evaluated": report["safety_gate_evaluated"],
        "effectiveness_evaluated": report["effectiveness_evaluated"],
        "total_score": report["total_score"],
        "max_score": report["max_score"],
        "rating": report["rating"],
        "advisory": True,
        "categories": report["categories"],
    }


def markdown_report(report: dict) -> str:
    lines = [
        f"# Static Skill Package Readiness: {report['name']}",
        "",
        f"Static score: {report['total_score']}/{report['max_score']} ({report['rating']})",
        "",
        "This score does not evaluate the safety gate or behavioral effectiveness.",
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
        help="Emit the compact rubric block consumed by the skill-builder deep audit Pass 3.",
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
