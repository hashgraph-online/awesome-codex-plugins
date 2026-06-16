#!/usr/bin/env python3
"""Bootstrap and run the Codex Usage Tracker MCP server.

Marketplace installs mirror only the plugin bundle, not a repo-local virtual
environment. This launcher creates a cached runtime on first use, installs the
package from GitHub, and then execs the real MCP server.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PACKAGE_SPEC = os.environ.get(
    "CODEX_USAGE_TRACKER_PACKAGE_SPEC",
    "codex-usage-tracking==0.6.1",
)
RUNTIME_VERSION = "0.6.1"
PACKAGE_SPEC_MARKER = ".codex-usage-tracker-package-spec"
MODULE_CHECK = (
    "import importlib.metadata; "
    "importlib.metadata.version('codex-usage-tracking'); "
    "importlib.metadata.version('mcp')"
)
MODULE_ARGS = ["-m", "codex_usage_tracker.mcp_server"]


def main() -> int:
    plugin_root = Path(__file__).resolve().parents[3]
    runtime_python = _runtime_python()

    for candidate in _local_candidate_pythons(plugin_root):
        if candidate.exists() and _can_import_server(candidate):
            _exec_server(candidate)

    if _can_use_runtime(runtime_python):
        _exec_server(runtime_python)

    _ensure_runtime(runtime_python)
    if not _can_import_server(runtime_python):
        print(
            "Codex Usage Tracker runtime installed, but the MCP server could not be imported.",
            file=sys.stderr,
        )
        return 1
    _exec_server(runtime_python)
    return 1


def _local_candidate_pythons(plugin_root: Path) -> list[Path]:
    candidates: list[Path] = []
    override = os.environ.get("CODEX_USAGE_TRACKER_MCP_PYTHON")
    if override:
        candidates.append(Path(override).expanduser())
    candidates.append(plugin_root / ".venv" / _python_bin())
    return candidates


def _runtime_python() -> Path:
    configured = os.environ.get("CODEX_USAGE_TRACKER_RUNTIME_DIR")
    runtime_dir = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".cache" / "codex-usage-tracker" / "mcp-runtime" / RUNTIME_VERSION
    )
    return runtime_dir / _python_bin()


def _python_bin() -> Path:
    return Path("Scripts/python.exe") if os.name == "nt" else Path("bin/python")


def _venv_root(python_path: Path) -> Path:
    return python_path.parents[1]


def _package_spec_marker(python_path: Path) -> Path:
    return _venv_root(python_path) / PACKAGE_SPEC_MARKER


def _can_use_runtime(python_path: Path) -> bool:
    if not python_path.exists() or not _can_import_server(python_path):
        return False
    marker = _package_spec_marker(python_path)
    try:
        return marker.read_text(encoding="utf-8").strip() == PACKAGE_SPEC
    except OSError:
        return False


def _can_import_server(python_path: Path) -> bool:
    try:
        result = subprocess.run(
            [str(python_path), "-c", MODULE_CHECK],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


def _ensure_runtime(python_path: Path) -> None:
    venv_root = _venv_root(python_path)
    if not python_path.exists():
        print(f"Creating Codex Usage Tracker MCP runtime at {venv_root}", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(venv_root)], check=True)
    print(f"Installing Codex Usage Tracker MCP runtime from {PACKAGE_SPEC}", file=sys.stderr)
    subprocess.run(
        [str(python_path), "-m", "pip", "install", "--upgrade", PACKAGE_SPEC],
        check=True,
    )
    _package_spec_marker(python_path).write_text(PACKAGE_SPEC + "\n", encoding="utf-8")


def _exec_server(python_path: Path) -> None:
    os.execv(str(python_path), [str(python_path), *MODULE_ARGS])


if __name__ == "__main__":
    raise SystemExit(main())
