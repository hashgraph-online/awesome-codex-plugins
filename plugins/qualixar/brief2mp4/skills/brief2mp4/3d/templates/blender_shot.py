"""b2m3d Blender shot: GLB -> studio-lit, camera-orbited render on the best GPU available.

GPU order: Metal on macOS; OptiX, CUDA, HIP, oneAPI on Windows and Linux; CPU otherwise.
Run: blender -b --factory-startup -P blender_shot.py -- <config.json>
Config keys: glb, out_dir, frames, fps, width, height, engine (cycles|eevee),
samples, orbit_from, orbit_to, height_ratio, distance, lens, transparent,
look (studio|dramatic|soft), floor (dark|shadow|none), view (agx|neutral|filmic),
save_blend. Prints: B2M3D_BLENDER {json}
"""
import json
import math
import sys
import time
from pathlib import Path

import bpy
from mathutils import Vector

CFG = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())


GPU_BACKENDS = ["METAL"] if sys.platform == "darwin" else ["OPTIX", "CUDA", "HIP", "ONEAPI"]


def setup_gpu(scene):
    """Enable the first GPU backend this Blender build and machine offer; else CPU."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in GPU_BACKENDS:
        try:
            prefs.compute_device_type = kind
            prefs.refresh_devices()
        except (TypeError, AttributeError, RuntimeError):
            continue  # this build does not offer that backend
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            for d in prefs.devices:
                d.use = d.type == kind
            scene.cycles.device = "GPU"
            return [f"{kind}: {d.name}" for d in gpus]
    scene.cycles.device = "CPU"
    return []


def setup_render(scene):
    engine = CFG.get("engine", "cycles")
    # The EEVEE identifier changed between Blender versions, so try each name it has had.
    for name in (["CYCLES"] if engine == "cycles" else ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"]):
        try:
            scene.render.engine = name
            break
        except TypeError as exc:
            print("B2M3D_WARN engine:", exc)
    devices = setup_gpu(scene) if engine == "cycles" else []
    if engine == "cycles":
        c = scene.cycles
        c.samples = int(CFG.get("samples", 96))
        c.use_adaptive_sampling = True
        c.adaptive_threshold = 0.02
        c.use_denoising = True
        for attr, val in (("denoiser", "OPENIMAGEDENOISE"), ("denoising_use_gpu", True)):
            if hasattr(c, attr):
                try:
                    setattr(c, attr, val)
                except (TypeError, AttributeError):
                    pass
        c.max_bounces = 8
        c.glossy_bounces = 4
        c.transmission_bounces = 8
    r = scene.render
    r.resolution_x, r.resolution_y = int(CFG.get("width", 1920)), int(CFG.get("height", 1080))
    r.resolution_percentage = 100
    r.fps = int(CFG.get("fps", 30))
    r.film_transparent = bool(CFG.get("transparent", False))
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA" if r.film_transparent else "RGB"
    r.filepath = CFG["out_dir"].rstrip("/") + "/frame_"
    scene.frame_start, scene.frame_end = 1, int(CFG.get("frames", 120))
    want = {"agx": "AgX", "neutral": "Khronos PBR Neutral", "filmic": "Filmic"}[CFG.get("view", "agx")]
    try:  # dynamic enum: static enum_items is a placeholder, so just try it
        scene.view_settings.view_transform = want
    except TypeError as exc:
        print("B2M3D_WARN view transform:", exc)
    if CFG.get("look_preset"):
        try:
            scene.view_settings.look = CFG["look_preset"]  # e.g. "AgX - Punchy"
        except TypeError as exc:
            print("B2M3D_WARN look:", exc)
    return devices


def import_glb():
    before = set(bpy.data.objects)
    src = CFG["glb"]
    if src.lower().endswith((".usd", ".usda", ".usdc", ".usdz")):
        bpy.ops.wm.usd_import(filepath=src, set_frame_range=False)
    elif src.lower().endswith(".obj"):
        bpy.ops.wm.obj_import(filepath=src)
    else:
        bpy.ops.import_scene.gltf(filepath=src)
    objs = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in objs if o.type == "MESH"]
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return meshes, lo, hi


def area_light(name, loc, target, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.size, data.color = energy, size, color
    obj = bpy.data.objects.new(name, data)
    obj.location = loc
    bpy.context.scene.collection.objects.link(obj)
    direction = Vector(target) - Vector(loc)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


LOOKS = {  # (rel position, energy per m^2 of scene, size ratio, colour)
    "studio": [((2.2, -2.0, 2.6), 900, 1.4, (1, 1, 1)), ((-2.4, 2.2, 1.6), 700, 0.8, (0.75, 0.85, 1)),
               ((-2.6, -1.8, 0.8), 160, 1.8, (1, 0.93, 0.86))],
    "dramatic": [((1.6, -1.4, 3.0), 1300, 0.9, (1, 0.96, 0.9)), ((-2.2, 2.6, 1.2), 1100, 0.5, (0.55, 0.65, 1))],
    "soft": [((0, -1.5, 3.2), 700, 2.6, (1, 1, 1)), ((-2.5, 1.5, 1.5), 250, 2.0, (1, 1, 1))],
}


def lights(centre, size):
    for i, (rel, energy, sz, col) in enumerate(LOOKS[CFG.get("look", "dramatic")]):
        loc = centre + Vector(rel) * size
        area_light(f"b2m3d_light_{i}", loc, centre, energy * size * size, sz * size, col)


def world(scene):
    w = bpy.data.worlds.new("b2m3d_world")
    scene.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = CFG.get("world_color", (0.012, 0.014, 0.02, 1))
    bg.inputs[1].default_value = float(CFG.get("world_strength", 1.0))


def floor(lo, centre, size):
    mode = CFG.get("floor", "shadow" if CFG.get("transparent") else "dark")
    if mode == "none":
        return
    bpy.ops.mesh.primitive_plane_add(size=size * 60, location=(centre.x, centre.y, lo.z))
    plane = bpy.context.active_object
    if mode == "shadow":
        plane.is_shadow_catcher = True
        return
    mat = bpy.data.materials.new("b2m3d_floor")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = tuple(CFG.get("floor_color", (0.0025, 0.0028, 0.0035))) + (1,)
    bsdf.inputs["Roughness"].default_value = float(CFG.get("floor_roughness", 0.42))
    plane.data.materials.append(mat)


def camera(centre, size, frames):
    rig = bpy.data.objects.new("b2m3d_rig", None)
    rig.location = centre
    bpy.context.scene.collection.objects.link(rig)
    cam_data = bpy.data.cameras.new("b2m3d_cam")
    cam_data.lens = float(CFG.get("lens", 70))
    cam_data.dof.use_dof = bool(CFG.get("dof", False))  # small objects = macro DOF; opt in
    cam_data.dof.aperture_fstop = float(CFG.get("fstop", 4.0))
    cam = bpy.data.objects.new("b2m3d_cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    dist = size * float(CFG.get("distance", 2.6))
    cam.location = (0, -dist, dist * float(CFG.get("height_ratio", 0.62)))
    cam.parent = rig
    track = cam.constraints.new("TRACK_TO")
    track.target = rig
    track.track_axis, track.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    cam_data.dof.focus_object = rig
    bpy.context.scene.camera = cam
    a0, a1 = math.radians(CFG.get("orbit_from", -30)), math.radians(CFG.get("orbit_to", 30))
    rig.rotation_euler = (0, 0, a0)
    rig.keyframe_insert("rotation_euler", index=2, frame=1)
    rig.rotation_euler = (0, 0, a1)
    rig.keyframe_insert("rotation_euler", index=2, frame=frames)


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    devices = setup_render(scene)
    meshes, lo, hi = import_glb()
    scene.frame_start, scene.frame_end = 1, int(CFG.get("frames", 120))  # importers may reset it
    centre, size = (lo + hi) / 2, max((hi - lo).length, 1e-4)
    world(scene)
    lights(centre, size)
    floor(lo, centre, size)
    camera(centre, size, scene.frame_end)
    if CFG.get("save_blend"):
        bpy.ops.wm.save_as_mainfile(filepath=CFG["save_blend"])
    if not CFG.get("setup_only"):
        bpy.ops.render.render(animation=True)
    print("B2M3D_BLENDER " + json.dumps({
        "out_dir": CFG["out_dir"], "frames": scene.frame_end, "engine": scene.render.engine,
        "gpu": devices, "device": scene.cycles.device if scene.render.engine == "CYCLES" else "GPU/EEVEE", "meshes": len(meshes), "size_m": round(size, 4),
        "view": scene.view_settings.view_transform, "seconds": round(time.time() - t0, 1)}))


main()
