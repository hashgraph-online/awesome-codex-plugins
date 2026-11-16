"""Where the 3D pack lives, and where its installed components live.

PACK    the folder this package ships in (js helpers, templates, presets).
home()  the install folder with the venv and node_modules: ``B2M3D_HOME`` if set,
        else ``~/.brief2mp4/3d`` (Windows: ``%USERPROFILE%\\.brief2mp4\\3d``).
Everything is resolved at call time so a test or a user can point B2M3D_HOME elsewhere.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
PRESETS = PACK / "presets" / "materials"
TEMPLATES = PACK / "templates"
IS_WINDOWS = os.name == "nt"
IS_MAC = sys.platform == "darwin"


def home() -> Path:
    env = os.environ.get("B2M3D_HOME")
    return Path(env).expanduser() if env else Path.home() / ".brief2mp4" / "3d"


def venv_python() -> Path:
    sub = ("Scripts", "python.exe") if IS_WINDOWS else ("bin", "python")
    return home().joinpath("venv", *sub)


def node_modules() -> Path:
    return home() / "node_modules"


def js_dir() -> Path:
    """node resolves ESM imports from the script's own folder upward, so the helpers
    are copied next to node_modules (see run.sync_js)."""
    return home() / "js"


def node() -> str | None:
    return shutil.which("node")


def _version_key(path: str) -> tuple[int, ...]:
    """'.../Blender 4.2/blender.exe' -> (4, 2), so the newest install sorts first."""
    return tuple(int(n) for n in re.findall(r"\d+", Path(path).parent.name))


def _blender_candidates() -> list[str]:
    if IS_MAC:
        return ["/Applications/Blender.app/Contents/MacOS/Blender"]
    if IS_WINDOWS:
        roots = {os.environ.get("ProgramFiles", r"C:\Program Files"), r"C:\Program Files"}
        found: list[str] = []
        for root in sorted(roots):
            found += glob.glob(str(Path(root) / "Blender Foundation" / "Blender *" / "blender.exe"))
        return sorted(found, key=_version_key, reverse=True)
    return ["/usr/bin/blender", "/usr/local/bin/blender", "/snap/bin/blender", "/opt/blender/blender"]


def blender() -> str | None:
    """B2M3D_BLENDER, then PATH, then the usual install folders of this OS."""
    env = os.environ.get("B2M3D_BLENDER")
    if env and Path(env).exists():
        return env
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    return next((c for c in _blender_candidates() if Path(c).exists()), None)
