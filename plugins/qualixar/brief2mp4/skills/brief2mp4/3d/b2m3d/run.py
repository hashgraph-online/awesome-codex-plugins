"""Subprocess helpers: run node scripts and Blender with clear errors."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import paths


class B2M3DError(RuntimeError):
    """A step failed; the message says which tool and why."""


def run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 3600,
        env: dict[str, str] | None = None) -> str:
    merged = {**os.environ, **(env or {})}
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=merged)
    except FileNotFoundError as exc:
        raise B2M3DError(f"cannot run {cmd[0]}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise B2M3DError(f"{Path(cmd[0]).name} timed out after {timeout}s") from exc
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout)[-2000:]
        raise B2M3DError(f"{Path(cmd[0]).name} exited {proc.returncode}:\n{tail}")
    return proc.stdout


def sync_js() -> Path:
    """Copy the pack's .mjs helpers next to node_modules (only when they differ)."""
    if not paths.node_modules().is_dir():
        raise B2M3DError(f"node components are not installed in {paths.home()}. Run: "
                         f"{paths.PACK / 'install_3d.sh'} --components core")
    dest = paths.js_dir()
    dest.mkdir(parents=True, exist_ok=True)
    for src in (paths.PACK / "js").glob("*.mjs"):
        target = dest / src.name
        if not target.exists() or target.read_bytes() != src.read_bytes():
            shutil.copyfile(src, target)
    return dest


def node_script(script: str, args: list[str], timeout: int = 3600) -> str:
    node = paths.node()
    if not node:
        raise B2M3DError("node was not found on PATH (Node.js 22 or newer is required)")
    return run([node, str(sync_js() / script), *args], timeout=timeout)


def blender_script(script: Path, config: dict, timeout: int = 7200) -> str:
    exe = paths.blender()
    if not exe:
        raise B2M3DError("Blender was not found. Install it, or set B2M3D_BLENDER to its executable "
                         "(run `python -m b2m3d doctor` for the install command).")
    # The config goes through a file: JSON on a command line is mangled by some Windows shells.
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(config, fh)
        cfg = Path(fh.name)
    try:
        return run([exe, "-b", "--factory-startup", "-P", str(script), "--", str(cfg)], timeout=timeout)
    finally:
        cfg.unlink(missing_ok=True)


def last_json(stdout: str, marker: str) -> dict:
    """Scripts print '<marker> {json}' as their result line."""
    for line in reversed(stdout.splitlines()):
        if line.startswith(marker + " "):
            return json.loads(line[len(marker) + 1:])
    raise B2M3DError(f"no {marker} result line in output:\n{stdout[-1500:]}")
