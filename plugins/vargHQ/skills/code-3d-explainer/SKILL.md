---
name: code-3d-explainer
description: >-
  Make a 3D explainer video of something you cannot film (a cell, an atom, a virus, a protein, an engine,
  a reactor, a black hole, a maths idea) entirely in code: a sourced fact sheet checked by a fresh critic
  subagent before any 3D work, the subject built in three.js from procedural geometry (and real data such
  as PDB coordinates) one part per beat with a label and a one-line fact, a camera that tours the build and
  zooms through scales to an x-ray cutaway of the whole, a live scale bar, deterministic 1080p rendering
  with headless Chrome (scripts/capture.ts) or HyperFrames, and QA scripts that check label overlap, phone
  legibility, reading time and that every word on screen is in the approved fact sheet. Includes a working
  21 s animal-cell film to copy. Use when someone asks for a 3D explainer, a science explainer video,
  "explain how X works in 3D", a cell / atom / virus / molecule / engine / reactor / black hole animation,
  "build it one part at a time", a cutaway or exploded view explained, a Kurzgesagt-style 3D explainer, a
  "zoom into the invisible" film, or a Fable 5.2 code explainer. Not for 2D maths and equation animations
  (manim-skill), short 2D motion formats (motion-formats), general HTML-to-video work (hyperframes),
  writing the script itself (video-script) or sound design and music (video-sound).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Bun 1.3+, Google Chrome or Chromium, ffmpeg; ImageMagick 7 for contact sheets (no FreeType needed).
  three.js r185 loads from jsDelivr (pinned) or is vendored with scripts/vendor_three.sh. No npm install,
  no API key, no credits. Measured on an Apple M4 Pro: the 21 s 1080p example renders in 51-54 s
  (11.7 frames/s, 4 headless tabs on the GPU, lossless PNG), 3x faster with JPEG frames for drafts, 22.5 s
  through HyperFrames (bunx hyperframes@0.9.15, 8 workers); software GL (no GPU) is ~1 frame/s. Optional
  narration uses the varg MCP or the varg-ai skill (ElevenLabs via varg, priced with estimate_cost first).
---

# 3D explainers built from code

A film of the invisible, made entirely in code: a cell built one organelle at a time, a zoom from a
fingertip to electron clouds, a reactor you take apart. Nothing is filmed or generated, so every frame
is exact, re-renderable and free. And because it *looks* authoritative, a wrong claim spreads further
than it would in a sketch. This skill makes the facts the first step and the last check.

The format went viral with Claude Fable 5.2 (2026-11-09). Science explainers built from code were the #2
use case on launch day (1.37M views, 5.8k bookmarks across 12 posts):

