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
from thoth.plan.compiler import compile_task_authority
from thoth.run.ledger import complete_run, heartbeat_run
from thoth.selftest_seed import seed_host_real_app

from .model import *
from .recorder import *

def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        shutil.rmtree(path, ignore_errors=True)


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
    except OSError:
        return False
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def _legacy_heavy_process_targets(
    *,
    proc_root: Path = Path("/proc"),
    current_pid: int | None = None,
    fixed_roots: Iterable[Path] | None = None,
) -> list[int]:
    roots = tuple((fixed_roots or (FIXED_CLAUDE_DIR, FIXED_CODEX_DIR, FIXED_RUNTIME_DIR)))
    current = int(current_pid or os.getpid())
    targets: set[int] = set()
    for entry in proc_root.iterdir():
        if not entry.is_dir() or not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == current:
            continue
        cmdline_bytes = b""
        try:
            cmdline_bytes = (entry / "cmdline").read_bytes()
        except OSError:
            cmdline_bytes = b""
        cmdline = cmdline_bytes.replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
        cwd: Path | None = None
        try:
            cwd = (entry / "cwd").resolve()
        except OSError:
            cwd = None
        if "python -m thoth.selftest" in cmdline and "--tier heavy" in cmdline:
            targets.add(pid)
            continue
        if any(str(root) in cmdline for root in roots):
            targets.add(pid)
            continue
        if cwd is not None and any(_path_is_within(cwd, root) for root in roots):
            targets.add(pid)
    return sorted(targets)


def _terminate_processes(
    pids: Iterable[int],
    *,
    proc_root: Path = Path("/proc"),
    term_timeout: float = 5.0,
    kill_timeout: float = 2.0,
) -> list[int]:
    remaining = sorted({int(pid) for pid in pids})
    for signum, timeout in ((signal.SIGTERM, term_timeout), (signal.SIGKILL, kill_timeout)):
        attempted: list[int] = []
        for pid in remaining:
            try:
                os.kill(pid, signum)
            except ProcessLookupError:
                continue
            except PermissionError:
                attempted.append(pid)
            else:
                attempted.append(pid)
        if not attempted:
            return []
        deadline = time.time() + timeout
        while True:
            remaining = [pid for pid in attempted if (proc_root / str(pid)).exists()]
            if not remaining or time.time() >= deadline:
                break
            time.sleep(0.05)
    return [pid for pid in remaining if (proc_root / str(pid)).exists()]


def _cleanup_legacy_heavy_processes() -> None:
    stale_pids = _legacy_heavy_process_targets()
    if not stale_pids:
        return
    still_running = _terminate_processes(stale_pids)
    if still_running:
        raise RuntimeError(f"failed to clear stale heavy host-real processes: {still_running}")


def _cleanup_legacy_heavy_tmp(*, preserve: Iterable[Path], tmp_root: Path = Path("/tmp")) -> None:
    preserve_paths = {item.resolve() for item in preserve}
    cleanup_patterns = ("thoth-heavy-*", "thoth-selftest-*")
    for pattern in cleanup_patterns:
        for candidate in tmp_root.glob(pattern):
            resolved = candidate.resolve()
            if resolved in preserve_paths:
                continue
            _remove_path(candidate)


def _http_get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=5) as response:  # noqa: S310 - local self-test URL
        return json.loads(response.read().decode("utf-8"))


def _selftest_runtime_exceeded_message() -> str:
    label = f" for {_SELFTEST_DEADLINE_LABEL}" if _SELFTEST_DEADLINE_LABEL else ""
    if _SELFTEST_DEADLINE_SECONDS is None:
        return f"Self-test exceeded the active runtime limit{label}."
    seconds = int(_SELFTEST_DEADLINE_SECONDS)
    return f"Self-test exceeded the active {seconds}s runtime limit{label}."


def _remaining_selftest_seconds() -> float | None:
    if _SELFTEST_DEADLINE is None:
        return None
    return max(0.0, _SELFTEST_DEADLINE - time.time())


class _SelftestBudget:
    def __init__(self, seconds: float | None, *, label: str) -> None:
        self.seconds = seconds
        self.label = label
        self._previous_deadline: float | None = None
        self._previous_label: str | None = None
        self._previous_seconds: float | None = None

    def __enter__(self) -> None:
        global _SELFTEST_DEADLINE, _SELFTEST_DEADLINE_LABEL, _SELFTEST_DEADLINE_SECONDS
        self._previous_deadline = _SELFTEST_DEADLINE
        self._previous_label = _SELFTEST_DEADLINE_LABEL
        self._previous_seconds = _SELFTEST_DEADLINE_SECONDS
        if self.seconds is None:
            _SELFTEST_DEADLINE = self._previous_deadline
            _SELFTEST_DEADLINE_SECONDS = self._previous_seconds
        else:
            requested_deadline = time.time() + self.seconds
            if self._previous_deadline is not None:
                _SELFTEST_DEADLINE = min(self._previous_deadline, requested_deadline)
                _SELFTEST_DEADLINE_SECONDS = max(0.0, _SELFTEST_DEADLINE - time.time())
            else:
                _SELFTEST_DEADLINE = requested_deadline
                _SELFTEST_DEADLINE_SECONDS = self.seconds
        _SELFTEST_DEADLINE_LABEL = self.label

    def __exit__(self, exc_type, exc, tb) -> None:
        global _SELFTEST_DEADLINE, _SELFTEST_DEADLINE_LABEL, _SELFTEST_DEADLINE_SECONDS
        _SELFTEST_DEADLINE = self._previous_deadline
        _SELFTEST_DEADLINE_LABEL = self._previous_label
        _SELFTEST_DEADLINE_SECONDS = self._previous_seconds


