# The open-source motion ecosystem: what else exists and how to connect it

brief2mp4's default stack is HyperFrames + Three.js + Blender + ffmpeg, plus the optional 3D pack. Read this file when a brief asks for something that stack does badly, or when the user already works in another tool. Star counts and licences were read from GitHub on 15 Nov 2026; check the repo before relying on a licence for commercial work.

The rule for bringing anything in: **it must render frame-exact from time, or it must be rendered first to a file** (video, PNG sequence, Lottie JSON, GLB) that HyperFrames then plays as a layer. Anything driven by a wall clock or `requestAnimationFrame` alone will drift across parallel render workers.

## Video frameworks (whole-video authoring)

| Repo | Stars | Licence | Best at | Use with brief2mp4 |
|---|---|---|---|---|
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | 84.5k | Apache-2.0 | HTML + CSS + GSAP to deterministic MP4, built for agents | The default spine. Its own agent skills: `npx hyperframes skills update` |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 73.3k | Remotion licence: free for individuals and small companies, company licence above a size | React components as video, big ecosystem, server-side rendering | If the user already has a Remotion project, build there. Its skills: `npx skills add remotion-dev/skills`. HyperFrames ships a `remotion-to-hyperframes` skill for porting |
| [motion-canvas/motion-canvas](https://github.com/motion-canvas/motion-canvas) | 19.9k | MIT | TypeScript generators for explainer animation, editor with timeline | Render to MP4 or a PNG sequence, then layer in HyperFrames |
| [midrender/revideo](https://github.com/midrender/revideo) | 4.2k | MIT | Motion Canvas fork aimed at programmatic, templated rendering | Same as Motion Canvas |
| [ManimCommunity/manim](https://github.com/ManimCommunity/manim) | 42.6k | MIT | Maths, equations, algorithms, graphs (the 3Blue1Brown style) | Render a transparent MOV/WebM insert, layer it in HyperFrames |
| [3b1b/manim](https://github.com/3b1b/manim) | 96.5k | MIT | The original Manim; faster moving, less stable API | Prefer the Community edition for agents |
| [mifi/editly](https://github.com/mifi/editly) | 5.6k | MIT | Declarative JSON slideshows and clip edits | Quick joins when no motion design is needed; ffmpeg alone usually suffices |

## Animation libraries (inside a HyperFrames composition)

| Repo | Stars | Licence | Best at | Notes |
|---|---|---|---|---|
| [greensock/GSAP](https://github.com/greensock/GSAP) | 30.7k | GSAP standard no-charge licence (free, including all plugins such as SplitText and MorphSVG) | Timelines, easing, text splitting, SVG morphing | HyperFrames seeks GSAP timelines directly. The default |
| [juliangarnier/anime](https://github.com/juliangarnier/anime) | 74.7k | MIT | Lightweight timelines, SVG, stagger | Seekable through its timeline API; drive it from `t` |
| [motiondivision/motion](https://github.com/motiondivision/motion) | 35.2k | MIT | React and vanilla UI animation | Fine for UI mocks if you drive progress from `t`, not from springs in real time |
| [airbnb/lottie-web](https://github.com/airbnb/lottie-web) | 32.5k | MIT | Playing After Effects exports (Lottie JSON) | Use `goToAndStop(frame, true)` from `t`. Good for icon and character loops |
| [LottieFiles/dotlottie-web](https://github.com/LottieFiles/dotlottie-web) | 0.9k | MIT | Faster Lottie and .lottie playback (WASM) | Set the frame from `t` |
| [rive-app/rive-wasm](https://github.com/rive-app/rive-wasm) | 1.0k | MIT | Interactive vector animation with state machines | Advance by fixed steps from `t`; test that a seek renders the same frame twice |

## 2D and creative-coding renderers

| Repo | Stars | Licence | Best at | Notes |
|---|---|---|---|---|
| [pixijs/pixijs](https://github.com/pixijs/pixijs) | 48.7k | MIT | Fast 2D WebGL: thousands of sprites, particles, filters | Render on demand from `t` with the ticker stopped |
| [processing/p5.js](https://github.com/processing/p5.js) | 24.4k | LGPL-2.1 | Generative art, sketches | Call `noLoop()` and `redraw()` per frame; seed `randomSeed()` |

## 3D engines and helpers

| Repo | Stars | Licence | Best at | Notes |
|---|---|---|---|---|
| [mrdoob/three.js](https://github.com/mrdoob/three.js) | 118.5k | MIT | The web 3D standard | The 3D default. See `references/threejs.md` |
| [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | 33.7k | MIT | Three.js as React components | Use `frameloop="never"` and call `advance(t)` once per frame |
| [pmndrs/drei](https://github.com/pmndrs/drei) | 10.2k | MIT | Ready-made R3F helpers (text, environments, controls) | Some helpers fetch from CDNs or use unseeded randomness at render: vendor the assets |
| [pmndrs/postprocessing](https://github.com/pmndrs/postprocessing) | 3.0k | Zlib | Bloom, depth of field, film grain for Three.js | Grain and noise effects need a seed driven from `t` |
| [BabylonJS/Babylon.js](https://github.com/BabylonJS/Babylon.js) | 26.4k | Apache-2.0 | Full engine with PBR, node materials, GUI | Turn off temporal effects or they smear across seeks |
| [playcanvas/engine](https://github.com/playcanvas/engine) | 17.3k | MIT | Fast WebGL/WebGPU engine, Gaussian splats | Update with a fixed `dt` from `t` |
| [google/filament](https://github.com/google/filament) | 20.7k | Apache-2.0 | Physically based rendering, accurate materials | Its post effects add per-frame noise; disable them for deterministic frames |
| [theatre-js/theatre](https://github.com/theatre-js/theatre) | 13.0k | Apache-2.0 | A keyframe editor for Three.js and the DOM | Last push Aug 2024. Useful for hand-keyed camera paths: export the keyframes and seek them by `t` |
| [blender/blender](https://github.com/blender/blender) | 22.0k | GPL (external tool) | Photoreal rendering, simulation, Geometry Nodes | Used headless. See `references/blender.md` |

## 3D asset pipeline (what the 3D pack builds on)

| Repo | Stars | Licence | Role |
|---|---|---|---|
| [CadQuery/cadquery](https://github.com/CadQuery/cadquery) | 6.1k | Apache-2.0 | Parametric CAD in Python: enclosures, gears, exact parts |
| [elalish/manifold](https://github.com/elalish/manifold) | 2.4k | Apache-2.0 | Fast, robust booleans that never leave broken meshes |
| [mikedh/trimesh](https://github.com/mikedh/trimesh) | 3.7k | MIT | Mesh loading, inspection and GLB export |
| [donmccurdy/glTF-Transform](https://github.com/donmccurdy/glTF-Transform) | 2.1k | MIT | Edit, compress and optimise GLB files |
| [zeux/meshoptimizer](https://github.com/zeux/meshoptimizer) | 8.9k | MIT | Simplify meshes and compress vertex data |
| [jrouwe/JoltPhysics](https://github.com/jrouwe/JoltPhysics) | 12.3k | MIT | Rigid-body physics, baked once to deterministic tracks |
| [AcademySoftwareFoundation/MaterialX](https://github.com/AcademySoftwareFoundation/MaterialX) | 2.3k | Apache-2.0 | Portable material definitions; a good source for physically based values when you write your own preset JSON |
| [PixarAnimationStudios/OpenUSD](https://github.com/PixarAnimationStudios/OpenUSD) | 7.6k | TOST (Apache-2.0 based) | Scene description for big multi-asset shots; not in the pack, convert to GLB first |

## Capture, reconstruction and mesh repair (outside the 3D pack)

Use these to turn a real object or place into an asset, or to repair a bad mesh, before the 3D pack takes over. Check licences: several are GPL, which is fine for making videos and matters only if you ship them inside a product.

| Repo | Stars | Licence | Role |
|---|---|---|---|
| [colmap/colmap](https://github.com/colmap/colmap) | 13.2k | BSD-style | Camera poses from photos (structure from motion); runs on CPU without CUDA |
| [ArthurBrussee/brush](https://github.com/ArthurBrussee/brush) | 5.3k | Apache-2.0 | Gaussian-splat training on any GPU (WebGPU), including Apple silicon |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | 12.2k | Apache-2.0 | NeRF and splat training; needs an NVIDIA GPU |
| [alicevision/Meshroom](https://github.com/alicevision/Meshroom) | 13.1k | MPL-2.0 | Photogrammetry to textured meshes; its GPU path needs CUDA |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | 14.2k | MIT | Point clouds, registration, surface reconstruction |
| [cnr-isti-vclab/meshlab](https://github.com/cnr-isti-vclab/meshlab) | 5.9k | GPL-3.0 | Mesh repair and remeshing (desktop) |
| [cnr-isti-vclab/PyMeshLab](https://github.com/cnr-isti-vclab/PyMeshLab) | 1.0k | GPL-3.0 | The same filters from Python: close holes, decimate, remesh |
| [wjakob/instant-meshes](https://github.com/wjakob/instant-meshes) | 6.3k | BSD-style | Quad remeshing; last commit 2022, prefer PyMeshLab |
| [sgenoud/replicad](https://github.com/sgenoud/replicad) | 0.7k | MIT (OpenCascade is LGPL) | CAD modelling in JavaScript, in the browser |

## Agent skills and prompt libraries for motion

These teach an agent craft: shot recipes, launch structure, polish passes, prompt patterns. Read them for ideas; follow each repo's licence before copying anything.

| Repo | Stars | Licence | What to take from it |
|---|---|---|---|
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 7.2k | see repo | Remotion best practices for agents |
| [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) `skills/` | (above) | Apache-2.0 | The HyperFrames contract, CLI, block registry, media and style-sampling skills |
| [heygen-com/hyperframes-launches](https://github.com/heygen-com/hyperframes-launches) | 0.7k | Apache-2.0 (brand media excluded) | Real launch-video compositions and storyboards: how a 30-60 s launch is paced |
| [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 19.8k | Apache-2.0 | Shot recipe cards, beat sync and sound design for product videos |
| [charlie947/motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) | 0.7k | MIT | Brand intake, motion prompts and a polish pass for launch-grade graphics |
| [yihui-dev/awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) | 15.3k | MIT | A large collection of videos made by Claude with the prompts behind them: study what a good prompt specifies |

## Finishing

| Repo | Stars | Licence | Role |
|---|---|---|---|
| [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | 67.3k | LGPL/GPL | Encode, join, mix, measure. Every route ends here (`scripts/finish.sh`) |

## Tools the checks and sound scripts call (optional, you install them)

brief2mp4 never bundles these. Each script prints the exact install command and a SKIP line, and exits 3, when its tool is missing: a delivery does not fail because an optional tool is absent, but a skipped check is never reported as a pass. Star counts and licences were read from GitHub on 22 Nov 2026.

| Tool | Stars | Licence | Used by | Note |
|---|---|---|---|---|
| [librosa](https://github.com/librosa/librosa) | 9.1k | ISC | `scripts/beat_grid.py` | Beat and onset detection. `python3 -m pip install --user librosa`. The tempo is an estimate, so the script fits a grid through the beats |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 5.6k | BSD-3-Clause | `scripts/cut_points.sh` | Scene cuts from a recording. `python3 -m pip install --user scenedetect opencv-python-headless`. Soft dissolves and screen recordings with little change can be missed: lower `--threshold` |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) | 77.6k | Apache-2.0 | `scripts/ocr_sweep.sh` | Reads text from frames. OCR misreads thin or wide-spaced display type, so a hit is a reason to look at the frame, and a miss is not proof |
| [Openverse](https://github.com/WordPress/openverse) (a WordPress project) | 0.7k | MIT (its code); each track has its own licence | `scripts/fetch_music.py`, `scripts/fetch_archive.py` | Search API for CC0, public domain and CC BY audio and images, no key for light use. Anonymous requests are rate limited. CC BY needs the credit in `ATTRIBUTION.md` in the description. Openverse reports what the host says: confirm on the source page |
| [Audiocraft / MusicGen](https://github.com/facebookresearch/audiocraft) (Meta) | 23.9k | Code MIT; **model weights CC BY-NC 4.0** | optional, see `references/sound.md`; `film.py assets --musicgen` | Music and effects from a prompt. Weights are non-commercial only |
| [F5-TTS](https://github.com/SWivid/F5-TTS) | 15.6k | Code MIT; **pre-trained models CC BY-NC** | optional, see `references/sound.md`; `film.py voice --voice f5-tts` | Voice-over and voice cloning. Clone only a voice you have the right to |
| [Natural Earth](https://github.com/nvkelso/natural-earth-vector) (Tom Patterson, Nathaniel Vaughn Kelso and contributors) | 2.3k | Public domain (naturalearthdata.com terms of use; the repository carries no SPDX licence) | `scripts/make_map.py` | Country outlines at 1:110m, shipped as a 54 KB subset so maps work offline (`data/NATURAL-EARTH.md` has the source and its SHA-256). The 110m set leaves out very small countries: pass `--geojson` with a finer file. Boundaries are drawn by their de facto status (Natural Earth's disputed-boundaries policy), which some countries restrict: check maps of disputed regions before publishing |
| [Wikimedia Commons](https://commons.wikimedia.org) (Wikimedia Foundation; a website and API, no repository) | n/a | each file has its own licence; only public domain, CC0 and CC BY are used | `scripts/fetch_archive.py` | Archive photos, maps and documents. The script rejects ShareAlike, NonCommercial, NoDerivatives and unknown licences, spaces its requests and identifies itself in the User-Agent. "Public domain" is as Commons tags it and differs by country: check the file page before a commercial release |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (Georgi Gerganov and contributors) | 55.4k | MIT | `scripts/split_takes.py` (optional) | Word timings for cutting a take into lines, through `whisper-cli` and a model you download. Without it, pauses alone are used, or word timings from `npx hyperframes transcribe` |
| [Demucs](https://github.com/adefossez/demucs) | 3.6k | MIT | optional, see `references/sound.md` | Splits a song into stems so cuts can follow the drums. The original Meta repository is archived; this is the maintained fork |

## 3D tools the pack can call (optional, you install them)

brief2mp4 never bundles these and never copies their code or weights. Each one is called through a small script or a documented recipe; `references/generators-3d.md` and `references/blender-live.md` say how, with the licence text quoted. Star counts and licences were read from GitHub on 22 Nov 2026. The notes are information, not legal advice.

| Tool | Stars | Licence | Used by | Note |
|---|---|---|---|---|
| [blender-mcp / MCP for Blender](https://github.com/ahujasid/mcp-for-blender) (Siddharth Ahuja; the repository was renamed from `blender-mcp`) | 35.3k | MIT | the live Blender route, `references/blender-live.md` | Lets an agent drive a running Blender. Third party, not made by Blender. Runs any Python you send it with no password on its socket, which opens on its own when Blender starts with the add-on enabled: localhost only, save first. By default it sends an anonymous usage record (tool name, timings, versions, OS); set `DISABLE_TELEMETRY=true` in the server's environment to turn that off (content collection is opt-in). Its paid hosted features are not used here |
| [Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) (Tencent) | 15.5k | Tencent Hunyuan 3D 2.0 Community License; **not valid in the European Union, United Kingdom and South Korea** | `scripts/gen3d.py run hunyuan3d` | Image to mesh, optional texture. The licence covers use of the tool and its output only inside its Territory, needs a Tencent licence if you had over 1 million monthly active users on its release date, and bars using it to improve another AI model. Its Acceptable Use Policy (Exhibit A) applies: label published output as machine-generated, no military use. Credit: "Hunyuan3D-2 (Tencent)". Its README: macOS, Windows and Linux, 6 GB of VRAM for shape, 16 GB with texture |
| [TRELLIS](https://github.com/microsoft/TRELLIS) (Microsoft) | 14.4k | MIT for its own code and models (the model cards say `license: mit`); **non-commercial in practice**: the GLB export imports nvdiffrast (NVIDIA, research or evaluation use only) and a Gaussian rasterizer under Inria's research-only terms, and `diffoctreerast` has the same terms | `scripts/gen3d.py run trellis --non-commercial` | Image or text to mesh, for research or evaluation only. The script prints the warning and runs only with `--non-commercial`; the install line for the research-only parts is opt-in. Needs an NVIDIA GPU with 16 GB or more per its README. Credit: "TRELLIS (Microsoft)" |
| [FLIP Fluids](https://github.com/rlguy/Blender-FLIP-Fluids) (Ryan L. Guy and Dennis Fassbaender) | 2.0k | Add-on code GPL, simulation engine MIT, some bundled content under a Standard Royalty Free licence | `3d/templates/recipes/b2m_flip_bake.py` | Liquids. Sold on [Superhive](https://superhivemarket.com/products/flipfluids) (formerly Blender Market); a free demo adds a watermark to the simulation meshes. brief2mp4 only runs Blender with it enabled |
| [Blender](https://github.com/blender/blender) | 22.3k | GPL (external tool) | `references/blender.md`, the recipes | Run as a separate program, never bundled |

## Picking between the frameworks

- **The brief is a motion graphic and an agent is building it:** HyperFrames. HTML and CSS are what language models write most reliably, the timeline is seekable by design, and lint plus snapshots catch mistakes before a render.
- **The user's team already ships React video:** Remotion, in their project, following their conventions. Check the licence tier for their company size.
- **A maths or algorithm explainer:** Manim inserts inside a HyperFrames film.
- **A designer will hand-tune keyframes:** Theatre.js for the camera or Lottie from After Effects, then seek either by `t` inside HyperFrames.
- **A product must look real:** the 3D pack's Blender route, or the Blender template, layered under HyperFrames type.

If you bring in a tool that is not listed here, apply the same test before you build on it: render frame 90 twice in separate runs and compare the PNGs. Identical files mean it is safe for parallel rendering.
