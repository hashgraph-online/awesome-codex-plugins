#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


FAIL_EXIT_CODE = 3
SCHEMA_VERSION = 1


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    _ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    _ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def _load_pack(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"pack file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"pack file is not valid JSON: {path}: {exc}") from exc

    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unsupported schema_version in {path}: {data.get('schema_version')!r}")

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"pack file must contain a non-empty cases array: {path}")

    for idx, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"case #{idx} is not an object")
        for field in ("id", "title", "attack_prompt", "severity", "targets"):
            if not case.get(field):
                raise ValueError(f"case #{idx} missing required field: {field}")
        if case["severity"] not in {"fail", "warn"}:
            raise ValueError(f"case {case['id']} has unsupported severity: {case['severity']}")
        if not isinstance(case["targets"], list) or not case["targets"]:
            raise ValueError(f"case {case['id']} must define at least one target")
        for target in case["targets"]:
            if not isinstance(target, dict):
                raise ValueError(f"case {case['id']} contains a non-object target")
            if not target.get("globs"):
                raise ValueError(f"case {case['id']} target missing globs")
            if not target.get("require_groups") and not target.get("forbidden_any"):
                raise ValueError(
                    f"case {case['id']} target must define require_groups and/or forbidden_any",
                )
    return data


def _compile_regex(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE)


def _match_excerpt(text: str, pattern: str) -> str | None:
    match = _compile_regex(pattern).search(text)
    if not match:
        return None
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    excerpt = text[line_start:line_end].strip()
    return excerpt[:200]


def _expand_globs(repo_root: Path, patterns: list[str]) -> list[str]:
    matches: set[str] = set()
    for pattern in patterns:
        for rel in glob.glob(pattern, root_dir=str(repo_root), recursive=True):
            candidate = Path(rel)
            if (repo_root / candidate).is_file():
                matches.add(candidate.as_posix())
    return sorted(matches)


def _evaluate_file(rel_path: str, text: str, target: dict[str, Any]) -> dict[str, Any]:
    applies_if_any = target.get("applies_if_any", [])
    if applies_if_any and not any(_match_excerpt(text, pattern) for pattern in applies_if_any):
        return {
            "path": rel_path,
            "status": "SKIP",
            "missing_groups": [],
            "forbidden_matches": [],
            "evidence": [],
            "reason": "target did not meet applies_if_any conditions",
        }

    evidence: list[dict[str, str]] = []
    missing_groups: list[dict[str, Any]] = []
    for group in target.get("require_groups", []):
        label = group.get("label", "unnamed requirement")
        matched = None
        for pattern in group.get("patterns", []):
            excerpt = _match_excerpt(text, pattern)
            if excerpt:
                matched = {"label": label, "pattern": pattern, "excerpt": excerpt}
                break
        if matched:
            evidence.append(matched)
        else:
            missing_groups.append({"label": label, "patterns": group.get("patterns", [])})

    forbidden_matches: list[dict[str, str]] = []
    for pattern in target.get("forbidden_any", []):
        excerpt = _match_excerpt(text, pattern)
        if excerpt:
            forbidden_matches.append({"pattern": pattern, "excerpt": excerpt})

    status = "PASS" if not missing_groups and not forbidden_matches else "FAIL"
    return {
        "path": rel_path,
        "status": status,
        "missing_groups": missing_groups,
        "forbidden_matches": forbidden_matches,
        "evidence": evidence,
    }


def _target_label(target: dict[str, Any]) -> str:
    label = target.get("label")
    if isinstance(label, str) and label.strip():
        return label.strip()
    globs = target.get("globs", [])
    return ", ".join(globs[:2]) if globs else "unnamed target"


def _aggregate_case_status(severity: str, target_results: list[dict[str, Any]]) -> str:
    failed = any(target["status"] == "FAIL" for target in target_results)
    if failed:
        return "FAIL" if severity == "fail" else "WARN"
    warned = any(target["status"] == "WARN" for target in target_results)
    if warned:
        return "WARN"
    return "PASS"


