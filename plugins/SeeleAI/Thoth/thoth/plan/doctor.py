"""Doctor payloads and review task inference for strict project authority."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from thoth.objects import OBJECT_KINDS, Store, summarize_object_graph, validate_object_envelope

from .compiler import collect_legacy_authority_rows
from .paths import SCHEMA_VERSION, authority_root, compiler_state_path, docs_root, project_manifest_path, work_items_dir
from .store import load_work_items, load_compiler_state, utc_now


def _read_json_strict(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"invalid_json:{exc}"
    if not isinstance(payload, dict):
        return {}, "not_object"
    return payload, None


def _object_file_problems(project_root: Path) -> list[str]:
    root = authority_root(project_root)
    if not root.exists():
        return [f"missing authority root: {root}"]
    problems: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            problems.append(f"unexpected authority entry: {child.relative_to(project_root)}")
            continue
        if child.name not in OBJECT_KINDS:
            problems.append(f"unknown object kind directory: {child.relative_to(project_root)}")
            continue
        for path in sorted(child.glob("*.json")):
            payload, error = _read_json_strict(path)
            if error:
                problems.append(f"{path.relative_to(project_root)}: {error}")
                continue
            if payload.get("object_id") != path.stem:
                problems.append(f"{path.relative_to(project_root)}: object_id does not match filename")
            if payload.get("kind") != child.name:
                problems.append(f"{path.relative_to(project_root)}: kind does not match directory")
            try:
                validate_object_envelope(project_root, payload)
            except Exception as exc:
                problems.append(f"{path.relative_to(project_root)}: {exc}")
    return problems


def _summary_is_current(project_root: Path, expected_summary: dict[str, Any], expected_problems: list[str]) -> tuple[bool, str]:
    summary_path = compiler_state_path(project_root)
    payload, error = _read_json_strict(summary_path)
    if error:
        return False, f"{summary_path}: {error}"
    current_summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    current_problems = payload.get("problems") if isinstance(payload.get("problems"), list) else []
    comparable_keys = (
        "decision_counts",
        "work_item_counts",
        "legacy_authority_count",
        "active_work_count",
        "ready_work_count",
        "blocked_work_count",
    )
    mismatches: list[str] = []
    for key in comparable_keys:
        if current_summary.get(key) != expected_summary.get(key):
            mismatches.append(key)
    if sorted(str(item) for item in current_problems) != sorted(str(item) for item in expected_problems):
        mismatches.append("problems")
    if mismatches:
        return False, "stale_fields=" + ",".join(mismatches)
    return True, str(summary_path)


def build_doctor_payload(project_root: Path) -> dict[str, Any]:
    graph = summarize_object_graph(project_root, ensure_tree=False)
    legacy_rows = collect_legacy_authority_rows(project_root)
    legacy_problems = [f"legacy authority {item.get('legacy_path')}: {item.get('reason')}" for item in legacy_rows]
    object_problems = _object_file_problems(project_root)
    problems = list(graph.get("problems", [])) + legacy_problems + object_problems
    summary = dict(graph.get("summary", {}))
    summary["legacy_authority_count"] = len(legacy_rows)
    decision_counts = summary.get("decision_counts", {})
    work_counts = summary.get("work_item_counts", {})
    legacy_authority_count = int(summary.get("legacy_authority_count", 0))
    active_work_count = int(summary.get("active_work_count", 0))
    project_payload = Store(project_root).read("project", "project")
    docs_project, docs_project_error = _read_json_strict(docs_root(project_root) / "project.json")
    summary_current, summary_detail = _summary_is_current(project_root, summary, problems)
    legacy_detail = f"legacy_authority_count={legacy_authority_count}"
    if legacy_rows:
        legacy_detail += " " + "; ".join(f"{item.get('legacy_path')}:{item.get('reason')}" for item in legacy_rows[:5])

    checks = [
        {
            "id": "authority-tree",
            "ok": authority_root(project_root).is_dir(),
            "detail": str(authority_root(project_root)),
        },
        {
            "id": "project-object-present",
            "ok": bool(project_payload) and project_manifest_path(project_root).is_file(),
            "detail": str(project_manifest_path(project_root)),
        },
        {
            "id": "project-doc-view-present",
            "ok": docs_project_error is None and docs_project.get("runtime", {}).get("authority") == ".thoth/objects",
            "detail": str(docs_root(project_root) / "project.json") if docs_project_error is None else docs_project_error,
        },
        {
            "id": "required-generated-views-present",
            "ok": all((docs_root(project_root) / name).is_file() for name in ("agent-entry.md", "source-map.json", "object-graph-summary.json")),
            "detail": "agent-entry.md, source-map.json, object-graph-summary.json",
        },
        {
            "id": "object-files-valid",
            "ok": not object_problems,
            "detail": "valid" if not object_problems else "; ".join(object_problems[:5]),
        },
        {
            "id": "object-graph-summary-current",
            "ok": summary_current,
            "detail": summary_detail,
        },
        {
            "id": "no-legacy-authority",
            "ok": legacy_authority_count == 0,
            "detail": legacy_detail,
        },
        {
            "id": "no-proposed-decisions",
            "ok": int(decision_counts.get("proposed", 0)) == 0,
            "detail": f"proposed_decisions={int(decision_counts.get('proposed', 0))}",
        },
        {
            "id": "no-blocked-work-items",
            "ok": int(work_counts.get("blocked", 0)) == 0,
            "detail": f"blocked={int(work_counts.get('blocked', 0))} ready={int(work_counts.get('ready', 0))} active={active_work_count}",
        },
        {
            "id": "no-legacy-yaml-authority",
            "ok": legacy_authority_count == 0,
            "detail": f"legacy_authority_count={legacy_authority_count}",
        },
        {
            "id": "compiler-state-written",
            "ok": compiler_state_path(project_root).exists(),
            "detail": str(compiler_state_path(project_root)),
        },
        {
            "id": "work-item-authority-present",
            "ok": work_items_dir(project_root).exists(),
            "detail": f"path={work_items_dir(project_root)}",
        },
    ]
    overall_ok = all(check["ok"] for check in checks)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "project_root": str(project_root.resolve()),
        "overall_ok": overall_ok,
        "checks": checks,
        "compiler": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": graph.get("generated_at"),
            "summary": summary,
            "blocked_work_ids": graph.get("blocked_work_ids", []),
            "invalid_work_ids": graph.get("invalid_work_ids", []),
            "problems": problems,
        },
        "summary": {
            "decision_counts": decision_counts,
            "work_item_counts": work_counts,
            "legacy_authority_count": legacy_authority_count,
            "active_work_count": active_work_count,
        },
    }


def render_doctor_text(payload: dict[str, Any]) -> str:
    lines = ["Thoth Doctor", ""]
    lines.append(f"Project: {payload.get('project_root')}")
    lines.append(f"Overall: {'PASS' if payload.get('overall_ok') else 'FAIL'}")
    lines.append("")
    lines.append("Checks:")
    for check in payload.get("checks", []):
        marker = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {marker} {check.get('id')}: {check.get('detail')}")
    compiler = payload.get("compiler", {})
    summary = compiler.get("summary", {})
    lines.append("")
    lines.append("Compiler Summary:")
    decision_counts = summary.get("decision_counts", {})
    work_counts = summary.get("work_item_counts", {})
    lines.append(
        "  decisions proposed={proposed} accepted={accepted} superseded={superseded}".format(
            proposed=int(decision_counts.get("proposed", 0)),
            accepted=int(decision_counts.get("accepted", 0)),
            superseded=int(decision_counts.get("superseded", 0)),
        )
    )
    lines.append(
        "  work ready={ready} blocked={blocked} active={active} validated={validated} total={total}".format(
            ready=int(work_counts.get("ready", 0)),
            blocked=int(work_counts.get("blocked", 0)),
            active=int(work_counts.get("active", 0)),
            validated=int(work_counts.get("validated", 0)),
            total=int(work_counts.get("total", 0)),
        )
    )
    lines.append(f"  legacy_authority_count={int(summary.get('legacy_authority_count', 0))}")
    problems = compiler.get("problems", [])
    if problems:
        lines.append("")
        lines.append("Problems:")
        for item in problems[:20]:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def compiler_summary(project_root: Path) -> dict[str, Any]:
    compiler = load_compiler_state(project_root)
    return compiler.get("summary", {}) if isinstance(compiler, dict) else {}


def infer_review_work_id(project_root: Path, target: str) -> str | None:
    normalized = target.strip()
    if not normalized:
        return None
    for task in load_work_items(project_root):
        binding = task.get("review_binding")
        if not isinstance(binding, dict):
            continue
        candidate = binding.get("target")
        if isinstance(candidate, str) and candidate.strip() == normalized:
            work_id = task.get("work_id")
            if isinstance(work_id, str) and work_id:
                return work_id
    return None
