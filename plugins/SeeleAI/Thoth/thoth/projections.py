"""Render host-specific projections from the host-neutral Thoth command specs."""

from __future__ import annotations

import json
from pathlib import Path

from .command_specs import COMMAND_SPECS, CommandSpec, PUBLIC_CODEX_COMMANDS
from .prompt_specs import render_codex_command_micro_prompt, render_command_contract_markdown


ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "thoth"
PLUGIN_VERSION = "0.2.0"
PLUGIN_REPOSITORY = "https://github.com/SeeleAI/Thoth"
PLUGIN_PACKAGE_DIR = "."
PLUGIN_SKILLS_PATH = "./plugins/thoth/skills"


def _frontmatter_allowed_tools(spec: CommandSpec) -> str:
    if not spec.allowed_tools:
        return ""
    return f"allowed-tools: {', '.join(spec.allowed_tools)}\n"


def _claude_bridge_rules(spec: CommandSpec) -> str:
    if spec.route_class == "mechanical_fast":
        return """- Treat the structured bridge payload above as the only authority for this invocation.
- If `bridge_success` is `false`, report the exact bridge failure and stop.
- If stdout starts with `version=`, repeat stdout exactly and output nothing else.
- If `bridge_success` is `true`, report only the real command result in one short receipt.
- If extra evidence is required, inspect only the smallest artifact explicitly named by the bridge payload.
- Do not launch broad Explore, Task, cache/source scans, or background investigation after the bridge result.
- If the result exposes blockers or asks for human decisions, use AskUserQuestion to ask only the unresolved questions and stop.
- Do not expand into runtime explanation, walkthroughs, or extra command execution."""
    rules = [
        "- Treat the structured bridge payload above as the only authority for this command invocation.",
        "- If `bridge_success` is `false`, report the exact bridge failure and stop.",
        "- If `run` or `loop` is missing `--work-id`, show the returned candidate work items exactly as provided and stop.",
        "- If `run` or `loop` is missing `--work-id`, do not invent, create, compile, or guess a work item.",
        "- If `bridge_success` is `true` and runtime events are present, summarize progress, terminal status, and risk from those events only.",
        "- Do not hand-edit `.thoth` or manually call runtime protocol commands; the Thoth RuntimeDriver advances phases.",
        "- If `packet.dispatch_mode` is `external_worker`, do not duplicate the work locally; report the run id, worker mode, and the correct follow-up only.",
        "- If you only describe what should happen next instead of reporting the executed runtime result, treat that as failure.",
    ]
    if spec.command_id in {"run", "loop", "auto"}:
        rules.extend(
            (
                "- If `packet.executor == codex`, the substantive execution must really flow through Codex rather than being silently done by Claude.",
                "- Runtime lifecycle is `plan -> execute -> validate -> reflect`; auto runs selected work through child loops.",
                "- Prefer running `packet.strict_task.eval_entrypoint.command` exactly as provided rather than inventing a parallel validator lifecycle.",
            )
        )
    if spec.command_id in {"run", "loop"}:
        rules.extend(
            (
                "- Use `packet.strict_task.goal_statement`, `packet.strict_task.authority_context`, `packet.strict_task.implementation_recipe`, and `packet.strict_task.eval_entrypoint` as the only task authority.",
                "- If plan reports `authority_complete=false` or `reason=needs_input`, stop and route the user back to `/thoth:discuss` instead of guessing.",
            )
        )
    if spec.command_id == "auto":
        rules.extend(
            (
                "- If the bridge payload exposes `body.monitor_command`, observe that command instead of executing work directly in the Claude session.",
                "- Prefer the Claude Monitor tool with `persistent=true` for `body.monitor_command` when available; otherwise use Bash to run the same watch command in the foreground.",
                "- Treat the monitor/watch JSONL stream as the only live progress authority; summarize progress and risks from those events only.",
                "- If the live observer is interrupted, do not stop the auto controller unless the user explicitly requests `/thoth:auto --stop <controller_id>`.",
            )
        )
    if spec.command_id == "review":
        rules.append(
            "- For `review`, inspect `packet.target`, produce structured findings matching `packet.required_review_shape`, and finish through the review protocol rather than free-form prose."
        )
        rules.append(
            "- If `packet.review_mode` is `exact_match`, reproduce that exact structured result and do not add prose or extra findings."
        )
        rules.append(
            "- If `packet.protocol_commands.complete_exact` exists, execute that exact completion command rather than deriving your own variant."
        )
    if spec.command_id == "discuss":
        rules.extend(
            (
                "- Use AskUserQuestion until goals, non-goals, constraints, accepted decisions, rejected options, acceptance, context evidence, risks, run instructions, and open questions are explicit.",
                "- On major semantic changes, write a draft authority checkpoint through `packet.protocol_commands.checkpoint_authority`.",
                "- When no material assumptions remain, write a semantic-lossless closure through `packet.protocol_commands.close_authority`.",
                "- Do not create ready work if any open_questions remain in the authority capsule.",
            )
        )
    return "\n".join(rules)


