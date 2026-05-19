"""Shared helpers for finding fresh review context from canonical run ledgers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from thoth.plan.store import load_work_result

from .io import _read_json
from .model import _parse_iso8601


def latest_fresh_review_context(
    project_root: Path,
    *,
    work_id: str | None,
    target: str | None,
) -> dict[str, Any]:
    if not work_id or not target:
        return {}
    work_result = load_work_result(project_root, work_id)
    last_closure_ts = _parse_iso8601(work_result.get("last_closure_at"))
    best: dict[str, Any] = {}
    runs_root = project_root / ".thoth" / "runs"
    if not runs_root.is_dir():
        return {}
    for run_dir in runs_root.iterdir():
        if not run_dir.is_dir():
            continue
        run_payload = _read_json(run_dir / "run.json")
        if run_payload.get("kind") != "review":
            continue
        if run_payload.get("work_id") != work_id or run_payload.get("target") != target:
            continue
        result_payload = _read_json(run_dir / "result.json")
        if result_payload.get("status") != "completed":
            continue
        finished_at = result_payload.get("finished_at") or result_payload.get("updated_at")
        finished_ts = _parse_iso8601(finished_at)
        if finished_ts is None:
            continue
        if last_closure_ts is not None and finished_ts <= last_closure_ts:
            continue
        current_best_ts = _parse_iso8601(best.get("finished_at")) if best else None
        if current_best_ts is not None and finished_ts <= current_best_ts:
            continue
        review_result = result_payload.get("result") if isinstance(result_payload.get("result"), dict) else {}
        best = {
            "run_id": run_payload.get("run_id") or run_dir.name,
            "target": target,
            "summary": result_payload.get("summary"),
            "finished_at": finished_at,
            "findings": review_result.get("findings", []),
        }
    return best
