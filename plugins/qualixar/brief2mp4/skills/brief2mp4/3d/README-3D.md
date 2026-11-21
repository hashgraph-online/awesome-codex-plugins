# The 3D pack (optional)

brief2mp4 works without this folder. The pack adds one thing: when a brief asks for real 3D (a product that falls and settles, an exploded view, a turntable, a logo with depth, a path-traced hero shot), it gives you a tested command line that goes from an idea to a HyperFrames project, without hand-writing a Three.js scene each time.

It is a Python module, `b2m3d`, plus a few Node helpers. Every subcommand prints one JSON result, so an agent can read what happened. Nothing here runs unless the brief needs it.

## Check and install

Check first. The command always exits 0 and prints one line you can branch on:

```bash
bash scripts/detect_3d.sh            # macOS, Linux
powershell -File scripts\detect_3d.ps1   # Windows
# 3d: ready (components: core,cad,blender)   or   3d: not installed
```

If it says `not installed` and the brief needs 3D, install only the components the brief needs. Nothing uses sudo or admin rights.

| Component | Installs | Size (macOS, measured) | Pick it when |
|---|---|---|---|
| `core` | Node: three, GSAP, glTF Transform, meshoptimizer, Jolt, two fonts. Python venv: numpy, scipy, trimesh, manifold3d | about 280 MB (venv 165, node_modules 111) | any `model`, `material`, `physics`, `optimize` or `hf` work |
| `cad` | CadQuery with the OpenCascade kernel | about 1.3 GB (large) | exact parametric CAD (fillets, assemblies); Manifold covers most shapes without it |
| `blender` | nothing: it finds a system Blender and prints how to install one | 0 | photoreal hero shots, glass, true soft shadows, alpha renders |

```bash
# macOS and Linux
bash 3d/install_3d.sh --components core
bash 3d/install_3d.sh --components core,cad
bash 3d/install_3d.sh --components blender      # only checks, prints the install command

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File 3d\install_3d.ps1 -Components core
powershell -ExecutionPolicy Bypass -File 3d\install_3d.ps1 -Components core,cad
```

Run these from this skill's folder (or give the full path). The installer needs Node.js 22 or newer and Python 3.12 or 3.13 on the PATH (the pinned numpy and scipy need 3.12+). If one is missing it stops and prints the command that installs it. To use a specific interpreter (for example one from uv on Debian 12, which ships 3.11), set `B2M3D_PYTHON`: `B2M3D_PYTHON="$(uv python find 3.12)" bash 3d/install_3d.sh`. Remove the pack with `bash 3d/install_3d.sh --uninstall` (or `install_3d.ps1 -Uninstall`); it only deletes a folder it created. It installs into `~/.brief2mp4/3d` (Windows: `%USERPROFILE%\.brief2mp4\3d`), keeps a Python venv, a `node_modules` folder and its own copy of the pack there (so moving or deleting the clone or plugin cache does not break it), prints what it installs and the disk size, and is safe to run again: finished work is skipped. Set `B2M3D_HOME` to use another folder. Versions are pinned in `requirements-core.txt`, `requirements-cad.txt` and `package.json` (with `package-lock.json`).

After install the command is `~/.brief2mp4/3d/venv/bin/brief2mp4-3d` (Windows: `venv\Scripts\brief2mp4-3d.cmd`), or `~/.brief2mp4/3d/venv/bin/python -m b2m3d` from any folder. The examples below write `b2m3d` for either form.

`b2m3d doctor` reports every component as ok or missing with the exact install command for your OS. If the pack is not installed, the skill's plain Three.js template (`templates/threejs/index.html`) still works for simple 3D.

## Commands

