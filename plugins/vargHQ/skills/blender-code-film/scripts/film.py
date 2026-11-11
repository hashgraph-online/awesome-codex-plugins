"""A film built and rendered by Blender from this one Python file: no downloaded models, textures or HDRIs.

    blender -b --factory-startup -P film.py -- --stills --draft --out render/stills   # one still per shot, 1/4 size
    blender -b --factory-startup -P film.py -- --draft --out render/draft             # every frame, 1/4 size
    blender -b --factory-startup -P film.py -- --out render/final                     # every frame, full size
    blender -b --factory-startup -P film.py -- --shot reveal --out render/final       # one shot only

Everything that changes the picture lives in SHOTS, LOOK and the build_* functions. The seed fixes every
random choice, so a re-render gives the same frames. Starter scene: a lantern orb drifts through a low-poly
forest valley at dusk, in three shots (wide, follow, reveal). Replace the world and the shots with yours.
"""

import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", default="render/final")
ap.add_argument("--draft", action="store_true", help="25%% size, few samples")
ap.add_argument("--stills", action="store_true", help="render the key frame of every shot only")
ap.add_argument("--shot", default=None, help="render one shot by name")
ap.add_argument("--percent", type=int, default=None, help="resolution percentage (overrides --draft's 25)")
ap.add_argument("--engine", default="eevee", choices=["eevee", "cycles"])
ap.add_argument("--no-haze", action="store_true", help="skip the haze volume (Cycles renders much faster)")
ap.add_argument("--samples", type=int, default=None, help="Cycles samples (default 32 draft, 256 final)")
ap.add_argument("--seed", type=int, default=7)
args = ap.parse_args(argv)

FPS = 24
W, H = 1920, 1080

# Look: one palette, one key light, one fill. Colours are linear RGB.
LOOK = {
    "sky": (0.030, 0.060, 0.090),
    "haze_density": 0.006,
    "ground": (0.10, 0.12, 0.08),
    "trunk": (0.10, 0.06, 0.04),
    "leaves": [(0.05, 0.16, 0.11), (0.03, 0.12, 0.10), (0.09, 0.17, 0.08)],
    "orb": (1.0, 0.33, 0.08),  # warm orange, close to #ff5315
    "key": (1.0, 0.45, 0.20),
    "fill": (0.20, 0.55, 0.65),  # soft teal
}

# Shots: frames are inclusive, positions in metres. The camera eases from cam[0] to cam[1] and looks at
# aim[0] → aim[1]; `key` is the frame rendered by --stills (the moment the shot is about).
SHOTS = [
    {"name": "wide", "start": 1, "end": 72, "lens": 24, "cam": [(-16, -30, 7.5), (-11, -26, 6.0)],
     "aim": [(0, -12, 1.5), (0, -9, 1.6)], "key": 48},
    {"name": "follow", "start": 73, "end": 144, "lens": 40, "cam": [(2.6, -10, 2.2), (2.0, 2, 2.4)],
     "aim": "orb", "key": 110},
    {"name": "reveal", "start": 145, "end": 216, "lens": 32, "cam": [(0, 8, 1.2), (0, 14, 9.0)],
     "aim": [(0, 20, 2.0), (0, 30, 3.0)], "key": 200},
]
END = SHOTS[-1]["end"]

rng = random.Random(args.seed)


# ── helpers ──────────────────────────────────────────────────────────────────

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = FPS
    s.frame_start, s.frame_end = 1, END
    return s


