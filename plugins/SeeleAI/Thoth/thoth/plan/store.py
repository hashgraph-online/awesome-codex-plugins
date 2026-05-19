"""Planning helpers backed by the canonical Thoth object store.

The durable planning authority is `.thoth/objects`. This module exposes
work-item and work-result helpers without reintroducing legacy contract/task
authority names.
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from thoth.objects import (
    Store,
    flatten_work_item,
    slugify,
    utc_now,
    work_item_from_payload,
)
from .paths import (
    SCHEMA_VERSION,
    WORK_RESULT_SUFFIX,
    authority_root,
    compiler_state_path,
    contracts_dir,
    decisions_dir,
    legacy_audit_path,
    project_manifest_path,
    work_result_path,
    work_items_dir,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _iter_json_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(candidate for candidate in path.glob("*.json") if candidate.is_file())


def _iter_work_item_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    return sorted(
        candidate
        for candidate in path.glob("*.json")
        if candidate.is_file() and not candidate.name.endswith(WORK_RESULT_SUFFIX)
    )


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "item"


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def _iter_work_result_files(project_root: Path) -> list[Path]:
    result_dir = work_result_path(project_root, ".keep").parent
    if not result_dir.is_dir():
        return []
    return sorted(
        candidate
        for candidate in result_dir.glob(f"*{WORK_RESULT_SUFFIX}")
        if candidate.is_file()
    )


def load_project_manifest(project_root: Path) -> dict[str, Any]:
    payload = Store(project_root).read("project", "project")
    if payload:
        project_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        if "project" in project_payload or "dashboard" in project_payload:
            return project_payload
    docs_manifest = project_root / ".thoth" / "docs" / "project.json"
    return _read_json(docs_manifest)


def ensure_work_authority_tree(project_root: Path) -> None:
    Store(project_root).ensure_tree()
    compiler_state_path(project_root).parent.mkdir(parents=True, exist_ok=True)
    work_result_path(project_root, ".keep").parent.mkdir(parents=True, exist_ok=True)
    if not compiler_state_path(project_root).exists():
        _write_json(
            compiler_state_path(project_root),
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at": utc_now(),
                "summary": {
                    "decision_counts": {"proposed": 0, "accepted": 0, "superseded": 0},
                    "work_item_counts": {
                        "ready": 0,
                        "blocked": 0,
                        "draft": 0,
                        "active": 0,
                        "validated": 0,
                        "failed": 0,
                        "abandoned": 0,
                        "total": 0,
                    },
                    "ready_work_count": 0,
                    "blocked_work_count": 0,
                    "active_work_count": 0,
                },
                "blocked_work_ids": [],
                "invalid_work_ids": [],
                "problems": [],
            },
        )
    if not legacy_audit_path(project_root).exists():
        _write_json(
            legacy_audit_path(project_root),
            {
                "schema_version": SCHEMA_VERSION,
                "generated_at": utc_now(),
                "legacy_tasks": [],
                "summary": {"total": 0, "invalid": 0},
            },
        )


def load_decisions(project_root: Path) -> list[dict[str, Any]]:
    return Store(project_root).list("decision")


def load_work_items(project_root: Path) -> list[dict[str, Any]]:
    return [flatten_work_item(work) for work in Store(project_root).list("work_item")]


def load_work_results(project_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in _iter_work_result_files(project_root):
        payload = _read_json(path)
        if payload:
            payload.setdefault("_path", str(path))
            rows.append(payload)
    return rows


def load_work_result_map(project_root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for payload in load_work_results(project_root):
        work_id = payload.get("work_id")
        if isinstance(work_id, str) and work_id and work_id not in rows:
            rows[work_id] = payload
    return rows


def load_work_result(project_root: Path, work_id: str) -> dict[str, Any]:
    return _read_json(work_result_path(project_root, work_id))


def load_compiler_state(project_root: Path) -> dict[str, Any]:
    ensure_work_authority_tree(project_root)
    return _read_json(compiler_state_path(project_root))


def _default_work_result(work_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "work_result",
        "work_id": work_id,
        "status": "idle",
        "source": "none",
        "usable": None,
        "meets_goal": None,
        "failure_class": None,
        "reasons": [],
        "conclusion": None,
        "current_summary": None,
        "evidence_paths": [],
        "recent_evidence": [],
        "recent_run_refs": [],
        "metrics": {},
        "latest_run": {},
        "latest_review": {},
        "last_attempt_at": None,
        "updated_at": None,
        "last_closure_at": None,
    }


def _normalize_work_result(work_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = _default_work_result(work_id)
    result.update(payload)
    result["schema_version"] = SCHEMA_VERSION
    result["kind"] = "work_result"
    result["work_id"] = work_id
    result["reasons"] = _normalize_string_list(result.get("reasons"))
    evidence_paths = result.get("evidence_paths")
    if not isinstance(evidence_paths, list):
        result["evidence_paths"] = []
    recent_evidence = result.get("recent_evidence")
    if not isinstance(recent_evidence, list):
        result["recent_evidence"] = []
    recent_run_refs = result.get("recent_run_refs")
    if not isinstance(recent_run_refs, list):
        result["recent_run_refs"] = []
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        result["metrics"] = {}
    if not isinstance(result.get("latest_run"), dict):
        result["latest_run"] = {}
    if not isinstance(result.get("latest_review"), dict):
        result["latest_review"] = {}
    if result.get("current_summary") in ("", []):
        result["current_summary"] = None
    return result


def upsert_work_result(project_root: Path, work_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_work_authority_tree(project_root)
    result = _normalize_work_result(work_id, payload)
    _write_json(work_result_path(project_root, work_id), result)
    return result


def _remove_stale_work_results(project_root: Path, active_work_ids: set[str]) -> None:
    for path in _iter_work_result_files(project_root):
        payload = _read_json(path)
        work_id = payload.get("work_id")
        if not isinstance(work_id, str) or work_id not in active_work_ids:
            path.unlink()


def load_work_for_execution(project_root: Path, work_id: str, *, require_ready: bool = True) -> dict[str, Any]:
    from .compiler import compile_task_authority

    compile_task_authority(project_root)
    payload = Store(project_root).read("work_item", work_id)
    if not payload:
        raise FileNotFoundError(f"Work item {work_id} not found in .thoth/objects/work_item")
    payload = flatten_work_item(payload)
    ready_state = payload.get("ready_state")
    if require_ready and ready_state != "ready":
        reason = payload.get("blocking_reason") or f"task is {ready_state}"
        raise ValueError(f"Work item {work_id} is not executable: {reason}")
    if require_ready and payload.get("runnable") is not True:
        raise ValueError(f"Work item {work_id} is not executable: work item is non-runnable")
    return payload


def _tokenize_work_query(value: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9]+", value.lower()) if token]


def _work_search_text(work: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in (
        "work_id",
        "title",
        "goal_statement",
        "module",
        "direction",
        "candidate_method_id",
        "blocking_reason",
    ):
        value = work.get(field)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    for field in ("decision_ids", "failure_classes", "baseline_ids"):
        values = work.get(field)
        if isinstance(values, list):
            parts.extend(str(item).strip() for item in values if isinstance(item, str) and item.strip())
    return " ".join(parts)


def suggest_work_items_for_query(project_root: Path, query: str, *, limit: int = 3) -> list[dict[str, Any]]:
    from .compiler import compile_task_authority

    compile_task_authority(project_root)
    work_items = load_work_items(project_root)
    normalized_query = " ".join(query.strip().lower().split())
    query_tokens = _tokenize_work_query(normalized_query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for work in work_items:
        ready_state = str(work.get("ready_state") or "")
        runnable = work.get("runnable") is True
        text = _work_search_text(work)
        haystack = text.lower()
        text_tokens = set(_tokenize_work_query(text))
        score = 0.0
        if ready_state == "ready":
            score += 3.0
        elif runnable:
            score += 1.5
        if normalized_query:
            if normalized_query in haystack:
                score += 8.0
            for token in query_tokens:
                if token in text_tokens:
                    score += 3.0
                elif token in haystack:
                    score += 1.0
        scored.append((score, work))
    scored.sort(
        key=lambda item: (
            item[0],
            1 if str(item[1].get("ready_state") or "") == "ready" else 0,
            1 if item[1].get("runnable") is True else 0,
            str(item[1].get("title") or ""),
            str(item[1].get("work_id") or ""),
        ),
        reverse=True,
    )
    picks = [work for _score, work in scored[: max(0, limit)]]
    return [
        {
            "work_id": str(work.get("work_id") or ""),
            "title": str(work.get("title") or work.get("work_id") or ""),
            "ready_state": str(work.get("ready_state") or ""),
            "module": str(work.get("module") or ""),
            "direction": str(work.get("direction") or ""),
            "goal_statement": str(work.get("goal_statement") or ""),
        }
        for work in picks
        if str(work.get("work_id") or "").strip()
    ]


def upsert_decision(project_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    store = Store(project_root)
    store.ensure_tree()
    decision_id = payload.get("object_id") or payload.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id.strip():
        question = payload.get("question") if isinstance(payload.get("question"), str) else "discussion"
        decision_id = f"DEC-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(question)[:24]}"
        payload["decision_id"] = decision_id
    status = str(payload.get("status") or "proposed")
    if status == "frozen":
        status = "accepted"
    if status == "open":
        status = "proposed"
    if status not in {"proposed", "accepted", "superseded"}:
        status = "proposed"
    title = str(payload.get("title") or payload.get("question") or decision_id)
    summary = str(payload.get("summary") or payload.get("question") or title)
    obj = store.upsert(
        kind="decision",
        object_id=decision_id,
        status=status,
        title=title,
        summary=summary,
        source=str(payload.get("source") or "discuss"),
        payload={
            "question": payload.get("question") or title,
            "selected_values": payload.get("selected_values", {}),
            "candidate_method_ids": payload.get("candidate_method_ids", []),
            "unresolved_gaps": payload.get("unresolved_gaps", []),
            "raw": payload,
        },
    )
    flattened = dict(payload)
    flattened.update(
        {
            "schema_version": SCHEMA_VERSION,
            "kind": "decision",
            "decision_id": obj["object_id"],
            "object_id": obj["object_id"],
            "status": "frozen" if obj["status"] == "accepted" else "open",
            "created_at": obj["created_at"],
            "updated_at": obj["updated_at"],
            "_path": str(store.path("decision", obj["object_id"])),
        }
    )
    return flattened


def upsert_work_item(project_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    store = Store(project_root)
    store.ensure_tree()
    work_id, status, work_payload = work_item_from_payload(payload)
    links = [
        {"type": "decided_by", "target": f"decision:{decision_id}"}
        for decision_id in _normalize_string_list(payload.get("decisions"))
        if store.read("decision", decision_id)
    ]
    authority_context = payload.get("authority_context") if isinstance(payload.get("authority_context"), dict) else {}
    source_discussion_id = authority_context.get("source_discussion_id")
    if isinstance(source_discussion_id, str) and source_discussion_id.strip() and store.read("discussion", source_discussion_id):
        links.append({"type": "primary_parent", "target": f"discussion:{source_discussion_id}"})
    obj = store.upsert(
        kind="work_item",
        object_id=work_id,
        status=status,
        title=str(payload.get("title") or work_id),
        summary=str(payload.get("goal") or payload.get("title") or work_id),
        source=str(payload.get("source_kind") or "discuss"),
        links=links,
        payload=work_payload,
        history_summary=f"upserted work_item {work_id}",
    )
    flattened = dict(payload)
    flattened.update(flatten_work_item(obj))
    return flattened


def create_discussion_placeholder(project_root: Path, content: str, *, host: str = "codex") -> dict[str, Any]:
    summary = content.strip() or "discussion"
    store = Store(project_root)
    store.ensure_tree()
    discussion_id = f"DISC-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(summary)[:24]}"
    obj = store.create(
        kind="discussion",
        object_id=discussion_id,
        status="inquiring",
        title=summary,
        summary=summary,
        source=f"discuss:{host}",
        payload={
            "messages": [{"role": "user", "content": content, "created_at": utc_now()}],
            "facts": [],
            "constraints": [],
            "decisions": [],
            "open_questions": [
                "candidate method universe not frozen",
                "execution plan not closed",
                "eval contract not closed",
            ],
            "closure_summary": None,
        },
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "discussion",
        "discussion_id": obj["object_id"],
        "object_id": obj["object_id"],
        "status": obj["status"],
        "question": summary,
        "unresolved_gaps": obj["payload"]["open_questions"],
        "_path": str(store.path("discussion", obj["object_id"])),
    }
