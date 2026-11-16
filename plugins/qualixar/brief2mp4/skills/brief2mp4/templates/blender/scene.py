"""brief2mp4 starter: a scripted Blender product turntable.

Run it headless (no Blender window needed):

    blender --background --factory-startup --python scene.py -- \
        --frames-dir frames --seconds 8 --fps 30 --samples 32

It writes PNG frames (frames/0001.png ...). Encode them with
scripts/finish.sh so the MP4 meets the delivery spec.

Everything is built from code: geometry, materials, lights, camera move and
title. Replace build_subject() with what the brief asks for; keep the rest.
"""

import argparse
import math
import os
import sys

import bpy


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frames-dir", default="frames")
    p.add_argument("--seconds", type=float, default=8.0)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--engine", default="EEVEE", choices=["EEVEE", "CYCLES"])
    p.add_argument("--title", default="TITLE")
    p.add_argument("--preview", action="store_true", help="render only 3 stills (start, middle, end)")
    return p.parse_args(argv)


def hex_rgba(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def material(name, color, roughness=0.4, metallic=0.0, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    # Find the shader node by type, never by its (localised) name.
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def set_engine(scene, wanted, samples):
    names = ["BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"] if wanted == "EEVEE" else ["CYCLES"]
    for name in names:
        try:
            scene.render.engine = name
            break
        except TypeError:
            continue
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            scene.cycles.device = "GPU"
        except Exception:
            scene.cycles.device = "CPU"
    else:
        scene.eevee.taa_render_samples = samples


def build_subject():
    """Placeholder product: a ceramic cup. Replace with the brief's object."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.55, depth=1.1, location=(0, 0, 0.55))
    cup = bpy.context.object
    bev = cup.modifiers.new("bevel", "BEVEL")
    bev.width = 0.04
    bev.segments = 4
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=0.28, minor_radius=0.06, location=(0.68, 0, 0.55),
                                     rotation=(math.radians(90), 0, 0))
    handle = bpy.context.object
    bpy.ops.object.shade_smooth()
    mat = material("ceramic", "#f4ece1", roughness=0.25)
    for ob in (cup, handle):
        ob.data.materials.append(mat)
    handle.parent = cup
    handle.matrix_parent_inverse = cup.matrix_world.inverted()  # keep its world position
    return cup


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.fps = args.fps
    frames = int(round(args.seconds * args.fps))
    scene.frame_start, scene.frame_end = 1, frames
    set_engine(scene, args.engine, args.samples)
    scene.render.image_settings.file_format = "PNG"
    frames_dir = os.path.abspath(args.frames_dir)
    scene.render.filepath = os.path.join(frames_dir, "")

    world = bpy.data.worlds.new("world")
    scene.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = hex_rgba("#2a2140")
    bg.inputs["Strength"].default_value = 0.4

    # Floor that fades into the background.
    bpy.ops.mesh.primitive_plane_add(size=400)
    bpy.context.object.data.materials.append(material("floor", "#2a2140", roughness=0.6))

    subject = build_subject()

    # Three-point light: key, rim, fill.
    def area(name, loc, energy, size, color="#ffffff"):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.size = size
        light.data.color = hex_rgba(color)[:3]
        direction = -light.location.normalized()
        light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return light

    area("key", (3, -3, 4), 600, 3)
    area("rim", (-3, 3, 3), 400, 2, "#ffb48a")
    area("fill", (-4, -2, 2), 120, 4)

    # Camera on a turntable: rotate an empty, the camera follows.
    bpy.ops.object.empty_add(location=(0, 0, 0.6))
    pivot = bpy.context.object
    bpy.ops.object.camera_add(location=(0, -6.5, 1.6))
    cam = bpy.context.object
    cam.parent = pivot
    cam.data.lens = 50
    track = cam.constraints.new("TRACK_TO")
    track.target = pivot
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    scene.camera = cam
    edit_prefs = bpy.context.preferences.edit
    edit_prefs.keyframe_new_interpolation_type = "LINEAR"  # constant turntable speed
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, math.radians(300))
    pivot.keyframe_insert("rotation_euler", frame=frames)

    # Title in 3D, scales up in the last 25% of the shot.
    bpy.ops.object.text_add(location=(0, 0, 1.55))
    title = bpy.context.object
    title.data.body = args.title
    title.data.align_x = "CENTER"
    title.data.size = 0.32
    title.data.extrude = 0.02
    title.data.materials.append(material("title", "#fff4e8", emission="#fff4e8", strength=1.5))
    title.parent = pivot  # always faces the camera
    title.location = (0, -0.6, 0.85)  # local to the pivot: above the subject, toward the camera
    title.rotation_euler = (math.radians(90), 0, 0)
    edit_prefs.keyframe_new_interpolation_type = "BEZIER"  # eased title
    start = int(frames * 0.75)
    title.scale = (0.001, 0.001, 0.001)
    title.keyframe_insert("scale", frame=start)
    title.scale = (1, 1, 1)
    title.keyframe_insert("scale", frame=min(frames, start + args.fps))

    if args.preview:
        for i, f in enumerate((1, frames // 2, frames)):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(frames_dir, f"preview_{i}.png")
            bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
    print(f"brief2mp4: rendered {frames} frames to {args.frames_dir}/")


if __name__ == "__main__":
    main()
