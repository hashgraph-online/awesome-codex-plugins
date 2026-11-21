"""b2m3d blender: path-traced hero shots with the system Blender (Cycles on the best GPU, else CPU)."""
from __future__ import annotations

from pathlib import Path

from . import encode, paths
from .run import B2M3DError, blender_script, last_json

SCRIPT = paths.TEMPLATES / "blender_shot.py"


def render(src: Path, out_dir: Path, *, mp4: Path | None = None, **cfg) -> dict:
    if not src.is_file():
        raise FileNotFoundError(f"input not found: {src}")
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.png"):
        old.unlink()
    config = {"glb": str(src.resolve()), "out_dir": str(out_dir.resolve()), **cfg}
    result = last_json(blender_script(SCRIPT, config), "B2M3D_BLENDER")
    frames = sorted(out_dir.glob("frame_*.png"))
    if len(frames) != result["frames"] and not cfg.get("setup_only"):
        raise B2M3DError(f"expected {result['frames']} frames, found {len(frames)} in {out_dir}")
    if mp4 and frames:
        result["video"] = encode.frames_to_video(out_dir, mp4, fps=int(cfg.get("fps", 30)),
                                                 alpha=bool(cfg.get("transparent")))
    return result
