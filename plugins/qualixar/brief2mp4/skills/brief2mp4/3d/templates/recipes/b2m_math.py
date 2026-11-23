"""b2m_math: the plain arithmetic of the Blender motion recipes, with no bpy import.

Everything here is pure Python, so it is tested on every operating system in CI without Blender
(tests/test_recipe_math.py). b2m_common re-exports these names, so recipes keep calling c.frame_list and the rest.
Option parsing lives here too: the shared options (COMMON), merged() and parse_args().
"""
from __future__ import annotations

import argparse
import math
import sys

TAU = 2 * math.pi

COMMON = {
    "out": "",            # folder for frames; empty means measure only, render nothing
    "render_frames": "",  # "1,48,10-12"; empty means every frame
    "fmt": "PNG",         # PNG, or BMP for tiny test frames
    "fps": 30, "width": 1920, "height": 1080, "samples": 16, "engine": "EEVEE",
    "bg": "#15171c", "floor": "#23262e", "subject": "#f2a65a", "accent": "#e4572e", "ink": "#f4efe6",
    "stage": True,        # False: add only the subject; keep the scene's own floor, lights, camera and world (live use)
    "caption": "",        # one short line shown low in the frame, as 3D text
    "caption_px": 54,     # caption height at the frame's own resolution (54 px at 1080p), with a short bar before it
    "caption_frames": "", # "a-b": the caption shows from frame a to frame b; empty means the whole shot
    "caption_fade": 0,    # frames the caption takes to fade in (and rise 10 px) and to fade out; 0 means always on
    "look": "plain",      # plain: floor plane, three lights (fast). studio: seamless backdrop, soft lights, ray tracing
    "orbit": 0.0,         # degrees per second the camera turns round its aim, at constant speed; 0 holds it still
    "json": "",           # also write the result to this file
}


def _bool(text: str) -> bool:
    return str(text).lower() in ("1", "true", "yes", "on")


def parse_args(defaults: dict, description: str, argv: list[str] | None = None, common: dict | None = None) -> dict:
    """Every key of defaults becomes --key-with-dashes, typed like its default. Arguments follow `--`."""
    if argv is None:
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description=description)
    for key, default in {**(COMMON if common is None else common), **defaults}.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(default, bool):          # --naive, or --naive 0
            ap.add_argument(flag, dest=key, type=_bool, nargs="?", const=True, default=default)
        else:
            ap.add_argument(flag, dest=key, type=type(default), default=default)
    return vars(ap.parse_args(argv))


def merged(defaults: dict, params: dict | None) -> dict:
    """defaults plus overrides; an unknown key is an error, so a typo cannot silently do nothing."""
    base = {**COMMON, **defaults}
    extra = set(params or {}) - set(base)
    if extra:
        raise KeyError(f"unknown parameter(s): {', '.join(sorted(extra))}")
    return {**base, **(params or {})}


def frame_list(spec: str, start: int, end: int) -> list[int]:
    """'1,48,10-12' -> [1, 10, 11, 12, 48]; empty -> start..end."""
    if not spec.strip():
        return list(range(start, end + 1))
    frames: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part[1:]:
            a, b = part.split("-", 1)
            frames.update(range(int(a), int(b) + 1))
        elif part:
            frames.add(int(part))
    return sorted(frames)


def _hex6(h: str) -> str:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)            # #fff is #ffffff
    if len(h) != 6:
        raise ValueError(f"colour {h!r}: use #rgb or #rrggbb")
    return h


def hex_rgba(h: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    """A hex colour as linear RGBA (Blender's colour inputs are linear)."""
    h = _hex6(h)
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, alpha)


