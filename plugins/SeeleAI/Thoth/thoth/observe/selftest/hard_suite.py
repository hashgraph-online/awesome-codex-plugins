from __future__ import annotations

import argparse
import json
import os
import re
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
from thoth.run.io import project_hash
from thoth.plan.compiler import compile_task_authority
from thoth.run.ledger import complete_run, heartbeat_run
from thoth.selftest_seed import seed_host_real_app

from .model import *
from .recorder import *
from .processes import *
from .capabilities import *
from .fixtures import *

def _local_supervisor(project_dir: Path, run_id: str) -> dict[str, Any]:
    selftest_path = project_dir / ".thoth" / "local-state" / project_hash(project_dir) / "runs" / run_id / "supervisor.json"
    if selftest_path.exists():
        try:
            payload = json.loads(selftest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            return payload
    probe = _run_command(
        [
            PYTHON,
            "-c",
            "from pathlib import Path; from thoth.run.lease import local_registry_root; "
            "import json,sys; p=local_registry_root(Path(sys.argv[1]))/'runs'/sys.argv[2]/'supervisor.json'; "
            "print((p.read_text() if p.exists() else '{}'))",
            str(project_dir),
            run_id,
        ],
        cwd=ROOT,
        timeout=20,
    )
    if probe.stdout.strip():
        try:
            return json.loads(probe.stdout)
        except json.JSONDecodeError:
            return {}
    return {}


def _start_dashboard(project_dir: Path, *, recorder: Recorder, rebuild: bool = False, extra_env: dict[str, str] | None = None) -> tuple[int, list[str]]:
    action = "rebuild" if rebuild else "start"
    result = _run_thoth(project_dir, "dashboard", action, timeout=180, env=extra_env)
    artifacts = _save_command(recorder, f"dashboard-{action}", result)
    if result.returncode != 0:
        raise RuntimeError(f"dashboard {action} failed")
    manifest = _read_json(project_dir / ".thoth" / "objects" / "project" / "project.json")
    payload = manifest.get("payload") if isinstance(manifest.get("payload"), dict) else {}
    port = int(payload.get("dashboard", {}).get("port", 8501))

    def _dashboard_ready() -> bool:
        try:
            return bool(_http_get_json(f"http://127.0.0.1:{port}/api/status").get("runtime"))
        except (URLError, TimeoutError, json.JSONDecodeError):
            return False

    _wait_until(
        _dashboard_ready,
        timeout=20,
        interval=0.5,
        description=f"dashboard on port {port}",
    )
    return port, artifacts


def _stop_dashboard(project_dir: Path, *, recorder: Recorder) -> list[str]:
    result = _run_thoth(project_dir, "dashboard", "stop", timeout=60)
    return _save_command(recorder, "dashboard-stop", result)


def _verify_host_run_completion(
    project_dir: Path,
    recorder: Recorder,
    *,
    check_name: str,
    run_id: str,
    expected_kind: str,
    expected_work_id: str | None = None,
    expected_host: str | None = None,
    expected_executor: str | None = None,
    expected_dispatch_mode: str | None = None,
    require_findings: bool = False,
    timeout: float = 30,
) -> list[str]:
    _wait_until(
        lambda: _state_payload(project_dir, run_id).get("status") in {"completed", "failed", "stopped"},
        timeout=timeout,
        interval=0.5,
        description=f"{check_name} run {run_id}",
    )
    run = _run_payload(project_dir, run_id)
    state = _state_payload(project_dir, run_id)
    acceptance = _result_payload(project_dir, run_id)
    artifacts = [
        str(project_dir / ".thoth" / "runs" / run_id / "run.json"),
        str(project_dir / ".thoth" / "runs" / run_id / "state.json"),
        str(project_dir / ".thoth" / "runs" / run_id / "result.json"),
        str(project_dir / ".thoth" / "runs" / run_id / "packet.json"),
        str(project_dir / ".thoth" / "runs" / run_id / "events.jsonl"),
    ]
    events = _events_payload(project_dir, run_id)
    findings = _review_findings_payload(project_dir, run_id, acceptance)
    ok = (
        run.get("kind") == expected_kind
        and state.get("status") == "completed"
        and acceptance.get("status") == "completed"
    )
    if expected_work_id is not None:
        ok = ok and run.get("work_id") == expected_work_id
    if expected_host is not None:
        ok = ok and run.get("host") == expected_host
    if expected_executor is not None:
        ok = ok and run.get("executor") == expected_executor
    if expected_dispatch_mode is not None:
        ok = ok and run.get("dispatch_mode") == expected_dispatch_mode
    if require_findings:
        ok = ok and len(findings) > 0
    ok = ok and not _host_run_uses_forbidden_fallback(acceptance, events)
    detail = (
        f"Verified {expected_kind} run {run_id}: status={state.get('status')} "
        f"acceptance={acceptance.get('status')} work_id={run.get('work_id')} "
        f"host={run.get('host')} executor={run.get('executor')} dispatch={run.get('dispatch_mode')}"
    )
    recorder.add(check_name, "passed" if ok else "failed", detail, artifacts)
    if not ok:
        raise RuntimeError(f"{check_name} failed for run {run_id}")
    return artifacts


def _repo_hard_suite(project_dir: Path, recorder: Recorder) -> dict[str, Any]:
    details: dict[str, Any] = {}
    _init_git_repo(project_dir)

    init_result = _run_thoth(project_dir, "init", timeout=60)
    recorder.add(
        "repo.init",
        "passed" if init_result.returncode == 0 else "failed",
        "Initialized a fresh temp project through the public CLI.",
        _save_command(recorder, "repo-init", init_result),
    )
    if init_result.returncode != 0:
        raise RuntimeError("thoth init failed")

    port = _free_port()
    _set_dashboard_port(project_dir, port)
    _seed_task(project_dir)

    discuss_payload = json.dumps(
        {
            "decision_id": "DEC-selftest-runtime",
            "scope_id": "frontend-runtime",
            "question": "Which runtime validation method should be executed for selftest?",
            "candidate_method_ids": ["real-cli-runtime-check"],
            "selected_values": {"candidate_method_id": "real-cli-runtime-check"},
            "status": "frozen",
            "unresolved_gaps": [],
        },
        ensure_ascii=False,
    )

    review_run_id = ""
    for name, argv in (
        ("repo.status_json", ["status", "--json"]),
        ("repo.doctor_quick", ["doctor", "--quick"]),
        ("repo.sync", ["sync"]),
        ("repo.discuss", ["discuss", "--decision-json", discuss_payload]),
        ("repo.review", ["review", "selftest", "review"]),
        ("repo.report", ["report"]),
    ):
        result = _run_thoth(project_dir, *argv, timeout=120)
        recorder.add(
            name,
            "passed" if result.returncode == 0 else "failed",
            f"Command {' '.join(argv)} completed with return code {result.returncode}.",
            _save_command(recorder, name, result),
        )
        if result.returncode != 0:
            raise RuntimeError(f"{name} failed")
        if name == "repo.review":
            review_packet = _extract_json(result.stdout)
            review_run_id = str(review_packet.get("run_id") or "")
            if review_run_id:
                stop_review = _run_thoth(project_dir, "run", "--stop", review_run_id, timeout=20)
                recorder.add(
                    "repo.review_stop",
                    "passed" if stop_review.returncode == 0 else "failed",
                    f"Stopped live review run {review_run_id} before execution lease-sensitive checks.",
                    _save_command(recorder, "repo-review-stop", stop_review),
                )
                if stop_review.returncode != 0:
                    raise RuntimeError("review stop failed")

    run_result = _run_thoth(project_dir, "run", "--work-id", "task-1", timeout=60)
    run_artifacts = _save_command(recorder, "run-live", run_result)
    run_packet = _extract_json(run_result.stdout)
    run_id = str(run_packet.get("run_id") or "")
    if run_result.returncode != 0 or not run_id:
        recorder.add("runtime.run_live_prepare", "failed", "Live run packet preparation failed.", run_artifacts)
        raise RuntimeError("run live prepare failed")
    recorder.add("runtime.run_live_prepare", "passed", f"Prepared live run packet {run_id}.", run_artifacts)
    watch_result = _run_thoth(project_dir, "run", "--watch", run_id, timeout=20)
    watch_artifacts = _save_command(recorder, "run-watch", watch_result)
    recorder.add("runtime.run_watch", "passed", f"Watch stream attached to {run_id}.", run_artifacts + watch_artifacts)

    stop_result = _run_thoth(project_dir, "run", "--stop", run_id, timeout=20)
    _wait_until(
        lambda: _state_payload(project_dir, run_id).get("status") == "stopped",
        timeout=15,
        description=f"run {run_id} to stop",
    )
    stop_artifacts = _save_command(recorder, "run-stop", stop_result)
    recorder.add("runtime.run_stop", "passed", f"Stopped live run {run_id}.", stop_artifacts)

    run_sleep_result = _run_thoth(
        project_dir,
        "run",
        "--work-id",
        "task-1",
        "--sleep",
        timeout=60,
        env={"THOTH_TEST_EXTERNAL_WORKER_MODE": "complete"},
    )
    run_sleep_artifacts = _save_command(recorder, "run-sleep", run_sleep_result)
    run_sleep_packet = _extract_json(run_sleep_result.stdout)
    run_sleep_id = str(run_sleep_packet.get("run_id") or "")
    if run_sleep_result.returncode != 0 or not run_sleep_id:
        recorder.add("runtime.run_sleep", "failed", "Sleep run creation failed.", run_sleep_artifacts)
        raise RuntimeError("run --sleep failed")
    _wait_until(
        lambda: _state_payload(project_dir, run_sleep_id).get("status") == "completed",
        timeout=15,
        description=f"sleep run {run_sleep_id} to complete",
    )
    recorder.add("runtime.run_sleep", "passed", f"Prepared sleep run packet {run_sleep_id}.", run_sleep_artifacts)

    loop_live_result = _run_thoth(project_dir, "loop", "--work-id", "task-1", timeout=60)
    loop_live_artifacts = _save_command(recorder, "loop-live", loop_live_result)
    loop_live_packet = _extract_json(loop_live_result.stdout)
    loop_live_id = str(loop_live_packet.get("run_id") or "")
    if loop_live_result.returncode != 0 or not loop_live_id:
        recorder.add("runtime.loop_live_prepare", "failed", "Live loop packet preparation failed.", loop_live_artifacts)
        raise RuntimeError("loop live prepare failed")
    recorder.add("runtime.loop_live_prepare", "passed", f"Prepared live loop packet {loop_live_id}.", loop_live_artifacts)
    loop_live_watch = _run_thoth(project_dir, "loop", "--watch", loop_live_id, timeout=20)
    loop_live_watch_artifacts = _save_command(recorder, "loop-watch", loop_live_watch)
    recorder.add("runtime.loop_watch", "passed", f"Watch stream attached to {loop_live_id}.", loop_live_artifacts + loop_live_watch_artifacts)
    loop_live_stop = _run_thoth(project_dir, "loop", "--stop", loop_live_id, timeout=20)
    _wait_until(
        lambda: _state_payload(project_dir, loop_live_id).get("status") == "stopped",
        timeout=15,
        description=f"loop {loop_live_id} to stop",
    )
    recorder.add("runtime.loop_live_stop", "passed", f"Stopped live loop {loop_live_id}.", _save_command(recorder, "loop-live-stop", loop_live_stop))

    loop_result = _run_thoth(
        project_dir,
        "loop",
        "--work-id",
        "task-1",
        "--sleep",
        timeout=60,
        env={"THOTH_TEST_EXTERNAL_WORKER_MODE": "hold"},
    )
    loop_artifacts = _save_command(recorder, "loop-sleep", loop_result)
    loop_packet = _extract_json(loop_result.stdout)
    loop_id = str(loop_packet.get("run_id") or "")
    if loop_result.returncode != 0 or not loop_id:
        recorder.add("runtime.loop_sleep", "failed", "Sleep loop creation failed.", loop_artifacts)
        raise RuntimeError("loop --sleep failed")
    _wait_until(
        lambda: _state_payload(project_dir, loop_id).get("status") in {"running", "completed"},
        timeout=15,
        description=f"loop {loop_id} to become running",
    )
    recorder.add("runtime.loop_sleep", "passed", f"Prepared sleep loop packet {loop_id}.", loop_artifacts)

    conflict_result = _run_thoth(project_dir, "run", "--work-id", "task-1", timeout=60)
    conflict_artifacts = _save_command(recorder, "lease-conflict-probe", conflict_result)
    if conflict_result.returncode == 1 and "Active lease already held" in conflict_result.stderr:
        recorder.add(
            "runtime.lease_conflict",
            "passed",
            f"Secondary live run was rejected while {loop_id} held the repo lease.",
            conflict_artifacts,
        )
    else:
        recorder.add(
            "runtime.lease_conflict",
            "failed",
            f"Secondary run did not hard-fail with lease conflict. returncode={conflict_result.returncode}",
            conflict_artifacts,
        )
        raise RuntimeError("lease conflict behavior regressed")

    loop_stop = _run_thoth(project_dir, "loop", "--stop", loop_id, timeout=20)
    _wait_until(
        lambda: _state_payload(project_dir, loop_id).get("status") in {"stopped", "completed"},
        timeout=15,
        description=f"loop {loop_id} to stop",
    )
    recorder.add("runtime.loop_stop", "passed", f"Stopped loop {loop_id}.", _save_command(recorder, "loop-stop", loop_stop))

    dashboard_run = _run_thoth(project_dir, "run", "--work-id", "task-1", timeout=60)
    dashboard_run_artifacts = _save_command(recorder, "dashboard-run-live", dashboard_run)
    dashboard_packet = _extract_json(dashboard_run.stdout)
    dashboard_run_id = str(dashboard_packet.get("run_id") or "")
    if dashboard_run.returncode != 0 or not dashboard_run_id:
        recorder.add("dashboard.live_run_prepare", "failed", "Dashboard freshness probe could not prepare a live run.", dashboard_run_artifacts)
        raise RuntimeError("dashboard live run prepare failed")
    recorder.add("dashboard.live_run_prepare", "passed", f"Prepared live run {dashboard_run_id} for dashboard freshness checks.", dashboard_run_artifacts)

    state_path = project_dir / ".thoth" / "runs" / dashboard_run_id / "state.json"
    state = _state_payload(project_dir, dashboard_run_id)
    state["last_heartbeat_at"] = "2000-01-01T00:00:00Z"
    state["updated_at"] = utc_now()
    _write_json(state_path, state)

    dashboard_env = {"THOTH_HEARTBEAT_STALE_MINUTES": "1"}
    dashboard_port, dashboard_artifacts = _start_dashboard(project_dir, recorder=recorder, rebuild=False, extra_env=dashboard_env)
    status_payload = _http_get_json(f"http://127.0.0.1:{dashboard_port}/api/status")
    task_payload = _http_get_json(f"http://127.0.0.1:{dashboard_port}/api/runs/{dashboard_run_id}")
    details["dashboard_port"] = dashboard_port
    recorder.write_json("api/status.json", status_payload)
    recorder.write_json("api/active-run.json", task_payload if isinstance(task_payload, dict) else {})
    stale = bool(task_payload.get("is_stale")) if isinstance(task_payload, dict) else False
    recorder.add(
        "dashboard.api_runtime",
        "passed" if stale else "failed",
        "Dashboard backend served the real temp project and reported stale heartbeat state.",
        dashboard_artifacts + [str(recorder.artifact_dir / "api" / "status.json"), str(recorder.artifact_dir / "api" / "active-run.json")],
    )
    if not stale:
        raise RuntimeError("dashboard did not report stale heartbeat")

    restart_artifacts = _stop_dashboard(project_dir, recorder=recorder)
    restarted_port, restarted_artifacts = _start_dashboard(project_dir, recorder=recorder, rebuild=False, extra_env=dashboard_env)
    if restarted_port != dashboard_port:
        raise RuntimeError("dashboard port drifted across restart")
    recorder.add(
        "dashboard.restart",
        "passed",
        f"Dashboard restarted cleanly on port {dashboard_port}.",
        restart_artifacts + restarted_artifacts,
    )

    hooks_config = render_codex_hooks_payload()
    hook_env = {"THOTH_SOURCE_ROOT": str(ROOT)}
    hook_start = _run_command(
        ["bash", "scripts/thoth-codex-hook.sh", "start"],
        cwd=project_dir,
        env=hook_env,
        timeout=60,
    )
    start_hook_payload: dict[str, Any] = {}
    if hook_start.stdout.strip():
        try:
            start_hook_payload = json.loads(hook_start.stdout)
        except json.JSONDecodeError:
            start_hook_payload = {}
    hook_end = _run_command(["bash", "scripts/session-end-check.sh"], cwd=project_dir, env=hook_env, timeout=60)
    hook_artifacts = [
        recorder.write_json("hooks/hooks.json", hooks_config),
        recorder.write_json("hooks/start-hook.json", start_hook_payload),
        *_save_command(recorder, "hook-start", hook_start),
        *_save_command(recorder, "hook-end", hook_end),
    ]
    session_start_hooks = hooks_config.get("hooks", {}).get("SessionStart", [])
    start_context = start_hook_payload.get("hookSpecificOutput", {}).get("additionalContext", "") if isinstance(start_hook_payload, dict) else ""
    hook_ok = bool(session_start_hooks) and hook_start.returncode == 0 and "Thoth project detected" in start_context and hook_end.returncode == 0
    recorder.add("hooks.local_success", "passed" if hook_ok else "failed", "Generated project hook configuration, start context injection, and session-end script completed.", hook_artifacts)
    if not hook_ok:
        raise RuntimeError("local session hook success path failed")

    broken_work = project_dir / ".thoth" / "objects" / "work_item" / "work-broken.json"
    _write_json(
        broken_work,
        {
            "schema_version": 1,
            "kind": "work_item",
            "object_id": "work-broken",
            "status": "ready",
            "title": "Broken contract",
            "summary": "Intentionally invalid work item for hook failure observability.",
            "revision": 1,
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "source": "selftest",
            "links": [],
            "payload": {"work_kind": "execution", "runnable": True, "missing_questions": []},
            "history": [],
        },
    )
    broken_hook = _run_command(["bash", "scripts/session-end-check.sh"], cwd=project_dir, env=hook_env, timeout=60)
    broken_artifacts = _save_command(recorder, "hook-broken", broken_hook)
    broken_work.unlink(missing_ok=True)
    degraded = broken_hook.returncode != 0
    recorder.add(
        "hooks.local_failure_observable",
        "passed" if degraded else "failed",
        "Broken work item object caused the generated session-end hook script to fail observably.",
        broken_artifacts,
    )
    if not degraded:
        raise RuntimeError("hook failure path was not observable")

    dashboard_run_stop = _run_thoth(project_dir, "run", "--stop", dashboard_run_id, timeout=20)
    _wait_until(
        lambda: _state_payload(project_dir, dashboard_run_id).get("status") in {"stopped", "completed"},
        timeout=15,
        description=f"dashboard run {dashboard_run_id} to stop",
    )
    recorder.add("dashboard.live_run_stop", "passed", f"Stopped dashboard live run {dashboard_run_id}.", _save_command(recorder, "dashboard-run-stop", dashboard_run_stop))
    _stop_dashboard(project_dir, recorder=recorder)

    details["run_id"] = run_id
    details["loop_id"] = loop_id
    details["dashboard_run_id"] = dashboard_run_id
    if review_run_id:
        details["review_run_id"] = review_run_id
    return details

__all__ = [name for name in globals() if not name.startswith("__")]
