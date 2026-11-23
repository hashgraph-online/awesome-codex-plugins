"""b2m_common: helpers shared by the brief2mp4 Blender motion recipes.

Every recipe has the same shape and works in two places:

  headless   blender -b --factory-startup -P b2m_<name>.py -- --out frames --frames 96
  live       import b2m_<name>; b2m_<name>.build({...})     (inside a running Blender; keeps the open scene)

A recipe exposes DEFAULTS (every knob), build(params, clear=False) which makes the scene and returns a state dict
(only the headless main() passes clear=True, which empties the file first), and
measure(state) which returns plain numbers that prove the motion did what it should. main() parses, builds, measures,
renders if --out is given, and prints one line: B2M3D_RECIPE {json}. Rules kept here so the recipes stay short:
colours go linear, nodes are found by type, engine names are tried in turn, and curves are read through fcurves()
because Blender 5 moved them into slotted actions. --look studio and --orbit are the shared look and camera move.
"""
from __future__ import annotations

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b2m_math import (COMMON, TAU, _bool, frame_list, hex_rgba, merged, mix_hex, parse_args,  # noqa: E402,F401
                      smoothstep)

MARKER = "B2M3D_RECIPE"


def material(name: str, color: str, roughness: float = 0.5, metallic: float = 0.0,
             emission: str | None = None, strength: float = 0.0, coat: float = 0.0, sheen: float = 0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")   # by type, never by name
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Coat Weight"].default_value, bsdf.inputs["Sheen Weight"].default_value = coat, sheen   # lacquer, cloth glow
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def paint(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def begin(name: str, clear: bool) -> bpy.types.Collection:
    """clear=True (headless main() only): an empty file. clear=False (the default, live): keep the user's scene and only
    replace the collection this recipe made last time, and the data it left behind, so running it twice does not pile
    up objects, meshes, materials or actions."""
    if clear:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    old = bpy.data.collections.get(f"b2m_{name}")
    if old is not None:
        made = _made_by(old)
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
        purge_orphans(made)
    coll = bpy.data.collections.new(f"b2m_{name}")
    scene.collection.children.link(coll)
    return coll


def _made_by(coll) -> list:
    """The data the recipe's objects used: meshes, curves, lights, cameras, materials and the actions keyed on them."""
    made: list = []
    for obj in coll.all_objects:
        owners = [obj, obj.data, getattr(obj.data, "shape_keys", None)]
        owners += [m for s in obj.material_slots for m in (s.material, getattr(s.material, "node_tree", None)) if m is not None]
        made += [o for o in owners[1:] if o is not None and not isinstance(o, bpy.types.ShaderNodeTree | bpy.types.Key)]
        made += [o.animation_data.action for o in owners if o is not None and getattr(o, "animation_data", None)
                 and o.animation_data.action is not None]
    return list(dict.fromkeys(made))


KINDS = (("meshes", "Mesh"), ("curves", "Curve"), ("materials", "Material"), ("actions", "Action"), ("lights", "Light"),
         ("cameras", "Camera"))


def purge_orphans(made: list) -> int:
    """Remove the data the recipe's old objects used once nothing else uses it; data still in use elsewhere stays."""
    removed, pending = 0, list(made)
    for _ in range(3):                    # a mesh frees its material, a material its action: a few passes
        for idb in list(pending):
            kind = next((k for k, t in KINDS if isinstance(idb, getattr(bpy.types, t))), None)
            if kind and idb.users == 0:
                getattr(bpy.data, kind).remove(idb)
                pending.remove(idb)
                removed += 1
    return removed


def keeps_selection(build):
    """Decorator for build(): the recipe selects objects to add rigid bodies and primitives; give the person's selection
    and active object back afterwards (objects the recipe removed are simply gone from it)."""
    def wrapped(params=None, clear=False):
        layer = bpy.context.view_layer
        names = {o.name for o in layer.objects if o.select_get()}
        active = layer.objects.active.name if layer.objects.active else None
        state = build(params, clear)
        layer = bpy.context.view_layer
        for o in layer.objects:
            o.select_set(o.name in names and not clear)
        layer.objects.active = layer.objects.get(active) if active and not clear else None
        return state
    wrapped.__doc__, wrapped.__name__ = build.__doc__, build.__name__
    return wrapped


def add(coll: bpy.types.Collection, obj: bpy.types.Object) -> bpy.types.Object:
    coll.objects.link(obj)
    return obj


def empty(coll, name: str, loc=(0, 0, 0), parent=None, display="PLAIN_AXES", size=0.1) -> bpy.types.Object:
    e = bpy.data.objects.new(name, None)
    e.empty_display_type, e.empty_display_size = display, size
    add(coll, e)
    if parent is not None:
        e.parent = parent          # parent first, then the local location: no parent-inverse jump
    e.location = loc
    return e


def mesh_object(coll, name: str, verts, faces, loc=(0, 0, 0)) -> bpy.types.Object:
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    obj.location = loc
    return add(coll, obj)


def set_engine(scene, wanted: str, samples: int) -> None:
    names = {"EEVEE": ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"], "CYCLES": ["CYCLES"], "WORKBENCH": ["BLENDER_WORKBENCH"]}[wanted.upper()]
    for name in names:
        try:
            scene.render.engine = name
            break
        except TypeError:
            continue
    if scene.render.engine == "CYCLES":
        scene.cycles.samples, scene.cycles.use_denoising = samples, True
    elif scene.render.engine != "BLENDER_WORKBENCH":
        scene.eevee.taa_render_samples = samples
    for view in ("Khronos PBR Neutral", "Standard"):      # look rule 1: a neutral view keeps palette colours
        try:
            scene.view_settings.view_transform = view
            break
        except TypeError:
            continue


def stage(scene, coll, p: dict, target=(0, 0, 0.6), cam=(4.5, -7.0, 3.0), lens=50.0, floor=True,
          floor_size=60.0) -> dict:
    """Floor, world, lights and a camera aimed at `target`: the recipe from references/blender.md. The camera sits on
    an orbit pivot at the aim (see `orbit`); lights ride the aim, so a recipe that moves the aim keeps its lighting."""
    aim = empty(coll, "b2m_aim", target)
    if not p["stage"]:
        return {"aim": aim, "floor": None, "camera": scene.camera}
    if p["look"] not in ("plain", "studio"):
        raise ValueError("look must be plain or studio")
    studio, r = p["look"] == "studio", scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = int(p["width"]), int(p["height"]), 100, int(p["fps"])
    set_engine(scene, p["engine"], int(p["samples"]))
    if studio and r.engine.startswith("BLENDER_EEVEE"):
        ee = scene.eevee                                         # reflections, bounce light, cleaner soft shadows
        ee.use_raytracing, ee.use_fast_gi, ee.fast_gi_distance, ee.shadow_ray_count, ee.shadow_step_count = True, True, 2.0, 2, 12
        scene.view_settings.exposure = -0.35                     # the pale backdrop otherwise sits near white
    world = bpy.data.worlds.new("b2m_world")
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value, bg.inputs["Strength"].default_value = hex_rgba(p["bg"]), 0.4 if studio else 0.6
    scene.world = world
    objs = {"aim": aim}
    if floor:
        half = floor_size / 2
        fl = _cyclorama(coll, target[0]) if studio else mesh_object(
            coll, "b2m_floor", [(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [(0, 1, 2, 3)])
        paint(fl, material("b2m_floor", p["floor"], roughness=0.8 if studio else 0.65))
        objs["floor"] = fl
    lights = (("key", (-4.5, -3.5, 6.0), 800, 3.0, "#fff6ec"), ("fill", (6.0, -5.5, 2.5), 110, 6.0, "#ffffff"),
              ("rim", (2.5, 5.0, 5.0), 800, 2.0, "#fffaf4"), ("wash", (0.0, 0.5, 7.5), 340, 16.0, "#ffffff")) if studio else \
             (("key", (-3.5, -4.5, 5.5), 600, 3.0, "#ffffff"), ("rim", (4.0, 4.5, 3.5), 400, 2.0, p["accent"]),
              ("fill", (5.0, -4.0, 2.0), 120, 5.0, "#ffffff"))
    for name, loc, watts, size, color in lights:
        data = bpy.data.lights.new("b2m_" + name, "AREA")
        data.energy, data.size, data.color = watts, size, hex_rgba(color)[:3]
        lamp = add(coll, bpy.data.objects.new("b2m_" + name, data))
        lamp.parent, lamp.location = aim, loc
        track(lamp, empty(coll, "b2m_wall_spot", (0, 5.5, 3.5), parent=aim) if name == "wash" else aim)
    pivot = empty(coll, "b2m_orbit", (0, 0, 0), parent=aim)          # turns about Z to orbit the camera
    cdata = bpy.data.cameras.new("b2m_cam")
    cdata.lens = lens
    camera = add(coll, bpy.data.objects.new("b2m_cam", cdata))
    camera.parent, camera.location = pivot, tuple(a - b for a, b in zip(cam, target))
    track(camera, aim)
    scene.camera = objs["camera"] = camera
    return objs


def _cyclorama(coll, x0=0.0, width=60.0, front=-30.0, back=6.0, radius=4.0, height=16.0, steps=16):
    """A seamless studio backdrop: the floor curves up into a back wall, so there is no horizon line anywhere."""
    prof = [(front, 0.0)] + [(back - radius + radius * math.sin(a), radius - radius * math.cos(a))
                             for a in (math.pi / 2 * i / steps for i in range(steps + 1))] + [(back, height)]
    verts = [(x0 + sx * width / 2, y, z) for y, z in prof for sx in (-1, 1)]
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(prof) - 1)]
    fl = mesh_object(coll, "b2m_floor", verts, faces)
    for poly in fl.data.polygons:
        poly.use_smooth = True
    return fl


def capsule(coll, name: str, r_top: float, r_bottom: float, length: float, mat, parent=None, loc=(0, 0, 0),
            squash: float = 1.0) -> bpy.types.Object:
    """A rounded rod hanging from its origin: the top end at z=0, the bottom end at z=-length, tapering from r_top
    to r_bottom; squash < 1 flattens it front to back. Limbs, links and pins are made of these."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=17, radius=1.0)
    obj = bpy.context.object
    bpy.context.collection.objects.unlink(obj)
    add(coll, obj).name = name
    for v in obj.data.vertices:
        x, y, z = v.co
        r, zc = (r_top, -r_top) if z >= 0 else (r_bottom, -length + r_bottom)
        v.co = (x * r * squash, y * r, zc + z * r)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.parent, obj.location = parent, loc
    paint(obj, mat)
    return obj


def track(obj, target) -> None:
    con = obj.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"


def caption(scene, coll, text: str, p: dict, camera) -> bpy.types.Object | None:
    """One short line of flat 3D text parented to the camera, bottom left inside the safe margin, after a short bar
    in the subject colour. With caption_fade it fades in while rising 10 px, holds, and fades out."""
    if not text or camera is None:
        return None
    cu = bpy.data.curves.new("b2m_caption", "FONT")
    cu.body, cu.size, cu.align_x, cu.align_y = text, 0.5, "LEFT", "BOTTOM"
    cu.font = bpy.data.fonts.load("<builtin>")          # a text curve made from code has no font until one is loaded
    ob = add(coll, bpy.data.objects.new("b2m_caption", cu))
    ratio = scene.render.resolution_x / scene.render.resolution_y
    depth = 1.0                                       # metres in front of the lens: close, so nothing in the set can hide it
    half_h = depth * (camera.data.sensor_width / 2 / ratio) / camera.data.lens   # half the view height at that depth
    half_w = half_h * ratio
    px = 2 * half_h / scene.render.resolution_y         # metres per pixel at that depth
    cu.size = size = float(p["caption_px"]) * px
    bar_w, x0, y0 = 0.14 * size, -half_w + 100 * px, -half_h + 70 * px
    bar = mesh_object(coll, "b2m_caption_bar", [(0, 0, 0), (bar_w, 0, 0), (bar_w, 0.72 * size, 0), (0, 0.72 * size, 0)], [(0, 1, 2, 3)])
    ink = material("b2m_caption", p["ink"], roughness=0.9, emission=p["ink"], strength=1.2)
    lead = material("b2m_caption_bar", p["subject"], roughness=0.9, emission=p["subject"], strength=1.0)
    for o, x, mat in ((ob, x0 + bar_w + 0.32 * size, ink), (bar, x0, lead)):
        o.parent, o.location, o.visible_shadow = camera, (x, y0, -depth), False
        paint(o, mat)
    fade = int(p["caption_fade"])
    span = frame_list(p["caption_frames"], scene.frame_start, scene.frame_end)
    for mat in (ink, lead) if fade > 0 else ():
        mat.surface_render_method = "BLENDED"
        alpha = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Alpha"]
        for frame, value in ((span[0] - 1, 0.0), (span[0], 0.0), (span[0] + fade, 1.0), (span[-1] - fade, 1.0), (span[-1], 0.0)):
            alpha.default_value = value
            alpha.keyframe_insert("default_value", frame=frame)
    for o in (ob, bar) if fade > 0 else ():
        for frame, dy in ((span[0], -10 * px), (span[0] + fade, 0.0)):
            o.location.y = y0 + dy
            o.keyframe_insert("location", index=1, frame=frame)
    return ob


def animate_orbit(scene, p: dict) -> None:
    """Turn the camera's pivot at `orbit` degrees a second, centred on the middle of the shot, extrapolated past both
    ends, so frames rendered beyond the scene range keep the same speed."""
    pivot, rate = bpy.data.objects.get("b2m_orbit"), float(p["orbit"])
    if pivot is None or rate == 0.0:
        return
    mid = (scene.frame_start + scene.frame_end) / 2
    for frame in (scene.frame_start, scene.frame_end):
        pivot.rotation_euler[2] = math.radians(rate * (frame - mid) / scene.render.fps)
        pivot.keyframe_insert("rotation_euler", index=2, frame=frame)
    for fc in fcurves(pivot):
        fc.extrapolation = "LINEAR"
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def fcurves(idb) -> list:
    """Every F-curve of an ID, on Blender 4.x and on 5.x (slotted actions)."""
    ad = getattr(idb, "animation_data", None)
    act = ad.action if ad else None
    if act is None:
        return []
    if hasattr(act, "fcurves"):
        return list(act.fcurves)
    out: list = []
    for layer in act.layers:
        for strip in layer.strips:
            bag = strip.channelbag(ad.action_slot) if ad.action_slot else None
            if bag:
                out += list(bag.fcurves)
    return out


def set_interpolation(ids, mode: str) -> None:
    for idb in ids:
        for fc in fcurves(idb):
            for kp in fc.keyframe_points:
                kp.interpolation = mode


def world_pos(obj, local=(0, 0, 0)) -> Vector:
    """World position of a point of an object, read from the evaluated copy (physics writes there)."""
    dg = bpy.context.evaluated_depsgraph_get()
    return obj.evaluated_get(dg).matrix_world @ Vector(local)


def render_frames(scene, out_dir: str, frames: list[int], fmt: str) -> list[str]:
    """Frames in ascending order, so simulations step forward. Names are 0001.png, 0002.png, ... (finish.sh reads them)."""
    os.makedirs(out_dir, exist_ok=True)
    scene.render.image_settings.file_format = fmt
    ext = {"PNG": "png", "BMP": "bmp", "JPEG": "jpg"}.get(fmt, fmt.lower())
    done = []
    for f in sorted(frames):
        scene.frame_set(f)
        path = os.path.join(out_dir, f"{f:04d}.{ext}")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        done.append(path)
    return done


def warm_up(scene, upto: int) -> None:
    """Step 1..upto once so cloth and rigid-body caches fill before any frame is rendered out of order."""
    for f in range(scene.frame_start, upto + 1):
        scene.frame_set(f)


def emit(result: dict, json_path: str = "") -> dict:
    result = {"blender": bpy.app.version_string, **result}
    if json_path:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    print(f"{MARKER} {json.dumps(result)}")
    return result


def verdict(result: dict, problems: list[str]) -> dict:
    """Add ok and warnings to a measurement, and print each warning, so a number out of range is never silent."""
    for line in problems:
        print(f"WARNING b2m: {line}", file=sys.stderr)
    return {**result, "ok": not problems, "warnings": problems}


def run_main(module_name: str, defaults: dict, description: str, build, measure) -> dict:
    """The standard main(): parse, build, measure, render, print."""
    p = parse_args(defaults, description)
    state = build(p, clear=True)                    # headless: start from an empty file
    scene = bpy.context.scene
    animate_orbit(scene, p)
    result = {"recipe": module_name, "frame_start": scene.frame_start, "frame_end": scene.frame_end,
              "fps": scene.render.fps, **measure(state)}
    if p["out"]:
        frames = frame_list(p["render_frames"], scene.frame_start, scene.frame_end)
        warm_up(scene, max(frames))
        result["rendered"] = render_frames(scene, p["out"], frames, p["fmt"])
    return emit(result, p["json"])

