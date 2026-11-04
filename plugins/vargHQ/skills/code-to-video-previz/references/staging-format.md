# staging.json: one scene, any renderer

The agent writes the scene as data and a small engine draws it. People who keep their token bills down converge on
this: "build the tool once, the agent only writes scene data". It also means the choice of tool is not final, because
`stage_three.ts` and `stage_blender.py` render the same file with the same lens maths. In our tests the two landed
every key point within 0.01% of the frame of each other.

## The world

- Metres. **x** right, **y** into the picture, **z** up, the floor at z = 0.
- `lens` is full-frame millimetres. The 36 mm sensor spans the longer side of the frame, in portrait too.
- `heading` is degrees on the floor: 0 faces +y (away from a camera at the origin), 90 faces +x, 180 faces the camera.
- Times are seconds on the film's timeline. Everything on screen is a pure function of time: no state, no random
  without a seed, so any frame renders the same in any order.

## The file

```json
{
  "title": "Rooftop standoff",
  "frame": { "w": 1280, "h": 720, "fps": 24 },
  "shots": [
    {
      "id": "s01", "start": 0, "end": 3.5, "lens": 28, "ease": "smooth",
      "subjects": ["ana"],
      "from": { "pos": [0, -7, 1.5], "look": [0, 2, 1.2] },
      "to":   { "pos": [0, -5, 1.5], "look": [0, 2, 1.2] }
    },
    {
      "id": "s02", "start": 3.5, "end": 6, "lens": 28, "path": "arc", "subjects": ["ana", "rival"],
      "from": { "pos": [-2.5, -2, 1.4], "look": [1.5, 2.5, 1.4] },
      "to":   { "pos": [3.5, -2.5, 1.4], "look": [1.5, 2.5, 1.4] }
    }
  ],
  "boxes": [
    { "name": "roof", "center": [0, 2, -0.1], "size": [20, 20, 0.2], "grey": 0.45 },
    { "name": "door", "center": [3, 6, 1.1], "size": [1.2, 0.3, 2.2], "grey": 0.25 },
    { "name": "van", "center": [8, 3, 1], "size": [4.5, 2, 2], "grey": 0.35,
      "keys": [ { "t": 0, "center": [8, 3, 1] }, { "t": 6, "center": [-2, 3, 1] } ] }
  ],
  "figures": [
    { "name": "ana", "height": 1.68, "color": 0.75, "keys": [
      { "t": 0, "pos": [-2, 2, 0], "heading": 90 },
      { "t": 3, "pos": [0, 2, 0], "heading": 90 },
      { "t": 5, "pos": [0, 2, 0], "heading": 180 } ] },
    { "name": "rival", "height": 1.8, "color": 0.25, "keys": [
      { "t": 0, "pos": [3, 3, 0], "heading": 270 } ] }
  ],
  "fill": 0.5
}
```

| field | what |
|---|---|
| `frame` | width, height, integer fps |
| `shots[]` | `id`, `start`, `end`, `lens`, `from` and `to` (`pos`, `look`, optional `lens` for a zoom, `roll` in degrees), `ease` (`smooth`, `linear`, `in`, `out`, `hold`), `path` (`arc` to orbit), `subjects` (names to audit), `visible_from` ({name: seconds} for a deliberate reveal), `keys` (a path with several keys in place of `from` and `to`: `t` in seconds from the shot's start, `pos`, `look`, optional `lens` and `roll`; default ease is linear; `solved_to_staging.py` writes this), `vp` ([u, v], where the vanishing point sits, for a painting or a shifted lens; default centre) |
| `boxes[]` | `name`, `center`, `size` (x, y, z), `grey` 0 to 1 or `color` [r, g, b], `rot_z`, `keys` for a moving box, `no_block: true` if the audit may ignore it (for blocking a view and for figures passing through), `rough` (0 to 1, default .85), `unlit: true` for a window or lamp that glows at its own colour and blocks no light |
| `figures[]` | stand-ins. Default `style` is a capsule with a ball head and a small nose, in the head's tone, that shows the facing: `height`, `color`, `head`, `keys` with `t`, `pos` (feet), `heading` |
| | `style: "joints"`: `top`, `legs`, optional `fore`, `head` (colours, grey or [r, g, b]) and `head_r` (metres), and `keys` with `t` and `joints` (`head neck hip shL shR elL elR haL haR knL knR ftL ftR`, world points). Use only when the poses matter |
| `flags[]` | four corners of a plane that casts shadow and is invisible to the camera, as a film set's flag: for a shadow edge you need in a certain place |
| `key` | optional light: `pos`, `aim`, `angle_deg`, `blend` (edge softness of the cone), `color`, `power_three`, `power_blender`, `soft` (source size in metres, Blender only: three.js shadows stay hard). One key only. Without it the scene is flat-lit, which is what a guide clip wants |
| `fill` | ambient level. Workbench ignores it and keeps its own dark grey background, so a bright sky needs a big box. Workbench also has soft studio shading, so large faces show a gradient |
| `tone` | `"none"` turns off filmic tone mapping (AgX), which desaturates. For colours you've sampled from a painting |
| `skin` | default colour for heads and forearms |
| `pins` | `{ "name": [ [x, y, z], [u, v], t ] }`: a world point, where it must land in the frame (fractions, top-left origin), and optionally when, in seconds on the film. Without `t`: at `pins_at`, default 0. A pin placed from its own reading proves only the maths, so hold some back |

## The commands

```bash
python3 scripts/check_staging.py staging.json            # numbers first: in frame, blocked, camera in a wall, pins
bun scripts/stage_three.ts staging.json still s02:1.5 stills/s02_mid.png
bun scripts/stage_three.ts staging.json film all renders/guide.mp4 --flat --grey

# the same file in Blender
uv run --python 3.13 --with bpy==5.2.3 python scripts/stage_blender.py staging.json still s02:1.5 eevee stills/s02_mid.png
uv run --python 3.13 --with bpy==5.2.3 python scripts/stage_blender.py staging.json film all workbench frames/ --blend scene.blend
ffmpeg -framerate 24 -i frames/f%04d.png -pix_fmt yuv420p -crf 18 renders/guide.mp4
```

Watch it live with `bun scripts/stage_three.ts staging.json live`, which prints a URL. The page plays the shots in a loop. It has no free camera: to move
the camera, edit the keys and render again. Three.js loads from jsDelivr, so renders need the network, unless you vendor it and change the import map.

The last rendered frame of a shot is at `end - 1/fps`, so a `to` key is approached, not shown. Set it one frame later if the end position has to land exactly.

## When to leave this format

It is a blocking format on purpose: boxes that turn only about z, stand-ins with fixed limb sizes, one key light. Slanted cloth or a carpet takes stairs of boxes: one agent used 80 tiers. Leave it when the job needs a rig, retargeted mocap, real
3D assets or a hand-tuned look. Pass `--blend scene.blend` and carry on in Blender with the camera and layout already
set, or move to `threejs-animatic` when a person needs a review UI with a camera map.
