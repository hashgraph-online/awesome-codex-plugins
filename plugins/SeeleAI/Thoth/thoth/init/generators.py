"""Project materialization generators for `.agent-os`, `.thoth`, scripts, and host projections."""

from __future__ import annotations

import json
import os
import shutil
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from thoth.command_specs import COMMAND_SPECS
from thoth.plan.compiler import compile_task_authority
from thoth.plan.store import ensure_work_authority_tree
from thoth.objects import Store

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
GENERATED_SCRIPT_FILES = [
    "install-hooks.sh",
    "check-required-files.sh",
    "session-end-check.sh",
    "validate-all.sh",
    "thoth-cli.sh",
    "thoth-codex-hook.sh",
]
GENERATED_TEST_FILES = ["tests/conftest.py", "tests/test_structure.py"]
MANAGED_DIRECTORY_ROOTS = [".claude", ".thoth", "scripts", "tests", "tools", "tools/dashboard"]
LEGACY_REMOVE_PATHS = [LEGACY_CONFIG_FILE, ".agent-os/research-tasks", "tests/test_validate.py", "tests/test_check_consistency.py", "tests/test_sync_todo.py", "tests/test_verify_completion.py"]
DISCOVERY_CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".vue", ".sh", ".rs", ".go", ".java", ".c", ".cc", ".cpp", ".h", ".hpp"}
THOTH_CLAUDE_BASH_ALLOW_PATTERN = "Bash(*thoth-claude-command.sh*)"

def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_config(config_json: str) -> dict[str, Any]:
    config = json.loads(config_json)
    project_dir = Path.cwd()
    config.setdefault("name", project_dir.name)
    config.setdefault("description", "")
    config.setdefault("language", "zh")
    config.setdefault("directions", [])
    config.setdefault("phases", DEFAULT_PHASES)
    config.setdefault("port", 8501)
    config.setdefault("theme", "warm-bear")

    directions = config["directions"]
    if isinstance(directions, str):
        directions = [d.strip() for d in directions.split(",") if d.strip()]
    config["directions"] = directions
    return config


def _normalize_direction_entry(direction: Any, index: int) -> dict[str, Any]:
    color = DIRECTION_COLORS[index % len(DIRECTION_COLORS)]
    if isinstance(direction, dict):
        direction_id = str(direction.get("id") or f"direction-{index + 1}").strip()
        return {
            "id": direction_id,
            "label_zh": direction.get("label_zh", direction_id),
            "label_en": direction.get("label_en", direction_id.title()),
            "color": direction.get("color", color),
        }
    direction_id = str(direction).strip() or f"direction-{index + 1}"
    return {
        "id": direction_id,
        "label_zh": direction_id,
        "label_en": direction_id.title(),
        "color": color,
    }


def generate_milestones(config: dict[str, Any], project_dir: Path) -> None:
    path = project_dir / ".agent-os" / "milestones.yaml"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content = textwrap.dedent(f"""\
# Milestones for {config['name']}
milestones: []
""")
    path.write_text(content, encoding="utf-8")


def generate_agent_os_docs(config: dict[str, Any], project_dir: Path) -> None:
    name = config["name"]
    templates = {
        "project-index.md": f"# Project Index\n\n- Project: {name}\n- Status: Initialized\n",
        "requirements.md": "# Requirements\n\n## User Goals\n- (Define goals here)\n",
        "architecture-milestones.md": "# Architecture & Milestones\n\n## Current Architecture\n- (Describe architecture)\n",
        "todo.md": "# TODO\n\n## Backlog\n\n## Ready\n\n## Doing\n\n## Blocked\n\n## Done\n\n## Verified\n\n## Abandoned\n",
        "cross-repo-mapping.md": "# Cross-Repo Mapping\n\n| Main ID | Local ID | Repo | Status |\n|---------|----------|------|--------|\n| (none) | | | |\n",
        "acceptance-report.md": "# Acceptance Report\n\n- No conclusions yet.\n",
        "lessons-learned.md": "# Lessons Learned\n\n- No failed explorations recorded yet.\n",
        "run-log.md": f"# Run Log\n\n- {_now_str()} [project initialization]\n  - Worked on: Project setup\n  - Evidence produced: .thoth authority, AGENTS.md, CLAUDE.md, codex hook projection\n",
        "change-decisions.md": f"# Change Decisions\n\n| ID | Date | Decision | Rationale | Impact |\n|----|------|----------|-----------|--------|\n| CD-001 | {_now_str()[:10]} | Project initialized | Starting from scratch | All files created |\n",
    }
    agent_os = project_dir / ".agent-os"
    agent_os.mkdir(parents=True, exist_ok=True)
    for filename, content in templates.items():
        path = agent_os / filename
        if path.exists():
            continue
        path.write_text(content, encoding="utf-8")


