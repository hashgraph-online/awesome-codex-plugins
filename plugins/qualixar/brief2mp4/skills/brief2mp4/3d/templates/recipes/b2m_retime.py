"""b2m_retime: change when the beats happen without redrawing the animation.

Timeline markers name the beats ("start", "hit", "end"). retime_between_markers() moves them to new frames and
stretches or squeezes every keyframe (and its handles) between two markers by the same ratio, so each segment keeps
its shape and the pose at each marker is unchanged. A marker the targets do not name stays where it is, so
`--targets hit=40` moves the hit and squeezes the segments either side of it. Keys on the objects, their data and
shape keys, their materials (and node trees) and, when no object list is given, the world are all remapped. Put a
key on every marker you retime between. Handles become free handles (their positions are kept, not recomputed),
which is what keeps the shape exact. Target frames are whole frames, like the markers.

The demo animates a ball that arcs down onto the floor at "hit" and leaves toward "end".

  blender -b --factory-startup -P b2m_retime.py -- --marks start=1,hit=25,end=49 --targets start=1,hit=40,end=60
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402
from b2m_math import make_mapper, parse_marks  # noqa: E402,F401  (pure functions, tested without Blender)

DEFAULTS = {
    "marks": "start=1,hit=25,end=49",   # the beats as the animation was authored: name=frame
    "targets": "start=1,hit=40,end=60",  # where each beat should land; empty means leave the timing alone
    "tail": 0,                           # frames to keep after the last marker
}


def animated_ids(objs, world=None) -> list:
    """Where keyframes can live: the objects, their data, shape keys and materials (with their node trees), and the
    world with its node tree when one is given."""
    ids: list = []

    def with_tree(idb):
        tree = getattr(idb, "node_tree", None)
        return [idb] + ([tree] if tree is not None else [])

    for o in objs:
        data = getattr(o, "data", None)
        ids += [o] + ([data] if data is not None else []) + ([data.shape_keys] if getattr(data, "shape_keys", None) else [])
        for slot in getattr(o, "material_slots", ()):
            if slot.material is not None and slot.material not in ids:
                ids += with_tree(slot.material)
    if world is not None:
        ids += with_tree(world)
    return ids


def retime_between_markers(scene, new_frames: dict, objs=None, tail: int = 0) -> dict:
    """Move the named markers to new_frames and remap the keys of objs (default: every object in the scene, and the
    world). Markers not named in new_frames stay put; frame_end follows the old end through the same map."""
    old = {m.name: float(m.frame) for m in scene.timeline_markers}
    mapper = make_mapper(old, new_frames)
    moved, last = 0, float("-inf")
    every = animated_ids(objs if objs is not None else list(scene.objects), scene.world if objs is None else None)
    for idb in every:
        for fc in c.fcurves(idb):
            for kp in fc.keyframe_points:      # freeze the handles where they are, so Blender cannot recompute them
                kp.handle_left_type = kp.handle_right_type = "FREE"
            for kp in fc.keyframe_points:      # the key and both handles go through the same map
                kp.co.x, kp.handle_left.x, kp.handle_right.x = mapper(kp.co.x), mapper(kp.handle_left.x), mapper(kp.handle_right.x)
                last = max(last, kp.co.x)
                moved += 1
            fc.update()
    for m in scene.timeline_markers:
        m.frame = int(round(mapper(old[m.name])))
    scene.frame_end = max(int(round(mapper(scene.frame_end))), int(round(last)) if moved else scene.frame_start) + int(tail)
    return {"map": mapper, "moved_keys": moved, "old": old}


def _ball(coll, p):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(-3, 0, 1.6))
    ball = bpy.context.object
    bpy.context.collection.objects.unlink(ball)
    c.add(coll, ball)
    bpy.ops.object.shade_smooth()
    c.paint(ball, c.material("b2m_ball", p["subject"], roughness=0.3))
    return ball


def _animate(ball, marks: dict):
    t0, t1, t2 = (marks[k] for k in ("start", "hit", "end"))
    path = [(t0, (-3.0, 0, 1.6), (1, 1, 1)), ((t0 + t1) / 2, (-1.4, 0, 0.95), (1, 1, 1)),
            (t1, (0.0, 0, 0.33), (1.25, 1.25, 0.7)), ((t1 + t2) / 2, (1.5, 0, 1.1), (0.95, 0.95, 1.1)),
            (t2, (3.0, 0, 1.6), (1, 1, 1))]
    for frame, loc, scl in path:
        ball.location, ball.scale = loc, scl
        ball.keyframe_insert("location", frame=frame)
        ball.keyframe_insert("scale", frame=frame)


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    coll = c.begin("retime", clear)
    scene = bpy.context.scene
    marks = parse_marks(p["marks"])
    scene.frame_start, scene.frame_end = int(min(marks.values())), int(max(marks.values()))
    objs = c.stage(scene, coll, p, target=(0, 0, 0.8), cam=(0, -8.5, 2.6), lens=42)
    ball = _ball(coll, p)
    _animate(ball, marks)
    for name, frame in marks.items():
        scene.timeline_markers.new(name, frame=int(frame))
    before = _sample(ball, [marks["start"] + (marks["end"] - marks["start"]) * k / 12 for k in range(13)])
    state = {"p": p, "ball": ball, "scene": scene, "marks": marks, "probe": before, "probes": sorted(before),
             "marker_pose": _sample(ball, list(marks.values()))}
    targets = parse_marks(p["targets"])
    if targets:
        info = retime_between_markers(scene, targets, [ball], int(p["tail"]))
        state["map"], state["moved_keys"] = info["map"], info["moved_keys"]
    c.caption(scene, coll, p["caption"], p, objs["camera"])     # after the retime: its frames are the final timeline's
    return state


def _sample(ball, frames):
    """{frame: (x, y, z, scale z)} straight from the curves, so fractional frames are fine."""
    curves = {(fc.data_path, fc.array_index): fc for fc in c.fcurves(ball)}
    return {f: tuple(curves[k].evaluate(f) for k in (("location", 0), ("location", 1), ("location", 2), ("scale", 2))) for f in frames}


def measure(state):
    scene, ball = state["scene"], state["ball"]
    result = {"markers_after": {m.name: m.frame for m in scene.timeline_markers}, "probes": len(state["probes"])}
    if "map" in state:
        mapper = state["map"]
        after = _sample(ball, [mapper(f) for f in state["probes"]])
        err = 0.0
        for f in state["probes"]:
            err = max(err, max(abs(a - b) for a, b in zip(state["probe"][f], after[mapper(f)])))
        # the pose at each marker's frame now against the authored pose at its old frame: catches markers left behind
        now = _sample(ball, [float(m.frame) for m in scene.timeline_markers])
        authored = state["marker_pose"]
        marker_err = max((max(abs(a - b) for a, b in zip(authored[state["marks"][m.name]], now[float(m.frame)]))
                          for m in scene.timeline_markers if m.name in state["marks"]), default=0.0)
        result.update({"shape_error": err, "marker_pose_error": marker_err, "moved_keys": state["moved_keys"]})
    return result


if __name__ == "__main__":
    c.run_main("retime", DEFAULTS, __doc__.split("\n")[0], build, measure)
