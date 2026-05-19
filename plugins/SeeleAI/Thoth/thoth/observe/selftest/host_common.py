from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import selectors
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError
from urllib.request import urlopen

import yaml

from thoth.init.render import render_codex_hooks_payload
from thoth.plan.compiler import compile_task_authority
from thoth.prompt_specs import (
    build_codex_selftest_command_probe_prompt,
    build_codex_selftest_review_probe_prompt,
    codex_installed_runtime_shell_command,
)
from thoth.run.io import project_hash
from thoth.run.ledger import complete_run, heartbeat_run
from thoth.selftest_seed import seed_host_real_app

from .model import *
from .recorder import *
from .processes import *
from .capabilities import *
from .fixtures import *
from .hard_suite import *
from .hard_suite import _local_supervisor

def _looks_like_transient_host_outage(result: CommandResult) -> bool:
    detail = f"{result.stdout}\n{result.stderr}".lower()
    return any(
        marker in detail
        for marker in (
            "api error: 503",
            '"subtype":"api_retry"',
            '"error_status":503',
            '"error":"server_error"',
            "no available accounts",
            "server-side issue",
            "try again in a moment",
            "status.claude.com",
            "temporarily unavailable",
            "无可用渠道",
        )
    )


def _run_supervisor_path(project_dir: Path, run_id: str) -> Path:
    return _host_local_registry_root(project_dir) / "runs" / run_id / "supervisor.json"


def _controller_supervisor_path(project_dir: Path, controller_id: str) -> Path:
    return _host_local_registry_root(project_dir) / "controllers" / controller_id / "supervisor.json"


def _host_local_state_env(project_dir: Path) -> dict[str, str]:
    return {"THOTH_LOCAL_STATE_DIR": str(project_dir / ".thoth" / "local-state")}


def _host_local_registry_root(project_dir: Path) -> Path:
    return Path(_host_local_state_env(project_dir)["THOTH_LOCAL_STATE_DIR"]) / project_hash(project_dir)


def _looks_like_claude_bridge_cold_start(result: CommandResult) -> bool:
    if result.returncode != 124:
        return False
    stdout = result.stdout
    if '"hook_event":"SessionStart"' not in stdout and '"hook_name":"SessionStart:startup"' not in stdout:
        return False
    return '"subtype":"task_started"' not in stdout


def _is_live_packet_public_command(public_command: str) -> bool:
    normalized = public_command.strip()
    if any(flag in normalized.split() for flag in ("--sleep", "--attach", "--watch", "--stop", "--resume")):
        return False
    prefixes = (
        "/thoth:run",
        "/thoth:loop",
        "/thoth:review",
        "$thoth run",
        "$thoth loop",
        "$thoth review",
        "thoth run",
        "thoth loop",
        "thoth review",
    )
    return normalized.startswith(prefixes)


def _effective_host_command_timeout(host_name: str, public_command: str, requested_timeout: float) -> float:
    if host_name == "claude" and not _is_live_packet_public_command(public_command):
        # Bridge-only slash commands should return quickly. Keeping this bounded
        # prevents upstream account outages from consuming the entire heavy gate.
        return min(requested_timeout, 25.0)
    return requested_timeout


def _claude_expected_args(public_command: str) -> list[str]:
    parts = shlex.split(public_command.strip())
    return parts[1:] if len(parts) > 1 else []


def _claude_arguments_match(event_arguments: list[Any], expected_args: list[str]) -> bool:
    normalized_event_args = [str(item) for item in event_arguments]
    if normalized_event_args == expected_args:
        return True
    if normalized_event_args[:2] == ["--host", "claude"]:
        return normalized_event_args[2:] == expected_args
    return False


def _read_claude_bridge_events(project_dir: Path) -> list[dict[str, Any]]:
    path = project_dir / ".thoth" / "derived" / "host-bridges" / "claude-command-events.jsonl"
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _normalize_claude_public_command_result(
    result: CommandResult,
    *,
    bridge_event: dict[str, Any],
) -> CommandResult:
    if result.returncode == 0:
        return result
    if result.returncode != 124:
        return result
    if not bridge_event or bridge_event.get("bridge_success") is not True or int(bridge_event.get("returncode", 1)) != 0:
        return result
    if "command timed out after" not in result.stderr.lower():
        return result
    return CommandResult(
        argv=result.argv,
        cwd=result.cwd,
        returncode=0,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=result.duration_seconds,
    )


def _write_claude_local_settings(project_dir: Path, repo_root: Path, recorder: Recorder) -> str:
    settings_path = project_dir / ".claude" / "settings.local.json"
    payload = {
        "$schema": "https://json.schemastore.org/claude-code-settings.json",
        "permissions": {
            "allow": [
                f"Bash(*{repo_root / 'scripts' / 'thoth-claude-command.sh'}*)",
            ]
        },
    }
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return recorder.write_text("claude/settings.local.json", settings_path.read_text(encoding="utf-8"))


def _run_claude_public_command(
    repo_root: Path,
    project_dir: Path,
    slash_command: str,
    *,
    recorder: Recorder,
    artifact_name: str,
    timeout: float = 240,
    env: dict[str, str] | None = None,
) -> tuple[CommandResult, list[str]]:
    result = _run_command(
        [
            "claude",
            "-p",
            "--plugin-dir",
            str(repo_root),
            "--permission-mode",
            "dontAsk",
            "--verbose",
            "--output-format",
            "stream-json",
            "--include-hook-events",
            slash_command,
        ],
        cwd=project_dir,
        env=env,
        timeout=timeout,
    )
    return result, _save_command(recorder, artifact_name, result)