def generate_dashboard(config: dict[str, Any], project_dir: Path) -> None:
    src = TEMPLATES_DIR / "dashboard"
    dest = project_dir / "tools" / "dashboard"
    shutil.copytree(src, dest, dirs_exist_ok=True)
    _write_dashboard_locale_selection(config, project_dir)


def _write_dashboard_locale_selection(config: dict[str, Any], project_dir: Path) -> None:
    locale = "en" if str(config.get("language", "zh")).strip().lower().startswith("en") else "zh"
    path = project_dir / "tools" / "dashboard" / "frontend" / "src" / "generated" / "locale.ts"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"export const defaultLocale = '{locale}' as const\n",
        encoding="utf-8",
    )


def render_project_instructions(config: dict[str, Any]) -> str:
    commands = "\n".join(f"- `{spec.command_id}`: {spec.summary}" for spec in COMMAND_SPECS)
    return textwrap.dedent(f"""\
# Thoth Project Instructions

This document is the canonical human-readable project instruction source for `{config["name"]}`.

## Runtime Authority

- `.thoth` is the only runtime authority.
- Canonical storage lives in `.thoth/objects/<kind>/<object_id>.json`.
- Planning authority is object-graph driven: `discussion -> decision -> work_item`.
- `work_item` replaces old contract/task authority; runnable work must be `ready`.
- `run` and `loop` only execute ready runnable work by `--work-id`.
- Current work-item payloads use `work_id`, `work_kind`, and `runnable`; old `task_id` and `work_type` fields are legacy migration inputs only.
- Free-form execution is forbidden; ambiguous work must go back through `discuss`.
- `init` must audit the current repository before it standardizes any Thoth-managed surface.
- `run` and `loop` are durable by default and support attach/watch/stop lifecycle.
- Hooks and subagents may enhance throughput but are never correctness requirements.
- Claude Code and Codex project surfaces must stay aligned when new features are introduced.

## Recovery Order

1. Read this file.
2. Read `.thoth/docs/agent-entry.md`.
3. Read `.thoth/docs/object-graph-summary.json`.
4. Read generated project docs only as read views, not authority.

## Public Surfaces

{commands}
""")


