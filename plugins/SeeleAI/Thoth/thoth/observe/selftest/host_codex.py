from __future__ import annotations

import os
from pathlib import Path

from .host_common import (
    _expected_host_review_result,
    _host_local_state_env,
    _looks_like_transient_host_outage,
    _normalize_codex_public_command_result,
    _run_codex_public_command,
    _run_host_real_flow,
    _safe_name,
    _write_host_real_discuss_payload_files,
)
from .capabilities import _ensure_codex_repo_hooks
from .model import CommandResult
from .recorder import Recorder

def _host_codex(
    repo_root: Path,
    project_dir: Path,
    recorder: Recorder,
    *,
    from_step: str | None = None,
    to_step: str | None = None,
) -> None:
    decision_path, contract_paths = _write_host_real_discuss_payload_files(project_dir)
    hook_artifacts = [_ensure_codex_repo_hooks(project_dir, recorder)]

    def run_public_command(public_command: str, *, recorder: Recorder, artifact_name: str, timeout: float = 240) -> tuple[CommandResult, list[str]]:
        done_token = f"{_safe_name(artifact_name).upper()}_DONE"
        extra_env = _host_local_state_env(project_dir)
        if os.environ.get("THOTH_SELFTEST_USE_LOCAL_RUNTIME") == "1":
            extra_env["THOTH_SELFTEST_RUNTIME_ROOT"] = str(repo_root)
        if "--sleep" in public_command.split():
            extra_env["THOTH_TEST_EXTERNAL_WORKER_MODE"] = "hold"
        elif public_command.strip().startswith(("$thoth run ", "$thoth loop ")):
            extra_env["THOTH_TEST_EXTERNAL_WORKER_MODE"] = "complete"
        result, artifacts = _run_codex_public_command(
            project_dir,
            public_command,
            done_token=done_token,
            recorder=recorder,
            artifact_name=artifact_name,
            timeout=timeout,
            env=extra_env,
        )
        result = _normalize_codex_public_command_result(
            result,
            public_command=public_command,
            done_token=done_token,
            allow_followup_commands=public_command.strip().startswith("$thoth review"),
        )
        return result, artifacts

    contract_commands = [
        f"$thoth discuss --work-json \"$(cat {path})\""
        for path in contract_paths
    ]
    artifacts, command_results = _run_host_real_flow(
        "codex",
        project_dir,
        recorder,
        run_public_command=run_public_command,
        commands={
            "init": "$thoth init",
            "status": "$thoth status",
            "doctor": "$thoth doctor --quick",
            "discuss_decision": f"$thoth discuss --decision-json \"$(cat {decision_path})\"",
            "discuss_contracts": contract_commands,
            "run_live": "$thoth run --host codex --executor codex --work-id task-runtime-probe",
            "run_sleep": "$thoth run --host codex --executor codex --sleep --work-id task-runtime-probe",
            "run_watch": lambda run_id: f"$thoth run --watch {run_id}",
            "run_stop": lambda run_id: f"$thoth run --stop {run_id}",
            "review": "$thoth review --work-id task-review-probe --host codex --executor codex tracker/review_probe.py",
            "loop_live": "$thoth loop --host codex --executor codex --work-id task-runtime-probe",
            "dashboard_start": "$thoth dashboard start",
            "dashboard_stop": "$thoth dashboard stop",
            "loop_sleep": "$thoth loop --host codex --executor codex --sleep --work-id task-runtime-probe",
            "loop_stop": lambda run_id: f"$thoth loop --stop {run_id}",
            "auto": "$thoth auto --host codex --executor codex --sleep --rounds 1 --min-runtime-seconds 0",
            "auto_stop": lambda controller_id: f"$thoth auto --stop {controller_id}",
            "sync": "$thoth init --sync",
        },
        from_step=from_step,
        to_step=to_step,
        review_expected_executor="codex",
        review_expected_result=_expected_host_review_result(),
    )
    artifacts.extend(str(item.get("hooks_path") or "") for item in hook_artifacts if isinstance(item, dict))
    conversations_path = project_dir / ".thoth" / "project" / "conversations.jsonl"
    skill_load_failed = any("failed to load skill" in result.stderr.lower() for result in command_results.values())
    if conversations_path.exists():
        artifacts.append(str(conversations_path))
    hook_seen = False
    if conversations_path.exists():
        hook_seen = "\"type\": \"hook\"" in conversations_path.read_text(encoding="utf-8")
    partial_window = from_step is not None or to_step is not None
    success = not skill_load_failed and all(result.returncode == 0 for result in command_results.values())
    if not partial_window:
        success = success and hook_seen
    check_name = "host.codex.window" if partial_window else "host.codex"
    if partial_window and success:
        status = "passed"
        detail = f"Codex host window completed successfully with from_step={from_step!r} to_step={to_step!r}."
    elif success:
        status = "passed"
        detail = "Codex host completed the host-real decision/run/review/loop flow through the installed `$thoth` skill and emitted hook ledger notes."
    elif any(_looks_like_transient_host_outage(result) for result in command_results.values()):
        status = "failed"
        detail = "Codex host matrix hit an upstream/transient host outage and exceeded the heavy gate's no-degraded policy."
    elif skill_load_failed:
        status = "failed"
        detail = "Codex host could not load the generated Thoth public skill, so the host-real surface is not valid."
    elif not hook_seen:
        status = "failed"
        detail = "Codex host completed the command flow, but no hook ledger notes were observed."
    else:
        status = "failed"
        result_codes = {command: result.returncode for command, result in command_results.items()}
        detail = f"Codex host execution failed. result_codes={result_codes}"
    recorder.add(check_name, status, detail, artifacts)