def _public_command_id(public_command: str) -> str:
    normalized = public_command.strip()
    if normalized.startswith("/thoth:"):
        head = normalized.split()[0]
        return head.removeprefix("/thoth:").strip() or "status"
    parts = shlex.split(normalized)
    if parts and parts[0] == "$thoth":
        return parts[1] if len(parts) >= 2 else "status"
    if parts and parts[0] == "thoth":
        return parts[1] if len(parts) >= 2 else "status"
    return parts[1] if len(parts) >= 2 else "status"


def _codex_prompt_for_public_command(public_command: str, done_token: str) -> str:
    shell_command = _shell_command_for_public_command(public_command)
    command_id = _public_command_id(public_command)
    if command_id == "review":
        return build_codex_selftest_review_probe_prompt(
            public_command=public_command,
            shell_command=shell_command,
            done_token=done_token,
        )
    return build_codex_selftest_command_probe_prompt(
        public_command=public_command,
        shell_command=shell_command,
        done_token=done_token,
    )


def _shell_command_for_public_command(public_command: str) -> str:
    shell_command = public_command.strip()
    if shell_command.startswith("$thoth ") or shell_command.startswith("thoth "):
        shell_command = codex_installed_runtime_shell_command(shell_command)
    return shell_command


def _canonical_public_shell_command(public_command: str) -> str:
    shell_command = public_command.strip()
    if shell_command.startswith("$thoth "):
        return f"thoth {shell_command[len('$thoth '):]}"
    return shell_command


def _codex_command_matches_public_command(command: str, public_command: str) -> bool:
    shell_command = _shell_command_for_public_command(public_command)
    canonical_command = _canonical_public_shell_command(public_command)
    if shell_command in command or canonical_command in command:
        return True
    public_parts = shlex.split(public_command.strip())
    if not public_parts or public_parts[0] not in {"$thoth", "thoth"} or len(public_parts) < 2:
        return False
    command_id = public_parts[1]
    if f" thoth {command_id}" not in command and f"' thoth {command_id}" not in command:
        return False
    required_flags = {
        "--decision-json",
        "--work-json",
        "--work-id",
        "--host",
        "--executor",
        "--sleep",
        "--watch",
        "--stop",
        "--rounds",
        "--min-runtime-seconds",
        "--quick",
    }
    for part in public_parts[2:]:
        if part.startswith("--") and part in required_flags and part not in command:
            return False
        if part.startswith("--"):
            continue
        if part.startswith("$("):
            continue
        if part and part not in command and part not in {"codex"}:
            return False
    return True


def _run_codex_public_command(
    project_dir: Path,
    public_command: str,
    *,
    done_token: str,
    recorder: Recorder,
    artifact_name: str,
    timeout: float = 240,
    env: dict[str, str] | None = None,
) -> tuple[CommandResult, list[str]]:
    result = _run_command(
        [
            "codex",
            "exec",
            "-m",
            os.environ.get("THOTH_CODEX_EXEC_MODEL", "gpt-5.4"),
            "--json",
            "--sandbox",
            "workspace-write",
            "-C",
            str(project_dir),
            _codex_prompt_for_public_command(public_command, done_token),
        ],
        cwd=project_dir,
        env=env,
        timeout=timeout,
    )
    return result, _save_command(recorder, artifact_name, result)