def generate_thoth_runtime(config: dict[str, Any], project_dir: Path) -> None:
    thoth_dir = project_dir / ".thoth"
    for rel in ("objects", "docs", "runs", "migrations", "derived"):
        (thoth_dir / rel).mkdir(parents=True, exist_ok=True)
    ensure_work_authority_tree(project_dir)
    directions = [_normalize_direction_entry(direction, index) for index, direction in enumerate(config.get("directions", []))]
    project_payload = {
        "name": config["name"],
        "description": config.get("description", ""),
        "language": config.get("language", "zh"),
        "directions": directions,
        "phases": config.get("phases", DEFAULT_PHASES),
    }
    dashboard_payload = {
        "port": config.get("port", 8501),
        "theme": config.get("theme", "warm-bear"),
    }
    Store(project_dir).upsert(
        kind="project",
        object_id="project",
        status="active",
        title=config["name"],
        summary=config.get("description", ""),
        source="init",
        payload={
            "project": project_payload,
            "dashboard": dashboard_payload,
            "runtime": {
                "authority": ".thoth/objects",
                "runs_dir": ".thoth/runs",
                "docs_dir": ".thoth/docs",
                "execution_policy": {
                    "mode": "ready-work-only",
                    "free_form_execution": False,
                    "work_source": ".thoth/objects/work_item",
                },
            },
            "hosts": {
                "claude": {"projection": "CLAUDE.md"},
                "codex": {"projection": "AGENTS.md"},
            },
        },
    )
    manifest = {
        "schema_version": 3,
        "project": project_payload,
        "dashboard": dashboard_payload,
        "runtime": {
            "authority": ".thoth/objects",
            "runs_dir": ".thoth/runs",
            "docs_dir": ".thoth/docs",
            "project_object": ".thoth/objects/project/project.json",
            "work_item_dir": ".thoth/objects/work_item",
            "object_graph_summary": ".thoth/docs/object-graph-summary.json",
            "execution_policy": {
                "mode": "ready-work-only",
                "free_form_execution": False,
                "work_source": ".thoth/objects/work_item",
            },
        },
        "hosts": {
            "claude": {"projection": "CLAUDE.md"},
            "codex": {"projection": "AGENTS.md"},
        },
        "legacy_removed": {
            "agent_os_authority": True,
            "contract_kind": True,
            "task_compiler": True,
            "dashboard_sqlite_authority": True,
        },
    }
    (thoth_dir / "docs" / "project.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (thoth_dir / "docs" / "agent-entry.md").write_text(render_project_instructions(config), encoding="utf-8")
    for rel in ("runs/.gitkeep", "migrations/.gitkeep", "derived/.gitkeep"):
        (thoth_dir / rel).write_text("", encoding="utf-8")
    compile_task_authority(project_dir)


def generate_pre_commit_config(config: dict[str, Any], project_dir: Path) -> None:
    content = textwrap.dedent("""\
repos:
  - repo: local
    hooks:
      - id: thoth-doctor
        name: Validate strict Thoth authority
        entry: bash scripts/thoth-cli.sh doctor --json
        language: system
        pass_filenames: false
      - id: thoth-sync
        name: Refresh generated Thoth projections
        entry: bash scripts/thoth-cli.sh init --sync
        language: system
        pass_filenames: false
""")
    (project_dir / ".pre-commit-config.yaml").write_text(content, encoding="utf-8")


def generate_scripts(config: dict[str, Any], project_dir: Path) -> None:
    scripts_dir = project_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    scripts = {
        "install-hooks.sh": "#!/usr/bin/env bash\nset -e\npre-commit install\n",
        "check-required-files.sh": "#!/usr/bin/env bash\nset -e\nfor f in .thoth/objects/project/project.json .thoth/docs/agent-entry.md .thoth/docs/object-graph-summary.json .thoth/derived/codex-hooks.json; do test -f \"$f\" || { echo \"MISSING: $f\"; exit 1; }; done\n",
        "thoth-cli.sh": "#!/usr/bin/env bash\nset -euo pipefail\nROOT=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"\ncd \"$ROOT\"\nif command -v thoth >/dev/null 2>&1; then\n  exec thoth \"$@\"\nfi\nif [ -n \"${THOTH_SOURCE_ROOT:-}\" ]; then\n  export PYTHONPATH=\"${THOTH_SOURCE_ROOT}${PYTHONPATH:+:${PYTHONPATH}}\"\n  exec python -m thoth.cli \"$@\"\nfi\necho \"Missing Thoth shell wrapper. Install drift: expected 'thoth' on PATH or THOTH_SOURCE_ROOT for source-checkout fallback.\" >&2\nexit 1\n",
        "session-end-check.sh": "#!/usr/bin/env bash\nset -euo pipefail\nbash scripts/thoth-cli.sh init --sync\nbash scripts/thoth-cli.sh doctor\nbash scripts/check-required-files.sh\n",
        "validate-all.sh": "#!/usr/bin/env bash\nset -euo pipefail\nbash scripts/thoth-cli.sh init --sync\nbash scripts/thoth-cli.sh doctor\nbash scripts/check-required-files.sh\n",
        "thoth-codex-hook.sh": "#!/usr/bin/env bash\nset -euo pipefail\nROOT=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"\ncd \"$ROOT\"\nEVENT=\"${1:-}\"\nif [ -z \"$EVENT\" ]; then\n  echo \"Usage: thoth-codex-hook.sh <start|stop>\" >&2\n  exit 0\nfi\nif command -v thoth >/dev/null 2>&1; then\n  exec thoth hook --host codex --event \"$EVENT\"\nfi\nif [ -n \"${THOTH_SOURCE_ROOT:-}\" ]; then\n  export PYTHONPATH=\"${THOTH_SOURCE_ROOT}${PYTHONPATH:+:${PYTHONPATH}}\"\n  exec python -m thoth.cli hook --host codex --event \"$EVENT\"\nfi\nexit 0\n",
    }
    for filename, content in scripts.items():
        path = scripts_dir / filename
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)


