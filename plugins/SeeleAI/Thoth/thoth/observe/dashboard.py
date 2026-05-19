"""Canonical dashboard runtime service."""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

from thoth.observe.read_model import load_config


def _manifest(project_root: Path) -> dict[str, Any]:
    return load_config(project_root)


def _python_bin(project_root: Path) -> str:
    runtime = _manifest(project_root).get("runtime", {})
    if isinstance(runtime, dict):
        value = runtime.get("python_bin")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "python"


def dashboard_port(project_root: Path) -> int:
    dashboard = _manifest(project_root).get("dashboard", {})
    if isinstance(dashboard, dict):
        value = dashboard.get("port")
        if isinstance(value, int):
            return value
    return 8501


def _pid_file(project_root: Path) -> Path:
    return project_root / ".thoth" / "derived" / "dashboard.pid"


def _log_file(project_root: Path) -> Path:
    return project_root / ".thoth" / "derived" / "dashboard.log"


def _status_file(project_root: Path) -> Path:
    return project_root / ".thoth" / "derived" / "dashboard.status.json"


def _port_file(project_root: Path) -> Path:
    return project_root / ".thoth" / "derived" / "dashboard.port"


def _backend_dir(project_root: Path) -> Path:
    return project_root / "tools" / "dashboard" / "backend"


def _frontend_dir(project_root: Path) -> Path:
    return project_root / "tools" / "dashboard" / "frontend"


def _read_pid(project_root: Path) -> int | None:
    path = _pid_file(project_root)
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        path.unlink(missing_ok=True)
        return None


