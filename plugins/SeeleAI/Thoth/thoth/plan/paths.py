"""Path helpers for canonical Thoth object authority."""

from __future__ import annotations

from pathlib import Path

SCHEMA_VERSION = 1
WORK_RESULT_SUFFIX = ".result.json"

def authority_root(project_root: Path) -> Path:
    return project_root / ".thoth" / "objects"


def docs_root(project_root: Path) -> Path:
    return project_root / ".thoth" / "docs"


def project_manifest_path(project_root: Path) -> Path:
    return authority_root(project_root) / "project" / "project.json"


def decisions_dir(project_root: Path) -> Path:
    return authority_root(project_root) / "decision"


def contracts_dir(project_root: Path) -> Path:
    return docs_root(project_root) / "legacy-contract-imports"


def work_items_dir(project_root: Path) -> Path:
    return authority_root(project_root) / "work_item"


def work_result_path(project_root: Path, work_id: str) -> Path:
    return docs_root(project_root) / "work-results" / f"{work_id}{WORK_RESULT_SUFFIX}"


def compiler_state_path(project_root: Path) -> Path:
    return docs_root(project_root) / "object-graph-summary.json"


def legacy_audit_path(project_root: Path) -> Path:
    return docs_root(project_root) / "legacy-audit.json"
