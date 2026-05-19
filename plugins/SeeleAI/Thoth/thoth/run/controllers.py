"""Controller services for loop, orchestration, and auto queues."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from thoth.objects import Store, active_work_ids, flatten_work_item, utc_now
from thoth.plan.store import load_work_for_execution


def _ready_work_ref(project_root: Path, work_id: str) -> dict[str, Any]:
    work = load_work_for_execution(project_root, work_id, require_ready=True)
    return {
        "work_id": work["work_id"],
        "revision": work["revision"],
        "title": work.get("title"),
    }


def _work_ref(work: dict[str, Any]) -> dict[str, Any]:
    return {
        "work_id": work["work_id"],
        "revision": work["revision"],
        "title": work.get("title"),
        "status": work.get("ready_state") or work.get("status"),
        "priority": int(work.get("priority") or 0),
    }


def auto_request_fingerprint(
    *,
    refs: list[dict[str, Any]],
    mode: str,
    host: str,
    executor: str,
    scope: str,
    rounds: int | None,
    min_runtime_seconds: int,
    sleep_requested: bool,
    fixed_queue: bool,
) -> dict[str, Any]:
    work_refs = [
        {
            "work_id": str(ref.get("work_id") or ""),
            "revision": int(ref.get("revision") or 0),
        }
        for ref in refs
        if isinstance(ref.get("work_id"), str) and ref.get("work_id")
    ]
    return {
        "mode": mode,
        "host": host,
        "executor": executor,
        "scope": scope,
        "rounds": rounds if isinstance(rounds, int) and rounds > 0 else None,
        "min_runtime_seconds": int(min_runtime_seconds),
        "sleep_requested": bool(sleep_requested),
        "fixed_queue": bool(fixed_queue),
        "work_refs": work_refs if fixed_queue else [],
    }


def build_auto_request_fingerprint(
    project_root: Path,
    *,
    work_ids: list[str] | None = None,
    mode: str = "loop",
    host: str,
    executor: str,
    scope: str = "all-open",
    rounds: int | None = None,
    min_runtime_seconds: int = 8 * 60 * 60,
    sleep_requested: bool = False,
) -> dict[str, Any]:
    refs = [_ready_work_ref(project_root, work_id) for work_id in work_ids or []]
    return auto_request_fingerprint(
        refs=refs,
        mode=mode,
        host=host,
        executor=executor,
        scope=scope,
        rounds=rounds,
        min_runtime_seconds=min_runtime_seconds,
        sleep_requested=sleep_requested,
        fixed_queue=bool(work_ids),
    )


def _dependency_ids(store: Store, work_id: str) -> set[str]:
    ids: set[str] = set()
    for dep in store.dependencies("work_item", work_id):
        dep_id = dep.get("object_id")
        if isinstance(dep_id, str) and dep_id:
            ids.add(dep_id)
    return ids


def list_auto_actionable_work(project_root: Path, *, scope: str = "all-open", limit: int | None = None) -> list[dict[str, Any]]:
    store = Store(project_root)
    locked = active_work_ids(project_root)
    rows: list[dict[str, Any]] = []
    closed = {"validated", "abandoned"}
    actionable = {"ready", "active", "failed"}
    for obj in store.list("work_item"):
        work = flatten_work_item(obj)
        status = str(work.get("ready_state") or work.get("status") or "")
        if status in closed:
            continue
        if scope == "ready" and status != "ready":
            continue
        if status not in actionable:
            continue
        deps = _dependency_ids(store, work["work_id"])
        if any((store.read("work_item", dep_id).get("status") not in closed) for dep_id in deps):
            continue
        scheduling = work.get("scheduling") if isinstance(work.get("scheduling"), dict) else {}
        order = scheduling.get("order")
        if not isinstance(order, int):
            order = 1_000_000
        status_rank = {"active": 0, "failed": 1, "ready": 2}.get(status, 9)
        work["_auto_sort_key"] = (
            status_rank,
            -int(scheduling.get("priority") or 0),
            order,
            str(work.get("updated_at") or ""),
            str(work.get("work_id") or ""),
        )
        work["_auto_locked"] = work["work_id"] in locked
        rows.append(work)
    rows.sort(key=lambda item: item["_auto_sort_key"])
    if scope == "priority-top" and rows:
        top_priority = int((rows[0].get("scheduling") or {}).get("priority") or 0)
        rows = [row for row in rows if int((row.get("scheduling") or {}).get("priority") or 0) == top_priority]
    if isinstance(limit, int) and limit > 0:
        rows = rows[:limit]
    return rows


def _dependency_work_ids(store: Store, work_id: str, requested: set[str]) -> set[str]:
    deps: set[str] = set()
    for dep in store.dependencies("work_item", work_id):
        dep_id = dep.get("object_id")
        if isinstance(dep_id, str) and dep_id in requested:
            deps.add(dep_id)
    return deps


def _dag_batches(project_root: Path, work_ids: list[str]) -> list[list[str]]:
    store = Store(project_root)
    requested = set(work_ids)
    remaining = set(work_ids)
    completed: set[str] = set()
    batches: list[list[str]] = []
    while remaining:
        batch = sorted(
            work_id
            for work_id in remaining
            if _dependency_work_ids(store, work_id, requested).issubset(completed)
        )
        if not batch:
            raise ValueError("orchestration dependency cycle or missing dependency batch")
        batches.append(batch)
        completed.update(batch)
        remaining.difference_update(batch)
    return batches


def create_orchestration_controller(
    project_root: Path,
    *,
    work_ids: list[str],
    host: str,
    executor: str,
) -> dict[str, Any]:
    if not work_ids:
        raise ValueError("orchestration requires at least one --work-id")
    refs = [_ready_work_ref(project_root, work_id) for work_id in work_ids]
    controller_id = f"controller-orchestration-{uuid.uuid4().hex[:12]}"
    batches = _dag_batches(project_root, [ref["work_id"] for ref in refs])
    return Store(project_root).create(
        kind="controller",
        object_id=controller_id,
        status="queued",
        title="Orchestration controller",
        summary=f"Queued orchestration for {len(refs)} work items",
        source="orchestration",
        payload={
            "controller_type": "orchestration",
            "host": host,
            "executor": executor,
            "work_refs": refs,
            "batches": batches,
            "cursor": {"batch_index": 0, "active_run_ids": [], "completed_work_ids": []},
            "created_at": utc_now(),
        },
    )


def create_auto_controller(
    project_root: Path,
    *,
    work_ids: list[str] | None = None,
    mode: str = "loop",
    host: str,
    executor: str,
    scope: str = "all-open",
    rounds: int | None = None,
    min_runtime_seconds: int = 8 * 60 * 60,
    sleep_requested: bool = False,
) -> dict[str, Any]:
    if mode not in {"run", "loop"}:
        raise ValueError("auto mode must be run or loop")
    if work_ids:
        refs = [_ready_work_ref(project_root, work_id) for work_id in work_ids]
    else:
        refs = [_work_ref(work) for work in list_auto_actionable_work(project_root, scope=scope)]
    controller_id = f"controller-auto-{uuid.uuid4().hex[:12]}"
    return Store(project_root).create(
        kind="controller",
        object_id=controller_id,
        status="queued",
        title="Auto queue controller",
        summary=f"Queued {len(refs)} work items for {mode}",
        source="auto",
        payload={
            "controller_type": "auto",
            "mode": mode,
            "host": host,
            "executor": executor,
            "scope": scope,
            "rounds": rounds,
            "min_runtime_seconds": min_runtime_seconds,
            "sleep_requested": sleep_requested,
            "fixed_queue": bool(work_ids),
            "request_fingerprint": auto_request_fingerprint(
                refs=refs,
                mode=mode,
                host=host,
                executor=executor,
                scope=scope,
                rounds=rounds,
                min_runtime_seconds=min_runtime_seconds,
                sleep_requested=sleep_requested,
                fixed_queue=bool(work_ids),
            ),
            "work_refs": refs,
            "queue": refs,
            "attempted_work_ids": [],
            "completed_work_ids": [],
            "failed_work_ids": [],
            "skipped_work_ids": [],
            "cursor": {"index": 0, "active_run_id": None, "completed_work_ids": [], "rounds_attempted": 0},
            "created_at": utc_now(),
        },
    )
