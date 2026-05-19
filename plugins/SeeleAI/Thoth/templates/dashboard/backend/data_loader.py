"""
data_loader.py — work-item dashboard loader for Thoth.

The dashboard only reads `.thoth` authority. Legacy `.agent-os/research-tasks`
and `.research-config.yaml` are not active runtime inputs.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import yaml


_cache: dict[str, Any] = {}
_cache_ts: dict[str, float] = {}
_file_mtime_cache: dict[str, tuple[float, Optional[dict[str, Any]]]] = {}
CACHE_TTL: float = float(os.environ.get("DASHBOARD_CACHE_TTL", "2"))


def _cached(key: str) -> Optional[Any]:
    if key in _cache and (time.time() - _cache_ts.get(key, 0)) < CACHE_TTL:
        return _cache[key]
    return None


def _set_cache(key: str, value: Any) -> Any:
    _cache[key] = value
    _cache_ts[key] = time.time()
    return value


def invalidate_cache() -> None:
    _cache.clear()
    _cache_ts.clear()
    _file_mtime_cache.clear()


def get_cache_info() -> dict:
    return {
        "ttl_seconds": CACHE_TTL,
        "cached_keys": list(_cache.keys()),
        "cached_timestamps": {k: v for k, v in _cache_ts.items()},
        "file_mtime_entries": len(_file_mtime_cache),
    }


def _read_json(path: Path) -> Optional[dict[str, Any]]:
    path_str = str(path)
    try:
        current_mtime = os.path.getmtime(path_str)
    except OSError:
        current_mtime = None

    if current_mtime is not None and path_str in _file_mtime_cache:
        cached_mtime, cached_data = _file_mtime_cache[path_str]
        if cached_mtime == current_mtime:
            return cached_data

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if current_mtime is not None:
        _file_mtime_cache[path_str] = (current_mtime, data)
    return data


def _safe_load_yaml(file_path: str | Path) -> Optional[dict]:
    path = Path(file_path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, yaml.YAMLError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _infer_project_root(base_dir: str | Path) -> Path:
    base = Path(base_dir).resolve()
    if (base / ".thoth" / "objects").exists():
        return base
    if base.name in {"work_item", "decision", "run", "controller"} and base.parent.name == "objects":
        return base.parent.parent.parent
    return base


def _load_manifest(project_root: Path) -> dict[str, Any]:
    obj = _read_json(project_root / ".thoth" / "objects" / "project" / "project.json") or {}
    payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}
    if payload:
        return payload
    return _read_json(project_root / ".thoth" / "docs" / "project.json") or {}


def _direction_entries(project_root: Path) -> list[dict[str, Any]]:
    manifest = _load_manifest(project_root)
    project = manifest.get("project", {}) if isinstance(manifest, dict) else {}
    directions = project.get("directions", [])
    rows: list[dict[str, Any]] = []
    if isinstance(directions, list):
        for item in directions:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                rows.append(item)
            elif isinstance(item, str) and item.strip():
                rows.append({"id": item.strip(), "label_en": item.strip().title()})
    return rows


def _read_directions_from_config(base_dir: Path) -> tuple[str, ...]:
    project_root = _infer_project_root(base_dir)
    directions = [row["id"] for row in _direction_entries(project_root)]
    if directions:
        return tuple(directions)
    task_dir = project_root / ".thoth" / "objects" / "work_item"
    found = sorted(
        {
            payload.get("direction")
            for path in task_dir.glob("*.json")
            for payload in [_read_json(path) or {}]
            if isinstance(payload.get("direction"), str) and payload.get("direction")
        }
    )
    return tuple(found)


DIRECTIONS = _read_directions_from_config(Path(__file__).resolve().parents[3])


def _load_work_result_map(project_root: Path) -> dict[str, dict[str, Any]]:
    task_dir = project_root / ".thoth" / "docs" / "work-results"
    rows: dict[str, dict[str, Any]] = {}
    if task_dir.is_dir():
        for path in sorted(task_dir.glob("*.result.json")):
            payload = _read_json(path)
            work_id = payload.get("work_id") if payload else None
            if isinstance(work_id, str) and work_id:
                payload["_path"] = str(path)
                rows[work_id] = payload
    return rows


def _flatten_work_item(payload: dict[str, Any], path: Path) -> dict[str, Any] | None:
    work_id = payload.get("object_id")
    if not isinstance(work_id, str) or not work_id:
        return None
    work_payload = payload.get("payload") if isinstance(payload.get("payload"), dict) else {}
    eval_contract = work_payload.get("eval_contract") if isinstance(work_payload.get("eval_contract"), dict) else {}
    row = {
        "schema_version": payload.get("schema_version"),
        "kind": "work_item",
        "id": work_id,
        "work_id": work_id,
        "title": payload.get("title") or work_id,
        "summary": payload.get("summary") or "",
        "module": work_payload.get("module") or work_payload.get("context") or "strict",
        "direction": work_payload.get("direction") or "general",
        "ready_state": payload.get("status"),
        "status": payload.get("status"),
        "runnable": work_payload.get("runnable") is True,
        "work_kind": work_payload.get("work_kind"),
        "goal_statement": work_payload.get("goal") or "",
        "implementation_recipe": work_payload.get("execution_plan") or [],
        "constraints": work_payload.get("constraints") or [],
        "eval_entrypoint": eval_contract.get("entrypoint") or {},
        "primary_metric": eval_contract.get("primary_metric") or {},
        "failure_classes": eval_contract.get("failure_classes") or [],
        "validate_output_schema": eval_contract.get("validate_output_schema") or {},
        "decision_ids": work_payload.get("decisions") or [],
        "depends_on": [
            {"work_id": str(link.get("target", "")).split(":", 1)[-1], "type": "hard"}
            for link in payload.get("links", [])
            if isinstance(link, dict) and link.get("type") == "depends_on"
        ],
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
        "_path": str(path),
    }
    return row


def _load_compiled_tasks(project_root: Path) -> list[dict[str, Any]]:
    task_dir = project_root / ".thoth" / "objects" / "work_item"
    work_result_map = _load_work_result_map(project_root)
    rows: list[dict[str, Any]] = []
    if not task_dir.is_dir():
        return rows
    for path in sorted(task_dir.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        row = _flatten_work_item(payload, path)
        if row is None:
            continue
        work_id = row["work_id"]
        if work_id in work_result_map:
            row["work_result"] = work_result_map[work_id]
        rows.append(row)
    return rows


def load_task(file_path: str | Path) -> Optional[dict]:
    return _read_json(Path(file_path))


def load_all_tasks(base_dir: str | Path) -> list[dict]:
    cached = _cached("tasks")
    if cached is not None:
        return cached
    project_root = _infer_project_root(base_dir)
    return _set_cache("tasks", _load_compiled_tasks(project_root))


def load_modules(base_dir: str | Path) -> list[dict]:
    cached = _cached("modules")
    if cached is not None:
        return cached

    project_root = _infer_project_root(base_dir)
    tasks = _load_compiled_tasks(project_root)
    modules: dict[tuple[str, str], dict[str, Any]] = {}
    for task in tasks:
        direction = str(task.get("direction") or "general")
        module = str(task.get("module") or "strict")
        key = (direction, module)
        item = modules.setdefault(
            key,
            {
                "id": module,
                "name": module,
                "direction": direction,
                "scientific_question": task.get("goal_statement", ""),
                "related_modules": {"upstream": [], "downstream": []},
            },
        )
        if not item.get("scientific_question") and isinstance(task.get("goal_statement"), str):
            item["scientific_question"] = task.get("goal_statement")
    return _set_cache("modules", list(modules.values()))


def get_paper_mapping(base_dir: str | Path) -> Optional[dict]:
    cached = _cached("paper_mapping")
    if cached is not None:
        return cached
    return _set_cache("paper_mapping", {})


def load_compiler_state(base_dir: str | Path) -> dict[str, Any]:
    cached = _cached("compiler_state")
    if cached is not None:
        return cached
    project_root = _infer_project_root(base_dir)
    return _set_cache("compiler_state", _read_json(project_root / ".thoth" / "docs" / "object-graph-summary.json") or {})


def load_decisions(base_dir: str | Path) -> list[dict[str, Any]]:
    cached = _cached("decisions")
    if cached is not None:
        return cached
    project_root = _infer_project_root(base_dir)
    rows: list[dict[str, Any]] = []
    decision_dir = project_root / ".thoth" / "objects" / "decision"
    if decision_dir.is_dir():
        for path in sorted(decision_dir.glob("*.json")):
            payload = _read_json(path)
            if payload:
                payload["_path"] = str(path)
                rows.append(payload)
    return _set_cache("decisions", rows)


def load_work_item_refs(base_dir: str | Path) -> list[dict[str, Any]]:
    cached = _cached("work_item_refs")
    if cached is not None:
        return cached
    project_root = _infer_project_root(base_dir)
    rows: list[dict[str, Any]] = []
    work_dir = project_root / ".thoth" / "objects" / "work_item"
    if work_dir.is_dir():
        for path in sorted(work_dir.glob("*.json")):
            payload = _read_json(path)
            if not payload:
                continue
            row = _flatten_work_item(payload, path)
            if row:
                rows.append(row)
    return _set_cache("work_item_refs", rows)


def load_project_config(base_dir: str | Path) -> dict[str, Any]:
    cached = _cached("project_config")
    if cached is not None:
        return cached
    project_root = _infer_project_root(base_dir)
    manifest = _load_manifest(project_root)
    project = manifest.get("project", {}) if isinstance(manifest, dict) else {}
    dashboard = manifest.get("dashboard", {}) if isinstance(manifest, dict) else {}
    payload = {
        "project": {
            "name": project.get("name", project_root.name),
            "description": project.get("description", ""),
            "language": project.get("language", "zh"),
        },
        "research": {
            "directions": _direction_entries(project_root),
            "phases": project.get("phases", []),
        },
        "dashboard": dashboard,
    }
    return _set_cache("project_config", payload)


def load_everything(base_dir: str | Path) -> dict:
    project_root = _infer_project_root(base_dir)
    return {
        "modules": load_modules(project_root),
        "tasks": load_all_tasks(project_root),
        "paper_mapping": get_paper_mapping(project_root),
        "compiler_state": load_compiler_state(project_root),
        "decisions": load_decisions(project_root),
        "work_items": load_work_item_refs(project_root),
        "config": load_project_config(project_root),
    }