```bash
b2m3d model spec.py out.glb [--param teeth=24] [--units mm|cm|m] [--up z|y] [--smooth 30]
b2m3d material presets
b2m3d material assign in.glb out.glb --assign lid=brushed_aluminum --assign '*=matte_plastic'
b2m3d material linear "#2a6f4e"            # sRGB hex -> linear triple
b2m3d optimize in.glb out.glb [--simplify 0.5] [--join] [--no-compress]
b2m3d physics scene.json track.json        # Jolt WASM bake, deterministic
b2m3d hf shot.json project/                # self-contained HyperFrames project
b2m3d blender in.glb frames/ --mp4 out.mp4 --look studio|dramatic|soft [--transparent] [--frames 120] [--samples 128]
b2m3d doctor
```

**model.** A spec is a Python file with `build(params)`, and `model` runs it as Python: only use specs you wrote or trust. It may set `PARAMS` (defaults), `UNITS` and `UP`. Return a `manifold3d.Manifold`, a trimesh, or a list of `{"name", "geom", "color", "metallic", "roughness"}` parts; with the `cad` component also a CadQuery Workplane or Assembly. CAD convention is millimetres and Z up; glTF is metres and Y up, and `--units` and `--up` convert. Vertex normals are cached before export: trimesh writes them only when cached, and without them Three.js renders the model flat-shaded. Colours in a part are linear (see look rule 4).

**material.** Presets are JSON files in `presets/materials/` (aluminium, steel, gold, copper, anodised blue, car paint, glossy and matte plastic, rubber, ceramic, clear and smoked glass, silicon die, circuit-board green, velvet, an emissive neon). `--assign` maps a node name (or `*` for all) to a preset or to a path of your own preset JSON. A colour you pick in sRGB must be converted to linear first: `linear = (srgb / 255) ** 2.2`. `material linear "#rrggbb"` does it. Skipping this renders dark colours about two stops too light.

**physics.** `scene.json` lists bodies (`box`, `sphere`, `cylinder` or `hull` from a GLB node), gravity, fps, duration and substeps. Jolt runs once, in WASM, at a fixed step, and the result is one pose per frame. The bake is byte-for-byte repeatable, which is what lets a parallel renderer seek to any frame. Static bodies use `"motion": "static"`. A hull body takes `"glb"` (path relative to the scene file) and optionally `"node"`.

**optimize.** Dedup, weld, resample, prune, optional simplify, then meshopt compression. Node names are kept, because `explode` addresses parts by node name; `--join` merges meshes and breaks that. Python readers cannot decode meshopt, so the pack decodes a temporary copy when `physics` needs the geometry.

**hf.** Turns a shot JSON into a HyperFrames project folder with three.js, GSAP, fonts and every GLB copied in. A render never touches the network. The page holds the first frame until models are loaded and shaders compiled (`window.__hf.buildReady`). Unknown keys in the shot are reported in `warnings`.

**blender.** Uses the system Blender (never bundled; it is GPL software run as an external program). It is found on the PATH, in `/Applications/Blender.app/Contents/MacOS/Blender`, in `C:\Program Files\Blender Foundation\Blender *\blender.exe`, or at `B2M3D_BLENDER`. GPU: Metal on macOS, OptiX then CUDA then HIP then oneAPI on Windows and Linux, else CPU (the result JSON says which). Encode: `hevc_videotoolbox` on macOS when ffmpeg has it, else `libx264`; with `--transparent` the output is ProRes 4444 (`prores_ks`, `.mov`) and the floor defaults to a shadow catcher. Run one Blender render at a time: it takes the whole GPU.

## Shot JSON for `hf`

```json
{ "duration": 8, "fps": 30, "width": 1920, "height": 1080,
  "physics": "build/track.json",
  "models": [
    { "src": "build/shell.glb", "track": "shell" },
    { "src": "build/logo.glb", "spin": 14, "reveal": { "start": 0.1, "duration": 1.1 } } ],
  "camera": { "fov": 28, "auto": { "azimuth": 30, "elevation": 26, "startPadding": 1.9, "padding": 1.05 } },
  "ground": { "shadow": 0.5 }, "lights": "dramatic", "tonemapping": "neutral", "envIntensity": 0.35,
  "titles": [ { "text": "Headline", "sub": "One line", "start": 5, "duration": 2.5 } ] }
```