def material(name, color, rough=0.7, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rough
    if emit:
        key = "Emission Color" if "Emission Color" in p.inputs else "Emission"
        p.inputs[key].default_value = (*emit, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def ground_z(x, y):
    """Height of the ground at (x, y): fractal hills, flattened into a valley along the path (x≈0)."""
    hills = noise.fractal(Vector((x * 0.045, y * 0.045, 0.0)), 0.6, 2.0, 4) * 3.2
    valley = min(1.0, (abs(x) / 9.0) ** 2)
    return hills * valley + 0.15 * noise.noise(Vector((x * 0.4, y * 0.4, 1.0)))


def orb_at(f):
    """Where the orb is on frame f: drifts up the valley with a slow sway and bob."""
    t = (f - 1) / (END - 1)
    y = -14 + 40 * t
    x = 1.2 * math.sin(t * math.tau * 1.3)
    z = ground_z(x, y) + 1.5 + 0.25 * math.sin(t * math.tau * 4)
    return Vector((x, y, z))


# ── the world ────────────────────────────────────────────────────────────────

def build_ground():
    size, n = 120.0, 160
    verts, faces = [], []
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = -size / 2 + size * i / n, -size / 2 + 20 + size * j / n
            verts.append((x, y, ground_z(x, y)))
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            faces.append((a, a + 1, a + n + 2, a + n + 1))
    me = bpy.data.meshes.new("ground")
    me.from_pydata(verts, [], faces)
    me.materials.append(material("ground", LOOK["ground"], rough=0.95))
    link(bpy.data.objects.new("ground", me))


def build_trees(count=420):
    trunk_m = material("trunk", LOOK["trunk"], rough=0.9)
    leaf_ms = [material(f"leaves{i}", c, rough=0.8) for i, c in enumerate(LOOK["leaves"])]
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.12, depth=1.6, location=(0, 0, 0.8))
    trunk = bpy.context.object
    trunk.data.materials.append(trunk_m)
    protos = []
    for k, m in enumerate(leaf_ms):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=1.1, depth=2.8, location=(0, 0, 2.6))
        crown = bpy.context.object
        crown.data.materials.append(m)
        protos.append(crown)
    # every camera position, sampled along its move: no tree may stand closer than 5 m to one
    cam_path = [Vector(a).lerp(Vector(b), k / 12) for sh in SHOTS for a, b in [sh["cam"]] for k in range(13)]
    placed = 0
    while placed < count:
        x, y = rng.uniform(-50, 50), rng.uniform(-35, 70)
        if abs(x) < 3.2 + rng.uniform(0, 2):  # keep the path clear
            continue
        if any((Vector((x, y)) - p.xy).length < 5.0 for p in cam_path):  # and the lens
            continue
        s = rng.uniform(0.7, 1.9)
        z = ground_z(x, y) - 0.1
        t = bpy.data.objects.new(f"trunk{placed}", trunk.data)
        t.location, t.scale = (x, y, z + 0.8 * s), (s, s, s)
        link(t)
        c = bpy.data.objects.new(f"crown{placed}", protos[placed % len(protos)].data)
        c.location, c.scale = (x, y, z + 2.6 * s), (s, s, s * rng.uniform(0.9, 1.3))
        c.rotation_euler.z = rng.uniform(0, math.tau)
        link(c)
        placed += 1
    for o in (trunk, *protos):  # the prototypes at the origin; their meshes live on in the copies
        bpy.data.objects.remove(o)


def build_orb():
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.32)
    orb = bpy.context.object
    orb.name = "orb"
    orb.data.materials.append(material("orb", LOOK["orb"], emit=LOOK["orb"], strength=40))
    orb.visible_shadow = False  # the lamp sits inside the orb: a shadow-casting orb would block all of it
    bpy.ops.object.shade_smooth()
    lamp = bpy.data.objects.new("orb_light", bpy.data.lights.new("orb_light", "POINT"))
    lamp.data.energy, lamp.data.color, lamp.data.shadow_soft_size = 900, LOOK["orb"], 0.3
    lamp.parent = orb
    link(lamp)
    for f in range(1, END + 1, 4):
        orb.location = orb_at(f)
        orb.keyframe_insert("location", frame=f)
    # fireflies: tiny static sparks along the valley
    spark = material("spark", LOOK["orb"], emit=LOOK["orb"], strength=25)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.035)
    proto = bpy.context.object.data
    proto.materials.append(spark)
    bpy.data.objects.remove(bpy.context.object)
    for i in range(160):
        x, y = rng.gauss(0, 4), rng.uniform(-20, 40)
        o = bpy.data.objects.new(f"spark{i}", proto)
        o.location = (x, y, ground_z(x, y) + rng.uniform(0.4, 3.5))
        o.visible_shadow = False
        link(o)
    return orb


def build_light_and_sky():
    s = bpy.context.scene
    w = bpy.data.worlds.new("world")
    s.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (*LOOK["sky"], 1)
    key = bpy.data.objects.new("key", bpy.data.lights.new("key", "SUN"))
    key.data.energy, key.data.color, key.data.angle = 4.0, LOOK["key"], math.radians(3)
    key.rotation_euler = (math.radians(58), 0, math.radians(195))  # low (32° up), from far behind the set: a rim
    link(key)
    fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "SUN"))
    fill.data.energy, fill.data.color = 0.6, LOOK["fill"]
    fill.rotation_euler = (math.radians(50), 0, math.radians(20))
    link(fill)