def mix_hex(a: str, b: str, t: float) -> str:
    """A colour t of the way from hex a to hex b, mixed in sRGB."""
    pa, pb = (tuple(int(_hex6(h)[i:i + 2], 16) for i in (0, 2, 4)) for h in (a, b))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def smoothstep(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# retime -------------------------------------------------------------------------------------------------------------

def parse_marks(text: str) -> dict:
    marks = {}
    for part in text.split(","):
        if part.strip():
            name, frame = part.split("=")
            marks[name.strip()] = float(frame)
    return marks


def make_mapper(old: dict, new: dict):
    """A function old frame -> new frame: straight lines between markers, a plain shift outside them.
    A marker that new does not name stays where it is, so a partial retime moves only the beats it names."""
    missing = set(new) - set(old)
    if missing:
        raise KeyError(f"no marker named {', '.join(sorted(missing))}; markers are {', '.join(sorted(old))}")
    fractional = sorted(n for n, f in new.items() if float(f) != int(f))
    if fractional:
        raise ValueError("target frames must be whole frames (timeline markers sit on whole frames): "
                         + ", ".join(f"{n}={new[n]:g}" for n in fractional))
    full = {**old, **new}                      # unnamed markers map to themselves
    names = sorted(full, key=lambda n: old[n])
    xs, ys = [old[n] for n in names], [full[n] for n in names]
    if any(b <= a for a, b in zip(ys, ys[1:])):
        raise ValueError("target frames must increase in the same order as the markers: "
                         + ", ".join(f"{n}={full[n]:g}" for n in names))

    def mapper(f: float) -> float:
        if f <= xs[0]:
            return ys[0] + (f - xs[0])
        if f >= xs[-1]:
            return ys[-1] + (f - xs[-1])
        for x0, x1, y0, y1 in zip(xs, xs[1:], ys, ys[1:]):
            if x0 <= f <= x1:
                return y0 + (f - x0) * (y1 - y0) / (x1 - x0)
        return f
    return mapper


# walk ---------------------------------------------------------------------------------------------------------------

def solve_leg(hip, target, l1, l2):
    """Two-bone IK in the vertical plane. Returns (thigh angle, shin angle, overshoot, reached target); angles are
    measured from straight down, positive toward +x. The knee always bends forward."""
    dx, dz = target[0] - hip[0], target[1] - hip[1]
    dist = math.hypot(dx, dz)
    reach = min(dist, l1 + l2 - 1e-4)
    overshoot = max(0.0, dist - (l1 + l2))
    fx, fz = hip[0] + dx * reach / dist, hip[1] + dz * reach / dist
    alpha = math.atan2(dx, -dz)
    beta = math.acos(max(-1.0, min(1.0, (l1 * l1 + reach * reach - l2 * l2) / (2 * l1 * reach))))
    t1 = alpha + beta
    kx, kz = hip[0] + l1 * math.sin(t1), hip[1] - l1 * math.cos(t1)
    t2 = math.atan2(fx - kx, -(fz - kz))
    return t1, t2, overshoot, (fx, fz)


def foot_target(k, offset, p, hip_x):
    """World (x, z) of one foot at frame index k. offset shifts the leg half a cycle for the other foot."""
    cycle, duty, speed, fps = float(p["cycle_frames"]), float(p["duty"]), float(p["speed"]), float(p["fps"])
    pos = k / cycle + offset
    n = math.floor(pos)
    phase = pos - n
    stride = speed * cycle / fps
    mid_k = (n + duty / 2 - offset) * cycle           # frame at the middle of this stance, when the hip is over the foot
    plant = hip_x(mid_k)
    if p["naive"]:
        half = stride * duty / 2
        return hip_x(k) + half * math.cos(TAU * phase), float(p["step_height"]) * max(0.0, math.sin(TAU * phase))
    if phase < duty:
        return plant, 0.0
    s = (phase - duty) / (1 - duty)
    return plant + stride * smoothstep(s), float(p["step_height"]) * math.sin(math.pi * s)


# fold ---------------------------------------------------------------------------------------------------------------

CREASE_SHARE = 0.06   # a crease spreads at most this share of the stack's width on each side


def crease_radius(radius: float, width: float) -> float:
    """The crease radius for a fold of a stack `width` wide: the asked radius, capped at CREASE_SHARE of the width,
    so later folds of a shrinking stack keep a crease in proportion (a 0.12 m crease would swallow a 0.25 m stack)."""
    return min(radius, CREASE_SHARE * width)


def fold_positions(cur, crease_x, axis_z, frac, radius):
    """Positions after turning the part to the right of crease_x by frac * 180 degrees about a line at (crease_x, axis_z).
    The turn angle ramps smoothly over the crease zone, so the crease is rounded. No point ends lower than it started:
    the start of the zone, left of the crease line, would otherwise dip through the layers under it and the floor."""
    out, zone = [], set()
    for i, (x, y, z) in enumerate(cur):
        t = (x - (crease_x - radius)) / (2 * radius)
        a = math.pi * frac * smoothstep(t)
        if 0.0 < t < 1.0:
            zone.add(i)
        dx, dz = x - crease_x, z - axis_z
        out.append((crease_x + dx * math.cos(a) - dz * math.sin(a), y, max(z, axis_z + dx * math.sin(a) + dz * math.cos(a))))
    return out, zone