def _codex_completed_command_items(stdout: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("type") != "item.completed":
            continue
        item = payload.get("item")
        if isinstance(item, dict) and item.get("type") == "command_execution":
            items.append(item)
    return items


def _codex_command_item(stdout: str, public_command: str) -> dict[str, Any]:
    for item in _codex_completed_command_items(stdout):
        command = str(item.get("command") or "")
        if _codex_command_matches_public_command(command, public_command):
            return item
    return {}


def _normalize_codex_public_command_result(
    result: CommandResult,
    *,
    public_command: str,
    done_token: str,
    allow_followup_commands: bool = False,
) -> CommandResult:
    completed_commands = _codex_completed_command_items(result.stdout)
    shell_command = _shell_command_for_public_command(public_command)
    canonical_command = _canonical_public_shell_command(public_command)
    is_watch_probe = "--watch" in shlex.split(canonical_command)
    command_id = _public_command_id(public_command)
    matching_commands = [
        item
        for item in completed_commands
        if _codex_command_matches_public_command(str(item.get("command") or ""), public_command)
    ]
    public_step = matching_commands[0] if matching_commands else None
    if public_step is None:
        return CommandResult(
            argv=result.argv,
            cwd=result.cwd,
            returncode=1,
            stdout=result.stdout,
            stderr=(result.stderr + "\nCodex did not execute the requested shell command: " + shell_command).strip(),
            duration_seconds=result.duration_seconds,
        )
    if public_step.get("status") != "completed" or int(public_step.get("exit_code") or 0) != 0:
        return CommandResult(
            argv=result.argv,
            cwd=result.cwd,
            returncode=1,
            stdout=result.stdout,
            stderr=(
                result.stderr
                + "\nCodex command execution failed: "
                + json.dumps(
                    {
                        "command": public_step.get("command"),
                        "status": public_step.get("status"),
                        "exit_code": public_step.get("exit_code"),
                    },
                    ensure_ascii=False,
                )
            ).strip(),
            duration_seconds=result.duration_seconds,
        )
    if not allow_followup_commands:
        if len(completed_commands) != 1:
            return CommandResult(
                argv=result.argv,
                cwd=result.cwd,
                returncode=1,
                stdout=result.stdout,
                stderr=(
                    result.stderr
                    + "\nCodex executed unexpected extra shell commands during a literal command probe."
                ).strip(),
                duration_seconds=result.duration_seconds,
            )
        failed_commands = [
            item
            for item in completed_commands
            if item.get("status") != "completed" or int(item.get("exit_code") or 0) != 0
        ]
        if failed_commands:
            first = failed_commands[0]
            return CommandResult(
                argv=result.argv,
                cwd=result.cwd,
                returncode=1,
                stdout=result.stdout,
                stderr=(
                    result.stderr
                    + "\nCodex command execution failed: "
                    + json.dumps(
                        {
                            "command": first.get("command"),
                            "status": first.get("status"),
                            "exit_code": first.get("exit_code"),
                        },
                        ensure_ascii=False,
                    )
                ).strip(),
                duration_seconds=result.duration_seconds,
            )
    missing_done_token = done_token not in result.stdout
    if missing_done_token and not is_watch_probe and command_id == "review":
        return CommandResult(
            argv=result.argv,
            cwd=result.cwd,
            returncode=1,
            stdout=result.stdout,
            stderr=(result.stderr + f"\nMissing done token: {done_token}").strip(),
            duration_seconds=result.duration_seconds,
        )
    if result.returncode != 0:
        return CommandResult(
            argv=result.argv,
            cwd=result.cwd,
            returncode=0,
            stdout=result.stdout,
            stderr=result.stderr,
            duration_seconds=result.duration_seconds,
        )
    return result


def _run_host_real_flow(
    host_name: str,
    project_dir: Path,
    recorder: Recorder,
    *,
    run_public_command,
    commands: dict[str, Any],
    review_expected_executor: str | None = None,
    review_expected_result: dict[str, Any] | None = None,
    from_step: str | None = None,
    to_step: str | None = None,
) -> tuple[list[str], dict[str, CommandResult]]:
    artifacts: list[str] = []
    command_results: dict[str, CommandResult] = {}
    claude_step_events: dict[str, dict[str, Any]] = {}
    seen_run_ids: set[str] = set()
    seen_controller_ids: set[str] = set()
    source_baseline = _host_real_source_fingerprint(project_dir)
    transient_retry_limit = 2
    transient_retry_window_seconds = 90.0
    ordered_step_ids = [
        "init",
        "status",
        "doctor",
        "discuss-decision",
        *[f"discuss-contract-{index}" for index, _ in enumerate(commands["discuss_contracts"], start=1)],
        "run-live",
        "run-sleep",
        "run-watch",
        "run-stop",
        "review",
        "dashboard-start",
        "dashboard-stop",
        "loop-live",
        "loop-sleep",
        "loop-stop",
        "auto",
        "auto-stop",
    ]
    ordered_step_ids.append("sync")
    step_index = {step_id: index for index, step_id in enumerate(ordered_step_ids)}
    if from_step is not None and from_step not in step_index:
        raise RuntimeError(f"unknown host-real from-step: {from_step}")
    if to_step is not None and to_step not in step_index:
        raise RuntimeError(f"unknown host-real to-step: {to_step}")
    start_index = step_index.get(from_step, 0)
    end_index = step_index.get(to_step, len(ordered_step_ids) - 1)
    if start_index > end_index:
        raise RuntimeError(f"invalid host-real step window: from-step={from_step} after to-step={to_step}")

    def is_sleep_command(public_command: str) -> bool:
        return "--sleep" in public_command.split()

    def expected_dispatch(public_command: str) -> str:
        return "external_worker" if is_sleep_command(public_command) else "live_native"

    def step_mode(step_id: str) -> str:
        index = step_index[step_id]
        if index < start_index or index > end_index:
            return "skipped"
        return "selected"

    def should_run(step_id: str) -> bool:
        index = step_index[step_id]
        return start_index <= index <= end_index

    def check_name(base: str, mode: str) -> str:
        if mode == "selected":
            return f"host.{host_name}.{base}"
        return f"host.{host_name}.prereq.{base}"

    def _command_check_name(step_id: str, mode: str) -> str:
        return check_name(f"command_executed.{step_id.replace('-', '_')}", mode)

    def _runtime_check_name(step_id: str, mode: str) -> str:
        return check_name(f"runtime_contract_ok.{step_id.replace('-', '_')}", mode)

    def _output_check_name(step_id: str, mode: str) -> str:
        return check_name(f"output_exact_match.{step_id.replace('-', '_')}", mode)

    def _matching_claude_event(previous_count: int, public_command: str) -> dict[str, Any]:
        expected_command_id = _public_command_id(public_command)
        expected_args = _claude_expected_args(public_command)
        events = _read_claude_bridge_events(project_dir)
        for event in events[previous_count:]:
            if event.get("command_id") != expected_command_id:
                continue
            if not _claude_arguments_match(list(event.get("arguments") or []), expected_args):
                continue
            return event
        return {}

    def _command_output(step_id: str, public_command: str, result: CommandResult) -> str:
        if host_name == "codex":
            item = _codex_command_item(result.stdout, public_command)
            return str(item.get("aggregated_output") or "")
        return str(claude_step_events.get(step_id, {}).get("stdout") or "")

    def _guard_source(step_id: str, mode: str) -> None:
        unchanged, payload = _host_real_source_unchanged(project_dir, source_baseline)
        artifact = recorder.write_json(
            f"host-{host_name}-{step_id}-source-guard.json",
            payload,
        )
        recorder.add(
            check_name(f"no_source_write.{step_id.replace('-', '_')}", mode),
            "passed" if unchanged else "failed",
            "Probe source files under tracker/ remained unchanged.",
            [artifact],
        )
        if not unchanged:
            raise RuntimeError(f"{host_name} step {step_id} modified probe source files")

    def _verify_sleep_probe_started(
        *,
        step_id: str,
        mode: str,
        run_id: str,
        expected_kind: str,
        expected_work_id: str,
        public_command: str,
        expected_executor: str | None = None,
    ) -> None:
        _wait_until(
            lambda: _state_payload(project_dir, run_id).get("status") in {"running", "completed", "failed", "stopped"},
            timeout=20,
            interval=0.5,
            description=f"{host_name} {step_id} {run_id} to start",
        )
        run = _run_payload(project_dir, run_id)
        state = _state_payload(project_dir, run_id)
        supervisor = _local_supervisor(project_dir, run_id)
        events = _events_payload(project_dir, run_id)
        worker_started = any("external worker" in str(event.get("message") or "").lower() for event in events)
        ok = (
            run.get("kind") == expected_kind
            and run.get("work_id") == expected_work_id
            and run.get("host") == host_name
            and run.get("dispatch_mode") == expected_dispatch(public_command)
            and bool(run.get("attachable", False))
            and state.get("status") == "running"
            and (
                str(supervisor.get("runtime") or "") == "external_worker"
                or str(state.get("supervisor_state") or "") == "running"
            )
            and worker_started
        )
        if expected_executor is not None:
            ok = ok and run.get("executor") == expected_executor
        detail = (
            f"Verified {expected_kind} sleep probe {run_id}: "
            f"status={state.get('status')} attachable={run.get('attachable')} "
            f"dispatch={run.get('dispatch_mode')} executor={run.get('executor')} "
            f"supervisor={supervisor.get('state') or state.get('supervisor_state')}"
        )
        recorder.add(_runtime_check_name(step_id, mode), "passed" if ok else "failed", detail, [
            str(project_dir / ".thoth" / "runs" / run_id / "run.json"),
            str(project_dir / ".thoth" / "runs" / run_id / "state.json"),
            str(project_dir / ".thoth" / "runs" / run_id / "events.jsonl"),
            str(_run_supervisor_path(project_dir, run_id)),
        ])
        if not ok:
            raise RuntimeError(f"{host_name} step {step_id} did not establish the expected runtime contract")
        _guard_source(step_id, mode)

    def _verify_live_probe_prepared(
        *,
        step_id: str,
        mode: str,
        run_id: str,
        expected_kind: str,
        expected_work_id: str,
        public_command: str,
        expected_executor: str | None = None,
    ) -> None:
        _wait_until(
            lambda: _state_payload(project_dir, run_id).get("status") in {"running", "completed", "failed", "stopped"},
            timeout=20,
            interval=0.5,
            description=f"{host_name} {step_id} {run_id} to prepare",
        )
        run = _run_payload(project_dir, run_id)
        state = _state_payload(project_dir, run_id)
        packet = _read_json(project_dir / ".thoth" / "runs" / run_id / "packet.json")
        ok = (
            run.get("kind") == expected_kind
            and run.get("work_id") == expected_work_id
            and run.get("host") == host_name
            and run.get("dispatch_mode") == expected_dispatch(public_command)
            and (
                (state.get("status") == "running" and bool(run.get("attachable", False)))
                or (state.get("status") == "completed" and not bool(run.get("attachable", True)))
            )
            and packet.get("dispatch_mode") == expected_dispatch(public_command)
        )
        if expected_executor is not None:
            ok = ok and run.get("executor") == expected_executor
        detail = (
            f"Verified {expected_kind} live probe {run_id}: "
            f"status={state.get('status')} attachable={run.get('attachable')} "
            f"dispatch={run.get('dispatch_mode')} executor={run.get('executor')}"
        )
        recorder.add(
            _runtime_check_name(step_id, mode),
            "passed" if ok else "failed",
            detail,
            [
                str(project_dir / ".thoth" / "runs" / run_id / "run.json"),
                str(project_dir / ".thoth" / "runs" / run_id / "state.json"),
                str(project_dir / ".thoth" / "runs" / run_id / "packet.json"),
            ],
        )
        if not ok:
            raise RuntimeError(f"{host_name} step {step_id} did not prepare or complete the expected live packet")
        _guard_source(step_id, mode)

    def _verify_sleep_probe_stopped(
        *,
        step_id: str,
        mode: str,
        run_id: str,
        expected_kind: str,
    ) -> None:
        _wait_until(
            lambda: _state_payload(project_dir, run_id).get("status") == "stopped",
            timeout=15,
            interval=0.5,
            description=f"{host_name} {step_id} {run_id} to stop",
        )
        run = _run_payload(project_dir, run_id)
        state = _state_payload(project_dir, run_id)
        result_payload = _result_payload(project_dir, run_id)
        ok = (
            run.get("kind") == expected_kind
            and state.get("status") == "stopped"
            and result_payload.get("status") == "stopped"
            and not bool(run.get("attachable", True))
        )
        detail = (
            f"Verified stopped {expected_kind} probe {run_id}: "
            f"status={state.get('status')} result={result_payload.get('status')} attachable={run.get('attachable')}"
        )
        recorder.add(_runtime_check_name(step_id, mode), "passed" if ok else "failed", detail, [
            str(project_dir / ".thoth" / "runs" / run_id / "run.json"),
            str(project_dir / ".thoth" / "runs" / run_id / "state.json"),
            str(project_dir / ".thoth" / "runs" / run_id / "result.json"),
        ])
        if not ok:
            raise RuntimeError(f"{host_name} step {step_id} did not stop cleanly")
        _guard_source(step_id, mode)

    def _verify_watch_output(*, step_id: str, mode: str, run_id: str, public_command: str, result: CommandResult) -> None:
        output = _command_output(step_id, public_command, result)
        ok = run_id in output and "status=" in output and "dispatch=external_worker" in output
        if not ok:
            summary_marker = f'"summary": "Watching {run_id}"'
            ok = summary_marker in output and (
                "external worker" in output.lower() or "heartbeat" in output.lower()
            )
        if not ok:
            try:
                payload = json.loads(output)
            except json.JSONDecodeError:
                payload = {}
            if isinstance(payload, dict):
                summary = str(payload.get("summary") or "")
                watch_output = str(payload.get("body", {}).get("watch_output") or "")
                ok = (
                    run_id in summary
                    or run_id in watch_output
                    or summary == f"Watching {run_id}"
                ) and ("external worker" in watch_output.lower() or "heartbeat" in watch_output.lower())
        recorder.add(
            _runtime_check_name(step_id, mode),
            "passed" if ok else "failed",
            f"Verified watch output for {run_id}.",
            [],
        )
        if not ok:
            raise RuntimeError(f"{host_name} step {step_id} did not expose the expected watch output")
        _guard_source(step_id, mode)

    def _latest_controller_id(*, exclude_controller_ids: set[str] | None = None) -> str:
        exclude = exclude_controller_ids or set()
        controllers_dir = project_dir / ".thoth" / "objects" / "controller"
        candidates: list[tuple[str, str]] = []
        if not controllers_dir.is_dir():
            return ""
        for path in controllers_dir.glob("*.json"):
            controller = _read_json(path)
            controller_id = str(controller.get("object_id") or path.stem)
            if controller_id in exclude:
                continue
            payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
            if payload.get("controller_type") != "auto":
                continue
            candidates.append((str(controller.get("updated_at") or controller.get("created_at") or ""), controller_id))
        candidates.sort()
        return candidates[-1][1] if candidates else ""

    def _verify_auto_controller_started(*, step_id: str, mode: str, public_command: str, result: CommandResult) -> str:
        output = _command_output(step_id, public_command, result)
        controller_id = ""
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            body = payload.get("body") if isinstance(payload.get("body"), dict) else {}
            controller_id = str(body.get("controller_id") or "")
        if not controller_id:
            controller_id = _latest_controller_id(exclude_controller_ids=seen_controller_ids)
        controller_path = project_dir / ".thoth" / "objects" / "controller" / f"{controller_id}.json"
        supervisor_path = _controller_supervisor_path(project_dir, controller_id)
        controller = _read_json(controller_path) if controller_id else {}
        supervisor = _read_json(supervisor_path) if controller_id else {}
        controller_payload = controller.get("payload") if isinstance(controller.get("payload"), dict) else {}
        ok = (
            bool(controller_id)
            and controller.get("kind") == "controller"
            and controller_payload.get("controller_type") == "auto"
            and controller_payload.get("host") == host_name
            and controller_payload.get("executor") == "codex"
            and bool(supervisor.get("pid") or supervisor.get("state"))
        )
        recorder.add(
            _runtime_check_name(step_id, mode),
            "passed" if ok else "failed",
            f"Verified auto controller {controller_id}: host={controller_payload.get('host')} executor={controller_payload.get('executor')} supervisor={supervisor.get('state')}.",
            [str(controller_path), str(supervisor_path)] if controller_id else [],
        )
        if not ok:
            raise RuntimeError(f"{host_name} step {step_id} did not start the expected auto controller")
        seen_controller_ids.add(controller_id)
        _guard_source(step_id, mode)
        return controller_id

    def execute(step_id: str, public_command: str, *, timeout: float = 240) -> CommandResult | None:
        mode = step_mode(step_id)
        if mode == "skipped":
            return None
        started = time.time()
        attempt = 0
        effective_timeout = _effective_host_command_timeout(host_name, public_command, timeout)
        _emit_selftest_progress(f"{host_name} step {step_id} mode={mode} begin")
        while True:
            attempt += 1
            base_artifact_name = f"host-{host_name}-{step_id}" if mode == "selected" else f"host-{host_name}-prereq-{step_id}"
            artifact_suffix = "" if attempt == 1 else f"-attempt-{attempt}"
            bridge_count_before = len(_read_claude_bridge_events(project_dir)) if host_name == "claude" else 0
            result, command_artifacts = run_public_command(
                public_command,
                recorder=recorder,
                artifact_name=f"{base_artifact_name}{artifact_suffix}",
                timeout=effective_timeout,
            )
            bridge_event = _matching_claude_event(bridge_count_before, public_command) if host_name == "claude" else {}
            if host_name == "claude":
                result = _normalize_claude_public_command_result(result, bridge_event=bridge_event)
            if mode == "selected":
                command_results[step_id] = result
            artifacts.extend(command_artifacts)
            if result.returncode == 0:
                execution_artifacts = list(command_artifacts)
                if host_name == "claude":
                    event = bridge_event
                    if not event or event.get("bridge_success") is not True:
                        recorder.add(
                            _command_check_name(step_id, mode),
                            "failed",
                            f"Claude did not record a matching successful bridge event for {public_command}.",
                            execution_artifacts,
                        )
                        raise RuntimeError(f"{host_name} step {step_id} did not record the expected bridge event")
                    claude_step_events[step_id] = event
                    execution_artifacts.append(
                        recorder.write_json(f"host-{host_name}-{step_id}-bridge-event.json", event)
                    )
                else:
                    item = _codex_command_item(result.stdout, public_command)
                    if not item:
                        recorder.add(
                            _command_check_name(step_id, mode),
                            "failed",
                            f"Codex did not execute the exact requested shell command for {public_command}.",
                            execution_artifacts,
                        )
                        raise RuntimeError(f"{host_name} step {step_id} did not execute the requested shell command")
                    execution_artifacts.append(
                        recorder.write_json(f"host-{host_name}-{step_id}-command-item.json", item)
                    )
                recorder.add(
                    _command_check_name(step_id, mode),
                    "passed",
                    f"Executed the literal public command probe for {public_command}.",
                    execution_artifacts,
                )
                _guard_source(step_id, mode)
                _emit_selftest_progress(f"{host_name} step {step_id} mode={mode} ok")
                return result
            if (
                host_name == "claude"
                and attempt < transient_retry_limit
                and (time.time() - started) <= transient_retry_window_seconds
                and not bridge_event
                and (
                    _looks_like_claude_bridge_cold_start(result)
                    or result.returncode == 124
                )
            ):
                time.sleep(min(3 * attempt, 6))
                continue
            transient = _looks_like_transient_host_outage(result)
            if transient and attempt <= transient_retry_limit and (time.time() - started) <= transient_retry_window_seconds:
                time.sleep(min(5 * attempt, 15))
                continue
            if transient:
                recorder.add(
                    _command_check_name(step_id, mode),
                    "failed",
                    f"{host_name} step {step_id} exceeded the bounded transient host retry budget.",
                    command_artifacts,
                )
                raise RuntimeError(
                    f"{host_name} step {step_id} hit an upstream/transient host outage and exceeded the bounded retry budget"
                )
            recorder.add(
                _command_check_name(step_id, mode),
                "failed",
                f"{host_name} step {step_id} failed with return code {result.returncode}.",
                command_artifacts,
            )
            raise RuntimeError(f"{host_name} step {step_id} failed with return code {result.returncode}")

    execute("init", commands["init"])
    _set_dashboard_port(project_dir, _free_port())
    execute("status", commands["status"])
    execute("doctor", commands["doctor"])
    execute("discuss-decision", commands["discuss_decision"])
    for index, command in enumerate(commands["discuss_contracts"], start=1):
        execute(f"discuss-contract-{index}", command)

    last_discuss_step = f"discuss-contract-{len(commands['discuss_contracts'])}"
    if should_run(last_discuss_step):
        compiler_summary = compile_task_authority(project_dir).get("summary", {})
        ready_count = int(compiler_summary.get("work_item_counts", {}).get("ready", 0))
        queue_count = int(compiler_summary.get("decision_queue_count", 0))
        compiler_ok = ready_count == 2 and queue_count == 0
        compiler_artifact = recorder.write_json(f"host-{host_name}-compiler-summary.json", compiler_summary)
        recorder.add(
            _runtime_check_name("compiler-ready", step_mode(last_discuss_step)),
            "passed" if compiler_ok else "failed",
            f"Structured discuss compiled the host-real work items: ready={ready_count} decision_queue={queue_count}.",
            [compiler_artifact],
        )
        if not compiler_ok:
            raise RuntimeError("compiled host-real work items were not ready after structured discuss")

    run_live_id = ""
    if should_run("run-live"):
        run_live_result = execute("run-live", commands["run_live"], timeout=45)
        run_live_id = _latest_run_id(
            project_dir,
            kind="run",
            work_id="task-runtime-probe",
            exclude_run_ids=seen_run_ids,
        )
        if not run_live_id:
            raise RuntimeError("run live probe did not create a new run ledger")
        seen_run_ids.add(run_live_id)
        if run_live_result is None:
            raise RuntimeError("run live result was unexpectedly missing")
        _verify_live_probe_prepared(
            step_id="run-live",
            mode=step_mode("run-live"),
            run_id=run_live_id,
            expected_kind="run",
            expected_work_id="task-runtime-probe",
            expected_executor=review_expected_executor if "--executor codex" in commands["run_live"] else None,
            public_command=commands["run_live"],
        )
        cleanup_live_stop = _run_thoth(project_dir, "run", "--stop", run_live_id, timeout=20)
        if cleanup_live_stop.returncode != 0:
            raise RuntimeError("repo-local cleanup stop for host run-live probe failed")
        _wait_until(
            lambda: _state_payload(project_dir, run_live_id).get("status") in {"stopped", "completed"},
            timeout=15,
            description=f"cleanup stop for live run {run_live_id}",
        )

    run_sleep_id = ""
    if should_run("run-sleep"):
        run_sleep_result = execute("run-sleep", commands["run_sleep"], timeout=45)
        run_sleep_id = _latest_run_id(
            project_dir,
            kind="run",
            work_id="task-runtime-probe",
            exclude_run_ids=seen_run_ids,
        )
        if not run_sleep_id:
            raise RuntimeError("run --sleep did not create a new run ledger")
        seen_run_ids.add(run_sleep_id)
        if run_sleep_result is None:
            raise RuntimeError("run --sleep result was unexpectedly missing")
        _verify_sleep_probe_started(
            step_id="run-sleep",
            mode=step_mode("run-sleep"),
            run_id=run_sleep_id,
            expected_kind="run",
            expected_work_id="task-runtime-probe",
            public_command=commands["run_sleep"],
            expected_executor=review_expected_executor if "--executor codex" in commands["run_sleep"] else None,
        )
        if not should_run("run-watch") and not should_run("run-stop"):
            cleanup_sleep_stop = _run_thoth(project_dir, "run", "--stop", run_sleep_id, timeout=20)
            if cleanup_sleep_stop.returncode != 0:
                raise RuntimeError("repo-local cleanup stop for host run-sleep probe failed")
            _wait_until(
                lambda: _state_payload(project_dir, run_sleep_id).get("status") in {"stopped", "completed"},
                timeout=15,
                description=f"cleanup stop for sleep run {run_sleep_id}",
            )

    if should_run("run-watch"):
        run_watch_command = commands["run_watch"](run_sleep_id) if callable(commands["run_watch"]) else str(commands["run_watch"]).format(run_id=run_sleep_id)
        run_watch_result = execute("run-watch", run_watch_command, timeout=25)
        if run_watch_result is None:
            raise RuntimeError("run --watch result was unexpectedly missing")
        _verify_watch_output(
            step_id="run-watch",
            mode=step_mode("run-watch"),
            run_id=run_sleep_id,
            public_command=run_watch_command,
            result=run_watch_result,
        )
        if not should_run("run-stop"):
            cleanup_watch_stop = _run_thoth(project_dir, "run", "--stop", run_sleep_id, timeout=20)
            if cleanup_watch_stop.returncode != 0:
                raise RuntimeError("repo-local cleanup stop for host run-watch probe failed")
            _wait_until(
                lambda: _state_payload(project_dir, run_sleep_id).get("status") in {"stopped", "completed"},
                timeout=15,
                description=f"cleanup stop for watched run {run_sleep_id}",
            )

    if should_run("run-stop"):
        run_stop_command = commands["run_stop"](run_sleep_id) if callable(commands["run_stop"]) else str(commands["run_stop"]).format(run_id=run_sleep_id)
        execute("run-stop", run_stop_command, timeout=25)
        _verify_sleep_probe_stopped(
            step_id="run-stop",
            mode=step_mode("run-stop"),
            run_id=run_sleep_id,
            expected_kind="run",
        )

    if should_run("review"):
        execute("review", commands["review"], timeout=120)
        review_run_id = _latest_run_id(project_dir, kind="review", work_id="task-review-probe", exclude_run_ids=seen_run_ids)
        if not review_run_id:
            raise RuntimeError("review did not create a new run ledger")
        seen_run_ids.add(review_run_id)
        artifacts.extend(
            _verify_host_run_completion(
                project_dir,
                recorder,
                check_name=_runtime_check_name("review", step_mode("review")),
                run_id=review_run_id,
                expected_kind="review",
                expected_work_id="task-review-probe",
                expected_host=host_name,
                expected_executor=review_expected_executor,
                expected_dispatch_mode=expected_dispatch(commands["review"]),
                require_findings=True,
                timeout=120,
            )
        )
        review_result = _canonical_review_result_payload(
            project_dir,
            review_run_id,
            _result_payload(project_dir, review_run_id),
        )
        review_exact_ok = review_expected_result is not None and review_result == review_expected_result
        review_artifact = recorder.write_json(
            f"host-{host_name}-review-result.json",
            review_result if isinstance(review_result, dict) else {},
        )
        recorder.add(
            _output_check_name("review", step_mode("review")),
            "passed" if review_exact_ok else "failed",
            "Review result matched the fixed expected single finding.",
            [review_artifact],
        )
        if not review_exact_ok:
            raise RuntimeError(f"{host_name} review output did not match the fixed expected finding")
        _guard_source("review", step_mode("review"))

    dashboard_port = int(_read_json(project_dir / ".thoth" / "project" / "project.json").get("dashboard", {}).get("port", 8501))
    if should_run("dashboard-start"):
        execute("dashboard-start", commands["dashboard_start"], timeout=60)
        dashboard_status: dict[str, Any] | None = None
        try:
            dashboard_status = _wait_for_http_json(
                f"http://127.0.0.1:{dashboard_port}/api/status",
                timeout=20,
                description=f"{host_name} dashboard start",
            )
        except RuntimeError:
            status_path = project_dir / ".thoth" / "derived" / "dashboard.status.json"
            if host_name == "codex" and status_path.exists():
                dashboard_status = _read_json(status_path)
            else:
                raise
        dashboard_status_artifact = recorder.write_json(f"host-{host_name}-dashboard-status.json", dashboard_status)
        dashboard_ready = isinstance(dashboard_status, dict) and bool(dashboard_status.get("runtime"))
        recorder.add(
            _runtime_check_name("dashboard-start", step_mode("dashboard-start")),
            "passed" if dashboard_ready else "failed",
            f"Dashboard started for {host_name} on port {dashboard_port}.",
            [dashboard_status_artifact],
        )
        if not dashboard_ready:
            raise RuntimeError(f"{host_name} dashboard did not become ready")
        if not should_run("dashboard-stop"):
            _stop_dashboard(project_dir, recorder=recorder)

    loop_live_id = ""
    if should_run("loop-live"):
        loop_live_result = execute("loop-live", commands["loop_live"], timeout=45)
        loop_live_id = _latest_run_id(project_dir, kind="loop", work_id="task-runtime-probe", exclude_run_ids=seen_run_ids)
        if not loop_live_id:
            raise RuntimeError("loop live probe did not create a new run ledger")
        seen_run_ids.add(loop_live_id)
        if loop_live_result is None:
            raise RuntimeError("loop live result was unexpectedly missing")
        _verify_live_probe_prepared(
            step_id="loop-live",
            mode=step_mode("loop-live"),
            run_id=loop_live_id,
            expected_kind="loop",
            expected_work_id="task-runtime-probe",
            expected_executor=review_expected_executor if "--executor codex" in commands["loop_live"] else None,
            public_command=commands["loop_live"],
        )
        cleanup_loop_live_stop = _run_thoth(project_dir, "loop", "--stop", loop_live_id, timeout=20)
        if cleanup_loop_live_stop.returncode != 0:
            raise RuntimeError("repo-local cleanup stop for host loop-live probe failed")
        _wait_until(
            lambda: _state_payload(project_dir, loop_live_id).get("status") in {"stopped", "completed"},
            timeout=15,
            description=f"cleanup stop for live loop {loop_live_id}",
        )

    loop_run_id = ""
    if should_run("loop-sleep"):
        loop_sleep_result = execute("loop-sleep", commands["loop_sleep"], timeout=45)
        loop_run_id = _latest_run_id(project_dir, kind="loop", work_id="task-runtime-probe", exclude_run_ids=seen_run_ids)
        if not loop_run_id:
            raise RuntimeError("loop --sleep did not create a new run ledger")
        seen_run_ids.add(loop_run_id)
        if loop_sleep_result is None:
            raise RuntimeError("loop --sleep result was unexpectedly missing")
        _verify_sleep_probe_started(
            step_id="loop-sleep",
            mode=step_mode("loop-sleep"),
            run_id=loop_run_id,
            expected_kind="loop",
            expected_work_id="task-runtime-probe",
            public_command=commands["loop_sleep"],
            expected_executor=review_expected_executor if "--executor codex" in commands["loop_sleep"] else None,
        )
        if not should_run("loop-stop"):
            cleanup_loop_sleep_stop = _run_thoth(project_dir, "loop", "--stop", loop_run_id, timeout=20)
            if cleanup_loop_sleep_stop.returncode != 0:
                raise RuntimeError("repo-local cleanup stop for host loop-sleep probe failed")
            _wait_until(
                lambda: _state_payload(project_dir, loop_run_id).get("status") in {"stopped", "completed"},
                timeout=15,
                description=f"cleanup stop for sleep loop {loop_run_id}",
            )

    if should_run("loop-stop"):
        loop_stop_command = commands["loop_stop"](loop_run_id) if callable(commands["loop_stop"]) else str(commands["loop_stop"]).format(run_id=loop_run_id)
        execute("loop-stop", loop_stop_command, timeout=25)
        _verify_sleep_probe_stopped(
            step_id="loop-stop",
            mode=step_mode("loop-stop"),
            run_id=loop_run_id,
            expected_kind="loop",
        )

    auto_controller_id = ""
    if should_run("auto"):
        auto_result = execute("auto", commands["auto"], timeout=60)
        if auto_result is None:
            raise RuntimeError("auto result was unexpectedly missing")
        auto_controller_id = _verify_auto_controller_started(
            step_id="auto",
            mode=step_mode("auto"),
            public_command=commands["auto"],
            result=auto_result,
        )
        if not should_run("auto-stop"):
            auto_cleanup = _run_thoth(project_dir, "auto", "--stop", auto_controller_id, timeout=20)
            if auto_cleanup.returncode != 0:
                raise RuntimeError("repo-local cleanup stop for host auto probe failed")

    if should_run("auto-stop"):
        auto_stop_command = commands["auto_stop"](auto_controller_id) if callable(commands["auto_stop"]) else str(commands["auto_stop"]).format(controller_id=auto_controller_id)
        execute("auto-stop", auto_stop_command, timeout=25)

    if should_run("dashboard-stop"):
        execute("dashboard-stop", commands["dashboard_stop"], timeout=30)
        pid_path = project_dir / ".thoth" / "derived" / "dashboard.pid"
        dashboard_stopped = not pid_path.exists()
        recorder.add(
            _runtime_check_name("dashboard-stop", step_mode("dashboard-stop")),
            "passed" if dashboard_stopped else "failed",
            f"Dashboard stop removed the pidfile for {host_name}.",
            [str(pid_path)] if pid_path.exists() else [],
        )
        if not dashboard_stopped:
            raise RuntimeError(f"{host_name} dashboard did not stop cleanly")
        _guard_source("dashboard-stop", step_mode("dashboard-stop"))

    if should_run("sync"):
        execute("sync", commands["sync"], timeout=240)
    return artifacts, command_results

__all__ = [name for name in globals() if not name.startswith("__")]
