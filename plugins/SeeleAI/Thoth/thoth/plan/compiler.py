"""Object graph summarizer for strict Thoth authority.

The legacy planning compiler has been removed from the authority path.
`compile_task_authority` now validates and summarizes the canonical
`.thoth/objects` graph, then writes a read-only docs view.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from thoth.objects import summarize_object_graph, utc_now

from .paths import SCHEMA_VERSION, compiler_state_path, legacy_audit_path
from .store import _read_yaml, _write_json, ensure_work_authority_tree


def collect_legacy_authority_rows(project_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    legacy_thoth_project = project_root / ".thoth" / "project"
    if legacy_thoth_project.exists():
        items.append(
            {
                "legacy_path": ".thoth/project",
                "legacy_id": "legacy-thoth-project",
                "status": "invalid",
                "reason": "legacy_thoth_project_authority_removed",
            }
        )
        for path in sorted(legacy_thoth_project.rglob("*")):
            if path.is_file():
                items.append(
                    {
                        "legacy_path": str(path.relative_to(project_root)),
                        "legacy_id": path.stem,
                        "status": "invalid",
                        "reason": "legacy_thoth_project_authority_removed",
                    }
                )
    legacy_research_tasks = project_root / ".agent-os" / "research-tasks"
    if legacy_research_tasks.is_dir():
        for path in sorted(legacy_research_tasks.rglob("*.y*ml")):
            if path.name in {"_module.yaml", "paper-module-mapping.yaml"}:
                continue
            payload = _read_yaml(path)
            legacy_id = payload.get("id") if isinstance(payload.get("id"), str) else path.stem
            if not isinstance(legacy_id, str) or not legacy_id:
                legacy_id = path.stem
            items.append(
                {
                    "legacy_path": str(path.relative_to(project_root)),
                    "legacy_id": legacy_id,
                    "status": "invalid",
                    "reason": "legacy_yaml_execution_authority_removed",
                }
            )
    return items


def audit_legacy_tasks(project_root: Path) -> dict[str, Any]:
    items = collect_legacy_authority_rows(project_root)
    audit = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "legacy_authority": items,
        "summary": {
            "total": len(items),
            "invalid": len(items),
        },
    }
    _write_json(legacy_audit_path(project_root), audit)
    return audit


def compile_task_authority(project_root: Path) -> dict[str, Any]:
    ensure_work_authority_tree(project_root)
    legacy_audit = audit_legacy_tasks(project_root)
    graph = summarize_object_graph(project_root)
    problems = list(graph.get("problems", []))
    for item in legacy_audit.get("legacy_authority", []):
        problems.append(f"legacy authority {item.get('legacy_id')}: {item.get('reason')}")
    graph["summary"]["legacy_authority_count"] = legacy_audit["summary"]["total"]
    graph["problems"] = problems
    _write_json(compiler_state_path(project_root), graph)
    return graph
