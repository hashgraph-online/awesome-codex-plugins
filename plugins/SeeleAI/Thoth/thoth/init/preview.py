"""Init/adopt preview planning."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
MANAGED_DIRECTORY_ROOTS = [".claude", ".thoth", "scripts", "tests", "tools", "tools/dashboard"]
LEGACY_REMOVE_PATHS = [LEGACY_CONFIG_FILE, ".agent-os/research-tasks", ".thoth/project", "tests/test_validate.py", "tests/test_check_consistency.py", "tests/test_sync_todo.py", "tests/test_verify_completion.py"]
DISCOVERY_CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".vue", ".sh", ".rs", ".go", ".java", ".c", ".cc", ".cpp", ".h", ".hpp"}
THOTH_CLAUDE_BASH_ALLOW_PATTERN = "Bash(*thoth-claude-command.sh*)"

def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _managed_path_list() -> list[str]:
    base = [
        ".pre-commit-config.yaml",
        "AGENTS.md",
        "CLAUDE.md",
        ".thoth/objects/project/project.json",
        ".thoth/docs/project.json",
        ".thoth/docs/agent-entry.md",
        ".thoth/docs/source-map.json",
        ".thoth/docs/object-graph-summary.json",
        ".thoth/docs/legacy-audit.json",
        ".thoth/runs/.gitkeep",
        ".thoth/migrations/.gitkeep",
        ".thoth/derived/.gitkeep",
        ".thoth/derived/codex-hooks.json",
    ]
    base.extend(f"scripts/{name}" for name in GENERATED_SCRIPT_FILES)
    base.extend(GENERATED_TEST_FILES)
    return base


def _detect_init_mode(audit: dict[str, Any]) -> str:
    existing = audit.get("existing", {})
    if existing.get("thoth_authority"):
        return "resume"
    if existing.get("research_config"):
        return "adopt"
    if existing.get("agent_os") or existing.get("legacy_agentos_alias"):
        return "adopt"
    if existing.get("docs") or existing.get("dashboard"):
        return "adopt"
    if audit.get("top_level_entries"):
        return "adopt"
    return "init"


def build_init_preview(project_dir: Path, audit: dict[str, Any]) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    preview = {
        "schema_version": 1,
        "generated_at": _utc_iso(),
        "mode": _detect_init_mode(audit),
        "create": [],
        "update": [],
        "preserve": [],
        "remove": [],
    }

    managed_update_targets = {
        ".pre-commit-config.yaml",
        "AGENTS.md",
        "CLAUDE.md",
        ".thoth/derived/codex-hooks.json",
        "tools/dashboard",
    }
    managed_update_targets.update(f"scripts/{name}" for name in GENERATED_SCRIPT_FILES)
    managed_update_targets.update(GENERATED_TEST_FILES)

    managed_create_if_missing = {
        ".thoth/objects/project/project.json",
        ".thoth/docs/project.json",
        ".thoth/docs/agent-entry.md",
        ".thoth/docs/source-map.json",
        ".thoth/runs/.gitkeep",
        ".thoth/migrations/.gitkeep",
        ".thoth/derived/.gitkeep",
    }
    for rel in MANAGED_DIRECTORY_ROOTS:
        path = project_dir / rel
        if path.exists() and not path.is_dir():
            preview["update"].append(rel)

    for rel in sorted(managed_update_targets | managed_create_if_missing):
        path = project_dir / rel
        if rel in managed_update_targets:
            (preview["update"] if path.exists() else preview["create"]).append(rel)
            continue
        if path.exists():
            preview["preserve"].append(rel)
        else:
            preview["create"].append(rel)

    preserve_paths = set(preview["preserve"])
    preserve_paths.update(audit.get("docs_files", []))
    preserve_paths.update(audit.get("agent_os_files", []))
    preserve_paths.update(audit.get("legacy_agentos_files", []))
    preserve_paths.update(audit.get("root_markdown_files", []))
    preview["preserve"] = sorted(preserve_paths)
    preview["remove"] = sorted(rel for rel in LEGACY_REMOVE_PATHS if (project_dir / rel).exists())
    return preview


@dataclass(frozen=True)
class InitPlan:
    mode: str
    create: list[str]
    update: list[str]
    preserve: list[str]
    remove: list[str]
    generated_at: str
    schema_version: int


def build_init_plan(project_dir: Path, audit: dict[str, Any]) -> InitPlan:
    preview = build_init_preview(project_dir, audit)
    return InitPlan(
        mode=str(preview.get("mode") or "init"),
        create=list(preview.get("create") or []),
        update=list(preview.get("update") or []),
        preserve=list(preview.get("preserve") or []),
        remove=list(preview.get("remove") or []),
        generated_at=str(preview.get("generated_at") or ""),
        schema_version=int(preview.get("schema_version") or 1),
    )
