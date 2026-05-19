"""Discussion authority capture and closure helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from thoth.objects import ActiveExecutionLock, Store, active_work_ids, slugify, utc_now

from .store import upsert_decision, upsert_work_item


SEMANTIC_EVENT_TYPES = {
    "goal",
    "non_goal",
    "constraint",
    "decision",
    "rejected_option",
    "acceptance",
    "context",
    "risk",
    "open_question",
    "run_instruction",
}


def _normalize_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(value)[:24]}"


def _normalize_event(raw: Any, index: int, *, status: str) -> dict[str, Any] | None:
    if isinstance(raw, str):
        summary = raw.strip()
        if not summary:
            return None
        return {
            "event_id": f"event-{index + 1}",
            "event_type": "context",
            "status": status,
            "source_summary": summary,
            "normalized_summary": summary,
            "evidence_anchor": {},
            "affects": [],
        }
    if not isinstance(raw, dict):
        return None
    event_type = str(raw.get("event_type") or raw.get("type") or "context").strip()
    if event_type not in SEMANTIC_EVENT_TYPES:
        event_type = "context"
    source_summary = _normalize_string(raw.get("source_summary") or raw.get("summary") or raw.get("text"))
    normalized_summary = _normalize_string(raw.get("normalized_summary") or source_summary)
    if not source_summary and not normalized_summary:
        return None
    evidence = raw.get("evidence_anchor")
    if not isinstance(evidence, dict):
        evidence = {}
    affects = _normalize_string_list(raw.get("affects"))
    return {
        "event_id": _normalize_string(raw.get("event_id")) or f"event-{index + 1}",
        "event_type": event_type,
        "status": status,
        "source_summary": source_summary or normalized_summary,
        "normalized_summary": normalized_summary or source_summary,
        "evidence_anchor": evidence,
        "affects": affects,
    }


def _normalize_events(value: Any, *, status: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        row = _normalize_event(item, index, status=status)
        if row:
            rows.append(row)
    return rows


def normalize_authority_context(
    capsule: dict[str, Any],
    *,
    discussion_id: str | None = None,
    decision_ids: list[str] | None = None,
    status: str = "closed",
) -> dict[str, Any]:
    """Normalize user/agent discussion closure into runtime authority context."""

    source = capsule.get("authority_context") if isinstance(capsule.get("authority_context"), dict) else capsule
    completeness = source.get("completeness") if isinstance(source.get("completeness"), dict) else {}
    open_questions = _normalize_string_list(source.get("open_questions"))
    if not open_questions:
        open_questions = _normalize_string_list(source.get("unresolved_gaps"))
    events = _normalize_events(
        source.get("semantic_events") or source.get("authority_events"),
        status=status,
    )
    resolved_decision_ids = decision_ids or _normalize_string_list(source.get("source_decision_ids"))
    is_closed = bool(completeness.get("is_closed")) if "is_closed" in completeness else status == "closed"
    if open_questions:
        is_closed = False
    return {
        "schema_version": 1,
        "source_discussion_id": discussion_id or _normalize_string(source.get("source_discussion_id")),
        "source_decision_ids": resolved_decision_ids,
        "semantic_events": events,
        "goal": source.get("goal", {}),
        "non_goals": source.get("non_goals", []),
        "constraints": source.get("constraints", []),
        "accepted_decisions": source.get("accepted_decisions", []),
        "rejected_options": source.get("rejected_options", []),
        "assumptions": source.get("assumptions", []),
        "acceptance": source.get("acceptance", {}),
        "context_evidence": source.get("context_evidence", []),
        "risks": source.get("risks", []),
        "run_instructions": source.get("run_instructions", []),
        "open_questions": open_questions,
        "language": source.get("language", {}),
        "completeness": {
            "is_closed": is_closed,
            "unresolved_count": len(open_questions),
            "blocking_reasons": _normalize_string_list(completeness.get("blocking_reasons")),
        },
    }


def _discussion_payload(current: dict[str, Any]) -> dict[str, Any]:
    payload = current.get("payload") if isinstance(current.get("payload"), dict) else {}
    return dict(payload)


def checkpoint_discussion_authority(
    project_root: Path,
    *,
    discussion_id: str,
    capsule: dict[str, Any],
) -> dict[str, Any]:
    store = Store(project_root)
    current = store.read("discussion", discussion_id)
    if not current:
        raise FileNotFoundError(f"discussion:{discussion_id} not found")
    payload = _discussion_payload(current)
    context = normalize_authority_context(capsule, discussion_id=discussion_id, status="draft")
    checkpoints = payload.get("draft_checkpoints") if isinstance(payload.get("draft_checkpoints"), list) else []
    checkpoint = {
        "checkpoint_id": _stable_id("CHK", discussion_id),
        "created_at": utc_now(),
        "authority_context": context,
    }
    payload["draft_checkpoints"] = [*checkpoints, checkpoint]
    payload["authority_events"] = context["semantic_events"]
    payload["open_questions"] = context["open_questions"]
    updated = store.update(
        "discussion",
        discussion_id,
        expected_revision=int(current.get("revision", 0)),
        updates={
            "status": "inquiring",
            "summary": str(current.get("summary") or current.get("title") or discussion_id),
            "payload": payload,
        },
        history_summary="discussion authority checkpointed",
        source="discuss",
    )
    return {"discussion": updated, "checkpoint": checkpoint}


def _decision_payloads(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = capsule.get("decisions")
    if not isinstance(decisions, list):
        decisions = capsule.get("accepted_decisions")
    if not isinstance(decisions, list):
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(decisions):
        if isinstance(item, str):
            rows.append(
                {
                    "decision_id": _stable_id("DEC", item),
                    "question": item,
                    "summary": item,
                    "status": "frozen",
                    "selected_values": {"value": item},
                    "unresolved_gaps": [],
                }
            )
        elif isinstance(item, dict):
            row = dict(item)
            row.setdefault("decision_id", _stable_id("DEC", str(row.get("question") or row.get("summary") or index)))
            row.setdefault("question", row.get("summary") or row["decision_id"])
            row.setdefault("status", "frozen")
            row.setdefault("unresolved_gaps", [])
            rows.append(row)
    return rows


def _build_work_payload(capsule: dict[str, Any], authority_context: dict[str, Any], decision_ids: list[str]) -> dict[str, Any] | None:
    work = capsule.get("work_item") if isinstance(capsule.get("work_item"), dict) else {}
    if not work:
        return None
    payload = dict(work)
    payload["decisions"] = decision_ids or payload.get("decisions") or authority_context.get("source_decision_ids") or []
    payload["authority_context"] = authority_context
    payload.setdefault("missing_questions", authority_context.get("open_questions", []))
    if authority_context.get("open_questions"):
        payload["status"] = "blocked"
    return payload


def close_discussion_authority(
    project_root: Path,
    *,
    discussion_id: str,
    capsule: dict[str, Any],
) -> dict[str, Any]:
    store = Store(project_root)
    current = store.read("discussion", discussion_id)
    if not current:
        raise FileNotFoundError(f"discussion:{discussion_id} not found")

    decision_rows = [upsert_decision(project_root, payload) for payload in _decision_payloads(capsule)]
    decision_ids = [str(item.get("decision_id") or item.get("object_id")) for item in decision_rows if item.get("decision_id") or item.get("object_id")]
    authority_context = normalize_authority_context(
        capsule,
        discussion_id=discussion_id,
        decision_ids=decision_ids,
        status="closed",
    )
    work_payload = _build_work_payload(capsule, authority_context, decision_ids)
    if not work_payload:
        authority_context["open_questions"] = [
            *authority_context.get("open_questions", []),
            "closed authority requires work_item payload",
        ]
        authority_context["completeness"]["is_closed"] = False
        authority_context["completeness"]["unresolved_count"] = len(authority_context["open_questions"])

    payload = _discussion_payload(current)
    payload["closure"] = authority_context
    payload["authority_events"] = authority_context["semantic_events"]
    payload["open_questions"] = authority_context["open_questions"]
    payload["linked_decision_ids"] = decision_ids

    if authority_context["open_questions"] or not authority_context["completeness"]["is_closed"]:
        updated = store.update(
            "discussion",
            discussion_id,
            expected_revision=int(current.get("revision", 0)),
            updates={"status": "inquiring", "payload": payload},
            history_summary="discussion authority close rejected by open questions",
            source="discuss",
        )
        return {
            "status": "needs_input",
            "discussion": updated,
            "authority_context": authority_context,
            "decisions": decision_rows,
            "work_item": None,
        }

    work_id = str(work_payload.get("work_id") or work_payload.get("object_id") or "")
    if work_id and work_id in active_work_ids(project_root):
        raise ActiveExecutionLock(f"work_item:{work_id} is locked by active execution")
    work_item = upsert_work_item(project_root, work_payload)
    payload["linked_work_ids"] = [str(work_item.get("work_id") or work_item.get("object_id"))]
    links = [{"type": "decided_by", "target": f"decision:{decision_id}"} for decision_id in decision_ids if store.read("decision", decision_id)]
    updated = store.update(
        "discussion",
        discussion_id,
        expected_revision=int(current.get("revision", 0)),
        updates={
            "status": "closed",
            "summary": str(authority_context.get("goal") or current.get("summary") or current.get("title") or discussion_id),
            "links": links,
            "payload": payload,
        },
        history_summary="discussion authority closed",
        source="discuss",
    )
    return {
        "status": "ok",
        "discussion": updated,
        "authority_context": authority_context,
        "decisions": decision_rows,
        "work_item": work_item,
    }


def load_authority_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("authority JSON must be an object")
    return data