def render_claude_command(spec: CommandSpec) -> str:
    runtime_invocation = f'"${{CLAUDE_PLUGIN_ROOT}}/scripts/thoth-claude-command.sh" {spec.command_id} $ARGUMENTS'
    live_packet_contract = spec.intelligence_tier == "high"
    disable_model_invocation = "false" if live_packet_contract else "true"
    if spec.command_id == "discuss":
        runtime_invocation = '''THOTH_DISCUSS_ARGUMENTS_FILE="$(mktemp -t thoth-discuss-arguments.XXXXXX)"
trap 'rm -f "$THOTH_DISCUSS_ARGUMENTS_FILE"' EXIT
cat > "$THOTH_DISCUSS_ARGUMENTS_FILE" <<'THOTH_DISCUSS_ARGUMENTS_EOF'
$ARGUMENTS
THOTH_DISCUSS_ARGUMENTS_EOF
"${CLAUDE_PLUGIN_ROOT}/scripts/thoth-claude-command.sh" discuss --thoth-arguments-file "$THOTH_DISCUSS_ARGUMENTS_FILE"'''
    elif spec.command_id == "review":
        runtime_invocation = f'"${{CLAUDE_PLUGIN_ROOT}}/scripts/thoth-claude-command.sh" {spec.command_id} --host claude $ARGUMENTS'
    elif spec.command_id in {"run", "loop", "auto"}:
        runtime_invocation = f'"${{CLAUDE_PLUGIN_ROOT}}/scripts/thoth-claude-command.sh" {spec.command_id} --host claude $ARGUMENTS'
    response_contract = _claude_bridge_rules(spec)
    prompt_contract = render_command_contract_markdown(spec.command_id, heading_level=3).strip()
    return f"""---
name: thoth:{spec.command_id}
description: {spec.summary}
argument-hint: "{spec.argument_hint}"
disable-model-invocation: {disable_model_invocation}
{_frontmatter_allowed_tools(spec)}---

# /thoth:{spec.command_id}

## Generated Surface

This file is generated from `thoth.command_specs.COMMAND_SPECS`. Do not hand edit.

## Real Runtime Execution

The repo-local Thoth runtime command for this slash command has already been
executed before Claude sees this prompt.

```!
{runtime_invocation}
```

## Response Contract

{response_contract}

## Authority Summary

{prompt_contract}
"""


