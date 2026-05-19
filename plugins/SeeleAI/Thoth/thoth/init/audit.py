"""Audit-first repository inspection for `thoth init`."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from thoth.plan.store import load_project_manifest
from .preview import _managed_path_list, _utc_iso

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

def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _read_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _claude_config_dir() -> Path:
    override = os.environ.get("THOTH_CLAUDE_CONFIG_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".claude"


def _claude_permissions_allow_bridge(payload: dict[str, Any]) -> bool:
    permissions = payload.get("permissions")
    if not isinstance(permissions, dict):
        return False
    allow = permissions.get("allow")
    if not isinstance(allow, list):
        return False
    for item in allow:
        if not isinstance(item, str):
            continue
        if "thoth-claude-command.sh" in item:
            return True
    return False


def detect_claude_bridge_permission(project_dir: Path) -> dict[str, Any]:
    config_dir = _claude_config_dir()
    global_path = config_dir / "settings.json"
    project_shared_path = project_dir / ".claude" / "settings.json"
    project_local_path = project_dir / ".claude" / "settings.local.json"

    global_allowed = _claude_permissions_allow_bridge(_read_json_dict(global_path))
    project_shared_allowed = _claude_permissions_allow_bridge(_read_json_dict(project_shared_path))
    project_local_allowed = _claude_permissions_allow_bridge(_read_json_dict(project_local_path))

    sources: list[str] = []
    if global_allowed:
        sources.append("global")
    if project_shared_allowed:
        sources.append("project")
    if project_local_allowed:
        sources.append("local")

    return {
        "effective_allowed": bool(sources),
        "sources": sources,
        "global_path": str(global_path),
        "project_shared_path": str(project_shared_path),
        "project_local_path": str(project_local_path),
        "allow_pattern": THOTH_CLAUDE_BASH_ALLOW_PATTERN,
    }


def _read_readme_summary(project_dir: Path) -> tuple[str, str]:
    for candidate in ("README.md", "readme.md"):
        path = project_dir / candidate
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        title = ""
        summary = ""
        for raw in lines:
            line = raw.strip()
            if not title and line.startswith("#"):
                title = line.lstrip("#").strip()
                continue
            if not summary and line and not line.startswith("#"):
                summary = line
                break
        return title, summary
    return "", ""


def _detect_language(project_dir: Path, legacy_config: dict[str, Any], manifest: dict[str, Any]) -> str:
    language = manifest.get("project", {}).get("language")
    if isinstance(language, str) and language.strip():
        return language.strip()
    language = legacy_config.get("project", {}).get("language")
    if isinstance(language, str) and language.strip():
        return language.strip()

    sample_paths = [
        project_dir / "AGENTS.md",
        project_dir / "CLAUDE.md",
        project_dir / "README.md",
        project_dir / ".agent-os" / "project-index.md",
    ]
    for path in sample_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
    return "en"


def _discover_directions(project_dir: Path, legacy_config: dict[str, Any], manifest: dict[str, Any]) -> list[Any]:
    configured = manifest.get("project", {}).get("directions")
    if isinstance(configured, list) and configured:
        return configured
    configured = legacy_config.get("research", {}).get("directions")
    if isinstance(configured, list) and configured:
        return configured

    task_root = project_dir / ".agent-os" / "research-tasks"
    discovered: list[str] = []
    if task_root.is_dir():
        for entry in sorted(task_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name.startswith("_"):
                continue
            discovered.append(entry.name)
    return discovered


def _git_status_summary(project_dir: Path) -> dict[str, Any]:
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        return {"present": False}

    branch = ""
    porcelain_lines: list[str] = []
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        ).stdout.strip()
        porcelain = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        ).stdout
        porcelain_lines = [line.rstrip() for line in porcelain.splitlines()]
    except Exception:
        return {"present": True, "branch": "", "dirty": None, "entries": []}

    dirty_entries = [line for line in porcelain_lines if not line.startswith("##")]
    return {
        "present": True,
        "branch": branch,
        "dirty": bool(dirty_entries),
        "entries": dirty_entries,
    }


def audit_repository_state(project_dir: Path) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    legacy_config = _read_yaml(project_dir / LEGACY_CONFIG_FILE)
    manifest = load_project_manifest(project_dir)
    readme_title, readme_summary = _read_readme_summary(project_dir)

    docs_files: list[str] = []
    docs_dir = project_dir / "docs"
    if docs_dir.is_dir():
        docs_files = sorted(str(path.relative_to(project_dir)) for path in docs_dir.rglob("*") if path.is_file())

    agent_os_files: list[str] = []
    agent_os_dir = project_dir / ".agent-os"
    if agent_os_dir.is_dir():
        agent_os_files = sorted(str(path.relative_to(project_dir)) for path in agent_os_dir.rglob("*") if path.is_file())

    legacy_agentos_files: list[str] = []
    legacy_agentos_dir = project_dir / ".agentos"
    if legacy_agentos_dir.is_dir():
        legacy_agentos_files = sorted(
            str(path.relative_to(project_dir)) for path in legacy_agentos_dir.rglob("*") if path.is_file()
        )

    root_markdown_files = sorted(
        entry.name
        for entry in project_dir.iterdir()
        if entry.is_file() and entry.suffix.lower() == ".md" and entry.name not in {"AGENTS.md", "CLAUDE.md"}
    )

    code_roots: set[str] = set()
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or ".thoth" in path.parts:
            continue
        if path.suffix in DISCOVERY_CODE_SUFFIXES:
            rel = path.relative_to(project_dir)
            root = rel.parts[0] if len(rel.parts) > 1 else "."
            code_roots.add(root)

    managed_paths = _managed_path_list()
    managed_existing = sorted(rel for rel in managed_paths if (project_dir / rel).exists())

    top_level_entries = sorted(
        entry.name for entry in project_dir.iterdir() if entry.name not in {".git", "__pycache__"}
    )

    return {
        "schema_version": 1,
        "audited_at": _utc_iso(),
        "project_root": str(project_dir),
        "git": _git_status_summary(project_dir),
        "existing": {
            "research_config": (project_dir / LEGACY_CONFIG_FILE).exists(),
            "thoth_authority": (project_dir / ".thoth").exists(),
            "agent_os": agent_os_dir.exists(),
            "legacy_agentos_alias": legacy_agentos_dir.exists(),
            "docs": docs_dir.exists(),
            "codex_reserved_path_present": (project_dir / ".codex").exists(),
            "dashboard": (project_dir / "tools" / "dashboard").exists(),
        },
        "top_level_entries": top_level_entries,
        "root_markdown_files": root_markdown_files,
        "docs_files": docs_files,
        "agent_os_files": agent_os_files,
        "legacy_agentos_files": legacy_agentos_files,
        "managed_existing": managed_existing,
        "code_roots": sorted(code_roots),
        "readme": {
            "title": readme_title,
            "summary": readme_summary,
        },
        "inferred": {
            "language": _detect_language(project_dir, legacy_config, manifest),
            "directions": _discover_directions(project_dir, legacy_config, manifest),
        },
        "legacy_research_task_files": sorted(
            str(path.relative_to(project_dir))
            for path in (project_dir / ".agent-os" / "research-tasks").rglob("*.y*ml")
            if path.is_file()
        ) if (project_dir / ".agent-os" / "research-tasks").is_dir() else [],
    }
