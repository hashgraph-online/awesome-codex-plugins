from __future__ import annotations

from pathlib import Path

from .fixtures import _compact_json, _host_real_contract_payloads, _host_real_decision_payload, _shell_quote
from .host_common import (
    _expected_host_review_result,
    _host_local_state_env,
    _looks_like_transient_host_outage,
    _read_claude_bridge_events,
    _run_claude_public_command,
    _run_host_real_flow,
    _write_claude_local_settings,
)
from .model import CommandResult
from .recorder import Recorder

def _host_claude(
    repo_root: Path,
    project_dir: Path,
    recorder: Recorder,
    *,
    from_step: str | None = None,
    to_step: str | None = None,
) -> None:
    artifacts = [_write_claude_local_settings(project_dir, repo_root, recorder)]

    def run_public_command(public_command: str, *, recorder: Recorder, artifact_name: str, timeout: float = 240) -> tuple[CommandResult, list[str]]:
        extra_env = _host_local_state_env(project_dir)
        if "--sleep" in public_command.split():
            extra_env["THOTH_TEST_EXTERNAL_WORKER_MODE"] = "hold"
        return _run_claude_public_command(
            repo_root,
            project_dir,
            public_command,
            recorder=recorder,
            artifact_name=artifact_name,
            timeout=timeout,
            env=extra_env,
        )

    decision_arg = _shell_quote(_compact_json(_host_real_decision_payload()))
    contract_commands = [
        f"/thoth:discuss --work-json {_shell_quote(_compact_json(contract))}"
        for contract in _host_real_contract_payloads()
    ]
    flow_artifacts, command_results = _run_host_real_flow(
        "claude",
        project_dir,
        recorder,
        run_public_command=run_public_command,
        commands={
            "init": "/thoth:init",
            "status": "/thoth:status",
            "doctor": "/thoth:doctor --quick",
            "discuss_decision": f"/thoth:discuss --decision-json {decision_arg}",
            "discuss_contracts": contract_commands,
            "run_live": "/thoth:run --executor codex --work-id task-runtime-probe",
            "run_sleep": "/thoth:run --executor codex --sleep --work-id task-runtime-probe",
            "run_watch": lambda run_id: f"/thoth:run --watch {run_id}",
            "run_stop": lambda run_id: f"/thoth:run --stop {run_id}",
            "review": "/thoth:review --work-id task-review-probe --executor codex tracker/review_probe.py",
            "loop_live": "/thoth:loop --executor codex --work-id task-runtime-probe",
            "dashboard_start": "/thoth:dashboard start",
            "dashboard_stop": "/thoth:dashboard stop",
            "loop_sleep": "/thoth:loop --executor codex --sleep --work-id task-runtime-probe",
            "loop_stop": lambda run_id: f"/thoth:loop --stop {run_id}",
            "auto": "/thoth:auto --executor codex --sleep --rounds 1 --min-runtime-seconds 0",
            "auto_stop": lambda controller_id: f"/thoth:auto --stop {controller_id}",
            "sync": "/thoth:init --sync",
        },
        review_expected_executor="codex",
        from_step=from_step,
        to_step=to_step,
        review_expected_result=_expected_host_review_result(),
    )
    artifacts.extend(flow_artifacts)
    partial_window = from_step is not None or to_step is not None

    combined_stdout = "\n".join(result.stdout for result in command_results.values())
    combined_stderr = "\n".join(result.stderr for result in command_results.values())
    bridge_events = _read_claude_bridge_events(project_dir)
    bridge_commands = [event.get("command_id") for event in bridge_events]
    bridge_success = {
        event.get("command_id"): bool(event.get("bridge_success"))
        for event in bridge_events
        if isinstance(event.get("command_id"), str)
    }
    bridge_path = project_dir / ".thoth" / "derived" / "host-bridges" / "claude-command-events.jsonl"
    if bridge_path.exists():
        artifacts.append(str(bridge_path))
    required_bridge_commands = ("init", "status", "doctor", "discuss", "run", "review", "dashboard", "loop", "auto")
    success = all(result.returncode == 0 for result in command_results.values())
    if not partial_window:
        success = success and all(command in bridge_commands for command in required_bridge_commands) and all(
            bridge_success.get(command) is True for command in required_bridge_commands
        )
    hook_seen = "hook" in combined_stdout.lower() or "session" in combined_stdout.lower()
    check_name = "host.claude.window" if partial_window else "host.claude"
    if partial_window and success:
        status = "passed"
        detail = f"Claude host window completed successfully with from_step={from_step!r} to_step={to_step!r}."
    elif success and hook_seen:
        status = "passed"
        detail = "Claude host completed the host-real decision/run/review/loop/auto flow through the public /thoth:* surface, including real `--executor codex` delegation."
    elif success:
        status = "failed"
        detail = "Claude host completed the command flow, but hook/session evidence was not visible in Claude output."
    elif any(_looks_like_transient_host_outage(result) for result in command_results.values()):
        status = "failed"
        detail = "Claude host matrix hit an upstream/transient host outage and exceeded the heavy gate's no-degraded policy."
    elif "requires approval" in f"{combined_stdout}\n{combined_stderr}".lower():
        status = "failed"
        detail = "Claude host slash commands still required approval for the bridge shell command, so the repo-local runtime did not execute autonomously."
    elif "shell command execution disabled by policy" in combined_stdout.lower():
        status = "failed"
        detail = "Claude host disabled skill shell execution, so /thoth:* could not bridge into the repo-local runtime."
    elif (project_dir / ".thoth" / "project" / "project.json").exists() and not bridge_events:
        status = "failed"
        detail = "Claude host created project state, but no Claude command bridge events were recorded. This indicates a prompt-only fallback rather than the real repo runtime."
    else:
        status = "failed"
        result_codes = {command: result.returncode for command, result in command_results.items()}
        detail = f"Claude host execution failed. result_codes={result_codes} bridge_commands={bridge_commands}"
    recorder.add(check_name, status, detail, artifacts)
