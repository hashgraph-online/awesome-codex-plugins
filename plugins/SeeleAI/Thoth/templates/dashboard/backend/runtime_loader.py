"""
runtime_loader.py -- Canonical run-ledger reader for the Thoth dashboard.

The dashboard must not infer long-running execution state from chat history or
task YAML files. Runtime truth lives under `.thoth/runs/<run_id>/`.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ACTIVE_RUN_STATUSES = {"queued", "running", "paused", "waiting_input", "stopping"}


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_timestamp(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            payload.setdefault("_line_no", line_no)
            records.append(payload)
    return records


def _event_seq(event: dict[str, Any]) -> int:
    seq = event.get("seq")
    if isinstance(seq, int):
        return seq
    return int(event.get("_line_no", 0))


def _normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    payload["seq"] = _event_seq(payload)
    payload["ts"] = payload.get("ts") or payload.get("timestamp")
    payload["kind"] = payload.get("kind") or payload.get("type") or "event"
    payload["level"] = payload.get("level") or "info"
    payload["message"] = payload.get("message") or payload.get("summary") or ""
    payload.pop("_line_no", None)
    return payload


def _latest_ts(*values: Any) -> Optional[str]:
    parsed = [_parse_timestamp(v) for v in values]
    parsed = [value for value in parsed if value is not None]
    if not parsed:
        return None
    return _format_timestamp(max(parsed))


def _runs_dir(project_root: Path) -> Path:
    return Path(os.environ.get("THOTH_RUNS_DIR", str(project_root / ".thoth" / "runs"))).resolve()


def list_runs(project_root: Path) -> list[dict[str, Any]]:
    project_root = project_root.resolve()
    runs_dir = _runs_dir(project_root)
    if not runs_dir.is_dir():
        return []

    stale_minutes = int(os.environ.get("THOTH_HEARTBEAT_STALE_MINUTES", "20"))
    now = datetime.now(timezone.utc)
    runs: list[dict[str, Any]] = []

    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir():
            continue

        run_data = _read_json(run_dir / "run.json")
        state_data = _read_json(run_dir / "state.json")
        result_data = _read_json(run_dir / "result.json")
        artifacts_data = _read_json(run_dir / "artifacts.json")
        supervisor_data = _read_json(run_dir / "supervisor.json")
        events = [_normalize_event(event) for event in _read_jsonl(run_dir / "events.jsonl")]
        events.sort(key=lambda item: item["seq"])

        run_id = str(run_data.get("run_id") or run_data.get("id") or state_data.get("run_id") or run_dir.name)
        work_id = run_data.get("work_id") or state_data.get("work_id")
        status = str(state_data.get("status") or run_data.get("status") or result_data.get("status") or "unknown")
        progress_pct = state_data.get("progress_pct")
        if not isinstance(progress_pct, (int, float)):
            progress_pct = state_data.get("progress")
        if not isinstance(progress_pct, (int, float)):
            progress_pct = 0.0
        progress_pct = round(max(0.0, min(100.0, float(progress_pct))), 1)

        last_event = events[-1] if events else None
        last_heartbeat_at = state_data.get("last_heartbeat_at")
        last_updated_at = _latest_ts(
            state_data.get("updated_at"),
            last_heartbeat_at,
            result_data.get("updated_at"),
            last_event.get("ts") if last_event else None,
            run_data.get("updated_at"),
            run_data.get("created_at"),
        )
        hb_dt = _parse_timestamp(last_heartbeat_at)
        is_stale = False
        if hb_dt is not None and status in ACTIVE_RUN_STATUSES:
            is_stale = (now - hb_dt).total_seconds() > stale_minutes * 60
        is_active = status in ACTIVE_RUN_STATUSES and not is_stale

        runs.append({
            "run_id": run_id,
            "work_id": work_id,
            "title": run_data.get("title") or run_id,
            "host": run_data.get("host"),
            "status": status,
            "phase": state_data.get("phase") or run_data.get("phase"),
            "progress_pct": progress_pct,
            "executor": run_data.get("executor"),
            "attachable": bool(run_data.get("attachable", True)),
            "created_at": run_data.get("created_at"),
            "started_at": run_data.get("started_at") or run_data.get("created_at"),
            "last_updated_at": last_updated_at,
            "last_heartbeat_at": last_heartbeat_at,
            "last_event_seq": state_data.get("last_event_seq") if isinstance(state_data.get("last_event_seq"), int) else (last_event["seq"] if last_event else 0),
            "is_active": is_active,
            "is_stale": is_stale,
            "stale": is_stale,
            "supervisor_state": state_data.get("supervisor_state") or supervisor_data.get("state"),
            "latest_message": last_event.get("message") if last_event else "",
            "artifact_count": len(artifacts_data.get("artifacts", [])) if isinstance(artifacts_data.get("artifacts"), list) else 0,
            "events_path": str((run_dir / "events.jsonl").resolve().relative_to(project_root)) if (run_dir / "events.jsonl").exists() else None,
        })

    runs.sort(
        key=lambda item: (
            _parse_timestamp(item.get("last_updated_at")) or datetime.min.replace(tzinfo=timezone.utc),
            item["run_id"],
        ),
        reverse=True,
    )
    return runs


def get_work_item_runs(project_root: Path, work_id: str) -> list[dict[str, Any]]:
    return [
        run
        for run in list_runs(project_root)
        if run.get("work_id") == work_id
    ]


def get_active_run_for_work_item(project_root: Path, work_id: str) -> Optional[dict[str, Any]]:
    work_runs = get_work_item_runs(project_root, work_id)
    for run in work_runs:
        if run.get("is_active"):
            return run
    return work_runs[0] if work_runs else None


def get_run_detail(project_root: Path, run_id: str) -> Optional[dict[str, Any]]:
    summary = next((run for run in list_runs(project_root) if run["run_id"] == run_id), None)
    if summary is None:
        return None
    run_dir = _runs_dir(project_root) / run_id
    return {
        **summary,
        "run": _read_json(run_dir / "run.json"),
        "state": _read_json(run_dir / "state.json"),
        "heartbeat": {"last_heartbeat_at": summary.get("last_heartbeat_at")},
        "artifacts": _read_json(run_dir / "artifacts.json"),
        "result": _read_json(run_dir / "result.json"),
    }


def get_run_events(project_root: Path, run_id: str, *, after_seq: Optional[int] = None, limit: int = 100) -> Optional[dict[str, Any]]:
    run_dir = _runs_dir(project_root) / run_id
    if not run_dir.is_dir():
        return None
    events = [_normalize_event(event) for event in _read_jsonl(run_dir / "events.jsonl")]
    events.sort(key=lambda item: item["seq"])
    if after_seq is not None:
        filtered = [event for event in events if event["seq"] > after_seq]
        payload = filtered[:limit]
        has_more = len(filtered) > len(payload)
    else:
        payload = events[-limit:]
        has_more = len(events) > len(payload)
    return {
        "run_id": run_id,
        "events": payload,
        "next_after_seq": payload[-1]["seq"] if payload else after_seq,
        "has_more": has_more,
    }


def runtime_overview(project_root: Path) -> dict[str, Any]:
    runs = list_runs(project_root)
    active_runs = [run for run in runs if run.get("is_active")]
    stale_runs = [run for run in runs if run.get("is_stale")]
    auto_controllers = _list_auto_controllers(project_root)
    active_auto = [row for row in auto_controllers if row.get("status") in {"queued", "running", "idle"}]
    return {
        "active_run_count": len(active_runs),
        "stale_run_count": len(stale_runs),
        "active_auto_count": len(active_auto),
        "active_runs": active_runs[:10],
        "active_auto_controllers": active_auto[:10],
        "last_runtime_update": runs[0].get("last_updated_at") if runs else None,
        "progress_source": "work_result_plus_run_ledger",
        "host_breakdown": sorted({run.get("host") for run in runs if run.get("host")}),
    }


def _list_auto_controllers(project_root: Path) -> list[dict[str, Any]]:
    controllers_dir = project_root / ".thoth" / "objects" / "controller"
    if not controllers_dir.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(controllers_dir.glob("*.json")):
        payload = _read_json(path)
        body = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
        if body.get("controller_type") != "auto":
            continue
        cursor = body.get("cursor") if isinstance(body.get("cursor"), dict) else {}
        rows.append(
            {
                "controller_id": payload.get("object_id") or path.stem,
                "status": payload.get("status"),
                "state": body.get("state"),
                "elapsed_seconds": body.get("elapsed_seconds"),
                "min_runtime_seconds": body.get("min_runtime_seconds"),
                "rounds_attempted": cursor.get("rounds_attempted"),
                "active_run_id": cursor.get("active_run_id"),
                "queue_count": len(body.get("queue")) if isinstance(body.get("queue"), list) else 0,
                "completed_count": len(body.get("completed_work_ids")) if isinstance(body.get("completed_work_ids"), list) else 0,
                "failed_count": len(body.get("failed_work_ids")) if isinstance(body.get("failed_work_ids"), list) else 0,
                "updated_at": payload.get("updated_at"),
            }
        )
    rows.sort(key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    return rows