def _emit_selftest_progress(message: str) -> None:
    if not _SELFTEST_STREAM_OUTPUT:
        return
    print(f"[thoth-selftest] {message}", file=sys.stderr, flush=True)


def _cap_selftest_timeout(timeout: float) -> float:
    remaining = _remaining_selftest_seconds()
    if remaining is None:
        return timeout
    if remaining <= 0:
        raise RuntimeError(_selftest_runtime_exceeded_message())
    return max(0.1, min(timeout, remaining))


def _wait_until(predicate, *, timeout: float, interval: float = 0.2, description: str) -> None:
    deadline = time.time() + _cap_selftest_timeout(timeout)
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(interval)
        remaining = _remaining_selftest_seconds()
        if remaining is not None and remaining <= 0:
            raise RuntimeError(_selftest_runtime_exceeded_message())
    raise RuntimeError(f"Timed out waiting for {description}")


def _run_command(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: float = 120,
) -> CommandResult:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    effective_timeout = _cap_selftest_timeout(timeout)
    started = time.time()
    _emit_selftest_progress(f"exec cwd={cwd} argv={json.dumps(argv, ensure_ascii=False)} timeout={effective_timeout:.1f}s")
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    selector = selectors.DefaultSelector()
    if process.stdout is not None:
        selector.register(process.stdout, selectors.EVENT_READ, data="stdout")
    if process.stderr is not None:
        selector.register(process.stderr, selectors.EVENT_READ, data="stderr")

    timed_out = False
    while selector.get_map():
        remaining = effective_timeout - (time.time() - started)
        if remaining <= 0:
            timed_out = True
            process.kill()
            break
        events = selector.select(timeout=min(0.1, remaining))
        if not events:
            if process.poll() is not None:
                events = [(key, None) for key in list(selector.get_map().values())]
            else:
                continue
        for key, _ in events:
            stream = key.fileobj
            data = b""
            try:
                data = stream.read1(4096) if hasattr(stream, "read1") else stream.read(4096)
            except OSError:
                data = b""
            if not data:
                selector.unregister(stream)
                stream.close()
                continue
            if key.data == "stdout":
                stdout_chunks.append(data)
                if _SELFTEST_STREAM_OUTPUT:
                    sys.stdout.write(data.decode("utf-8", errors="ignore"))
                    sys.stdout.flush()
            else:
                stderr_chunks.append(data)
                if _SELFTEST_STREAM_OUTPUT:
                    sys.stderr.write(data.decode("utf-8", errors="ignore"))
                    sys.stderr.flush()

    if timed_out:
        deadline = time.time() + 1.0
        while selector.get_map() and time.time() < deadline:
            events = selector.select(timeout=0.05)
            if not events:
                break
            for key, _ in events:
                stream = key.fileobj
                data = b""
                try:
                    data = stream.read1(4096) if hasattr(stream, "read1") else stream.read(4096)
                except OSError:
                    data = b""
                if not data:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if key.data == "stdout":
                    stdout_chunks.append(data)
                else:
                    stderr_chunks.append(data)

    for key in list(selector.get_map().values()):
        try:
            selector.unregister(key.fileobj)
        except Exception:
            pass
        try:
            key.fileobj.close()
        except Exception:
            pass

    try:
        process.wait(timeout=1.0 if timed_out else 0.5)
    except subprocess.TimeoutExpired:
        try:
            process.terminate()
        except Exception:
            pass
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                pass

    stdout = b"".join(stdout_chunks).decode("utf-8", errors="ignore")
    stderr = b"".join(stderr_chunks).decode("utf-8", errors="ignore")
    if timed_out:
        timeout_note = f"Command timed out after {effective_timeout:.1f}s."
        stderr = f"{stderr}\n{timeout_note}".strip()
        _emit_selftest_progress(f"timeout argv={json.dumps(argv, ensure_ascii=False)} after {effective_timeout:.1f}s")
        return CommandResult(
            argv=argv,
            cwd=str(cwd),
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=round(time.time() - started, 3),
        )
    _emit_selftest_progress(
        f"done rc={process.returncode} argv={json.dumps(argv, ensure_ascii=False)} duration={time.time() - started:.3f}s"
    )
    return CommandResult(
        argv=argv,
        cwd=str(cwd),
        returncode=int(process.returncode or 0),
        stdout=stdout,
        stderr=stderr,
        duration_seconds=round(time.time() - started, 3),
    )


def _save_command(recorder: Recorder, name: str, result: CommandResult) -> list[str]:
    stem = _safe_name(name)
    return [
        recorder.write_text(
            f"commands/{stem}.txt",
            textwrap.dedent(
                f"""\
                CWD: {result.cwd}
                ARGV: {json.dumps(result.argv, ensure_ascii=False)}
                RETURN CODE: {result.returncode}
                DURATION: {result.duration_seconds:.3f}s

                --- STDOUT ---
                {result.stdout}

                --- STDERR ---
                {result.stderr}
                """
            ),
        )
    ]

__all__ = [name for name in globals() if not name.startswith("__")]
