"""Migration backup, displacement, and source-map helpers for init."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .preview import _detect_init_mode, _utc_iso

LEGACY_CONFIG_FILE = ".research-config.yaml"
ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = ROOT / "templates"

DEFAULT_PHASES = [
    {"id": "survey", "label_zh": "文献综述", "label_en": "Survey", "weight": 20},
    {"id": "method_design", "label_zh": "方案设计", "label_en": "Method Design", "weight": 20},
    {"id": "experiment", "label_zh": "实验", "label_en": "Experiment", "weight": 40},
    {"id": "conclusion", "label_zh": "结论", "label_en": "Conclusion", "weight": 20},
]

DIRECTION_COLORS = ["#CC8B3A", "#8BA870", "#D4907A", "#9B7CB5", "#6B9BD2", "#D4A76A", "#7BC8A4", "#C87B8A"]
REQUIRED_AGENT_OS_FILES = ["project-index.md", "requirements.md", "architecture-milestones.md", "todo.md", "cross-repo-mapping.md", "acceptance-report.md", "lessons-learned.md", "run-log.md", "change-decisions.md"]
OPTIONAL_AGENT_OS_FILES = ["milestones.yaml"]
GENERATED_SCRIPT_FILES = ["install-hooks.sh", "check-required-files.sh", "session-end-check.sh", "validate-all.sh", "thoth-cli.sh", "thoth-codex-hook.sh"]
GENERATED_TEST_FILES = ["tests/conftest.py", "tests/test_structure.py"]
MANAGED_DIRECTORY_ROOTS = [".agent-os", ".claude", ".thoth", "scripts", "tests", "tools", "tools/dashboard"]
LEGACY_REMOVE_PATHS = [LEGACY_CONFIG_FILE, ".agent-os/research-tasks", "tests/test_validate.py", "tests/test_check_consistency.py", "tests/test_sync_todo.py", "tests/test_verify_completion.py"]
DISCOVERY_CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".vue", ".sh", ".rs", ".go", ".java", ".c", ".cc", ".cpp", ".h", ".hpp"}
THOTH_CLAUDE_BASH_ALLOW_PATTERN = "Bash(*thoth-claude-command.sh*)"
BACKUP_SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", "dist"}


def _backup_ignore(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in BACKUP_SKIP_DIRS}

def _backup_existing_path(project_dir: Path, migration_dir: Path, relpath: str) -> None:
    source = project_dir / relpath
    if not source.exists():
        return
    target = migration_dir / "backup" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=_backup_ignore)
    else:
        shutil.copy2(source, target)


def _remove_existing_path(project_dir: Path, relpath: str) -> None:
    target = project_dir / relpath
    if not target.exists():
        return
    if target.is_dir():
        shutil.rmtree(target)
    else:
        target.unlink()


def _displace_existing_path(project_dir: Path, migration_dir: Path, relpath: str) -> str | None:
    source = project_dir / relpath
    if not source.exists():
        return None
    target = migration_dir / "displaced" / relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    source.rename(target)
    return str((Path("displaced") / relpath).as_posix())


def _managed_directory_conflicts(project_dir: Path) -> list[str]:
    conflicts: list[str] = []
    for rel in MANAGED_DIRECTORY_ROOTS:
        path = project_dir / rel
        if path.exists() and not path.is_dir():
            conflicts.append(rel)
    return sorted(conflicts)


def _write_source_map(project_dir: Path, audit: dict[str, Any], preview: dict[str, Any]) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": _utc_iso(),
        "mode": preview.get("mode", _detect_init_mode(audit)),
        "authority": {
            "project_manifest": ".thoth/objects/project/project.json",
            "instructions": ".thoth/docs/agent-entry.md",
        },
        "projections": {
            "claude": "CLAUDE.md",
            "codex": "AGENTS.md",
            "codex_hooks_projection": ".thoth/derived/codex-hooks.json",
        },
        "host_reserved_paths": {
            "codex": ".codex",
        },
        "managed_paths": sorted(set(preview["create"] + preview["update"] + preview["preserve"])),
        "removed_legacy_paths": preview.get("remove", []),
        "preserved_docs": audit.get("docs_files", []),
        "preserved_root_markdown": audit.get("root_markdown_files", []),
        "preserved_agent_os_files": audit.get("agent_os_files", []),
        "legacy_agentos_files": audit.get("legacy_agentos_files", []),
        "code_roots": audit.get("code_roots", []),
    }
    path = project_dir / ".thoth" / "docs" / "source-map.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
