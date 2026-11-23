"""b2m_flip_bake: bake a FLIP Fluids liquid from the command line, then render frames. Optional add-on, you install it.

FLIP Fluids (a Blender add-on, GPL, sold on Superhive; a watermarked demo is free) simulates liquids. brief2mp4
does not include it. You build the liquid in Blender with the add-on (a Domain, a Fluid, Obstacles) and save the
.blend. This script opens that file, runs the add-on's own command-line bake operator, and renders PNG frames.
It does not set the liquid up for you: the add-on's scene setup is a UI workflow, and a bad guess here would
only look like a working simulation.

  blender -b scene.blend -P b2m_flip_bake.py -- --out frames --render-frames 1-90
  blender -b -P b2m_flip_bake.py -- --blend scene.blend --bake 0 --out frames     (render an existing cache)

Run it WITHOUT --factory-startup, so the add-on you enabled in Preferences is loaded. That also loads every other
add-on you enabled (an MCP add-on that starts a server, for one), and if "Auto Run Python Scripts" is on in your
Preferences, scripts saved inside the .blend run too: open only files you trust, or turn that preference off.
Without the add-on the script prints a SKIP result and exits normally. The file's own engine, samples and view
transform are kept unless you pass --engine or --samples.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import b2m_common as c  # noqa: E402

FACTORY_STARTUP = False     # read by `b2m3d recipe run`: this recipe needs the user's enabled add-ons

# Empty engine and samples 0: keep the file's own render settings (engine, samples, view transform), which the person
# chose when they lit the liquid. Pass --engine or --samples only to change them. Width and height 0: keep the file's own.
DEFAULTS = {"blend": "", "bake": True, "width": 0, "height": 0, "engine": "", "samples": 0}


def addon_ready() -> bool:
    try:
        bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd.get_rna_type()
        return True
    except (AttributeError, KeyError):
        return False


def main():
    p = c.parse_args(DEFAULTS, __doc__.split("\n")[0])
    if p["blend"]:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(p["blend"]))
    if not addon_ready():
        return c.emit({"recipe": "flip_bake", "skipped": True, "reason": "the FLIP Fluids add-on is not enabled in this Blender: "
                       "install it from https://github.com/rlguy/Blender-FLIP-Fluids (demo) or Superhive (full), enable it in "
                       "Preferences, and run this without --factory-startup"}, p["json"])
    scene = bpy.context.scene
    if p["bake"]:
        bpy.ops.flip_fluid_operators.bake_fluid_simulation_cmd()          # the add-on's documented command-line bake
    if p["width"] and p["height"]:
        scene.render.resolution_x, scene.render.resolution_y = int(p["width"]), int(p["height"])
    if p["engine"]:
        c.set_engine(scene, p["engine"], int(p["samples"]) or 64)
    elif int(p["samples"]):
        if scene.render.engine == "CYCLES":
            scene.cycles.samples = int(p["samples"])
        elif scene.render.engine.startswith("BLENDER_EEVEE"):
            scene.eevee.taa_render_samples = int(p["samples"])
    result = {"recipe": "flip_bake", "skipped": False, "baked": bool(p["bake"]), "frame_start": scene.frame_start,
              "frame_end": scene.frame_end, "engine": scene.render.engine}
    if p["out"]:
        result["rendered"] = render(scene, p)
    return c.emit(result, p["json"])


def render(scene, p) -> list[str]:
    """The whole range as one animation render, the way the add-on's wiki renders from the command line (`-a`), so its
    frame-change mesh loading runs as it does there; a --render-frames subset goes frame by frame."""
    if p["render_frames"].strip():
        return c.render_frames(scene, p["out"], c.frame_list(p["render_frames"], scene.frame_start, scene.frame_end), p["fmt"])
    os.makedirs(p["out"], exist_ok=True)
    scene.render.image_settings.file_format = p["fmt"]
    scene.render.filepath = os.path.join(p["out"], "####")
    bpy.ops.render.render(animation=True)
    ext = {"PNG": "png", "BMP": "bmp", "JPEG": "jpg"}.get(p["fmt"], p["fmt"].lower())
    return [os.path.join(p["out"], f"{f:04d}.{ext}") for f in range(scene.frame_start, scene.frame_end + 1)]


if __name__ == "__main__":
    main()
