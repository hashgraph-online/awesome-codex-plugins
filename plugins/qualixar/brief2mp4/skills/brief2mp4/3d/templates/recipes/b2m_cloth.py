"""b2m_cloth: a sheet of cloth drops onto an object and the floor, then settles.

The cloth is a grid with a Cloth modifier; the floor and the object get Collision modifiers. The simulation is
stepped frame by frame in order (a cloth cache must be filled forward), then frames can be rendered in any order.
The result reports where the cloth ended up, so a script can check it fell, stayed above the floor and draped.

  blender -b --factory-startup -P b2m_cloth.py -- --object sphere --frames 90 --out frames
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402

BASE_FPS = 30.0   # the frame rate the cloth settings were tuned at; other rates scale the speed multiplier

DEFAULTS = {
    "frames": 90,
    "object": "sphere",       # sphere, box or none
    "object_size": 0.55,      # sphere radius, or box half-width, in metres
    "cloth_size": 2.4,        # square sheet, side in metres
    "cloth_res": 32,          # quads per side; 20 is quick, 32 looks good
    "drop_height": 1.6,       # height of the sheet at frame 1
    "delay": 0,               # frames the sheet hangs still before it is released
    "mass": 0.3,              # kilograms for the sheet; lower is lighter and floatier
    "bend": 0.6,              # bending stiffness: low drapes into folds, high holds shape
    "quality": 6,             # solver steps per frame
    "self_collision": False,  # folds that rest on themselves; slower
    "smooth_levels": 0,       # Subdivision after the cloth, in the render only (the numbers are read from the sim)
    "thickness": 0.0,         # render-only thickness of the sheet in metres (a Solidify after the cloth); 0 = a bare surface
    "sheen": 0.0,             # the soft edge glow of fabric, 0-1
}


def _target(coll, p):
    """The object the cloth lands on, standing on the floor. Returns (object or None, top height)."""
    size = float(p["object_size"])
    if p["object"] == "none":
        return None, 0.0
    if p["object"] == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size, segments=48, ring_count=24, location=(0, 0, size))
    elif p["object"] == "box":
        bpy.ops.mesh.primitive_cube_add(size=2 * size, location=(0, 0, size))
    else:
        raise ValueError("object must be sphere, box or none")
    obj = bpy.context.object
    bpy.context.collection.objects.unlink(obj)
    c.add(coll, obj)
    bpy.ops.object.shade_smooth()
    c.paint(obj, c.material("b2m_pedestal", p["accent"], roughness=0.4))
    return obj, 2 * size


def _collider(obj):
    obj.modifiers.new("Collision", "COLLISION")
    obj.collision.thickness_outer = 0.015
    obj.collision.cloth_friction = 6.0


def _sheet(coll, p):
    n, side, z = int(p["cloth_res"]), float(p["cloth_size"]), float(p["drop_height"])
    verts = [(-side / 2 + side * i / n, -side / 2 + side * j / n, z) for j in range(n + 1) for i in range(n + 1)]
    faces = [(j * (n + 1) + i, j * (n + 1) + i + 1, (j + 1) * (n + 1) + i + 1, (j + 1) * (n + 1) + i) for j in range(n) for i in range(n)]
    sheet = c.mesh_object(coll, "b2m_cloth", verts, faces)
    for poly in sheet.data.polygons:
        poly.use_smooth = True
    c.paint(sheet, c.material("b2m_cloth", p["subject"], roughness=0.75, sheen=float(p["sheen"])))
    mod = sheet.modifiers.new("Cloth", "CLOTH")
    s, col = mod.settings, mod.collision_settings
    s.quality, s.mass, s.bending_stiffness = int(p["quality"]), float(p["mass"]), float(p["bend"])
    s.tension_stiffness = s.compression_stiffness = 15.0
    s.shear_stiffness, s.air_damping = 5.0, 1.0
    r = bpy.context.scene.render
    s.time_scale = BASE_FPS * r.fps_base / r.fps         # Blender steps cloth per frame: keep its speed in seconds at any fps
    s.quality = max(s.quality, math.ceil(int(p["quality"]) * s.time_scale))   # and the same solver steps per second
    col.use_collision, col.distance_min, col.collision_quality = True, 0.015, 4
    col.use_self_collision = bool(p["self_collision"])
    mod.point_cache.frame_start, mod.point_cache.frame_end = 1 + int(p["delay"]), int(p["frames"])
    if int(p["smooth_levels"]) > 0:
        sub = sheet.modifiers.new("Smooth", "SUBSURF")      # render only: toggling it while stepping would reset the cloth cache
        sub.show_viewport, sub.show_render, sub.render_levels = False, True, int(p["smooth_levels"])
    if float(p["thickness"]) > 0:
        solid = sheet.modifiers.new("Thickness", "SOLIDIFY")  # render only, like the smoothing: the measured sim is untouched
        solid.show_viewport, solid.thickness, solid.offset = False, float(p["thickness"]), 1.0
    return sheet


def _check(p) -> None:
    top = 2 * float(p["object_size"]) if p["object"] != "none" else 0.0
    if float(p["drop_height"]) <= top + 0.05:
        raise ValueError(f"drop_height {p['drop_height']} starts the sheet inside the {p['object']} (its top is at {top:g} m): "
                         "raise it above the object")
    if not 0 <= int(p["delay"]) < int(p["frames"]) - 1:
        raise ValueError(f"delay {p['delay']} must be under frames - 1 ({int(p['frames']) - 1}), or the sheet is never released")


@c.keeps_selection
def build(params=None, clear=False):
    p = c.merged(DEFAULTS, params)
    _check(p)
    coll = c.begin("cloth", clear)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, int(p["frames"])
    objs = c.stage(scene, coll, p, target=(0, 0, 0.45), cam=(0.0, -6.2, 2.4), lens=45)
    if objs["floor"] is not None:
        _collider(objs["floor"])
    pedestal, top = _target(coll, p)
    if pedestal is not None:
        _collider(pedestal)
    sheet = _sheet(coll, p)
    c.caption(scene, coll, p["caption"], p, objs["camera"])
    return {"p": p, "sheet": sheet, "scene": scene, "top": top, "n": int(p["cloth_res"]), "delay": int(p["delay"])}


def _positions(sheet):
    """Evaluated vertex positions of the simulated sheet (the smoothing modifier is render-only, so it is not in them)."""
    ev = sheet.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    pts = [tuple(v.co) for v in mesh.vertices]
    ev.to_mesh_clear()
    return pts


def measure(state):
    scene, sheet, n = state["scene"], state["sheet"], state["n"]
    end, mid = scene.frame_end, (n // 2) * (n + 1) + n // 2
    scene.frame_set(1)
    start = _positions(sheet)
    last_ten, before, centre_z = None, None, [start[mid][2]]
    for f in range(2, end + 1):
        scene.frame_set(f)
        pts = _positions(sheet)
        centre_z.append(pts[mid][2])
        if f == state["delay"] + 1 and state["delay"] > 0:
            before = pts                                  # the frame the sheet is released: still where it started
        if f == end - 10:
            last_ten = pts
    final = pts if end > 1 else start
    zs = [q[2] for q in final]
    nan = sum(1 for q in final if any(math.isnan(v) for v in q))
    centre = final[mid]
    edge = [final[j * (n + 1) + i][2] for j in range(n + 1) for i in range(n + 1) if i in (0, n) or j in (0, n)]
    moved = [math.dist(a, b) for a, b in zip(final, last_ten or final)]
    halfway = (centre_z[0] + centre[2]) / 2               # seconds from release until the centre has fallen half way
    fall = next((i for i, z in enumerate(centre_z) if z <= halfway), None)
    fps = scene.render.fps / scene.render.fps_base
    return {"start_mean_z": sum(q[2] for q in start) / len(start), "final_min_z": min(zs), "final_max_z": max(zs),
            "floor_z": 0.0, "object_top_z": state["top"], "centre_z": centre[2], "edge_mean_z": sum(edge) / len(edge),
            "motion_last_10_frames": sum(moved) / len(moved), "nan_vertices": nan, "vertices": len(final),
            "half_fall_s": (fall - state["delay"]) / fps if fall is not None else None,
            "moved_before_release": max((math.dist(a, b) for a, b in zip(start, before)), default=0.0) if before else 0.0}


if __name__ == "__main__":
    c.run_main("cloth", DEFAULTS, __doc__.split("\n")[0], build, measure)