def render_codex_skill() -> str:
    command_lines = "\n".join(f"- `$thoth {spec.command_id}`: {spec.summary}" for spec in COMMAND_SPECS)
    route_lines = "\n".join(
        f"- `{spec.command_id}` -> `{spec.route_class}` / `{spec.intelligence_tier}` / `{spec.packet_authority_mode}`"
        for spec in COMMAND_SPECS
    )
    return f"""---
name: thoth
description: Official Codex public surface for the Thoth authority runtime. Use this skill when the user wants to operate Thoth through the single `$thoth <command>` public entry.
---

# Thoth

Official Codex public surface for Thoth. This skill is generated from the same host-neutral command specification that renders the Claude `/thoth:*` commands.

## Public Entry

Use the single public entrypoint:

- `$thoth <command>`

Supported commands:
{command_lines}

## Dispatcher

- `.thoth` is the only runtime authority.
- Parse the requested `$thoth <command>`, then open only the matching micro prompt under `./commands/<command>.md`.
- Execute the literal shell command immediately; do not replace it with explanation.
- If `thoth` is not on PATH, use the installed Codex plugin cache or marketplace-root runtime entrypoint described by the micro prompt; do not use a local checkout as fallback.
- If neither PATH nor the installed Codex plugin cache / marketplace root contains the runtime entrypoint, treat that as host install drift.
- Do not create alternative public Codex variants such as `run:codex` or `loop:codex`.

## Route Table

{route_lines}

## Shared Rules

- `init`, `status`, `doctor`, and `dashboard` are mechanical fast-path commands and should return only short receipts.
- `discuss`, `run`, `loop`, `auto`, and open-ended `review` are high-intelligence paths.
- `review` exact-match/probe flows are protocol-fast: if the packet exposes an exact result, do not improvise.
- `run` and `loop` use one RuntimeDriver: lifecycle is `plan -> execute -> validate -> reflect`; live is foreground monitor, `--sleep` is detached monitor.
- Host hooks and subagents may improve throughput but are never correctness requirements.
"""


def render_codex_agent_metadata() -> str:
    return """interface:
  display_name: "thoth"
  short_description: "Official Codex public surface for the Thoth authority runtime."
  default_prompt: "Use $thoth as the single public entrypoint for Thoth and operate the shared .thoth runtime through $thoth <command>."
"""


def render_plugin_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "description": "Official Codex-native public surface for the Thoth authority runtime.",
        "author": {
            "name": "SeeleAI",
            "url": "https://github.com/SeeleAI",
        },
        "homepage": f"{PLUGIN_REPOSITORY}#readme",
        "repository": PLUGIN_REPOSITORY,
        "license": "MIT",
        "keywords": [
            "thoth",
            "codex",
            "claude-code",
            "agent",
            "runtime",
            "dashboard",
        ],
        "skills": PLUGIN_SKILLS_PATH,
        "interface": {
            "displayName": "Thoth",
            "shortDescription": "Single Codex entrypoint for the shared Thoth runtime.",
            "longDescription": "Operate Thoth through one $thoth command surface backed by the shared .thoth authority, durable run ledger, and dashboard-visible project state.",
            "developerName": "SeeleAI",
            "category": "Productivity",
            "capabilities": ["Read", "Write", "Execute"],
            "websiteURL": PLUGIN_REPOSITORY,
            "defaultPrompt": [
                "Show the current Thoth project status and active runs.",
                "Initialize Thoth in this repository and render project layers.",
                "Start a durable Thoth run for the current task.",
            ],
            "composerIcon": "./assets/thoth-icon.svg",
            "brandColor": "#3B82F6",
        },
    }


def render_claude_plugin_manifest() -> dict:
    return {
        "name": PLUGIN_NAME,
        "version": PLUGIN_VERSION,
        "description": "Dashboard-centric Agent Project OS for auditable AI execution, persistent project state, and human-visible workflow orchestration.",
        "author": {
            "name": "SeeleAI",
            "url": "https://github.com/SeeleAI",
        },
        "homepage": PLUGIN_REPOSITORY,
        "repository": PLUGIN_REPOSITORY,
        "license": "MIT",
        "keywords": [
            "research",
            "project-management",
            "dashboard",
            "autonomous",
            "audit",
            "execution",
        ],
    }