def build_haze():
    """Haze lives in a box around the set, never in the world: in Eevee a world volume is infinite and
    swallows the sun and the sky (the frame goes black at any density)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 15, 18))
    box = bpy.context.object
    box.name, box.scale = "haze", (180, 180, 40)
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    mn = m.node_tree.nodes
    mn.remove(mn["Principled BSDF"])
    vol = mn.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = LOOK["haze_density"]
    vol.inputs["Color"].default_value = (0.6, 0.75, 0.85, 1)
    vol.inputs["Anisotropy"].default_value = 0.5  # forward scatter: the haze glows toward the key light
    m.node_tree.links.new(vol.outputs["Volume"], mn["Material Output"].inputs["Volume"])
    box.data.materials.append(m)


# ── cameras: one per shot, bound to markers ──────────────────────────────────

def ease_keys(obj, path, a, b, f0, f1):
    setattr(obj, path, Vector(a))
    obj.keyframe_insert(path, frame=f0)
    setattr(obj, path, Vector(b))
    obj.keyframe_insert(path, frame=f1)  # Bezier keys with auto-clamped handles: ease in and out


def build_cameras(orb):
    s = bpy.context.scene
    for shot in SHOTS:
        cam = bpy.data.objects.new(f"cam_{shot['name']}", bpy.data.cameras.new(shot["name"]))
        cam.data.lens = shot["lens"]
        cam.data.clip_end = 400
        link(cam)
        if shot["aim"] == "orb":
            target = orb
        else:
            target = link(bpy.data.objects.new(f"aim_{shot['name']}", None))
            ease_keys(target, "location", shot["aim"][0], shot["aim"][1], shot["start"], shot["end"])
        ease_keys(cam, "location", shot["cam"][0], shot["cam"][1], shot["start"], shot["end"])
        c = cam.constraints.new("TRACK_TO")
        c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = target
        cam.data.dof.aperture_fstop = 2.8 if shot["aim"] == "orb" else 5.6
        m = s.timeline_markers.new(shot["name"], frame=shot["start"])
        m.camera = cam
        if shot is SHOTS[0]:
            s.camera = cam


# ── render ───────────────────────────────────────────────────────────────────

def setup_render():
    s = bpy.context.scene
    r = s.render
    engines = [e.identifier for e in r.bl_rna.properties["engine"].enum_items]
    if args.engine == "cycles":
        r.engine = "CYCLES"
        s.cycles.samples = args.samples or (32 if args.draft else 256)
        s.cycles.use_denoising = True
        # --factory-startup leaves Cycles on the CPU: switch on the GPU backend this machine has
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = backend
            except TypeError:
                continue
            prefs.get_devices()
            if any(d.type == backend for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == backend
                s.cycles.device = "GPU"
                break
    else:
        r.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        s.eevee.taa_render_samples = 16 if args.draft else 96
        # volumetric_end: haze stops at 100 m by default and the far sky shows a clean band
        for attr, val in (("use_raytracing", True), ("volumetric_tile_size", "4"), ("use_volumetric_shadows", True), ("volumetric_end", 260.0)):
            if hasattr(s.eevee, attr):
                try:
                    setattr(s.eevee, attr, val)
                except Exception:
                    pass
    r.resolution_x, r.resolution_y = W, H
    r.resolution_percentage = args.percent or (25 if args.draft else 100)
    r.use_motion_blur = not args.stills
    r.image_settings.file_format = "PNG"
    try:
        s.view_settings.view_transform = "AgX"
        s.view_settings.look = "AgX - Punchy"
    except Exception:
        pass


def render():
    s = bpy.context.scene
    out = Path(args.out).absolute()
    out.mkdir(parents=True, exist_ok=True)
    shots = [sh for sh in SHOTS if not args.shot or sh["name"] == args.shot]
    if args.stills:
        for sh in shots:
            s.frame_set(sh["key"])
            s.render.filepath = str(out / f"{sh['name']}_{sh['key']:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    s.render.filepath = str(out / "frame_")
    for sh in shots:
        s.frame_start, s.frame_end = sh["start"], sh["end"]
        bpy.ops.render.render(animation=True)
    s.frame_start, s.frame_end = 1, END


if __name__ == "__main__":
    reset()
    build_light_and_sky()
    if not args.no_haze:
        build_haze()
    build_ground()
    build_trees()
    orb = build_orb()
    build_cameras(orb)
    setup_render()
    Path(args.out).absolute().mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args.out).absolute() / "film.blend"))
    render()
    print(f"done: {args.out}")