def render_host_projection(config: dict[str, Any]) -> str:
    return textwrap.dedent(f"""\
# AGENTS.md

This file is a generated project operation contract for `{config["name"]}`.

## Mission

- Preserve user-defined goals, requirements, and acceptance boundaries.
- Recover context from files rather than chat history.
- Treat `.thoth/objects` as the only project/runtime authority.

## Recovery Order

1. Read this file.
2. Read `.thoth/docs/agent-entry.md`.
3. Read `.thoth/docs/object-graph-summary.json`.
4. Read `.thoth/objects/project/project.json` and relevant linked objects.

## Runtime Rules

- Planning authority lives in `.thoth/objects/discussion`, `.thoth/objects/decision`, and `.thoth/objects/work_item`.
- There is no standalone Contract kind; goal, constraints, execution plan, eval, runtime policy, and decisions live inside `work_item.payload`.
- Current executable authority uses `work_item`, `work_id`, `work_kind`, and `runnable`.
- Legacy `task_id` and `work_type` inputs may be read only by managed migration; current authority objects must not write them.
- `run` and `loop` execute by `--work-id` only; free-form goals belong in `discuss`.
- `discuss` owns unresolved intent. If goals, constraints, acceptance, or authority are unclear, keep the work in discussion instead of creating runnable work.
- Active run/controller references lock the target work item until terminal state.
- `run` and `loop` are durable by default and support attach/watch/stop lifecycle.
- Hooks and subagents may enhance throughput but are never correctness dependencies.
- Dashboard, status, and doctor are read surfaces derived from `.thoth/objects` and `.thoth/runs/*`; they are not authority writers.
- New feature work must keep Claude Code and Codex project surfaces in sync.

## Think Before Coding

- State material assumptions before implementing.
- If multiple interpretations are plausible, expose the difference instead of silently choosing.
- If the simple solution satisfies the work item and validator, prefer it.
- If important context is missing, return to `discuss` rather than guessing.

## Simplicity First

- Implement only what the current work item requires.
- Do not add speculative configurability, abstractions, or future-proofing.
- Avoid defensive branches for impossible cases unless the work item or validator requires them.
- If the implementation grows larger than the problem, reduce the scope before continuing.

## Surgical Changes

- Edit only files needed for the current work item.
- Preserve local style and surrounding structure.
- Remove only dead imports, variables, or helpers caused by the current change.
- Report adjacent issues separately instead of folding them into unrelated edits.

## Goal-Driven Execution

- Translate broad requests into verifiable success conditions.
- Reproduce bugs before fixing when possible.
- Verify the exact behavior changed by the implementation.
- Do not mark work complete until implementation, validation, and evidence are recorded.
""")


def generate_host_projections(config: dict[str, Any], project_dir: Path) -> None:
    content = render_host_projection(config)
    agents_path = project_dir / "AGENTS.md"
    claude_path = project_dir / "CLAUDE.md"
    agents_path.write_text(content, encoding="utf-8")
    try:
        if claude_path.exists():
            claude_path.unlink()
        os.link(agents_path, claude_path)
    except OSError:
        claude_path.write_text(content, encoding="utf-8")


def render_codex_hooks_payload() -> dict[str, Any]:
    def _hook_command(event: str) -> str:
        return (
            "bash -lc '"
            f"if command -v thoth >/dev/null 2>&1; then exec thoth hook --host codex --event {event}; fi; "
            "ROOT=\"$(git rev-parse --show-toplevel 2>/dev/null || pwd)\"; "
            f"if [ -x \"$ROOT/scripts/thoth-codex-hook.sh\" ]; then exec bash \"$ROOT/scripts/thoth-codex-hook.sh\" {event}; fi; "
            "exit 0'"
        )

    return {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": _hook_command("start"),
                            "statusMessage": "Loading Thoth runtime context",
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": _hook_command("stop"),
                            "statusMessage": "Recording Thoth runtime summary",
                        }
                    ],
                }
            ],
        }
    }


def generate_codex_hook_projection(project_dir: Path) -> None:
    payload = render_codex_hooks_payload()
    path = project_dir / ".thoth" / "derived" / "codex-hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_tests(config: dict[str, Any], project_dir: Path) -> None:
    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "conftest.py").write_text("from pathlib import Path\n\nPROJECT_ROOT = Path(__file__).parent.parent\n", encoding="utf-8")
    (tests_dir / "test_structure.py").write_text(textwrap.dedent("""\
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".thoth/objects/project/project.json",
    ".thoth/docs/agent-entry.md",
    ".thoth/docs/object-graph-summary.json",
    ".thoth/docs/legacy-audit.json",
    ".thoth/derived/codex-hooks.json",
]


def test_required_files_exist():
    root = Path(__file__).parent.parent
    missing = [path for path in REQUIRED_FILES if not (root / path).exists()]
    assert not missing, missing
"""), encoding="utf-8")