def render_claude_marketplace() -> dict:
    return {
        "name": PLUGIN_NAME,
        "owner": {
            "name": "SeeleAI",
            "url": "https://github.com/SeeleAI",
        },
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "description": "Dashboard-centric Agent Project OS with project bootstrap, execution loops, audit visibility, validation, reporting, and executor-mode Codex delegation.",
                "version": PLUGIN_VERSION,
                "author": {
                    "name": "SeeleAI",
                    "url": "https://github.com/SeeleAI",
                },
                "source": "./",
                "category": "productivity",
            }
        ],
    }


def render_codex_marketplace() -> dict:
    return {
        "name": PLUGIN_NAME,
        "interface": {
            "displayName": "Thoth",
        },
        "owner": {
            "name": "SeeleAI",
            "url": "https://github.com/SeeleAI",
        },
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "version": PLUGIN_VERSION,
                "source": {
                    "source": "local",
                    "path": PLUGIN_PACKAGE_DIR,
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Productivity",
            }
        ],
    }


def sync_repository_surfaces(root: Path | None = None) -> list[Path]:
    """Render all generated repository surfaces from the canonical spec."""
    repo_root = (root or ROOT).resolve()
    written: list[Path] = []

    commands_dir = repo_root / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    public_ids = {spec.command_id for spec in COMMAND_SPECS}
    for stale in commands_dir.glob("*.md"):
        if stale.stem not in public_ids:
            stale.unlink()
    for spec in COMMAND_SPECS:
        path = commands_dir / f"{spec.command_id}.md"
        path.write_text(render_claude_command(spec), encoding="utf-8")
        written.append(path)

    plugin_root = repo_root / PLUGIN_PACKAGE_DIR
    plugin_skills_root = repo_root / PLUGIN_SKILLS_PATH.removeprefix("./")
    plugin_skill_path = plugin_skills_root / "thoth" / "SKILL.md"
    plugin_skill_path.parent.mkdir(parents=True, exist_ok=True)
    plugin_skill_path.write_text(render_codex_skill(), encoding="utf-8")
    written.append(plugin_skill_path)

    plugin_commands_dir = plugin_skills_root / "thoth" / "commands"
    plugin_commands_dir.mkdir(parents=True, exist_ok=True)
    for stale in plugin_commands_dir.glob("*.md"):
        if stale.stem not in public_ids:
            stale.unlink()
    for spec in COMMAND_SPECS:
        command_path = plugin_commands_dir / f"{spec.command_id}.md"
        command_path.write_text(render_codex_command_micro_prompt(spec.command_id), encoding="utf-8")
        written.append(command_path)

    plugin_agent_metadata_path = plugin_skills_root / "thoth" / "agents" / "openai.yaml"
    plugin_agent_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    plugin_agent_metadata_path.write_text(render_codex_agent_metadata(), encoding="utf-8")
    written.append(plugin_agent_metadata_path)

    legacy_plugin_path = repo_root / "plugins" / "thoth" / ".codex-plugin" / "plugin.json"
    legacy_plugin_path.unlink(missing_ok=True)
    plugin_path = repo_root / ".codex-plugin" / "plugin.json"
    plugin_path.parent.mkdir(parents=True, exist_ok=True)
    plugin_path.write_text(json.dumps(render_plugin_manifest(), indent=2) + "\n", encoding="utf-8")
    written.append(plugin_path)

    claude_plugin_path = repo_root / ".claude-plugin" / "plugin.json"
    claude_plugin_path.parent.mkdir(parents=True, exist_ok=True)
    claude_plugin_path.write_text(json.dumps(render_claude_plugin_manifest(), indent=2) + "\n", encoding="utf-8")
    written.append(claude_plugin_path)

    claude_marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    claude_marketplace_path.write_text(json.dumps(render_claude_marketplace(), indent=2) + "\n", encoding="utf-8")
    written.append(claude_marketplace_path)

    marketplace_path = repo_root / ".agents" / "plugins" / "marketplace.json"
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    marketplace_path.write_text(json.dumps(render_codex_marketplace(), indent=2) + "\n", encoding="utf-8")
    written.append(marketplace_path)
    return written
