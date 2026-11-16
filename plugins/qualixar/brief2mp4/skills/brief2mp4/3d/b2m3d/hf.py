"""b2m3d hf: turn a shot JSON into a self-contained, frame-seekable HyperFrames project.

The project vendors three.js, GSAP, fonts and every GLB, so a render never touches the
network, and every frame is a pure function of time (see templates/shot-runtime.js).
Titles are GSAP tweens on the same paused timeline.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import paths
from .hf_html import FONTS, render_html
from .run import B2M3DError

THREE_FILES = ["build/three.module.js", "build/three.core.js"]
THREE_ADDONS = ["loaders/GLTFLoader.js", "loaders/HDRLoader.js", "libs/meshopt_decoder.module.js",
                "environments/RoomEnvironment.js", "postprocessing", "shaders", "utils"]

SHOT_KEYS = {"name", "duration", "fps", "width", "height", "physics", "models", "camera", "ground",
             "lights", "tonemapping", "exposure", "envIntensity", "envRotation", "hdri", "bloom",
             "bounds", "background", "accent", "font", "titles"}
MODEL_KEYS = {"src", "position", "rotation", "scale", "track", "trackStart", "spin", "spinOffset",
              "float", "reveal", "explode"}
TITLE_KEYS = {"text", "kicker", "sub", "start", "duration", "size", "position"}


def _num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate(shot: dict, physics: dict | None) -> list[str]:
    """Raise ValueError on a shot that cannot render; return warnings (unknown keys)."""
    errors: list[str] = []
    if not _num(shot.get("duration")) or shot["duration"] <= 0:
        errors.append("'duration' must be a number of seconds above 0")
    for key in ("width", "height", "fps"):
        if not isinstance(shot.get(key), int) or shot[key] <= 0:
            errors.append(f"'{key}' must be a positive integer")
    models = shot.get("models")
    if not isinstance(models, list) or not models:
        errors.append("'models' must be a non-empty list of {src, ...}")
    for i, m in enumerate(models if isinstance(models, list) else []):
        if not isinstance(m, dict) or not isinstance(m.get("src"), str):
            errors.append(f"models[{i}] needs a 'src' path to a .glb")
        elif m.get("track") and (physics is None or m["track"] not in physics.get("tracks", {})):
            errors.append(f"models[{i}].track '{m['track']}' is not in the physics bake "
                          f"(set shot 'physics' to the track.json from `b2m3d physics`)")
    for i, t in enumerate(shot.get("titles", [])):
        if not isinstance(t, dict) or not t.get("text") or not _num(t.get("start")) or not _num(t.get("duration")):
            errors.append(f"titles[{i}] needs 'text', 'start' and 'duration'")
    if errors:
        raise ValueError("invalid shot JSON: " + "; ".join(errors))
    return _unknown_keys(shot)


def _unknown_keys(shot: dict) -> list[str]:
    warnings = [f"unknown shot key '{k}' (ignored)" for k in shot if k not in SHOT_KEYS]
    for i, m in enumerate(shot["models"]):
        warnings += [f"unknown key '{k}' in models[{i}] (ignored)" for k in m if k not in MODEL_KEYS]
    for i, t in enumerate(shot.get("titles", [])):
        warnings += [f"unknown key '{k}' in titles[{i}] (ignored)" for k in t if k not in TITLE_KEYS]
    return warnings


def _copy(src: Path, dst: Path) -> None:
    if not src.exists():
        raise B2M3DError(f"missing file {src}. Is the `core` component installed? "
                         f"Run: {paths.PACK / 'install_3d.sh'} --components core")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def vendor(out: Path) -> None:
    nm = paths.node_modules()
    three = nm / "three"
    for f in THREE_FILES:
        _copy(three / f, out / "vendor/three" / f)
    for f in THREE_ADDONS:
        _copy(three / "examples/jsm" / f, out / "vendor/three/addons" / f)
    for rel in FONTS.values():
        _copy(nm / rel, out / "fonts" / Path(rel).name)
    _copy(nm / "gsap/dist/gsap.min.js", out / "vendor/gsap.min.js")
    _copy(paths.TEMPLATES / "shot-runtime.js", out / "b2m3d-runtime.js")


def _asset_name(src: Path, taken: dict[str, Path]) -> str:
    """Keep the file name; add a counter when two different files share it."""
    name, n = src.name, 1
    while name in taken and taken[name] != src:
        n += 1
        name = f"{src.stem}-{n}{src.suffix}"
    taken[name] = src
    return name


def _assets(shot: dict, base: Path, out: Path) -> dict:
    taken: dict[str, Path] = {}
    models = []
    for m in shot["models"]:
        src = (base / m["src"]).resolve()
        if not src.is_file():
            raise FileNotFoundError(f"model not found: {src}")
        name = _asset_name(src, taken)
        _copy(src, out / "assets" / name)
        models.append({**m, "src": f"assets/{name}"})
    shot = {**shot, "models": models}
    if shot.get("hdri"):
        src = (base / shot["hdri"]).resolve()
        name = _asset_name(src, taken)
        _copy(src, out / "assets" / name)
        shot = {**shot, "hdri": f"assets/{name}"}
    return shot


def scaffold(shot_path: Path, out: Path) -> dict:
    shot = {"width": 1920, "height": 1080, "fps": 30, **json.loads(shot_path.read_text(encoding="utf-8"))}
    base = shot_path.parent
    physics = json.loads((base / shot["physics"]).read_text(encoding="utf-8")) if shot.get("physics") else None
    warnings = validate(shot, physics)
    out.mkdir(parents=True, exist_ok=True)
    vendor(out)
    shot = _assets(shot, base, out)
    (out / "index.html").write_text(render_html(shot, physics), encoding="utf-8")
    return {"out": str(out), "models": len(shot["models"]), "duration": shot["duration"],
            "physics_bodies": len(physics["tracks"]) if physics else 0, "warnings": warnings}
