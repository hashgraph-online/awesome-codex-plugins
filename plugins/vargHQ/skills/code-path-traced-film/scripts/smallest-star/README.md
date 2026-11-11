# The Smallest Star

A 70-second animated fable in which everything is code written by Claude Fable 5.2 in one session:
the story, a path tracer written from scratch, both characters, the meadow, the light, the score and
the edit. No 3D software, no models, no textures, no video or music model.

The whole prompt was: "make something insane to show on X power of Fable 5.2; Inspire by https://varg.ai/how-to".

## What is in here

| Path | What it is |
|---|---|
| `timeline.json` | The film as data: 13 sections on a 3/4 bar grid at 72 bpm, captions, sound cues. Picture, score and assembly all read it |
| `src/shader.js` | The renderer: a WebGL2 path tracer plus denoise, bloom and tone-map passes |
| `src/engine.js` | Accumulates samples into float buffers, runs the passes, reads frames back |
| `src/world.js` | World layout (path, pond, house, props) shared by the shader and the animation |
| `src/shots.js` | Every shot as a function of time: camera, firefly, mouse, lights |
| `render.ts` | Driver: serves the page, runs headless Chrome on the GPU, writes PNG frames, resumes |
| `audio/score.py` | The score, ambience and sound effects, synthesized with numpy |
| `post/compose.py` | Captions, title, making-of wipe, end card, final encode |
| `live/` | The same renderer as one interactive HTML page |
| `skill/SKILL.md` | The method, written up as an agent skill |

## How the picture is made

- **Shapes.** The mouse, the firefly, mushrooms, stones, the log and the house are signed distance
  fields blended like clay. Each blade of grass is a parabolic ribbon that a ray meets by solving one
  quadratic; blades live in a grid that rays walk cell by cell. The ground is a heightfield. The pond is a
  plane with ripples in its normal.
- **Light.** Rays leave a thin-lens camera (depth of field), bounce, and sample three lights directly at
  every hit: the moon, the firefly's lantern and the window of the house. Grass transmits light and tints
  the shadows it casts. Motion blur comes from rendering each sample at a slightly different time.
- **Cleaning up.** Samples are averaged in float buffers. A filter guided by first-hit normal, depth,
  albedo and per-pixel variance removes the remaining noise. Bloom, a filmic curve and a grade follow.
- **Sound.** A lullaby waltz in B minor that turns to D major when the light blooms: music box, pad, bass,
  crickets, wing buzz and footfalls, all computed from sines and noise and mixed to -16 LUFS.

Captions use a system font (Iowan Old Style). Everything else on screen is computed by `src/`.

## Run it

Needs Google Chrome, Bun, Python 3 with numpy and Pillow, and ffmpeg.

```bash
# one still at a film time (seconds), or a look-development view
bun render.ts --out /tmp/stills --w 960 --h 540 --spp 16 --t 31.5
bun render.ts --out /tmp/stills --w 960 --h 540 --spp 16 --dev dev_mouse:0.2

# the whole film as a contact sheet's worth of drafts
bun render.ts --out /tmp/sheet --w 480 --h 270 --spp 8 --quality draft --t 2.5,7.5,12.5,17,21,25,30,36,42.5,47.5,58.5

# final frames (resumes if interrupted), the making-of passes, then the score and the assembly
bun render.ts --out /tmp/final --w 1280 --h 720 --spp 20 --frames 0-1439 --set post.grain=0
bun render.ts --out /tmp/final --w 1280 --h 720 --spp 20 --frames 1560-1679 --set post.grain=0
bun render.ts --out /tmp/brk --w 1280 --h 720 --spp 8 --flatspp --frames 660-779 --modes 2,1 --name b
bun render.ts --out /tmp/brk --w 1280 --h 720 --spp 1 --flatspp --frames 660-779 --modes 4 --name n
python3 audio/score.py
python3 post/compose.py --frames /tmp/final --brk /tmp/brk --out out/the-smallest-star.mp4

# the live page
python3 live/build.py /tmp
```
