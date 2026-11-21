#!/usr/bin/env python3
"""Render staging.json with headless Blender. The same file renders in three.js (stage_three.html).

Run it with pip's bpy (uv run --python 3.13 --with bpy==5.2.3 python stage_blender.py ...) or a Blender install
(blender -b -P stage_blender.py -- ...). Arguments:

  stage_blender.py staging.json still SHOT[:lt] [workbench|eevee|cycles] out.png [WxH]
  stage_blender.py staging.json film  all|s01,s02 [workbench|eevee|cycles] out_dir [WxH]
  Add --blend scene.blend after the size to also save the file for an artist.

Film mode writes numbered PNGs. Encode them:
  ffmpeg -framerate 24 -i out_dir/f%04d.png -pix_fmt yuv420p -crf 18 previz.mp4
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
BLEND = None
if "--blend" in argv:
    i = argv.index("--blend")
    BLEND = argv[i + 1]
    del argv[i:i + 2]
SCENE_FILE, MODE, WHICH, ENGINE, OUT = argv[:5]
S = json.load(open(SCENE_FILE))
W, H = (int(x) for x in argv[5].split("x")) if len(argv) > 5 else (S["frame"]["w"], S["frame"]["h"])
FPS = S["frame"]["fps"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
_mats = {}


def smooth(x):
    return x * x * (3 - 2 * x)


def rgb(spec):
    if isinstance(spec, (int, float)):
        return (spec, spec, spec)
    return tuple(spec)


def mat(spec, rough=.85, unlit=False):
    c = rgb(spec)
    key = (c, rough, unlit)
    if key not in _mats:
        m = bpy.data.materials.new("m%d" % len(_mats))
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0, 0, 0, 1) if unlit else (*c, 1)
        b.inputs["Roughness"].default_value = rough
        if unlit:                      # a window or a lamp: glows at its own colour, whatever the light does
            b.inputs["Emission Color"].default_value = (*c, 1)
            b.inputs["Emission Strength"].default_value = 1.0
        m.diffuse_color = (*c, 1)      # what Workbench shows in material colour mode
        _mats[key] = m
    return _mats[key]


def shade():
    bpy.ops.object.shade_smooth()


def new_box(name, center, size, color, rot_z=0, rough=.85, unlit=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center, rotation=(0, 0, math.radians(rot_z)))
    o = bpy.context.object
    o.name, o.scale = name, size
    o.data.materials.append(mat(color, rough, unlit))
    if unlit:
        o.visible_shadow = False
    return o


def new_ball(name, r, color, stretch=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=14, radius=r)
    o = bpy.context.object
    o.name, o.scale = name, stretch
    o.data.materials.append(mat(color))
    shade()
    return o


class Limb:
    """A cylinder and two caps between two moving points."""

    def __init__(self, name, r, color):
        bpy.ops.mesh.primitive_cylinder_add(vertices=18, radius=r, depth=1)
        self.body = bpy.context.object
        self.body.name = name
        self.body.rotation_mode = "QUATERNION"
        self.body.data.materials.append(mat(color))
        shade()
        self.a, self.b = new_ball(name + "_a", r * .985, color), new_ball(name + "_b", r * .985, color)

    def place(self, p, q, frame=None):
        p, q = Vector(p), Vector(q)
        d = q - p
        self.body.location = (p + q) / 2
        self.body.rotation_quaternion = (d if d.length > 1e-4 else Vector((0, 0, 1))).to_track_quat("Z", "Y")
        self.body.scale = (1, 1, max(d.length, 1e-3))
        self.a.location, self.b.location = p, q
        if frame is not None:
            for o, path in ((self.body, "location"), (self.body, "rotation_quaternion"), (self.body, "scale"),
                            (self.a, "location"), (self.b, "location")):
                o.keyframe_insert(path, frame=frame)


def lerp_keys(keys, t, field):
    if t <= keys[0]["t"]:
        return keys[0][field]
    for a, b in zip(keys, keys[1:]):
        if t <= b["t"]:
            x = smooth((t - a["t"]) / max(b["t"] - a["t"], 1e-6))
            return [u + (v - u) * x for u, v in zip(a[field], b[field])]
    return keys[-1][field]


def lerp_scalar(keys, t, field, default=0.0):
    ks = [dict(t=k["t"], v=[k.get(field, default)]) for k in keys]
    return lerp_keys(ks, t, "v")[0]


JOINT_LIMBS = [("neck", "hip", "torso"), ("shL", "elL", "upper"), ("elL", "haL", "fore"), ("shR", "elR", "upper"),
               ("elR", "haR", "fore"), ("hip", "knL", "thigh"), ("knL", "ftL", "shin"), ("hip", "knR", "thigh"),
               ("knR", "ftR", "shin")]
RADII = dict(torso=.115, upper=.055, fore=.042, thigh=.08, shin=.058)


class Figure:
    def __init__(self, f):
        self.f = f
        self.style = f.get("style", "capsule")
        self.keys = f["keys"]
        self.static = len(self.keys) < 2
        if self.style == "joints":
            top, legs = f.get("top", .3), f.get("legs", .2)
            colors = dict(torso=top, upper=top, fore=f.get("fore", S.get("skin", .6)), thigh=legs, shin=legs)
            self.limbs = [(a, b, Limb(f"{f['name']}_{part}{i}", RADII[part], colors[part]))
                          for i, (a, b, part) in enumerate(JOINT_LIMBS)]
            self.head = new_ball(f["name"] + "_head", f.get("head_r", .115), f.get("head", S.get("skin", .6)), (.9, .95, 1.12))
        else:
            h = f.get("height", 1.75)
            color = f.get("color", .5)
            self.height = h
            self.body = Limb(f["name"] + "_body", h * .115, color)
            self.head = new_ball(f["name"] + "_head", h * .085, f.get("head", S.get("skin", .6)))
            self.nose = new_box(f["name"] + "_nose", (0, 0, 0), (h * .05, h * .06, h * .035), f.get("head", S.get("skin", .6)))
            self.nose.rotation_mode = "XYZ"

    def apply(self, t, frame=None):
        if self.style == "joints":
            j = {n: lerp_keys([dict(t=k["t"], v=k["joints"][n]) for k in self.keys], t, "v")
                 for n in self.keys[0]["joints"]}
            for a, b, limb in self.limbs:
                limb.place(j[a], j[b], frame)
            self.head.location = j["head"]
            if frame is not None:
                self.head.keyframe_insert("location", frame=frame)
            return
        p = lerp_keys(self.keys, t, "pos")
        hd = math.radians(lerp_scalar(self.keys, t, "heading"))
        h = self.height
        f = Vector((math.sin(hd), math.cos(hd), 0))
        b = Vector(p)
        r = h * .115
        self.body.place(b + Vector((0, 0, r)), b + Vector((0, 0, h * .72)), frame)
        hc = b + Vector((0, 0, h * .9))
        self.head.location = hc
        self.nose.location = hc + f * h * .085
        self.nose.rotation_euler = (0, 0, -hd)
        if frame is not None:
            self.head.keyframe_insert("location", frame=frame)
            self.nose.keyframe_insert("location", frame=frame)
            self.nose.keyframe_insert("rotation_euler", frame=frame)


class MovingBox:
    def __init__(self, b):
        self.b = b
        self.static = "keys" not in b
        self.o = new_box(b["name"], b["center"], b["size"], b.get("color", b.get("grey", .5)), b.get("rot_z", 0),
                         b.get("rough", .85), b.get("unlit", False))

    def apply(self, t, frame=None):
        if "keys" in self.b:
            self.o.location = lerp_keys(self.b["keys"], t, "center")
            if frame is not None:
                self.o.keyframe_insert("location", frame=frame)


boxes = [MovingBox(b) for b in S.get("boxes", [])]
figures = [Figure(f) for f in S.get("figures", [])]

for fl in S.get("flags", []):
    me = bpy.data.meshes.new(fl["name"])
    me.from_pydata([tuple(v) for v in fl["verts"]], [], [(0, 1, 2, 3)])
    me.update()
    o = bpy.data.objects.new(fl["name"], me)
    scene.collection.objects.link(o)
    o.visible_camera = False           # a flag casts shadow and the camera never sees it

world = bpy.data.worlds.new("w")
scene.world = world
world.use_nodes = True
fill = S.get("fill", .12)
world.node_tree.nodes["Background"].inputs[0].default_value = (fill, fill, fill, 1)
if S.get("key"):
    k = S["key"]
    bpy.ops.object.light_add(type="SPOT", location=k["pos"])
    key = bpy.context.object
    key.data.energy = k.get("power_blender", 3000)
    key.data.spot_size = math.radians(k.get("angle_deg", 60))
    key.data.spot_blend = k.get("blend", .05)
    key.data.shadow_soft_size = k.get("soft", .02)
    key.data.color = k.get("color", (1, 1, 1))
    key.rotation_mode = "QUATERNION"
    key.rotation_quaternion = (Vector(k["aim"]) - key.location).to_track_quat("-Z", "Y")

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.sensor_fit = "AUTO"           # the sensor spans the longer side: same as stage_three.html
cam.data.clip_start = .05
cam.rotation_mode = "QUATERNION"
scene.camera = cam


def ease(kind, x):
    x = max(0., min(1., x))
    return {"linear": x, "in": x * x, "out": 1 - (1 - x) ** 2, "hold": 0.}.get(kind, smooth(x))


def cam_at(shot, lt):
    if "keys" in shot:                 # a path with several keys, for instance from solve_camera.py
        K = shot["keys"]
        i = 0
        while i < len(K) - 2 and lt > K[i + 1]["t"]:
            i += 1
        p, q = K[i], K[min(i + 1, len(K) - 1)]
        x = ease(shot.get("ease", "linear"), (lt - p["t"]) / max(q["t"] - p["t"], 1e-6))
        L0, L1 = p.get("lens", shot.get("lens", 35)), q.get("lens", shot.get("lens", 35))
        return (Vector(p["pos"]).lerp(Vector(q["pos"]), x), Vector(p["look"]).lerp(Vector(q["look"]), x), L0 + (L1 - L0) * x,
                p.get("roll", 0) + (q.get("roll", 0) - p.get("roll", 0)) * x)
    x = ease(shot.get("ease", "smooth"), lt / max(shot["end"] - shot["start"], 1e-6))
    a, b = shot["from"], shot.get("to", shot["from"])
    look = Vector(a["look"]).lerp(Vector(b["look"]), x)
    if shot.get("path") == "arc":
        # orbit: angle and radius interpolate around the look point, so the camera never passes through the subject
        pa, pb = Vector(a["pos"]) - look, Vector(b["pos"]) - look
        aa, ab = math.atan2(pa.y, pa.x), math.atan2(pb.y, pb.x)
        d = (ab - aa + math.pi) % (2 * math.pi) - math.pi
        ra, rb = math.hypot(pa.x, pa.y), math.hypot(pb.x, pb.y)
        rad, ang = ra + (rb - ra) * x, aa + d * x
        pos = look + Vector((rad * math.cos(ang), rad * math.sin(ang), pa.z + (pb.z - pa.z) * x))
    else:
        pos = Vector(a["pos"]).lerp(Vector(b["pos"]), x)
    lens = a.get("lens", shot.get("lens", 35)) + (b.get("lens", shot.get("lens", 35)) - a.get("lens", shot.get("lens", 35))) * x
    return pos, look, lens, a.get("roll", 0) + (b.get("roll", 0) - a.get("roll", 0)) * x


def set_cam(shot, lt, frame=None):
    pos, look, lens, roll = cam_at(shot, lt)
    cam.data.sensor_width = shot.get("sensor", 36)
    cam.location = pos
    cam.rotation_quaternion = (look - pos).to_track_quat("-Z", "Y") @ Quaternion((0, 0, 1), math.radians(roll))
    cam.data.lens = lens
    # vp: where the vanishing point sits in the frame (a shifted lens, as in a painting). Default: the centre.
    u0, v0 = shot.get("vp", (.5, .5))
    cam.data.shift_x = (.5 - u0) * W / max(W, H)
    cam.data.shift_y = (v0 - .5) * H / max(W, H)
    if frame is not None:
        cam.data.keyframe_insert("shift_x", frame=frame)
        cam.data.keyframe_insert("shift_y", frame=frame)
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_quaternion", frame=frame)
        cam.data.keyframe_insert("lens", frame=frame)


r = scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps = W, H, 100, FPS
r.image_settings.file_format = "PNG"
if ENGINE == "workbench":
    r.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_shadows, sh.show_object_outline = "STUDIO", "MATERIAL", False, False
elif ENGINE == "eevee":
    r.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 16
else:
    r.engine = "CYCLES"
    scene.cycles.samples, scene.cycles.device, scene.cycles.use_denoising = 48, "CPU", True
scene.view_settings.view_transform = "AgX" if ENGINE != "workbench" and S.get("tone") != "none" else "Standard"

t0 = time.time()
if MODE == "still":
    sid, _, lt = WHICH.partition(":")
    shot = next(s for s in S["shots"] if s["id"] == sid) if sid else S["shots"][0]
    lt = float(lt or 0)
    set_cam(shot, lt)
    T = shot["start"] + lt
    for o in boxes + figures:
        o.apply(T)
    r.filepath = os.path.abspath(OUT)
    bpy.ops.render.render(write_still=True)
    print("RENDER_S", round(time.time() - t0, 2), ENGINE, f"{W}x{H}", "1 frame", r.filepath)
else:
    ids = None if WHICH == "all" else WHICH.split(",")
    shots = [s for s in S["shots"] if ids is None or s["id"] in ids]
    os.makedirs(OUT, exist_ok=True)
    frame = 0
    movers = [o for o in boxes + figures if not o.static]
    for o in boxes + figures:          # what doesn't move gets no keys, which keeps the file readable for an artist
        if o.static:
            o.apply(shots[0]["start"])
    for shot in shots:
        n = round((shot["end"] - shot["start"]) * FPS)
        scene.timeline_markers.new(shot["id"], frame=frame + 1)
        for i in range(n):
            frame += 1
            lt = i / FPS
            set_cam(shot, lt, frame)
            for o in movers:
                o.apply(shot["start"] + lt, frame)
    scene.frame_start, scene.frame_end = 1, frame
    r.filepath = os.path.join(os.path.abspath(OUT), "f")
    bpy.ops.render.render(animation=True)
    print("RENDER_S", round(time.time() - t0, 2), ENGINE, f"{W}x{H}", frame, "frames", OUT)
if BLEND:
    cam.name = cam.data.name = "CAM_film"
    names = {f["name"] for f in S.get("figures", [])}
    groups = {k: bpy.data.collections.new(k) for k in ("SET", "FIGURES", "CAMERA_LIGHT")}
    for g in groups.values():
        scene.collection.children.link(g)
    for o in list(scene.collection.objects):
        g = "CAMERA_LIGHT" if o.type in ("CAMERA", "LIGHT") else "FIGURES" if o.name.split("_")[0] in names else "SET"
        groups[g].objects.link(o)
        scene.collection.objects.unlink(o)
    r.filepath = "//frames/f"
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(BLEND))
    print("SAVED", BLEND)
