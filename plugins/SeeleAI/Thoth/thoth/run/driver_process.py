"""Private process entrypoint for detached Thoth runtime drivers."""

from __future__ import annotations

import argparse
import signal
import time
from pathlib import Path

from .driver import SilentSink, execute_runtime_controller
from .ledger import _update_state, _write_stopped_result, fail_run, heartbeat_run
from .lease import release_repo_lease
from .model import RunHandle
from .supervisor import write_run_supervisor
from .worker import (
    ExternalWorkerPhaseDriver,
    TestPhaseDriver,
    _normalize_worker_executor,
    _test_external_worker_mode,
    _worker_timeout_seconds,
)


def _terminalize_stopped_driver(handle: RunHandle) -> int:
    _update_state(handle, status="stopped", phase="stopped", progress_pct=100, supervisor_state="stopped")
    _write_stopped_result(handle)
    release_repo_lease(handle.project_root, handle.run_id)
    write_run_supervisor(handle, state="stopped", runtime="runtime_driver")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private Thoth runtime driver process.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve()
    handle = RunHandle(project_root=project_root, run_id=args.run_id)
    run_payload = handle.run_json()
    if not run_payload:
        return 1

    interrupted = False

    def _mark_stop(_signum, _frame):
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGTERM, _mark_stop)
    signal.signal(signal.SIGINT, _mark_stop)
    write_run_supervisor(handle, state="running", runtime="runtime_driver")
    heartbeat_run(project_root, args.run_id, phase="runtime_driver_start", progress_pct=5, note="runtime driver started")

    test_mode = _test_external_worker_mode()
    if test_mode == "hold":
        while True:
            if interrupted or handle.state_json().get("status") == "stopping":
                return _terminalize_stopped_driver(handle)
            heartbeat_run(project_root, args.run_id, phase="runtime_driver_test_hold", progress_pct=25, note="runtime driver hold test seam heartbeat")
            time.sleep(0.5)
    if test_mode == "fail":
        driver = TestPhaseDriver("fail")
    elif test_mode == "complete":
        driver = TestPhaseDriver("complete")
    else:
        executor = _normalize_worker_executor(run_payload.get("executor"))
        driver = ExternalWorkerPhaseDriver(executor=executor, timeout_seconds=_worker_timeout_seconds(run_payload))

    try:
        status = execute_runtime_controller(project_root, args.run_id, driver=driver, sink=SilentSink())
    except Exception as exc:
        fail_run(
            project_root,
            args.run_id,
            summary="Runtime driver failed.",
            reason=str(exc),
            result_payload={"worker_runtime": "runtime_driver", "executor": run_payload.get("executor")},
        )
        write_run_supervisor(handle, state="failed", runtime="runtime_driver")
        return 1
    final_state = handle.state_json().get("status")
    runtime_state = "completed" if final_state == "completed" else "stopped" if final_state == "stopped" else "failed"
    write_run_supervisor(handle, state=runtime_state, runtime="runtime_driver")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
