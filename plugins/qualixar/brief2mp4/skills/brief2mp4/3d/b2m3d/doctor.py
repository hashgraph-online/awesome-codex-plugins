"""b2m3d doctor: report each component as ok or missing, with the exact install command for this OS."""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path

from . import paths

NODE_PACKAGES = ["three", "gsap", "@gltf-transform/core", "@gltf-transform/extensions",
                 "@gltf-transform/functions", "meshoptimizer", "jolt-physics",
                 "@fontsource-variable/inter", "@fontsource-variable/space-grotesk"]
CORE_PY_MODULES = ["numpy", "scipy", "trimesh", "manifold3d"]
BLENDER_HINTS = {
    "darwin": "brew install --cask blender   (or download from https://www.blender.org/download/)",
    "win32": "winget install BlenderFoundation.Blender   (or download from https://www.blender.org/download/)",
    "linux": "install Blender 4.2 or newer from your package manager or https://www.blender.org/download/",
}


def install_command(components: str) -> str:
    if paths.IS_WINDOWS:
        return f'powershell -ExecutionPolicy Bypass -File "{paths.PACK / "install_3d.ps1"}" -Components {components}'
    return f'bash "{paths.PACK / "install_3d.sh"}" --components {components}'


def _probe(cmd: list[str], timeout: int = 60) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)[:160]
    text = (proc.stdout or proc.stderr).strip()
    return proc.returncode == 0, (text.splitlines() or [""])[0][:160]


def _node_versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for pkg in NODE_PACKAGES:
        pj = paths.node_modules() / pkg / "package.json"
        out[pkg] = json.loads(pj.read_text(encoding="utf-8"))["version"] if pj.exists() else None
    return out


def _py_modules(modules: list[str]) -> dict[str, bool]:
    py = paths.venv_python()
    if not py.exists():
        return {m: False for m in modules}
    code = "import importlib.util as u,json;print(json.dumps({m:u.find_spec(m) is not None for m in %r}))" % modules
    ok, text = _probe([str(py), "-c", code])
    return json.loads(text) if ok else {m: False for m in modules}


def check_core() -> dict:
    node = paths.node()
    node_pkgs = _node_versions()
    py_mods = _py_modules(CORE_PY_MODULES)
    missing = (([] if node else ["node on PATH (Node.js 22 or newer)"])
               + [f"npm:{k}" for k, v in node_pkgs.items() if v is None]
               + [f"python:{k}" for k, v in py_mods.items() if not v])
    return {"ok": not missing, "missing": missing, "node": node, "node_packages": node_pkgs,
            "python_modules": py_mods, "venv_python": str(paths.venv_python()),
            "install": install_command("core")}


def check_cad() -> dict:
    ok = _py_modules(["cadquery"])["cadquery"]
    return {"ok": ok, "missing": [] if ok else ["python:cadquery"], "optional": True,
            "install": install_command("cad"), "note": "large download (OpenCascade kernel)"}


def check_blender() -> dict:
    exe = paths.blender()
    version = _probe([exe, "--version"])[1] if exe else None
    hint = BLENDER_HINTS["darwin" if paths.IS_MAC else "win32" if paths.IS_WINDOWS else "linux"]
    return {"ok": bool(exe), "optional": True, "path": exe, "version": version,
            "missing": [] if exe else ["blender executable"], "install": hint,
            "note": "Blender is GPL software used as an external program; set B2M3D_BLENDER to point at a custom install"}


def check_tools() -> dict:
    ffmpeg = shutil.which("ffmpeg")
    listing = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout if ffmpeg else ""
    return {"node": paths.node(), "npx": shutil.which("npx"), "ffmpeg": ffmpeg,
            "hevc_videotoolbox": "hevc_videotoolbox" in listing, "libx264": "libx264" in listing,
            "prores_ks": "prores_ks" in listing}


def run_all() -> dict:
    components = {"core": check_core(), "cad": check_cad(), "blender": check_blender()}
    return {"ok": components["core"]["ok"], "home": str(paths.home()), "platform": platform.platform(),
            "components": components, "tools": check_tools()}