def _evaluate_case(repo_root: Path, case: dict[str, Any]) -> dict[str, Any]:
    target_results: list[dict[str, Any]] = []
    for target in case["targets"]:
        matched_files = _expand_globs(repo_root, list(target.get("globs", [])))
        file_results: list[dict[str, Any]] = []
        if not matched_files:
            target_results.append(
                {
                    "label": _target_label(target),
                    "globs": target.get("globs", []),
                    "matched_files": [],
                    "status": "FAIL",
                    "files": [],
                    "reason": "no files matched target globs",
                },
            )
            continue

        for rel_path in matched_files:
            text = (repo_root / rel_path).read_text(encoding="utf-8", errors="ignore")
            file_results.append(_evaluate_file(rel_path, text, target))

        target_status = "PASS"
        if any(result["status"] == "FAIL" for result in file_results):
            target_status = "FAIL"
        elif any(result["status"] == "WARN" for result in file_results):
            target_status = "WARN"

        target_results.append(
            {
                "label": _target_label(target),
                "globs": target.get("globs", []),
                "matched_files": matched_files,
                "status": target_status,
                "files": file_results,
            },
        )

    case_status = _aggregate_case_status(case["severity"], target_results)
    return {
        "id": case["id"],
        "title": case["title"],
        "severity": case["severity"],
        "attack_prompt": case["attack_prompt"],
        "status": case_status,
        "targets": target_results,
    }


def _build_report(repo_root: Path, pack_path: Path, pack: dict[str, Any]) -> dict[str, Any]:
    case_results = [_evaluate_case(repo_root, case) for case in pack["cases"]]
    verdict = "PASS"
    if any(case["status"] == "FAIL" for case in case_results):
        verdict = "FAIL"
    elif any(case["status"] == "WARN" for case in case_results):
        verdict = "WARN"

    matched_files = sorted(
        {
            rel_path
            for case in case_results
            for target in case["targets"]
            for rel_path in target.get("matched_files", [])
        },
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "repo_root": str(repo_root),
        "pack_file": str(pack_path),
        "pack_name": pack.get("name", pack_path.name),
        "verdict": verdict,
        "case_count": len(case_results),
        "files_scanned": matched_files,
        "failed_cases": [case["id"] for case in case_results if case["status"] == "FAIL"],
        "warn_cases": [case["id"] for case in case_results if case["status"] == "WARN"],
        "results": case_results,
    }


def _write_report(out_dir: Path, report: dict[str, Any]) -> None:
    redteam_dir = out_dir / "redteam"
    _write_json(redteam_dir / "redteam-results.json", report)

    lines = [
        "# Prompt Redteam Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Repo root: `{report['repo_root']}`",
        f"- Pack: `{report['pack_name']}`",
        f"- Verdict: **{report['verdict']}**",
        f"- Cases: `{report['case_count']}`",
        f"- Files scanned: `{len(report['files_scanned'])}`",
        "",
        "## Case Results",
        "",
    ]

    for case in report["results"]:
        lines.extend(
            [
                f"### {case['id']} — {case['status']}",
                "",
                f"- Severity: `{case['severity']}`",
                f"- Attack: `{case['attack_prompt']}`",
            ],
        )
        for target in case["targets"]:
            lines.append(f"- Target `{target['label']}`: `{target['status']}`")
            if target.get("reason"):
                lines.append(f"  reason: {target['reason']}")
            for file_result in target.get("files", []):
                lines.append(f"  file `{file_result['path']}`: `{file_result['status']}`")
                for missing in file_result.get("missing_groups", []):
                    lines.append(f"    missing `{missing['label']}`")
                for forbidden in file_result.get("forbidden_matches", []):
                    lines.append(f"    forbidden `{forbidden['pattern']}` -> `{forbidden['excerpt']}`")
        lines.append("")

    _write_text(redteam_dir / "redteam-results.md", "\n".join(lines).rstrip() + "\n")


def scan(repo_root: Path, pack_file: Path, out_dir: Path) -> int:
    pack = _load_pack(pack_file)
    report = _build_report(repo_root, pack_file, pack)
    _write_report(out_dir, report)
    return FAIL_EXIT_CODE if report["verdict"] == "FAIL" else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="prompt_redteam.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("--repo-root", required=True, help="Repository root to scan")
    scan_parser.add_argument("--pack-file", required=True, help="JSON attack pack file")
    scan_parser.add_argument("--out-dir", required=True, help="Directory to write artifacts to")

    args = parser.parse_args()

    if args.cmd == "scan":
        repo_root = Path(args.repo_root).expanduser().resolve()
        pack_file = Path(args.pack_file).expanduser().resolve()
        out_dir = Path(args.out_dir).expanduser().resolve()
        if not repo_root.exists() or not repo_root.is_dir():
            print(f"error: repo root not found: {repo_root}", file=sys.stderr)
            return 2
        try:
            return scan(repo_root, pack_file, out_dir)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
