"""Canonical Thoth object graph store.

This module is the only writer for durable `.thoth/objects` authority files.
Command handlers, run services, tests, and read models should call `Store`
instead of writing object JSON directly.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = 1

OBJECT_KINDS = {
    "project",
    "discussion",
    "decision",
    "work_item",
    "controller",
    "run",
    "phase_result",
    "artifact",
    "doc_view",
}

LINK_TYPES = {
    "primary_parent",
    "depends_on",
    "blocks",
    "decided_by",
    "spawned_by",
    "produced_by",
    "evidence_for",
    "supersedes",
}

ACTIVE_EXECUTION_STATUSES = {"queued", "running", "paused", "waiting_input", "stopping"}
TERMINAL_EXECUTION_STATUSES = {"completed", "failed", "stopped", "validated", "budget_exhausted"}

DISCUSSION_STATUSES = {"inquiring", "closed", "blocked_by_active_execution"}
DECISION_STATUSES = {"proposed", "accepted", "superseded"}
WORK_ITEM_STATUSES = {"draft", "blocked", "ready", "active", "validated", "failed", "abandoned"}
CONTROLLER_STATUSES = ACTIVE_EXECUTION_STATUSES | TERMINAL_EXECUTION_STATUSES
RUN_STATUSES = ACTIVE_EXECUTION_STATUSES | TERMINAL_EXECUTION_STATUSES
PHASE_RESULT_STATUSES = {"pending", "completed", "failed"}
ARTIFACT_STATUSES = {"available", "missing", "superseded"}
DOC_VIEW_STATUSES = {"generated", "stale"}
PROJECT_STATUSES = {"active", "archived"}

STATUS_BY_KIND = {
    "project": PROJECT_STATUSES,
    "discussion": DISCUSSION_STATUSES,
    "decision": DECISION_STATUSES,
    "work_item": WORK_ITEM_STATUSES,
    "controller": CONTROLLER_STATUSES,
    "run": RUN_STATUSES,
    "phase_result": PHASE_RESULT_STATUSES,
    "artifact": ARTIFACT_STATUSES,
    "doc_view": DOC_VIEW_STATUSES,
}

REQUIRED_WORK_PAYLOAD_FIELDS = (
    "goal",
    "context",
    "constraints",
    "execution_plan",
    "eval_contract",
    "runtime_policy",
    "decisions",
)


def default_authority_context(payload: dict[str, Any], *, decision_ids: list[str] | None = None) -> dict[str, Any]:
    """Build a closed, compact authority context for direct work-item payloads."""

    decisions = decision_ids if decision_ids is not None else _normalize_string_list(payload.get("decisions"))
    goal = payload.get("goal") or ""
    constraints = payload.get("constraints") if isinstance(payload.get("constraints"), list) else []
    execution_plan = payload.get("execution_plan") if isinstance(payload.get("execution_plan"), list) else []
    eval_contract = payload.get("eval_contract") if isinstance(payload.get("eval_contract"), dict) else {}
    return {
        "schema_version": 1,
        "source_discussion_id": "",
        "source_decision_ids": decisions,
        "semantic_events": [],
        "goal": {"source_summary": goal, "normalized_summary": goal},
        "non_goals": [],
        "constraints": constraints,
        "accepted_decisions": decisions,
        "rejected_options": [],
        "assumptions": [],
        "acceptance": {
            "source_summary": eval_contract.get("entrypoint", {}).get("command", "") if isinstance(eval_contract.get("entrypoint"), dict) else "",
            "normalized_summary": eval_contract.get("primary_metric", {}),
        },
        "context_evidence": [],
        "risks": [],
        "run_instructions": execution_plan,
        "open_questions": [],
        "language": {"source": "unspecified", "runtime": "normalized"},
        "completeness": {"is_closed": True, "unresolved_count": 0, "blocking_reasons": []},
    }


def normalize_scheduling(value: Any) -> dict[str, Any]:
    scheduling = value if isinstance(value, dict) else {}
    priority = scheduling.get("priority")
    if not isinstance(priority, int):
        priority = 0
    order = scheduling.get("order")
    if order is not None and not isinstance(order, int):
        order = None
    estimated_minutes = scheduling.get("estimated_minutes")
    if estimated_minutes is not None and (
        not isinstance(estimated_minutes, int) or estimated_minutes <= 0
    ):
        estimated_minutes = None
    return {
        "priority": priority,
        "order": order,
        "estimated_minutes": estimated_minutes,
    }


class StoreError(RuntimeError):
    """Base class for canonical store failures."""


class SchemaError(StoreError):
    """Raised when an object violates the canonical schema."""


class RevisionConflict(StoreError):
    """Raised when optimistic revision checks fail."""


class ActiveExecutionLock(StoreError):
    """Raised when a mutation targets active execution-owned work."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return normalized or "item"


