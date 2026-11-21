# Blender with an agent

## Three ways to connect

| route | what it is | use it when |
|---|---|---|
| **Headless `bpy`** (`scripts/stage_blender.py`) | Blender as a Python module, no window | repeatable builds, CI, no install. We tested this path |
| **`ahujasid/mcp-for-blender`** | community MCP (MIT, formerly `blender-mcp`). `look` through the camera, at angles and as frame strips, plus asset libraries and 3D generators. Turn telemetry off | an open scene you direct live, and an agent that needs to see |
| **Official Blender Lab MCP** ([blender.org/lab/mcp-server](https://www.blender.org/lab/mcp-server/)) | from the Blender project, GPL-3.0-or-later, Blender 5.1+. Python, file and object summaries, screenshots, viewport renders, API and manual search. No assets | inspecting files, API lookups. It warns that it runs LLM code "without any guards" and recommends a virtual machine |
| `bpy-dev/blender-mcp` | a fork with headless tools on saved files | headless plus MCP. Its 30% time and 15% tokens numbers are self-reported, on one task |

Both main MCP servers default to port 9876. "Official" on X is unreliable: ask for the link. No neutral test of MCP
against headless exists. Our synthesis, which is judgement and not data: live MCP for directing, headless for repeatable builds.

## Install

```bash
# no install, tested on macOS arm64 with Python 3.13 (the wheel is about 245 MB; ours took 20 minutes on a slow line)
uv run --python 3.13 --with bpy==5.2.3 python scripts/stage_blender.py staging.json still s01:0 workbench out.png

# a normal Blender install works too
blender -b -P scripts/stage_blender.py -- staging.json still s01:0 workbench out.png
```

`bpy` pins one Python version per release. Blender 5.2's needs exactly 3.13. Rendering on a Linux box without a GPU
hasn't been tested with this script; Cycles on CPU is the safe fallback there.

## Which engine

Same staging, Apple Silicon, 1280x720, 96 frames, our run:

| renderer | time | use |
|---|---|---|
| Blender Workbench | 8 s | the guide clip: flat, fast, no light to copy |
| Three.js in headless Chrome (software WebGL) | 18 s | the guide clip or a live preview |
| Blender EEVEE | 35 s | stills and a look check with real shadows |
| Blender Cycles (CPU, 48 samples) | 15 to 24 s for one still, so 25 to 40 min for this clip | a final render, rarely a previz |

Set Workbench to material colour so identity colours show; a forced single grey erases them. Pros disagree on one
point: two of them found that motion blur in the previz helps Seedance read fast motion, so a plain viewport capture can be
too clean for propellers and the like. Render that one shot in EEVEE with motion blur and compare.

## Keep the agent out of what it's bad at

Reports converge: blocking and cameras are fine, and curves, organic forms, concept-art matching and bespoke rigs are not.

- "Still very far away from the concept art image." (Sebastian Aaltonen, 30 years in rendering, per his bio)
- "Tripo plus manual cleanup is still the fastest accelerated modeling workflow right now." (Kiaran Ritchie, *The Art of Rigging*)
- "Honestly, Claude is really bad at modeling objects" (@greeimm, whose piece a tool author showcased)

So the agent arranges and you source:

| need | use |
|---|---|
| walks, runs, stock acting | Mixamo FBX |
| custom motion from a phone video | `MaxLiu22/Motion2MixamoRig` (one person, head to toe; check the SMPL-X licence) |
| props and characters | Tripo or Meshy, plus cleanup |
| ready assets | BlenderKit, Poly Haven, Sketchfab through `mcp-for-blender` |
| simple hard-surface and layout | the agent, in `bpy` |

One team's three-tier rule is worth copying: AI in `bpy`, Tripo SM or Tripo HD, chosen by how closely the object is seen and
whether its shape needs editing.

## The loop inside Blender

1. Build at real scale, metres, Z up, ground at z = 0. Say what is where and which way it faces.
2. Add one named camera per shot with a timeline marker, so playback cuts like an edit. Reframe by moving the aim target.
3. Look through every camera: first, middle and last frame. Fix what isn't faithful, logical or well composed.
4. Run numbers: in frame, not occluded, feet on the ground, no intersections.
5. Workbench render at 24 fps for timing. Save a new version each time.

PJ Ace's public prompts follow these same steps and add a storyboard page step: `references/prompts.md`.

A note on cost: the bill moves rather than vanishes. "Video generations went down, but remaking the previz melted my
Claude credits." Keep rounds small, and let the agent write scene data, not a new tool each time.
