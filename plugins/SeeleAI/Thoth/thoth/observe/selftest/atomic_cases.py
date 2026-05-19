"""Atomic selftest cases for repo-local and host-surface capabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from thoth.init.generators import (
    generate_agent_os_docs,
    generate_codex_hook_projection,
    generate_dashboard,
    generate_host_projections,
    generate_scripts,
    generate_thoth_runtime,
    parse_config,
)
from thoth.init.audit import audit_repository_state
from thoth.init.migration import _write_source_map
from thoth.init.preview import build_init_preview
from thoth.init.render import render_codex_hooks_payload
from thoth.plan.compiler import compile_task_authority
from thoth.plan.store import load_work_for_execution
from thoth.run.packets import prepare_execution
from thoth.run.service import stop_run
from thoth.selftest_seed import seed_host_real_app

from .fixtures import (
    _canonical_review_result_payload,
    _expected_host_review_result,
    _read_json,
    _result_payload,
    _run_payload,
    _seed_host_real_repo,
    _seed_host_real_tasks,
    _seed_task,
    _set_dashboard_port,
    _state_payload,
    _write_host_real_discuss_payload_files,
    _write_json,
)
from .hard_suite import _start_dashboard, _stop_dashboard
from .host_claude import _host_claude
from .host_codex import _host_codex
from .model import PYTHON, ROOT, utc_now
from .processes import _free_port, _http_get_json, _run_command, _save_command, _wait_until
from .recorder import Recorder, _extract_json


def _artifact_paths_for_run(project_dir: Path, run_id: str) -> list[str]:
    run_dir = project_dir / ".thoth" / "runs" / run_id
    return [
        str(run_dir / "run.json"),
        str(run_dir / "state.json"),
        str(run_dir / "result.json"),
        str(run_dir / "packet.json"),
        str(run_dir / "phase_state.json"),
    ]


def _stop_runtime_for_cleanup(project_dir: Path, run_id: str, recorder: Recorder, *, label: str, command: str = "run") -> None:
    stop_result = _run_command([PYTHON, "-m", "thoth.cli", command, "--stop", run_id], cwd=project_dir, env={"PYTHONPATH": str(ROOT)}, timeout=20)
    _save_command(recorder, label, stop_result)
    if stop_result.returncode == 0:
        return
    stop_run(project_dir, run_id)


def _extract_runtime_run_id(stdout: str) -> str:
    for raw in stdout.splitlines():
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and str(payload.get("type") or "").startswith("thoth."):
            run_id = payload.get("run_id")
            if isinstance(run_id, str) and run_id.strip():
                return run_id.strip()
    return ""


def _materialize_selftest_project(
    project_dir: Path,
    recorder: Recorder,
    *,
    include_dashboard: bool,
    label: str,
) -> None:
    config = parse_config(
        json.dumps(
            {
                "name": project_dir.name,
                "description": "Atomic selftest fixture",
                "language": "en",
                "directions": [],
                "port": 8501,
                "theme": "warm-bear",
            }
        )
    )
    generate_agent_os_docs(config, project_dir)
    generate_thoth_runtime(config, project_dir)
    generate_scripts(config, project_dir)
    generate_host_projections(config, project_dir)
    generate_codex_hook_projection(project_dir)
    if include_dashboard:
        generate_dashboard(config, project_dir)
    audit = audit_repository_state(project_dir)
    preview = build_init_preview(project_dir, audit)
    _write_source_map(project_dir, audit, preview)
    compile_task_authority(project_dir)
    recorder.add(
        label,
        "passed",
        f"Materialized the minimal Thoth authority fixture (dashboard={include_dashboard}).",
        [
            str(project_dir / ".thoth" / "objects" / "project" / "project.json"),
            str(project_dir / "scripts" / "session-end-check.sh"),
        ],
    )


def _prepare_runtime_project(
    work_root: Path,
    recorder: Recorder,
    *,
    work_id: str = "task-1",
    include_dashboard: bool = False,
) -> Path:
    project_dir = work_root / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    _run_command(["git", "init"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.email", "selftest@example.com"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.name", "Thoth Selftest"], cwd=project_dir, timeout=20)
    _materialize_selftest_project(
        project_dir,
        recorder,
        include_dashboard=include_dashboard,
        label="setup.runtime_seed",
    )
    _set_dashboard_port(project_dir, _free_port())
    _seed_task(project_dir, work_id=work_id)
    return project_dir


def _prepare_probe_project(work_root: Path, recorder: Recorder) -> Path:
    project_dir = work_root / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    seed_host_real_app(project_dir)
    _run_command(["git", "init"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.email", "selftest@example.com"], cwd=project_dir, timeout=20)
    _run_command(["git", "config", "user.name", "Thoth Selftest"], cwd=project_dir, timeout=20)
    _materialize_selftest_project(
        project_dir,
        recorder,
        include_dashboard=False,
        label="setup.probe_seed",
    )
    return project_dir


def _compile_probe_tasks(project_dir: Path, recorder: Recorder, *, label_prefix: str) -> None:
    decision_path, contract_paths = _write_host_real_discuss_payload_files(project_dir)
    decision_result = _run_command(
        [PYTHON, "-m", "thoth.cli", "discuss", "--decision-json", decision_path.read_text(encoding="utf-8")],
        cwd=project_dir,
        env={"PYTHONPATH": str(ROOT)},
        timeout=60,
    )
    recorder.add(
        f"{label_prefix}.decision",
        "passed" if decision_result.returncode == 0 else "failed",
        "Recorded the fixed decision payload through the public discuss surface.",
        _save_command(recorder, f"{label_prefix}-decision", decision_result),
    )
    if decision_result.returncode != 0:
        raise RuntimeError("probe decision discuss failed")
    for index, contract_path in enumerate(contract_paths, start=1):
        contract_result = _run_command(
            [PYTHON, "-m", "thoth.cli", "discuss", "--work-json", contract_path.read_text(encoding="utf-8")],
            cwd=project_dir,
            env={"PYTHONPATH": str(ROOT)},
            timeout=60,
        )
        recorder.add(
            f"{label_prefix}.contract_{index}",
            "passed" if contract_result.returncode == 0 else "failed",
            f"Recorded fixed contract payload {index} through the public discuss surface.",
            _save_command(recorder, f"{label_prefix}-contract-{index}", contract_result),
        )
        if contract_result.returncode != 0:
            raise RuntimeError(f"probe contract discuss {index} failed")


def _assert_probe_tasks_ready(project_dir: Path, recorder: Recorder, *, check_name: str) -> None:
    summary = compile_task_authority(project_dir).get("summary", {})
    work_counts = summary.get("work_item_counts", {}) if isinstance(summary.get("work_item_counts"), dict) else {}
    decision_counts = summary.get("decision_counts", {}) if isinstance(summary.get("decision_counts"), dict) else {}
    ready_count = int(work_counts.get("ready", 0))
    queue_count = int(decision_counts.get("proposed", 0))
    work_items_dir = project_dir / ".thoth" / "objects" / "work_item"
    ok = (
        ready_count == 2
        and queue_count == 0
        and (work_items_dir / "task-runtime-probe.json").exists()
        and (work_items_dir / "task-review-probe.json").exists()
    )
    artifact = recorder.write_json(f"{check_name}.json", summary)
    recorder.add(
        check_name,
        "passed" if ok else "failed",
        f"Compiled fixed probe work items: ready={ready_count} proposed_decisions={queue_count}.",
        [artifact],
    )
    if not ok:
        raise RuntimeError("compiled probe tasks were not ready")


def case_plan_discuss_compile(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_probe_project(work_root, recorder)
    _compile_probe_tasks(project_dir, recorder, label_prefix="plan.discuss.compile")
    _assert_probe_tasks_ready(project_dir, recorder, check_name="plan.discuss.compile")


def case_runtime_run_live(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    run_result = _run_command([PYTHON, "-m", "thoth.cli", "run", "--work-id", "task-1"], cwd=project_dir, env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "complete"}, timeout=60)
    run_artifacts = _save_command(recorder, "runtime-run-live", run_result)
    run_id = _extract_runtime_run_id(run_result.stdout)
    if run_result.returncode != 0 or not run_id:
        recorder.add("runtime.run.live", "failed", "Live run execution failed.", run_artifacts)
        raise RuntimeError("live run execution failed")
    phase_state = _read_json(project_dir / ".thoth" / "runs" / run_id / "phase_state.json")
    state = _state_payload(project_dir, run_id)
    result = _result_payload(project_dir, run_id)
    phase_statuses = phase_state.get("phase_statuses") if isinstance(phase_state.get("phase_statuses"), dict) else {}
    reflect_exists = (project_dir / ".thoth" / "runs" / run_id / "reflect.json").exists()
    ok = (
        state.get("status") == "completed"
        and result.get("status") == "completed"
        and result.get("result", {}).get("validate_passed") is True
        and phase_statuses.get("plan") == "completed"
        and phase_statuses.get("execute") == "completed"
        and phase_statuses.get("validate") == "completed"
        and reflect_exists
    )
    recorder.add(
        "runtime.run.live",
        "passed" if ok else "failed",
        f"Live run executed plan->execute->validate->reflect and terminalized with status={state.get('status')}.",
        run_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    if not ok:
        raise RuntimeError("runtime.run.live failed")


def case_runtime_run_sleep(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    run_result = _run_command(
        [PYTHON, "-m", "thoth.cli", "run", "--work-id", "task-1", "--sleep"],
        cwd=project_dir,
        env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "complete"},
        timeout=60,
    )
    run_artifacts = _save_command(recorder, "runtime-run-sleep", run_result)
    packet = _extract_json(run_result.stdout)
    run_id = str(packet.get("run_id") or "")
    if run_result.returncode != 0 or not run_id:
        recorder.add("runtime.run.sleep", "failed", "Sleep run preparation failed.", run_artifacts)
        raise RuntimeError("run --sleep preparation failed")
    _wait_until(
        lambda: _state_payload(project_dir, run_id).get("status") == "completed",
        timeout=20,
        description=f"sleep run {run_id} to complete",
    )
    state = _state_payload(project_dir, run_id)
    result = _result_payload(project_dir, run_id)
    ok = packet.get("dispatch_mode") == "external_worker" and state.get("status") == "completed" and result.get("status") == "completed"
    recorder.add(
        "runtime.run.sleep",
        "passed" if ok else "failed",
        f"Sleep run established the external-worker ledger and completed with status={state.get('status')}.",
        run_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    if not ok:
        raise RuntimeError("runtime.run.sleep failed")


def case_runtime_run_validate_fail(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    run_result = _run_command([PYTHON, "-m", "thoth.cli", "run", "--work-id", "task-1"], cwd=project_dir, env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "fail"}, timeout=60)
    run_artifacts = _save_command(recorder, "runtime-run-validate-fail", run_result)
    run_id = _extract_runtime_run_id(run_result.stdout)
    if run_result.returncode != 1 or not run_id:
        recorder.add("runtime.run.validate_fail", "failed", "Live run validate failure did not terminalize as expected.", run_artifacts)
        raise RuntimeError("validate-fail live run failed")
    phase_state = _read_json(project_dir / ".thoth" / "runs" / run_id / "phase_state.json")
    state = _state_payload(project_dir, run_id)
    result = _result_payload(project_dir, run_id)
    phase_statuses = phase_state.get("phase_statuses") if isinstance(phase_state.get("phase_statuses"), dict) else {}
    reflect_exists = (project_dir / ".thoth" / "runs" / run_id / "reflect.json").exists()
    ok = (
        state.get("status") == "failed"
        and result.get("status") == "failed"
        and result.get("result", {}).get("validate_passed") is False
        and phase_statuses.get("validate") == "failed"
        and phase_statuses.get("reflect") == "completed"
        and reflect_exists
    )
    recorder.add(
        "runtime.run.validate_fail",
        "passed" if ok else "failed",
        f"Validator failure forced reflect and failed terminalization with status={state.get('status')}.",
        run_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    if not ok:
        raise RuntimeError("runtime.run.validate_fail failed")


def case_runtime_loop_live(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    loop_result = _run_command([PYTHON, "-m", "thoth.cli", "loop", "--work-id", "task-1"], cwd=project_dir, env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "complete"}, timeout=60)
    loop_artifacts = _save_command(recorder, "runtime-loop-live", loop_result)
    run_id = _extract_runtime_run_id(loop_result.stdout)
    if loop_result.returncode != 0 or not run_id:
        recorder.add("runtime.loop.live", "failed", "Live loop execution failed.", loop_artifacts)
        raise RuntimeError("loop live execution failed")
    phase_state = _read_json(project_dir / ".thoth" / "runs" / run_id / "phase_state.json")
    state = _state_payload(project_dir, run_id)
    result = _result_payload(project_dir, run_id)
    loop_state = phase_state.get("loop") if isinstance(phase_state.get("loop"), dict) else {}
    child_run_ids = loop_state.get("child_run_ids") if isinstance(loop_state.get("child_run_ids"), list) else []
    ok = (
        state.get("status") == "completed"
        and result.get("status") == "completed"
        and len(child_run_ids) >= 1
        and result.get("result", {}).get("validate_passed") is True
    )
    recorder.add(
        "runtime.loop.live",
        "passed" if ok else "failed",
        f"Live loop converged through the parent phase_state with child_runs={len(child_run_ids)}.",
        loop_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    if not ok:
        raise RuntimeError("runtime.loop.live failed")


def case_runtime_loop_sleep(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    loop_result = _run_command(
        [PYTHON, "-m", "thoth.cli", "loop", "--work-id", "task-1", "--sleep"],
        cwd=project_dir,
        env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "hold"},
        timeout=60,
    )
    loop_artifacts = _save_command(recorder, "runtime-loop-sleep", loop_result)
    packet = _extract_json(loop_result.stdout)
    run_id = str(packet.get("run_id") or "")
    if loop_result.returncode != 0 or not run_id:
        recorder.add("runtime.loop.sleep", "failed", "Sleep loop preparation failed.", loop_artifacts)
        raise RuntimeError("loop --sleep preparation failed")
    _wait_until(
        lambda: _state_payload(project_dir, run_id).get("status") in {"running", "completed"},
        timeout=20,
        description=f"sleep loop {run_id} to start",
    )
    state = _state_payload(project_dir, run_id)
    ok = packet.get("dispatch_mode") == "external_worker" and state.get("status") == "running" and bool(_run_payload(project_dir, run_id).get("attachable"))
    recorder.add(
        "runtime.loop.sleep",
        "passed" if ok else "failed",
        f"Sleep loop established an attachable external-worker ledger with status={state.get('status')}.",
        loop_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    _stop_runtime_for_cleanup(project_dir, run_id, recorder, label="runtime-loop-sleep-cleanup-stop", command="loop")
    if not ok:
        raise RuntimeError("runtime.loop.sleep failed")


def case_runtime_loop_lease_conflict(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    loop_result = _run_command(
        [PYTHON, "-m", "thoth.cli", "loop", "--work-id", "task-1", "--sleep"],
        cwd=project_dir,
        env={"PYTHONPATH": str(ROOT), "THOTH_TEST_EXTERNAL_WORKER_MODE": "hold"},
        timeout=60,
    )
    loop_artifacts = _save_command(recorder, "runtime-loop-lease-conflict", loop_result)
    packet = _extract_json(loop_result.stdout)
    run_id = str(packet.get("run_id") or "")
    if loop_result.returncode != 0 or not run_id:
        recorder.add("runtime.loop.lease_conflict", "failed", "Sleep loop preparation failed.", loop_artifacts)
        raise RuntimeError("loop sleep preparation for lease conflict failed")
    _wait_until(
        lambda: _state_payload(project_dir, run_id).get("status") in {"running", "completed"},
        timeout=20,
        description=f"sleep loop {run_id} to start",
    )
    conflict = _run_command([PYTHON, "-m", "thoth.cli", "run", "--work-id", "task-1"], cwd=project_dir, env={"PYTHONPATH": str(ROOT)}, timeout=20)
    conflict_artifacts = _save_command(recorder, "runtime-loop-lease-conflict-second-run", conflict)
    ok = conflict.returncode == 1 and "Active lease already held" in conflict.stderr
    recorder.add(
        "runtime.loop.lease_conflict",
        "passed" if ok else "failed",
        f"Second run was rejected while loop {run_id} held the lease.",
        loop_artifacts + conflict_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    _stop_runtime_for_cleanup(project_dir, run_id, recorder, label="runtime-loop-lease-conflict-cleanup-stop", command="loop")
    if not ok:
        raise RuntimeError("runtime.loop.lease_conflict failed")


def case_review_exact_match(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_probe_project(work_root, recorder)
    _compile_probe_tasks(project_dir, recorder, label_prefix="review.exact_match.compile")
    _assert_probe_tasks_ready(project_dir, recorder, check_name="review.exact_match.compile")
    review_result = _run_command(
        [PYTHON, "-m", "thoth.cli", "review", "--work-id", "task-review-probe", "tracker/review_probe.py"],
        cwd=project_dir,
        env={"PYTHONPATH": str(ROOT)},
        timeout=60,
    )
    review_artifacts = _save_command(recorder, "review-exact-match", review_result)
    packet = _extract_json(review_result.stdout)
    run_id = str(packet.get("run_id") or "")
    complete_exact = str(packet.get("protocol_commands", {}).get("complete_exact") or "")
    if review_result.returncode != 0 or not run_id or not complete_exact:
        recorder.add("review.exact_match", "failed", "Review exact-match packet preparation failed.", review_artifacts)
        raise RuntimeError("review exact-match packet preparation failed")
    complete_env = {"PYTHONPATH": str(ROOT)}
    complete_result = _run_command(["bash", "-lc", complete_exact], cwd=project_dir, env=complete_env, timeout=20)
    completion_artifacts = _save_command(recorder, "review-exact-complete", complete_result)
    canonical = _canonical_review_result_payload(project_dir, run_id, _result_payload(project_dir, run_id))
    ok = complete_result.returncode == 0 and canonical == _expected_host_review_result()
    recorder.add(
        "review.exact_match",
        "passed" if ok else "failed",
        "Packet-provided exact completion produced the fixed expected review finding.",
        review_artifacts + completion_artifacts + _artifact_paths_for_run(project_dir, run_id),
    )
    if not ok:
        raise RuntimeError("review.exact_match failed")


def case_observe_dashboard(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder, include_dashboard=True)
    task = load_work_for_execution(project_dir, "task-1", require_ready=True)
    handle, packet = prepare_execution(
        project_dir,
        command_id="run",
        title=str(task.get("title") or "task-1"),
        work_id="task-1",
        host="codex",
        executor="codex",
        sleep_requested=True,
        strict_task=task,
        goal=str(task.get("title") or "task-1"),
    )
    run_id = handle.run_id
    run_artifact = recorder.write_json("dashboard/prepared-run-packet.json", packet)
    state_path = project_dir / ".thoth" / "runs" / run_id / "state.json"
    state = _state_payload(project_dir, run_id)
    state["status"] = "running"
    state["phase"] = "runtime_driver_test_hold"
    state["supervisor_state"] = "running"
    state["last_heartbeat_at"] = "2000-01-01T00:00:00Z"
    state["updated_at"] = utc_now()
    _write_json(state_path, state)
    dashboard_port, dashboard_artifacts = _start_dashboard(project_dir, recorder=recorder, rebuild=False, extra_env={"THOTH_HEARTBEAT_STALE_MINUTES": "1"})
    status_payload = _http_get_json(f"http://127.0.0.1:{dashboard_port}/api/status")
    task_payload = _http_get_json(f"http://127.0.0.1:{dashboard_port}/api/runs/{run_id}")
    stale = bool(task_payload.get("is_stale")) if isinstance(task_payload, dict) else False
    status_artifact = recorder.write_json("dashboard/status.json", status_payload if isinstance(status_payload, dict) else {})
    task_artifact = recorder.write_json("dashboard/run.json", task_payload if isinstance(task_payload, dict) else {})
    recorder.add(
        "observe.dashboard",
        "passed" if stale else "failed",
        "Dashboard backend reported the stale runtime state from the shared ledger.",
        [run_artifact] + dashboard_artifacts + [status_artifact, task_artifact, str(project_dir / ".thoth" / "runs" / run_id / "state.json")],
    )
    _stop_runtime_for_cleanup(project_dir, run_id, recorder, label="observe-dashboard-cleanup-stop")
    _stop_dashboard(project_dir, recorder=recorder)
    if not stale:
        raise RuntimeError("observe.dashboard failed")


def case_hooks_codex(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    project_dir = _prepare_runtime_project(work_root, recorder)
    hooks_config = render_codex_hooks_payload()
    hook_env = {"THOTH_SOURCE_ROOT": str(ROOT)}
    hook_start = _run_command(["bash", "scripts/thoth-codex-hook.sh", "start"], cwd=project_dir, env=hook_env, timeout=60)
    start_payload: dict[str, Any] = {}
    if hook_start.stdout.strip():
        try:
            start_payload = json.loads(hook_start.stdout)
        except json.JSONDecodeError:
            start_payload = {}
    hook_end = _run_command(["bash", "scripts/session-end-check.sh"], cwd=project_dir, env=hook_env, timeout=60)
    hook_artifacts = [
        recorder.write_json("hooks/hooks.json", hooks_config),
        recorder.write_json("hooks/start-hook.json", start_payload),
        *_save_command(recorder, "hooks-start", hook_start),
        *_save_command(recorder, "hooks-end", hook_end),
    ]
    start_context = start_payload.get("hookSpecificOutput", {}).get("additionalContext", "") if isinstance(start_payload, dict) else ""
    ok = bool(hooks_config.get("hooks", {}).get("SessionStart")) and hook_start.returncode == 0 and "Thoth project detected" in start_context and hook_end.returncode == 0
    recorder.add(
        "hooks.codex",
        "passed" if ok else "failed",
        "Generated Codex hook payload and session-end validation stayed mechanically observable.",
        hook_artifacts,
    )
    if not ok:
        raise RuntimeError("hooks.codex failed")

def _host_case_window(case_id: str) -> tuple[str, str | None, str]:
    if case_id.startswith("surface.codex."):
        host = "codex"
    elif case_id.startswith("surface.claude."):
        host = "claude"
    else:
        raise ValueError(f"unsupported host case id: {case_id}")
    suffix = case_id.split(".", 2)[2]
    from_step: str | None = None
    if suffix == "discuss.compile":
        from_step = "discuss-decision"
        step = "discuss-contract-2"
    elif suffix == "run.live_prepare":
        from_step = "run-live"
        step = "run-live"
    elif suffix == "run.sleep_prepare":
        from_step = "run-sleep"
        step = "run-sleep"
    elif suffix == "run.watch":
        from_step = "run-sleep"
        step = "run-watch"
    elif suffix == "run.stop":
        from_step = "run-sleep"
        step = "run-stop"
    elif suffix == "review.exact_match":
        from_step = "review"
        step = "review"
    elif suffix == "loop.live_prepare":
        from_step = "loop-live"
        step = "loop-live"
    elif suffix == "loop.sleep_prepare":
        from_step = "loop-sleep"
        step = "loop-sleep"
    elif suffix == "loop.stop":
        from_step = "loop-sleep"
        step = "loop-stop"
    elif suffix == "auto.sleep_prepare":
        from_step = "auto"
        step = "auto"
    elif suffix == "auto.stop":
        from_step = "auto"
        step = "auto-stop"
    elif suffix == "dashboard.start":
        from_step = "dashboard-start"
        step = "dashboard-start"
    elif suffix == "dashboard.stop":
        from_step = "dashboard-start"
        step = "dashboard-stop"
    else:
        step = suffix.replace(".", "-")
    if suffix in {"status", "doctor", "sync", "init_sync"}:
        from_step = step
    if suffix == "init_sync":
        from_step = "sync"
        step = "sync"
    if suffix == "init":
        from_step = "init"
    return host, from_step, step


def run_host_atomic_case(case_id: str, work_root: Path, recorder: Recorder) -> None:
    host, from_step, to_step = _host_case_window(case_id)
    project_dir = work_root / "project"
    _seed_host_real_repo(project_dir, recorder)
    suffix = case_id.split(".", 2)[2]
    if suffix != "init":
        _materialize_selftest_project(
            project_dir,
            recorder,
            include_dashboard=suffix.startswith("dashboard."),
            label=f"{case_id}.materialize",
        )
    if suffix.startswith(("run.", "loop.", "review.", "auto.")):
        _seed_host_real_tasks(project_dir)
    recorder.add(
        f"{case_id}.seed_repo",
        "passed",
        f"Seeded disposable host probe repo for {host}.",
        [],
    )
    if host == "claude":
        _host_claude(ROOT, project_dir, recorder, from_step=from_step, to_step=to_step)
    else:
        _host_codex(ROOT, project_dir, recorder, from_step=from_step, to_step=to_step)


def case_surface_codex_init(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.init", work_root, recorder)


def case_surface_codex_status(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.status", work_root, recorder)


def case_surface_codex_doctor(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.doctor", work_root, recorder)


def case_surface_codex_discuss_compile(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.discuss.compile", work_root, recorder)


def case_surface_codex_run_live_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.run.live_prepare", work_root, recorder)


def case_surface_codex_run_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.run.sleep_prepare", work_root, recorder)


def case_surface_codex_run_watch(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.run.watch", work_root, recorder)


def case_surface_codex_run_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.run.stop", work_root, recorder)


def case_surface_codex_review_exact_match(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.review.exact_match", work_root, recorder)


def case_surface_codex_loop_live_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.loop.live_prepare", work_root, recorder)


def case_surface_codex_loop_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.loop.sleep_prepare", work_root, recorder)


def case_surface_codex_loop_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.loop.stop", work_root, recorder)


def case_surface_codex_auto_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.auto.sleep_prepare", work_root, recorder)


def case_surface_codex_auto_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.auto.stop", work_root, recorder)


def case_surface_codex_dashboard_start(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.dashboard.start", work_root, recorder)


def case_surface_codex_dashboard_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.dashboard.stop", work_root, recorder)


def case_surface_codex_init_sync(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.codex.init_sync", work_root, recorder)


def case_surface_claude_init(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.init", work_root, recorder)


def case_surface_claude_status(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.status", work_root, recorder)


def case_surface_claude_doctor(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.doctor", work_root, recorder)


def case_surface_claude_discuss_compile(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.discuss.compile", work_root, recorder)


def case_surface_claude_run_live_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.run.live_prepare", work_root, recorder)


def case_surface_claude_run_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.run.sleep_prepare", work_root, recorder)


def case_surface_claude_run_watch(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.run.watch", work_root, recorder)


def case_surface_claude_run_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.run.stop", work_root, recorder)


def case_surface_claude_review_exact_match(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.review.exact_match", work_root, recorder)


def case_surface_claude_loop_live_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.loop.live_prepare", work_root, recorder)


def case_surface_claude_loop_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.loop.sleep_prepare", work_root, recorder)


def case_surface_claude_loop_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.loop.stop", work_root, recorder)


def case_surface_claude_auto_sleep_prepare(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.auto.sleep_prepare", work_root, recorder)


def case_surface_claude_auto_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.auto.stop", work_root, recorder)


def case_surface_claude_dashboard_start(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.dashboard.start", work_root, recorder)


def case_surface_claude_dashboard_stop(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.dashboard.stop", work_root, recorder)


def case_surface_claude_init_sync(work_root: Path, recorder: Recorder, _capabilities: dict[str, Any]) -> None:
    run_host_atomic_case("surface.claude.init_sync", work_root, recorder)