Paths are relative to the shot file. Top level: `duration` (required), `fps`, `width`, `height`, `physics`, `models`, `camera`, `ground`, `lights`, `tonemapping`, `exposure`, `envIntensity`, `envRotation`, `hdri`, `bloom`, `bounds`, `background` (CSS), `accent`, `font` (`Inter` or `Space Grotesk`), `titles`.

Model keys: `src`, `position`, `rotation` (degrees), `scale`, `track` (a body name from the physics bake) with `trackStart`, `spin` (degrees per second) with `spinOffset`, `float` (`amp`, `speed`), `reveal` (scale in: `start`, `duration`, `ease`), `explode` (`start`, `duration`, `dirs` as `{partName: [x, y, z]}` offsets in the model's own space, or `step` for an even lift of each child), and glTF animation clips, which play automatically and are seeked by time.

Camera: `auto` (starts wide on the landing zone, pushes to the settled pose; it does not know about `explode`, so for an exploded finish use `keys`), `orbit` (`from`, `to`, `radius`, `height`, `ease`), or `keys` (a list of `{t, pos, target, fov, ease}`). Eases: `linear`, `inOutCubic`, `outExpo`, `inOutSine`. Lights: `"studio"`, `"dramatic"`, `"soft"`, or your own list of `{type: key|rim|fill, color, intensity, pos}`. Titles: `text`, `sub`, `kicker` (empty by default), `start`, `duration`, `size`, `position` (`bottom-left`, `top-left`, `center`, `bottom-center`). Default colours are a neutral grey gradient and a near-white accent; set `background` and `accent` to the palette you chose for the video.

## What the brief says, and what to build

| The brief says | Build |
|---|---|
| "parts fall and settle", "things drop and pile up" | One GLB per part, `physics` bake, each model with `track`, `camera.auto` (frame the landing zone, parts fall into frame). Keep drops about 0.25 m apart for parts the size of a hand; for small parts lower gravity (`"gravity": [0, -3, 0]`) reads better. |
| "show what's inside", "exploded view", "take it apart" | `explode` with `dirs` per part, `ease` in and out, a camera `keys` pull-back so the whole column stays in frame. |
| "turntable", "rotate it", "show every side" | `spin` on the model (degrees per second) and a fixed `orbit` or `keys` camera; or, for a photoreal one, `blender --look studio`. |
| "hero product shot", "premium", "glass", "cinematic close-up" | `blender --look dramatic` (add `--transparent` for an overlay), then use the frames or MP4 as video inside the HyperFrames composition. |
| "logo in 3D", "our mark with depth" | `model` a Manifold extrusion of the mark, `material assign` a preset, `reveal` plus a slow `spin` or `float`, `bloom` only if the logo glows. |
| "floating", "hovering" | `float` on the model, `ground.shadow` low (0.3). |
| "glowing", "neon" | an emissive preset (`neon_emissive`) and `bloom` on, the only case where bloom is right. |
| "title over the 3D" | `titles` in the shot; they share the same paused timeline, so they seek like everything else. |
| anything the shot keys cannot say | plain Three.js with `templates/threejs/index.html`, or write the scene by hand following `references/threejs.md`. |

Snapshot every 3D shot and look at the frames before the full render:

```bash
cd project && npx --yes hyperframes@0.8.216 lint
npx --yes hyperframes@0.8.216 snapshot --at 0.5,1.5,3,6,7.5 --no-end
```

Open the contact sheet. Check that the subject is in frame at every sampled time, that shadows sit under the parts, and that colours are right. Then render: `npx hyperframes render --workers 4 --quality delivery -o out.mp4`.

## Look rules (each one learned from a frame that failed)

1. **Tone mapping Neutral by default** (`"tonemapping": "neutral"`). Filmic curves shift product colours; Neutral keeps a green board green. In Blender use the AgX or "Khronos PBR Neutral" view.
2. **Environment dim, key light strong.** `envIntensity` 0.3 to 0.45 with the `dramatic` rig. A bright environment flattens everything.
3. **The floor is a shadow catcher** (`"ground": {"shadow": 0.5}`) over the CSS background. A glossy coloured floor catches the rim light as a glowing column. Set `ground.y` if parts do not rest on the lowest point of the models.
4. **Colours in glTF are linear.** Convert sRGB with `(c / 255) ** 2.2` before you write them.
5. **Bloom off unless something is emissive.** Specular hotspots bloom into blobs.
6. **Physics for parts on a desk:** restitution 0.05, friction 1.0, linear damping 0.6, angular damping 0.9, drops staggered. Otherwise parts scatter far wider than they are and the framing makes them tiny.
7. **Frame the landing zone, not the fall** (`camera.auto`), so parts fall into frame.
8. **Depth of field off for small objects** in Blender. f/4 on a 5 cm part is a macro lens and everything goes soft.
9. **No fixed palette.** Pick one for the video from the brief, and set `background` and `accent` to it.

## Determinism contract

HyperFrames seeks frames out of order across parallel Chrome workers. So every visible value is a pure function of the time `t`. Physics is baked once and replayed by lookup with interpolation between frames. The runtime uses no `Date.now`, `performance.now`, unseeded `Math.random`, `setAnimationLoop` or network fetch. If you hand-write extra JavaScript for a shot, keep to the same rules.

## Gotchas already handled (do not reintroduce)

- trimesh exports normals only if they are cached; otherwise Three.js is flat-shaded. `model` caches them.
- trimesh cannot read meshopt-compressed GLBs; `physics` decodes a temporary copy.
- `physics` hulls are convex and limited to 200 points. A part with a hollow cannot hold another part inside; stack parts instead.
- Blender's `view_transform` and the EEVEE engine name differ between versions; the script tries each name.
- Blender receives its config through a temporary file, because JSON on a command line is mangled by some Windows shells.
- CadQuery's first import can take close to a minute (compiled bytecode is cached after that).
- With no GPU, HyperFrames falls back to software WebGL: slower but correct. `--workers 4` is a safe default.

## Tests

`tests/run_tests.sh` at the repository root runs the fast tests (model, material, physics and project determinism, the offline check, detect and doctor). `tests/run_tests.sh --slow` adds the renders: example 04 through lint and a short 1080p render, a one-frame Blender render, and the fallback path with the pack hidden. Install `core,dev` first (the `dev` component is pytest).

## Credits and licences

The pack itself is MIT, like the rest of this repository. It builds on, and credits, these projects. Check each licence before you ship a video or an asset inside a product.

| Project | Licence | Used for |
|---|---|---|
| three.js | MIT | the 3D renderer in the HyperFrames page |
| glTF Transform (`@gltf-transform`) | MIT | materials, optimise, decompress |
| meshoptimizer | MIT | mesh compression and simplification |
| Jolt Physics (`jolt-physics`, JoltPhysics.js) | MIT | rigid-body bake |
| manifold3d | Apache-2.0 | robust boolean geometry |
| sharp and libvips | Apache-2.0 and LGPL-3.0 | image handling inside glTF Transform; installed from npm as a dependency, not bundled in this repository |
| CadQuery (and OpenCascade through `cadquery-ocp`) | Apache-2.0 (OpenCascade is LGPL-2.1 with an exception) | optional parametric CAD |
| trimesh | MIT | meshes, hulls, GLB export |
| NumPy, SciPy | BSD-3-Clause | numerics |
| GSAP | the GSAP "no charge" standard licence (gsap.com/standard-license), not MIT | the paused timeline; vendored into each render project |
| Inter, Space Grotesk (`@fontsource-variable`) | SIL Open Font Licence 1.1 | title fonts |
| Blender | GPL | external program for path-traced shots; not bundled, not linked |
| HyperFrames | see its own licence | the renderer |