def objects_root(project_root: Path) -> Path:
    return project_root / ".thoth" / "objects"


def docs_root(project_root: Path) -> Path:
    return project_root / ".thoth" / "docs"


def object_path(project_root: Path, kind: str, object_id: str) -> Path:
    return objects_root(project_root) / kind / f"{object_id}.json"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _normalize_links(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    links: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        link_type = item.get("type")
        target = item.get("target")
        if isinstance(link_type, str) and isinstance(target, str) and link_type in LINK_TYPES and target.strip():
            links.append({"type": link_type, "target": target.strip()})
    return links


def _normalize_history(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    history: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            history.append(dict(item))
    return history


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _active_status(value: Any) -> bool:
    return isinstance(value, str) and value in ACTIVE_EXECUTION_STATUSES


def _object_ref(kind: str, object_id: str) -> str:
    return f"{kind}:{object_id}"


def parse_object_ref(value: str) -> tuple[str, str] | None:
    if ":" not in value:
        return None
    kind, object_id = value.split(":", 1)
    if kind not in OBJECT_KINDS or not object_id:
        return None
    return kind, object_id


def active_work_ids(project_root: Path) -> set[str]:
    locked: set[str] = set()
    store = Store(project_root)
    for kind in ("run", "controller"):
        for item in store.list(kind):
            if not _active_status(item.get("status")):
                continue
            payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
            work_id = payload.get("work_id")
            if isinstance(work_id, str) and work_id:
                locked.add(work_id)
    return locked


def work_item_ready_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "task_id" in payload:
        errors.append("task_id is legacy current-authority shape; run thoth init --migrate apply")
    if "work_type" in payload:
        errors.append("work_type is legacy current-authority shape; use work_kind")
    work_kind = payload.get("work_kind")
    runnable = payload.get("runnable")
    if work_kind not in {"execution", "milestone"}:
        errors.append("work_kind must be execution or milestone")
    if not isinstance(runnable, bool):
        errors.append("runnable must be boolean")
    if runnable is True and work_kind != "execution":
        errors.append("only execution work_items may be runnable")
    missing_questions = payload.get("missing_questions")
    if missing_questions is None:
        missing_questions = []
    if not isinstance(missing_questions, list):
        errors.append("missing_questions must be a list")
    elif any(isinstance(item, str) and item.strip() for item in missing_questions):
        errors.append("ready runnable work_item requires missing_questions=[]")
    if runnable is True:
        for field in REQUIRED_WORK_PAYLOAD_FIELDS:
            value = payload.get(field)
            if value in (None, "", [], {}):
                errors.append(f"runnable work_item requires {field}")
        execution_plan = payload.get("execution_plan")
        if not isinstance(execution_plan, list) or not execution_plan:
            errors.append("execution_plan must be a non-empty list")
        eval_contract = payload.get("eval_contract")
        if not isinstance(eval_contract, dict):
            errors.append("eval_contract must be an object")
        else:
            entrypoint = eval_contract.get("entrypoint")
            metric = eval_contract.get("primary_metric")
            validate_schema = eval_contract.get("validate_output_schema")
            if not isinstance(entrypoint, dict) or not isinstance(entrypoint.get("command"), str) or not entrypoint.get("command", "").strip():
                errors.append("eval_contract.entrypoint.command is required")
            if not isinstance(metric, dict) or not all(metric.get(key) not in (None, "", []) for key in ("name", "direction", "threshold")):
                errors.append("eval_contract.primary_metric requires name/direction/threshold")
            if not isinstance(validate_schema, dict) or validate_schema.get("type") != "object":
                errors.append("eval_contract.validate_output_schema.type must be object")
        runtime_policy = payload.get("runtime_policy")
        if not isinstance(runtime_policy, dict):
            errors.append("runtime_policy must be an object")
        authority_context = payload.get("authority_context")
        if authority_context is not None:
            if not isinstance(authority_context, dict):
                errors.append("authority_context must be an object")
            else:
                completeness = authority_context.get("completeness") if isinstance(authority_context.get("completeness"), dict) else {}
                if completeness.get("is_closed") is not True:
                    errors.append("authority_context.completeness.is_closed must be true")
                open_questions = authority_context.get("open_questions")
                if not isinstance(open_questions, list):
                    errors.append("authority_context.open_questions must be a list")
                elif any(isinstance(item, str) and item.strip() for item in open_questions):
                    errors.append("ready runnable work_item requires authority_context.open_questions=[]")
    return errors


def validate_object_envelope(project_root: Path, obj: dict[str, Any], *, check_links: bool = True) -> None:
    kind = obj.get("kind")
    if kind not in OBJECT_KINDS:
        raise SchemaError(f"invalid object kind: {kind}")
    object_id = obj.get("object_id")
    if not isinstance(object_id, str) or not object_id.strip():
        raise SchemaError("missing object_id")
    if obj.get("schema_version") != SCHEMA_VERSION:
        raise SchemaError(f"invalid schema_version for {object_id}")
    status = obj.get("status")
    if status not in STATUS_BY_KIND[kind]:
        raise SchemaError(f"invalid {kind} status: {status}")
    if not isinstance(obj.get("revision"), int) or int(obj["revision"]) < 1:
        raise SchemaError("revision must be a positive integer")
    for field in ("title", "summary", "created_at", "updated_at", "source"):
        if not isinstance(obj.get(field), str):
            raise SchemaError(f"{field} must be a string")
    if not isinstance(obj.get("payload"), dict):
        raise SchemaError("payload must be an object")
    if not isinstance(obj.get("history"), list):
        raise SchemaError("history must be a list")
    links = _normalize_links(obj.get("links"))
    if len(links) != len(obj.get("links", [])):
        raise SchemaError("links must be typed object references")
    if check_links:
        for link in links:
            parsed = parse_object_ref(link["target"])
            if parsed is None:
                raise SchemaError(f"invalid link target: {link['target']}")
            target_kind, target_id = parsed
            if target_kind == kind and target_id == object_id:
                raise SchemaError("object cannot link to itself")
            if not object_path(project_root, target_kind, target_id).exists():
                raise SchemaError(f"unknown link target: {link['target']}")
    if kind == "work_item":
        payload = obj["payload"]
        ready_errors = work_item_ready_errors(payload)
        if obj.get("status") == "ready":
            for error in ready_errors:
                raise SchemaError(error)
            if payload.get("runnable") is not True:
                raise SchemaError("ready work_item must be runnable")
        if obj.get("status") == "active" and payload.get("runnable") is not True:
            raise SchemaError("active work_item must be runnable")


@dataclass
class Store:
    project_root: Path

    @property
    def root(self) -> Path:
        return objects_root(self.project_root)

    def ensure_tree(self) -> None:
        for kind in OBJECT_KINDS:
            (self.root / kind).mkdir(parents=True, exist_ok=True)
        docs_root(self.project_root).mkdir(parents=True, exist_ok=True)

    def path(self, kind: str, object_id: str) -> Path:
        if kind not in OBJECT_KINDS:
            raise SchemaError(f"invalid object kind: {kind}")
        return object_path(self.project_root, kind, object_id)

    def read(self, kind: str, object_id: str) -> dict[str, Any]:
        return _read_json(self.path(kind, object_id))

    def list(self, kind: str) -> list[dict[str, Any]]:
        if kind not in OBJECT_KINDS:
            raise SchemaError(f"invalid object kind: {kind}")
        path = self.root / kind
        if not path.is_dir():
            return []
        rows: list[dict[str, Any]] = []
        for candidate in sorted(path.glob("*.json")):
            payload = _read_json(candidate)
            if payload:
                payload.setdefault("_path", str(candidate))
                rows.append(payload)
        return rows

    def create(
        self,
        *,
        kind: str,
        object_id: str,
        status: str,
        title: str,
        summary: str = "",
        source: str = "thoth",
        links: list[dict[str, str]] | None = None,
        payload: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.ensure_tree()
        if self.path(kind, object_id).exists():
            raise RevisionConflict(f"{kind}:{object_id} already exists")
        now = utc_now()
        obj = {
            "schema_version": SCHEMA_VERSION,
            "object_id": object_id,
            "kind": kind,
            "status": status,
            "title": title,
            "summary": summary,
            "revision": 1,
            "created_at": now,
            "updated_at": now,
            "source": source,
            "links": _normalize_links(links or []),
            "payload": payload or {},
            "history": history or [
                {
                    "revision": 1,
                    "at": now,
                    "summary": "object created",
                    "source": source,
                    "changed_fields": ["*"],
                }
            ],
        }
        validate_object_envelope(self.project_root, obj)
        _write_json_atomic(self.path(kind, object_id), obj)
        return obj

    def upsert(
        self,
        *,
        kind: str,
        object_id: str,
        status: str,
        title: str,
        summary: str = "",
        source: str = "thoth",
        links: list[dict[str, str]] | None = None,
        payload: dict[str, Any] | None = None,
        history_summary: str = "object upserted",
    ) -> dict[str, Any]:
        current = self.read(kind, object_id)
        if not current:
            return self.create(
                kind=kind,
                object_id=object_id,
                status=status,
                title=title,
                summary=summary,
                source=source,
                links=links,
                payload=payload,
            )
        return self.update(
            kind,
            object_id,
            expected_revision=int(current.get("revision", 0)),
            updates={
                "status": status,
                "title": title,
                "summary": summary,
                "source": source,
                "links": _normalize_links(links or []),
                "payload": payload or {},
            },
            history_summary=history_summary,
            source=source,
        )

    def update(
        self,
        kind: str,
        object_id: str,
        *,
        expected_revision: int | None = None,
        updates: dict[str, Any],
        history_summary: str,
        source: str = "thoth",
    ) -> dict[str, Any]:
        self.ensure_tree()
        current = self.read(kind, object_id)
        if not current:
            raise FileNotFoundError(f"{kind}:{object_id} not found")
        if expected_revision is not None and int(current.get("revision", 0)) != expected_revision:
            raise RevisionConflict(f"{kind}:{object_id} revision conflict")
        if kind == "work_item" and object_id in active_work_ids(self.project_root):
            raise ActiveExecutionLock(f"work_item:{object_id} is locked by active execution")
        mutable = dict(current)
        changed_fields = sorted(str(key) for key in updates)
        mutable.update(updates)
        mutable["revision"] = int(current.get("revision", 0)) + 1
        mutable["updated_at"] = utc_now()
        mutable["links"] = _normalize_links(mutable.get("links"))
        mutable["history"] = _normalize_history(mutable.get("history"))
        mutable["history"].append(
            {
                "revision": mutable["revision"],
                "at": mutable["updated_at"],
                "summary": history_summary,
                "source": source,
                "changed_fields": changed_fields,
            }
        )
        validate_object_envelope(self.project_root, mutable)
        _write_json_atomic(self.path(kind, object_id), mutable)
        return mutable

    def tombstone(
        self,
        kind: str,
        object_id: str,
        *,
        expected_revision: int | None = None,
        reason: str = "tombstoned",
    ) -> dict[str, Any]:
        terminal_status = {
            "work_item": "abandoned",
            "decision": "superseded",
            "discussion": "blocked_by_active_execution",
            "controller": "stopped",
            "run": "stopped",
            "artifact": "superseded",
            "doc_view": "stale",
            "project": "archived",
            "phase_result": "failed",
        }[kind]
        return self.update(
            kind,
            object_id,
            expected_revision=expected_revision,
            updates={"status": terminal_status},
            history_summary=reason,
        )

    def link(self, source_kind: str, source_id: str, *, link_type: str, target_kind: str, target_id: str) -> dict[str, Any]:
        if link_type not in LINK_TYPES:
            raise SchemaError(f"invalid link type: {link_type}")
        current = self.read(source_kind, source_id)
        if not current:
            raise FileNotFoundError(f"{source_kind}:{source_id} not found")
        target_ref = _object_ref(target_kind, target_id)
        if not self.read(target_kind, target_id):
            raise SchemaError(f"unknown link target: {target_ref}")
        links = _normalize_links(current.get("links"))
        next_link = {"type": link_type, "target": target_ref}
        if next_link not in links:
            links.append(next_link)
        return self.update(
            source_kind,
            source_id,
            expected_revision=int(current.get("revision", 0)),
            updates={"links": links},
            history_summary=f"linked {link_type} {target_ref}",
        )

    def unlink(self, source_kind: str, source_id: str, *, link_type: str, target_kind: str, target_id: str) -> dict[str, Any]:
        current = self.read(source_kind, source_id)
        if not current:
            raise FileNotFoundError(f"{source_kind}:{source_id} not found")
        target_ref = _object_ref(target_kind, target_id)
        links = [
            link
            for link in _normalize_links(current.get("links"))
            if not (link["type"] == link_type and link["target"] == target_ref)
        ]
        return self.update(
            source_kind,
            source_id,
            expected_revision=int(current.get("revision", 0)),
            updates={"links": links},
            history_summary=f"unlinked {link_type} {target_ref}",
        )

    def children(self, parent_kind: str, parent_id: str) -> list[dict[str, Any]]:
        target_ref = _object_ref(parent_kind, parent_id)
        rows: list[dict[str, Any]] = []
        for kind in OBJECT_KINDS:
            for item in self.list(kind):
                if any(link.get("type") == "primary_parent" and link.get("target") == target_ref for link in _normalize_links(item.get("links"))):
                    rows.append(item)
        return rows

    def dependencies(self, kind: str, object_id: str) -> list[dict[str, Any]]:
        item = self.read(kind, object_id)
        rows: list[dict[str, Any]] = []
        for link in _normalize_links(item.get("links")):
            if link["type"] != "depends_on":
                continue
            parsed = parse_object_ref(link["target"])
            if parsed is None:
                continue
            target_kind, target_id = parsed
            target = self.read(target_kind, target_id)
            if target:
                rows.append(target)
        return rows

    def evidence(self, kind: str, object_id: str) -> list[dict[str, Any]]:
        target_ref = _object_ref(kind, object_id)
        rows: list[dict[str, Any]] = []
        for artifact in self.list("artifact"):
            if any(link.get("type") == "evidence_for" and link.get("target") == target_ref for link in _normalize_links(artifact.get("links"))):
                rows.append(artifact)
        return rows


def flatten_work_item(obj: dict[str, Any]) -> dict[str, Any]:
    payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
    eval_contract = payload.get("eval_contract") if isinstance(payload.get("eval_contract"), dict) else {}
    runtime_policy = payload.get("runtime_policy") if isinstance(payload.get("runtime_policy"), dict) else {}
    scheduling = normalize_scheduling(payload.get("scheduling"))
    work_id = str(obj.get("object_id") or "")
    flattened = {
        "schema_version": obj.get("schema_version"),
        "kind": "work_item",
        "work_id": work_id,
        "id": work_id,
        "title": obj.get("title", work_id),
        "summary": obj.get("summary", ""),
        "status": obj.get("status"),
        "revision": obj.get("revision"),
        "ready_state": obj.get("status"),
        "runnable": payload.get("runnable") is True,
        "work_kind": payload.get("work_kind"),
        "goal_statement": payload.get("goal"),
        "context": payload.get("context"),
        "constraints": payload.get("constraints", []),
        "implementation_recipe": payload.get("execution_plan", []),
        "eval_entrypoint": eval_contract.get("entrypoint", {}),
        "primary_metric": eval_contract.get("primary_metric", {}),
        "failure_classes": eval_contract.get("failure_classes", []),
        "validate_output_schema": eval_contract.get("validate_output_schema", {}),
        "runtime_contract": runtime_policy,
        "scheduling": scheduling,
        "priority": scheduling["priority"],
        "review_binding": eval_contract.get("review_binding", {}),
        "review_expectation": eval_contract.get("review_expectation"),
        "decision_ids": payload.get("decisions", []),
        "authority_context": payload.get("authority_context", {}),
        "links": obj.get("links", []),
        "created_at": obj.get("created_at"),
        "updated_at": obj.get("updated_at"),
        "_path": obj.get("_path"),
    }
    missing = work_item_ready_errors(payload)
    flattened["blocking_reason"] = "; ".join(missing)
    return flattened


LEGACY_WORK_JSON_FIELDS = {
    "contract_id",
    "task_id",
    "work_type",
    "decision_ids",
    "goal_statement",
    "implementation_recipe",
    "eval_entrypoint",
    "primary_metric",
    "failure_classes",
    "validate_output_schema",
    "runtime_contract",
    "blocking_gaps",
}


def work_item_from_payload(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    legacy_fields = sorted(field for field in LEGACY_WORK_JSON_FIELDS if field in payload)
    if legacy_fields or payload.get("status") == "frozen":
        raise SchemaError(
            "work-json must use work_item semantics; legacy contract/task fields are not accepted: "
            + ", ".join(legacy_fields or ["status=frozen"])
        )
    work_id = str(payload.get("work_id") or payload.get("object_id") or "").strip()
    if not work_id:
        work_id = f"work-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(str(payload.get('title') or 'work'))[:24]}"
    title = str(payload.get("title") or work_id)
    status = str(payload.get("status") or "").strip()
    missing_questions = _normalize_string_list(payload.get("missing_questions"))
    decisions = _normalize_string_list(payload.get("decisions"))
    authority_context = payload.get("authority_context") if isinstance(payload.get("authority_context"), dict) else None
    work_payload = {
        "work_kind": str(payload.get("work_kind") or "execution"),
        "runnable": bool(payload.get("runnable", True)),
        "goal": payload.get("goal") or title,
        "context": payload.get("context") or "",
        "constraints": payload.get("constraints") or [],
        "execution_plan": payload.get("execution_plan") or [],
        "eval_contract": payload.get("eval_contract") if isinstance(payload.get("eval_contract"), dict) else {},
        "runtime_policy": payload.get("runtime_policy")
        if isinstance(payload.get("runtime_policy"), dict)
        else {"loop": {"max_iterations": 10, "max_runtime_seconds": 28800}},
        "scheduling": normalize_scheduling(payload.get("scheduling")),
        "decisions": decisions,
        "missing_questions": missing_questions,
        "authority_context": authority_context or default_authority_context(payload, decision_ids=decisions),
    }
    ready_errors = work_item_ready_errors(work_payload)
    if status not in WORK_ITEM_STATUSES:
        status = "ready" if not ready_errors else "blocked"
    elif status == "ready" and ready_errors:
        status = "blocked"
    return work_id, status, work_payload


def summarize_object_graph(project_root: Path, *, ensure_tree: bool = True) -> dict[str, Any]:
    store = Store(project_root)
    if ensure_tree:
        store.ensure_tree()
    decision_counts = {"proposed": 0, "accepted": 0, "superseded": 0}
    work_counts = {"ready": 0, "blocked": 0, "draft": 0, "active": 0, "validated": 0, "failed": 0, "abandoned": 0, "total": 0}
    problems: list[str] = []
    blocked_work_ids: list[str] = []
    invalid_work_ids: list[str] = []
    for decision in store.list("decision"):
        status = decision.get("status")
        if status in decision_counts:
            decision_counts[status] += 1
    for work in store.list("work_item"):
        status = str(work.get("status") or "blocked")
        if status in work_counts:
            work_counts[status] += 1
        work_counts["total"] += 1
        payload = work.get("payload") if isinstance(work.get("payload"), dict) else {}
        errors = work_item_ready_errors(payload)
        if status in {"blocked", "draft"}:
            blocked_work_ids.append(str(work.get("object_id")))
        if status == "ready" and errors:
            invalid_work_ids.append(str(work.get("object_id")))
            problems.extend(f"work_item {work.get('object_id')}: {error}" for error in errors)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "summary": {
            "decision_counts": decision_counts,
            "work_item_counts": work_counts,
            "ready_work_count": work_counts["ready"],
            "blocked_work_count": len(blocked_work_ids),
            "active_work_count": len(active_work_ids(project_root)),
        },
        "blocked_work_ids": sorted(set(blocked_work_ids)),
        "invalid_work_ids": sorted(set(invalid_work_ids)),
        "problems": problems,
    }