def _process_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _write_pid(project_root: Path, pid: int) -> None:
    path = _pid_file(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{pid}\n", encoding="utf-8")


def _write_port(project_root: Path, port: int) -> None:
    path = _port_file(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{port}\n", encoding="utf-8")


def _write_status(project_root: Path, payload: dict[str, Any]) -> None:
    path = _status_file(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _cleanup_dashboard_metadata(project_root: Path) -> None:
    _pid_file(project_root).unlink(missing_ok=True)
    _status_file(project_root).unlink(missing_ok=True)
    _port_file(project_root).unlink(missing_ok=True)


def _probe_dashboard_status(port: int, *, timeout: float = 3.0) -> dict[str, Any]:
    opener = build_opener(ProxyHandler({}))
    with opener.open(f"http://127.0.0.1:{port}/api/status", timeout=timeout) as response:  # noqa: S310
        body = response.read().decode("utf-8")
    return json.loads(body)


def _wait_for_dashboard_status(project_root: Path, port: int, *, timeout: float = 20.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            payload = _probe_dashboard_status(port)
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.25)
            continue
        _write_status(project_root, payload)
        _write_port(project_root, port)
        return payload
    raise RuntimeError(f"Dashboard API did not become ready on port {port}: {last_error!r}")


def _pid_from_log(project_root: Path) -> int | None:
    log_path = _log_file(project_root)
    if not log_path.exists():
        return None
    for line in reversed(log_path.read_text(encoding="utf-8", errors="ignore").splitlines()):
        marker = "Started server process ["
        if marker not in line:
            continue
        candidate = line.split(marker, 1)[1].split("]", 1)[0].strip()
        if candidate.isdigit():
            return int(candidate)
    return None


def _pid_matches_dashboard(project_root: Path, pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    proc_dir = Path("/proc") / str(pid)
    try:
        cmdline = (proc_dir / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", errors="ignore")
    except OSError:
        return False
    if "uvicorn" not in cmdline or "app:app" not in cmdline:
        return False
    try:
        cwd = (proc_dir / "cwd").resolve()
    except OSError:
        return False
    return cwd == _backend_dir(project_root).resolve()


def _maybe_build_frontend(project_root: Path, *, required: bool) -> None:
    frontend_dir = _frontend_dir(project_root)
    if not frontend_dir.is_dir():
        return
    dist_dir = frontend_dir / "dist"
    if dist_dir.is_dir() and not required:
        return
    subprocess.run(["npm", "run", "build"], cwd=str(frontend_dir), check=required)


def start_dashboard(project_root: Path, *, rebuild: bool = False) -> dict[str, Any]:
    pid = _read_pid(project_root)
    port = dashboard_port(project_root)
    if _process_alive(pid) and _pid_matches_dashboard(project_root, pid):
        return {"status": "ok", "action": "start", "summary": f"Dashboard already running at http://localhost:{port}", "pid": pid}
    _cleanup_dashboard_metadata(project_root)

    backend_dir = _backend_dir(project_root)
    if not backend_dir.is_dir():
        raise FileNotFoundError(f"Dashboard backend not found at {backend_dir}")

    _maybe_build_frontend(project_root, required=rebuild)
    log_path = _log_file(project_root)
    pid_path = _pid_file(project_root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    python_bin = _python_bin(project_root)
    launch_cmd = " ".join(
        [
            "nohup",
            "bash",
            "-lc",
            shlex.quote(
                " ".join(
                    [
                        "host_pid=\"$(awk '/^NSpid:/ {print $2; exit}' /proc/self/status)\"",
                        "&&",
                        "if [ -z \"$host_pid\" ]; then host_pid=\"$$\"; fi",
                        "&&",
                        f"echo \"$host_pid\" > {shlex.quote(str(pid_path))}",
                        "&&",
                        "exec",
                        shlex.quote(python_bin),
                        "-m",
                        "uvicorn",
                        "app:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        str(port),
                    ]
                )
            ),
            f">>{shlex.quote(str(log_path))}",
            "2>&1",
            "</dev/null",
            "&",
            "echo $!",
        ]
    )
    launch = subprocess.run(
        ["bash", "-lc", launch_cmd],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        timeout=20,
        env=os.environ.copy(),
    )
    if launch.returncode != 0:
        raise RuntimeError(f"Dashboard launch failed. Check {_log_file(project_root)}")
    pid_text = (launch.stdout or "").strip().splitlines()
    fallback_pid = int(pid_text[-1]) if pid_text and pid_text[-1].strip().isdigit() else 0
    time.sleep(1.0)
    try:
        _wait_for_dashboard_status(project_root, port)
    except RuntimeError:
        _cleanup_dashboard_metadata(project_root)
        raise RuntimeError(f"Dashboard failed to start. Check {_log_file(project_root)}")
    pid = _read_pid(project_root) or _pid_from_log(project_root) or fallback_pid
    if pid:
        _write_pid(project_root, pid)
    return {"status": "ok", "action": "start", "summary": f"Dashboard running at http://localhost:{port}", "pid": pid}


def stop_dashboard(project_root: Path) -> dict[str, Any]:
    pid = _read_pid(project_root)
    if not _process_alive(pid) or not _pid_matches_dashboard(project_root, pid):
        _cleanup_dashboard_metadata(project_root)
        return {"status": "ok", "action": "stop", "summary": "Dashboard is not running.", "pid": None}

    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + 5.0
    while time.time() < deadline and _process_alive(pid):
        time.sleep(0.25)
    if _process_alive(pid):
        os.kill(pid, signal.SIGKILL)
    _cleanup_dashboard_metadata(project_root)
    return {"status": "ok", "action": "stop", "summary": f"Dashboard stopped (PID: {pid})", "pid": pid}


def rebuild_dashboard(project_root: Path) -> dict[str, Any]:
    stop_dashboard(project_root)
    _maybe_build_frontend(project_root, required=True)
    return start_dashboard(project_root, rebuild=False)


def manage_dashboard(project_root: Path, action: str) -> dict[str, Any]:
    action = action.strip().lower()
    if action == "start":
        return start_dashboard(project_root)
    if action == "stop":
        return stop_dashboard(project_root)
    if action == "rebuild":
        return rebuild_dashboard(project_root)
    raise ValueError(f"Unknown dashboard action: {action}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Thoth dashboard manager")
    parser.add_argument("action", nargs="?", default="start", choices=("start", "stop", "rebuild"))
    args = parser.parse_args(argv)
    result = manage_dashboard(Path.cwd(), args.action)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
