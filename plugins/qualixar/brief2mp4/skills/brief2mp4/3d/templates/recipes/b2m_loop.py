"""b2m_loop: a seamless loop. Frame 1 and the last frame are the same picture, and every curve is cyclic.

A faceted gem turns whole turns, bobs, and carries a ring that rocks. The period is loop_frames - 1 frames:
frame loop_frames repeats frame 1, so a video made from frames 1 .. loop_frames - 1 loops with no stutter.
Every curve gets a CYCLES modifier, which also makes Blender smooth the handles across the seam.

  blender -b --factory-startup -P b2m_loop.py -- --loop-frames 73 --turns 1 --out frames --render-frames 1-72
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402

DEFAULTS = {
    "loop_frames": 73,   # frame 1 .. loop_frames; the loop itself is loop_frames - 1 frames long
    "turns": 1,          # whole turns of the gem per loop (an integer, or the seam jumps)
    "bob": 0.12,         # metres up and down
    "bob_cycles": 1,     # whole bobs per loop
    "rock": 14.0,        # degrees the ring rocks each way
    "rock_cycles": 2,    # whole rocks per loop
    "glow": 0.6,         # emission strength of the ring; 0 for a plain lacquered ring
}


def _gem(coll, p):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.7, location=(0, 0, 1.0))
    gem = bpy.context.object
    bpy.context.collection.objects.unlink(gem)
    c.add(coll, gem)
    for poly in gem.data.polygons:
        poly.use_smooth = False
    c.paint(gem, c.material("b2m_gem", p["subject"], roughness=0.3, metallic=0.1, coat=0.7))
    bpy.ops.mesh.primitive_torus_add(major_radius=1.15, minor_radius=0.05, location=(0, 0, 0))
    ring = bpy.context.object
    bpy.context.collection.objects.unlink(ring)
    c.add(coll, ring)
    ring.parent = gem
    c.paint(ring, c.material("b2m_ring", p["accent"], roughness=0.3, metallic=0.3, coat=0.6, emission=p["accent"],
                             strength=float(p["glow"])))
    return gem, ring


def setattr_path(obj, path, index, value):
    vec = getattr(obj, path)
    vec[index] = value
    setattr(obj, path, vec)


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    if int(p["turns"]) != p["turns"]:
        raise ValueError("turns must be a whole number, or the last frame will not match the first")
    n, fps = int(p["loop_frames"]), float(p["fps"])
    if n < 4:
        raise ValueError("loop_frames must be at least 4: frame loop_frames repeats frame 1, so the loop is loop_frames - 1 long")
    sweep = float(p["orbit"]) * (n - 1) / fps                # degrees the camera turns over one loop
    if abs(sweep - 360 * round(sweep / 360)) > 1e-6:
        raise ValueError(f"orbit {p['orbit']:g} deg/s turns the camera {sweep:g} degrees per loop, so the seam jumps: use 0, "
                         f"or a whole turn per loop ({360 * fps / (n - 1):g} deg/s)")
    coll = c.begin("loop", clear)
    scene = bpy.context.scene
    n = int(p["loop_frames"])
    scene.frame_start, scene.frame_end = 1, n
    objs = c.stage(scene, coll, p, target=(0, 0, 1.0), cam=(0, -6.5, 2.2), lens=45)
    gem, ring = _gem(coll, p)
    period = n - 1
    turns, bob = int(p["turns"]), float(p["bob"])
    # Constant spin: two keys, linear, cyclic (offset mode). Bob and rock: a key every quarter cycle, smooth, cyclic.
    for frame, z in ((1, 0.0), (n, c.TAU * turns)):
        setattr_path(gem, "rotation_euler", 2, z)
        gem.keyframe_insert("rotation_euler", index=2, frame=frame)
    c.set_interpolation([gem], "LINEAR")
    for cycles, amp, path, idx, target, base in (
            (int(p["bob_cycles"]), bob, "location", 2, gem, 1.0),
            (int(p["rock_cycles"]), c.math.radians(p["rock"]), "rotation_euler", 0, ring, 0.0)):
        quarters = 4 * cycles
        for k in range(quarters + 1):
            frame = 1 + period * k / quarters
            setattr_path(target, path, idx, base + amp * c.math.sin(c.TAU * k / quarters))
            target.keyframe_insert(path, index=idx, frame=frame)
    for idb in (gem, ring):
        for fc in c.fcurves(idb):
            mod = fc.modifiers.new("CYCLES")     # first modifier: Blender then smooths the handles across the seam
            if idb is gem and fc.data_path == "rotation_euler":
                mod.mode_before = mod.mode_after = "REPEAT_OFFSET"   # a spin keeps counting up instead of wrapping to 0
            fc.update()
    c.caption(scene, coll, p["caption"], p, objs["camera"])
    return {"p": p, "gem": gem, "ring": ring, "scene": scene, "period": period}


def _slope_gap(fc, seam_frame):
    """Slope just before the seam against the slope just after it, relative to the curve's own range."""
    d = 0.05
    values = [kp.co.y for kp in fc.keyframe_points]
    span = (max(values) - min(values)) or 1.0
    before = (fc.evaluate(seam_frame) - fc.evaluate(seam_frame - d)) / d
    after = (fc.evaluate(seam_frame + d) - fc.evaluate(seam_frame)) / d
    return abs(after - before) / span


def _matrix(obj):
    m = obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
    return [m[i][j] for i in range(4) for j in range(4)]


def measure(state):
    scene, gem, ring = state["scene"], state["gem"], state["ring"]
    n = scene.frame_end
    curves = [fc for idb in (gem, ring) for fc in c.fcurves(idb)]
    cyclic = [fc for fc in curves if fc.modifiers and fc.modifiers[0].type == "CYCLES"]
    gap = 0.0
    for obj in (gem, ring) + ((scene.camera,) if scene.camera is not None else ()):   # the camera too: an orbit can break it
        scene.frame_set(1)
        first = _matrix(obj)
        scene.frame_set(n)
        gap = max(gap, max(abs(a - b) for a, b in zip(first, _matrix(obj))))
    slope = max((_slope_gap(fc, n) for fc in curves), default=0.0)
    return {"curves": len(curves), "cyclic_curves": len(cyclic), "period_frames": state["period"],
            "pose_gap": gap, "seam_slope_gap": slope}


if __name__ == "__main__":
    c.run_main("loop", DEFAULTS, __doc__.split("\n")[0], build, measure)
