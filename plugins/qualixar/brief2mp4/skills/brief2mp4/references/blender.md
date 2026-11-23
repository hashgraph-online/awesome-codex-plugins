# Blender, scripted and headless

Blender builds and renders 3D from a Python script with no window open. Use it when the brief wants something that should look physically real: a product on a table, glass, metal, ceramic, soft shadows.

Start from `templates/blender/scene.py`. It builds a whole scene from code (floor, product, three lights, a turntable camera, a 3D title that scales in) and renders PNG frames.

## Run it

```bash
# 3 stills (first, middle, last frame): seconds, not minutes. Do this first.
blender --background --factory-startup --python scene.py -- --frames-dir frames --preview

# The full shot as numbered PNGs
blender --background --factory-startup --python scene.py -- --frames-dir frames --seconds 8 --fps 30

# Encode to a delivery MP4
scripts/finish.sh --in frames --out final.mp4 --seconds 8
```

Everything after `--` goes to the script. `--factory-startup` ignores the user's own Blender settings so the result is the same on every machine. macOS path if `blender` is not found: `/Applications/Blender.app/Contents/MacOS/Blender`.

Render frames, not a video file, from Blender: a crash at frame 200 keeps frames 1-199, and ffmpeg does the encoding properly.

## Engines

| Engine | Use it for | Settings |
|---|---|---|
| EEVEE | Almost everything. Fast, good soft shadows | 32-64 samples |
| Cycles | When the brief wants realism: glass, caustics, true reflections | 64-128 samples plus denoising; on Apple Silicon try the Metal GPU |

Engine names changed across Blender versions. Set them inside a `try` and fall back (the template does this): EEVEE is `BLENDER_EEVEE` in current releases and was `BLENDER_EEVEE_NEXT` in some 4.x releases.

Measure before you commit to a full render: time the `--preview` run, divide by 3, multiply by the frame count.

## Writing robust scripts

- Find shader nodes by **type**, not name: `next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")`. Node names are translated in other languages.
- Colours on the Principled BSDF are linear. Convert hex from sRGB (the template's `hex_rgba` does it), or the palette comes out washed.
- When you parent one object to another after creating both, set `child.matrix_parent_inverse = parent.matrix_world.inverted()`, or the child jumps.
- Set `bpy.context.preferences.edit.keyframe_new_interpolation_type` to `"LINEAR"` before keyframing a constant turntable and back to `"BEZIER"` for eased moves.
- Always build from `read_factory_settings(use_empty=True)` so no default cube or light sneaks in.

## Light, camera, material: a recipe that rarely fails

- **Three area lights:** a large key in front and to one side (about 600 W, size 3 m), a smaller rim behind on the other side in a warm palette colour (about 400 W), a weak broad fill (about 120 W). Point each at the subject.
- **Background:** a dark world colour from the palette at low strength, and a big floor in a slightly lighter shade so the shadow has something to land on and the horizon disappears.
- **Camera:** 50 mm lens, a few metres away, a `TRACK_TO` constraint on an empty at the subject's centre. Animate the empty's rotation for a turntable; animate the camera's distance for a push-in. One move per shot.
- **Materials:** roughness 0.2-0.3 for glazed ceramic and plastic, 0.05 plus metallic 1.0 for polished metal, transmission 1.0 for glass (Cycles for best results).
- **Title in 3D:** a text object with a little extrude and an emissive material, parented to the camera rig so it always faces the lens. Or skip 3D text and put the title on top in HyperFrames.

## Checks

- Look at the three preview stills before the full render: subject in frame, nothing cut off, the floor horizon invisible, the title readable.
- After the full render, run `scripts/check_delivery.sh` and `scripts/contact_sheet.sh` on the finished MP4 like any other path.

## More Blender routes

- **Motion that is hard by hand** (seamless loops, retiming between markers, cloth, hinged chains, folding, walking forward with planted feet): tested parameterised scripts in `references/blender-recipes.md`, run with `b2m3d recipe run <name>`.
- **A Blender window you can talk to** (blender-mcp): `references/blender-live.md`. Decide live, render headless; headless stays the default for every shot that ships.
- **A prop from an image or a text prompt, or a liquid**: optional tools you install, in `references/generators-3d.md`.