| Post | What | Lesson |
|---|---|---|
| [@claudeai, by @kevin_t_ngo](https://x.com/claudeai/status/2120174844822298730) (448k views, 2.7k bookmarks) | "A 3D model of a cell, built entirely from code one organelle at a time" | the build-up *is* the explanation: one part per beat |
| [@anxuanng](https://x.com/anxuanng/status/2120088745139638375) (586k views) | a 3D film zooming into atoms: "why your fingers never really touch" | the replies took apart the physics: it is electrostatic repulsion and Pauli exclusion, not Zeno's paradox. Beautiful frames, wrong mechanism. Hence the fact sheet and the critic |
| @konstantinsaifo | "explain how a nuclear reactor works by building one you can take apart in three.js" | exploded views: parts slide out on their beats |
| @cube_224 | a ~3 min film on Rubik's cubes and maths, "understandable by middle-schoolers, avoiding the usual clichés" | compute every number; ban the clichés in the brief |

The example here is our own build (not a copy): `examples/animal-cell/`, 21 s at 1080p, 9 parts, ending on
a labelled cutaway: [the full film](https://s3.varg.ai/files/4325c578-378d-4c43-ae53-3cc3218df1ea/file_b6dc1bd5642f.mp4)
(1920×1080, 17.7 MB). Your own renders go to `renders/master.mp4`.

## Quick start

```bash
cp -r <skill>/examples/animal-cell my-film && cp -r <skill>/scripts my-film/scripts && cd my-film
bun scripts/capture.ts . --stills 2.6,8.4,20.5                 # look at qa/stills/*.png first
bun scripts/capture.ts . --out renders/master.mp4 --labels qa/labels.json
bun scripts/check_labels.ts qa/labels.json                     # overlap, safe area, phone size, reading time
bun scripts/check_facts.ts factsheet.md qa/labels.json         # every word on screen is in the sheet
bun scripts/sheet.ts renders/master.mp4 qa/sheet.png --n 24 --cols 6 --tile 400
bun scripts/sheet.ts renders/master.mp4 qa/phone.png --phone   # 390 px tiles = a phone feed
```

Open `index.html?dev=1` through any static server for a scrubber (space plays, arrows step frames).
Then replace `factsheet.md`, `story.json` and `cell.js` with your subject; `lib/` is the engine.

## The workflow

1. **Fact sheet first** (`references/fact-sheet.md`, worked example `examples/animal-cell/factsheet.md`).
   Every string the film will show, word for word, with a source that actually says it; the real size of
   every part next to the model size; every simplification on purpose (counts, enlargements, invented
   colours, empty space, missing parts); the claims you deliberately do not make. If the film explains
   *why* something happens, the mechanism is its own sourced row.
2. **Critic pass 1** before any 3D work: a fresh subagent (Agent tool, web access) with the prompt in
   `references/critic-prompt.md`. It must not be the agent that wrote the sheet. Apply every FIX, paste
   the verdict into the sheet's "Critic log", set `Status: **approved for build**`. On the cell it found
   a dozen real problems (see below).
3. **Beat sheet** in `story.json`: one entrance window per part (`timing`), one label per part (`labels`:
   anchor, side, in/out, name, fact, factId), titles and end card (`texts`), the scale bar and where it
   must hide, the camera keys. ~2.2 s per part is the floor (reading time, below).
4. **Build the subject in code**, one part at a time (`references/build-and-camera.md`): procedural
   geometry in real units, real data where it exists (PDB coordinates for molecules, published dimensions
   for machines), no downloaded models. Each part enters on its own beat: grow, slide in, draw on, sweep
   in with a glowing front. Heroes (what the camera visits) are hand-placed; everything else is scattered
   by a seeded sampler that keeps clear of the heroes and of the camera path.
5. **Camera tour through scales**: establish the whole → part by part, closer and closer (the live scale
   bar goes 5 µm → 500 nm → 200 nm) → x-ray → pull out to a cutaway of the whole, held ≥ 2.5 s with every
   part tagged. Move-hold-move: an *arrive* key and a slow push-in key per part, monotone interpolation
   (never overshoots), holds as long as the label needs to be read.
6. **Optional narration** (`references/narration.md`): script only from sheet rows, `estimate_cost` then
   varg `generate_speech` (ElevenLabs), word timestamps drive label in-times; `capture.ts --audio`.
7. **Render deterministically at 1920×1080** (`references/render.md`): `render(t)` is a pure function of
   t; capture.ts screenshots the page (labels are HTML) frame by frame in parallel tabs and pipes them into
   ffmpeg. The same `index.html` renders through HyperFrames (`bunx hyperframes@0.9.15 render`). Prove it:
   `capture.ts --check 10`.
8. **QA, every render** (`references/labels.md`):
   - `check_labels.ts`: no overlapping text, 64 px side margins, names ≥ 46 px (9 px on a phone), every
     label readable for 0.3 s + words / 4.5 s;
   - `check_facts.ts`: on-screen text equals the sheet, every claim sourced, critic verdict PASS;
   - look at `qa/sheet.png` and `qa/phone.png` yourself with the Read tool;
   - critic pass 2: a *new* subagent compares the frames with the sheet and signs off.
9. **Preview**: `bash scripts/cut_preview.sh renders/master.mp4 <start> <dur> preview.mp4` (1280×720,
   6–10 s, 0.4–2 MB; raise `CRF` if the grain makes it big).

## Rules that came from real failures

**Accuracy**
- The sheet's source must *say it*. Our first sheet cited Wikipedia for a mitochondrion "0.5–1 µm wide";
  Wikipedia gives an area (0.75–3 µm²). It quoted a sentence about ATP that is no longer in the article.
- Hedge to the truth, not to vagueness: "Holds the DNA" became "Holds nearly all the cell's DNA"
  (mitochondria have their own); "Digest waste with acidic enzymes" became "Break down waste in an acidic
  interior" (the enzymes are hydrolases in an acidic lumen, not acids).
- Enlarged parts break the scale bar: hide it in those shots (the ribosome close-up would have shown a
  500 nm bar next to 120 nm ribosomes labelled "25–30 nm").
- Put the caveat on screen: "Simplified: far fewer parts, colours invented" / "Small parts drawn larger
  than real", ≥ 2 s, 44 px, near-white (34 px grey was unreadable on a phone).
- A label must never sit over a different part, and its dot must sit *on* its part. Text lingers at most
  0.25 s after its anchor leaves the frame; 0.5 s left "Golgi apparatus" floating over mitochondria. The
  frame critic also caught a ribosome dot on empty space and a cytoskeleton dot hidden behind a
  mitochondrion.

**Labels and timing**
- Name 64 px / fact 40 px / end tags 46 px with a soft dark scrim; the 40 px end tags failed the phone
  check (8.1 px on a 390 px feed).
- Reading time is the binding constraint: nine labelled parts with 7–9 words each need ~21 s. Our first
  timing gave the ER label 1.5 s; the check caught it and the camera holds grew to fit.
- Alternate label sides between beats; consecutive labels overlap in time by ~0.5 s and must not overlap
  in space. End-card tags go in columns sorted by anchor height, laid out all at once.

**Look**
- Near-black, two accents (orange `#ff5315`, teal), colour by system, soft depth from DOF + bokeh specks +
  fog-dark background, grain. Bloom threshold ≥ 0.7: bright cream parts and sharp speculars became
  glowing balls and light bulbs.
- Translucent "x-ray" shells for containers (membrane, envelope, ER) so the inside reads; opaque stylized
  solids for parts; shells must not write the DOF depth.
- A part rendering as one flat colour = its faces are back faces (a `LatheGeometry` profile drawn top to
  bottom). The Golgi was a flat teal leaf until the profile was reversed; then it became the best shot.
- Cutaway = clip the containers with two shared planes (`clipIntersection`), rebuild the cut faces as
  geometry with a bilayer line at the edge, keep small parts whole, turn the wedge ~28° off the camera.

**Rendering**
- Headless Chrome on macOS uses the Metal GPU with no flags; Linux without a GPU falls back to
  SwiftShader (~1 frame/s at 1080p for this scene).
- PNG encoding is the bottleneck: JPEG frames are ~3× faster (SSIM 0.98); keep PNG for the master.
- A CDN import that never arrives hangs a render forever (we lost one to a DNS outage): capture.ts now
  times out every DevTools call; vendor three.js with `scripts/vendor_three.sh` (load 0.5 s vs 2–13 s).
- HyperFrames needs `data-no-timeline` on a three-only root (or each render waits 45 s for a GSAP
  timeline) and local `@font-face` files.

## The example: an animal cell, built one part at a time

`examples/animal-cell/`: membrane → nucleus with pores → x-ray to the nucleolus → rough ER growing from
the nuclear envelope (with ribosomes on it and on the outer nuclear membrane) → Golgi stack and vesicles →
mitochondria with cristae → a polysome (ribosomes on one mRNA) → lysosomes with enzyme granules →
microtubules from the centrosome → a 100° wedge cut, labelled. 21 s, 630 frames, 1 unit = 1 µm, a 20 µm
cell. All on-screen text from `factsheet.md` (25 rows, 7 simplifications). Critic pass 1 on the sheet:
PASS WITH FIXES, all applied. Critic pass 2 on the frames: FIX FIRST, 9 findings, 7 fixed and 2 listed as
limits. QA on the final render: `check_labels` all pass, `check_facts` 36 texts all sourced,
`--check 10` byte-identical.

| file | what |
|---|---|
| `index.html` | page + HyperFrames root, import map (three r185), fonts, label CSS |
| `story.json` | palette, look, timing, labels, texts, scale bar, camera keys |
| `cell.js` | the subject: geometry, placement, anchors, `update(t)` |
| `lib/explainer.js` | engine: renderer + post, PCHIP camera keys, labels and columns, scale bar, `window.__film`, `hf-seek`, dev scrubber |
| `lib/materials.js` | `shell`, `solid`, `glow`, `bokeh` shaders with clipping and focus dimming |
| `factsheet.md` | the approved sheet with the critic log |
| `fonts/` | Inter and JetBrains Mono (OFL) |
| `qa/` | written by the QA commands: `labels.json`, `sheet.png`, `phone.png` (not kept in the repo) |

## Scripts

| script | does |
|---|---|
| `scripts/capture.ts` | render MP4 / stills / label boxes / determinism check / `--eval` from any page that publishes `window.__film`; system Chrome over DevTools, no npm |
| `scripts/check_labels.ts` | overlap, safe area, anchor covered, phone size, reading time on the real render |
| `scripts/check_facts.ts` | on-screen text vs the fact sheet, sources, critic verdict, approval |
| `scripts/sheet.ts` | contact sheets from a video or a stills folder, `--phone` 390 px tiles, `--at` times |
| `scripts/cut_preview.sh` | the 1280×720 catalog preview with duration and size checks |
| `scripts/vendor_three.sh` | copy three.js into the project and point the import map at it |

## References

| file | read it for |
|---|---|
| `references/fact-sheet.md` | the template, source rules, real-data sources (PDB, PubChem, NASA, NIST) |
| `references/critic-prompt.md` | the critic prompts (sheet, then frames) and the Zeno lesson |
| `references/labels.md` | label anatomy and sizes, placement, reading time, the scale bar, the checker |
| `references/build-and-camera.md` | part recipes, placement, the look, the cutaway, camera keys and pacing |
| `references/render.md` | determinism contract, capture.ts, HyperFrames, measured speeds, troubleshooting |
| `references/narration.md` | optional voiceover on varg and syncing labels to words |
| `references/subjects.md` | atoms, viruses, proteins, DNA, reactors, engines, black holes, maths: parts, data, traps |

## Related skills

`threejs-animatic` (three.js previz and the seek-safe rendering it shares), `hyperframes` and
`hyperframes-animation` (HTML → video, the three.js adapter), `manim-skill` (2D maths), `motion-formats`
(short 2D formats), `video-script` (writing the script), `video-sound` (sound and music), `varg-ai`
(voiceover and any generated media).
