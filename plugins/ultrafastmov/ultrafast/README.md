<a href="https://ultrafast.mov"><img src="https://github.com/user-attachments/assets/c17c81aa-cb68-4b5a-8bc6-f43c64f16e1c" width="100%" alt="ultrafast: shot on the GPU. A pottery class teaser plays beside an excerpt of the document that made it; it exported in 1.68 s at 1080×1920."></a>

<h3 align="center">Shaders, 3D, motion type and camera optics,<br>written by your agent and rendered on the GPU. Open source.</h3>

<p align="center">
<a href="https://crates.io/crates/ultrafast"><img src="https://img.shields.io/crates/v/ultrafast?style=flat-square&labelColor=1d1b19&color=ff48b0&label=crates.io" alt="crates.io"></a>
<a href="https://pypi.org/project/ultrafastmov/"><img src="https://img.shields.io/pypi/v/ultrafastmov?style=flat-square&labelColor=1d1b19&color=0078bf&label=PyPI" alt="PyPI"></a>
<a href="https://www.npmjs.com/package/ultrafastmov"><img src="https://img.shields.io/npm/v/ultrafastmov?style=flat-square&labelColor=1d1b19&color=0078bf&label=npm" alt="npm"></a>
<a href="https://github.com/ultrafastmov/ultrafast/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/ultrafastmov/ultrafast/ci.yml?branch=main&style=flat-square&labelColor=1d1b19&label=CI" alt="CI"></a>
<a href="#license"><img src="https://img.shields.io/badge/licence-Apache--2.0%20or%20MIT-ffe800?style=flat-square&labelColor=1d1b19" alt="Apache-2.0 or MIT"></a>
<a href="docs/MCP.md"><img src="https://img.shields.io/badge/MCP-20%20tools-ff48b0?style=flat-square&labelColor=1d1b19" alt="MCP: 20 tools"></a>
<a href="https://www.opensourcealternatives.to"><img src="https://www.opensourcealternatives.to/badge-osa.svg" height="20" alt="As seen on Open Source Alternatives"></a>
<a href="https://alternativeto.net/software/ultrafast/about/?utm_source=badge&utm_medium=referral"><img src="https://alternativeto.net/static/badges/badge-wide-dark.svg" height="20" alt="You can find us on AlternativeTo"></a>
<a href="https://glama.ai/mcp/servers/ultrafastmov/ultrafast"><img src="https://glama.ai/mcp/servers/ultrafastmov/ultrafast/badges/score.svg" height="20" alt="ultrafast MCP server on Glama"></a>
</p>

<p align="center">
<a href="https://ultrafast.mov"><b>ultrafast.mov</b></a> ·
<a href="https://ultrafast.mov/docs/">Quickstart</a> ·
<a href="https://ultrafast.mov/examples/">Examples</a> ·
<a href="https://ultrafast.mov/use-cases/">Use cases</a> ·
<a href="docs/AGENT_GUIDE.md">Agent guide</a> ·
<a href="https://ultrafast.mov/compare/">Compare</a>
</p>

```sh
curl -fsSL https://ultrafast.mov/install.sh | sh
```

Then tell your agent **“Go to ultrafast.mov and make…”**, or connect it yourself
([Claude Code, Codex, Cursor, Gemini CLI](#wherever-your-agent-runs)). macOS
(Apple silicon) and Linux; [other ways to install](#install).

## How it compares

<a href="https://github.com/ultrafastmov/benchmarks"><img src="https://github.com/user-attachments/assets/7ac15f0e-19bd-41b2-9314-1fae4dd501f7" width="100%" alt="Render time, end to end, for three 10-second videos on one RTX 5090 workstation, Remotion and HyperFrames at their fastest settings. Title card: ultrafast 0.66 s, Remotion 2.32 s, HyperFrames 3.53 s. Chart: 0.72, 2.25, 3.31 s. Footage and captions: 0.78, 6.69, 4.46 s. Tokens an agent writes for one 10-second short: ultrafast 1,234, Remotion 1,868, HyperFrames 1,680, Shotstack 1,657."></a>

| | **ultrafast** | Remotion | HyperFrames | Shotstack |
|---|---|---|---|---|
| Draws each frame with | **GPU kernels, Metal or Vulkan; no browser** | headless Chrome, a screenshot per frame | headless Chrome, captured frame by frame | a hosted renderer |
| Renders on | **your GPU, locally or with `uf serve`** | your machine, or Lambda or Cloud Run in your cloud | your machine; Lambda, Cloud Run or HeyGen's cloud | Shotstack's cloud only |
| Render a 10 s video, end to end² | **0.66–0.78 s** | 2.25–6.69 s at its fastest, 4.45–8.53 s by default | 3.31–4.46 s at its fastest, 3.71–5.05 s by default | not measured: it renders only in its own cloud |
| Tokens an agent writes for a 10 s short¹ | **1,234** | 1,868 | 1,680 | 1,657 |
| Licence | **Apache-2.0 or MIT** | source-available; companies of 4 or more need a paid licence | Apache-2.0 | proprietary API |
| Cost to render | **your own GPU, nothing else** | free on your machine; a company licence; your cloud bill | free on your machine; your cloud bill or HeyGen credits | 5–20¢ a rendered minute |

<sub>¹ Measured 22 November 2026: the same 10-second 1080×1920 short (footage, an animated title, three lines of detail, captions timed to each word, a grade and grain), written the way each tool's own docs and agent skills recommend, counted with the o200k_base tokenizer over the files the agent writes. Counting only what is typed after each tool's scaffold: 1,218, 1,660, 1,500 and 1,657. Remotion 4.0.545, HyperFrames 0.9.79; the Shotstack edit was validated, not rendered. Projects and counts: [ultrafastmov/benchmarks/tokens](https://github.com/ultrafastmov/benchmarks/tree/main/tokens). Competitor facts are from their own docs: [Remotion and HyperFrames](https://ultrafast.mov/compare/#sources), [Shotstack](https://shotstack.io/pricing/).</sub>

<sub>² Three 10-second videos: a 1080×1920 title card, a 1920×1080 chart, and 1080×1920 footage with word-timed captions. Each is 300 frames to H.264, timed from command start to the finished MP4, median of 5 warm runs on one RTX 5090 workstation (Ryzen 9 9950X3D2). “Fastest” is the best of every setting tried for each tool (concurrency 2 to 32, a prebuilt bundle, GPU flags, NVENC); ultrafast ran its default command. Cold first runs: ultrafast 1.8–2.1 s, Remotion 8.4–12.6 s, HyperFrames 3.7–5.6 s. At the same nominal CRF 18, ultrafast's hardware-encoded files are 1.15 to 1.75 times the size of Remotion's and 0.62 to 1.23 times HyperFrames'. Measured with ultrafast 0.2.0 on the night of 23 November 2026, and Remotion 4.0.545 and HyperFrames 0.9.79 on 22 November. Every project, run and caveat: [ultrafastmov/benchmarks](https://github.com/ultrafastmov/benchmarks).</sub>

Pick a browser renderer instead when your team already builds the parts as React
components or HTML, or you need Remotion's embeddable web player or HeyGen's
avatars and voices; pick Shotstack when you want a hosted API and no GPU of
your own.

## Made by asking.

What agents made with it, and each brief in a sentence. Every film comes with
the document that made it.

<table>
<tr>
<td width="50%" valign="top">
<a href="https://ultrafast.mov/use-cases/#launches"><img src="https://github.com/user-attachments/assets/84852966-4a4c-431e-baa1-81a754881ad1" width="100%" alt="Lens launch: a 35 mm lens rendered in 3D by ultrafast, its iris and an exploded view of its elements"></a>
<p><b>Launch films</b><br>
<code>you</code> A launch film for our 35 mm lens: the knurling, the iris, an exploded view, then the price.</p>
<sub>16:9 · 1920×1080 · 16 s · exported in <b>4.88 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/product.json">document</a></sub>
</td>
<td width="50%" valign="top">
<a href="https://ultrafast.mov/use-cases/#at-scale"><img src="https://github.com/user-attachments/assets/db6709ee-e08c-4f0a-8471-56a364a2b020" width="100%" alt="Year in review: four members' films from one document, each with its own numbers and colours"></a>
<p><b>One video per customer</b><br>
<code>you</code> Make every member their year in review from this spreadsheet.</p>
<sub>9:16 · 1080×1920 · 12 s · exported in <b>1.37 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/wrapped.json">document</a></sub>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="https://ultrafast.mov/use-cases/#data"><img src="https://github.com/user-attachments/assets/d3480a8a-e2eb-4fb9-ba92-ba7ff7482a89" width="100%" alt="The Keeling Curve: Mauna Loa CO₂ drawn month by month"></a>
<p><b>Data stories</b><br>
<code>you</code> Turn NOAA's Mauna Loa CO₂ file into a chart for Instagram.</p>
<sub>4:5 · 1080×1350 · 16 s · exported in <b>1.50 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/keeling.json">document</a></sub>
</td>
<td width="50%" valign="top">
<a href="https://ultrafast.mov/use-cases/#loops"><img src="https://github.com/user-attachments/assets/e3474d56-5715-4a54-b410-c3e154ff8619" width="100%" alt="Celadon dish: a reaction-diffusion pattern grows across a glazed dish"></a>
<p><b>Loops and visuals</b><br>
<code>you</code> A 15-second loop for the album cover: something growing, in celadon.</p>
<sub>1:1 · 1080×1080 · 15 s · exported in <b>1.06 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/bloom.json">document</a></sub>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="#watch-three-at-full-length"><img src="https://github.com/user-attachments/assets/f7bd7f49-c343-4cb5-b4bf-f686f7a5f9bd" width="100%" alt="Two launches, one count: Apollo 11 and Artemis I cut together on the 1969 countdown"></a>
<p><b>Documentaries and recaps</b><br>
<code>you</code> Cut the Apollo 11 and Artemis I launches together on the 1969 countdown. Make it feel like a documentary.</p>
<sub>2.39:1 · 1920×804 · 22.5 s · exported in <b>3.36 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/liftoff.json">document</a> · <a href="#watch-three-at-full-length">full length, with sound ↓</a></sub>
</td>
<td width="50%" valign="top">
<a href="#watch-three-at-full-length"><img src="https://github.com/user-attachments/assets/c03b0c30-19ad-4bad-a9c4-99d576c9bbaa" width="100%" alt="Podcast clip: an astronaut talks about Earth from orbit, with word-by-word captions"></a>
<p><b>Podcast and interview clips</b><br>
<code>you</code> Pull the best 25 seconds from this episode. Captions on, vertical, our colours.</p>
<sub>9:16 · 1080×1920 · 27.5 s · exported in <b>4.07 s</b> · <code>review</code>: 0 findings · <a href="https://ultrafast.mov/examples/podcast.json">document</a> · <a href="#watch-three-at-full-length">full length, with sound ↓</a></sub>
</td>
</tr>
</table>

<sub>Export times are wall-clock `uf export` runs on one RTX 5090. The documentary and the podcast cut NASA film and sound, which is in the public domain. More films, each with its document: [ultrafast.mov/examples](https://ultrafast.mov/examples/).</sub>

### Watch three at full length

https://github.com/user-attachments/assets/97a03c21-85e9-4bd4-8cf5-e0e954d8869f

https://github.com/user-attachments/assets/4dc54f6a-fc8e-41ad-92c7-d5dd55e85242

https://github.com/user-attachments/assets/279b8b3e-051a-412d-b155-2d2e94f7f137

<sub>The documentary (sound on), the lens launch film and the podcast clip (sound on). The lens, its iris and every element of the exploded view are geometry and materials in the document, lit and rendered by ultrafast.</sub>

## Edit it by asking.

<img src="https://github.com/user-attachments/assets/a00e869f-a802-4b64-a265-14fcf62088b3" width="100%" alt="A conversation with a coding agent. You: a 10-second vertical teaser for my pottery class. The agent's film shows a vase on the wheel. You: make it a wide bowl instead of a vase. The agent edited one node, and the film now shows a bowl; the type, light and timing are unchanged.">

Your agent edits the video, not the pixels. One sentence changed one node: the
pot's shape, its camera and its shader. The type, light and timing stayed as
they were. This works today in Claude Code, Codex, Cursor and Gemini CLI with
`uf mcp`.

## First draft: eight findings. Second: none.

<img src="https://github.com/user-attachments/assets/cf0ea5c0-d84e-49c2-9374-c30ca8e57bcf" width="100%" alt="Contact sheets of two drafts. The first is marked up in red pen: a white flash, a clipped title, low-contrast and tiny text, a line on screen too briefly. The second is stamped 0 findings, beside the loop: new, check, review, export.">

Agents check their own work before anyone watches. `uf review` read all 300
frames of the teaser in 4.7 s and reported what a person would catch: text
that is clipped, too small, too low in contrast or on screen too briefly, and
seizure-risk flashing (WCAG 2.3.1). The agent fixed the document and ran it
again.

```sh
uf new vertical teaser.json     # start from a template
uf check teaser.json            # problems, without rendering
uf review teaser.json           # reads every frame
uf export teaser.json teaser.mp4
```

## 3D, 2D, or both.

<img src="https://github.com/user-attachments/assets/1d96ecf7-61f5-44b3-b24b-4823731480d7" width="100%" alt="Four prints: the lens in 3D; the same lens with the camera turned 84 degrees; a Swiss-style concert poster of type and shapes; the pottery teaser with a 3D pot under set type.">

One engine renders 3D models, type, vector shapes, charts and footage, and
composites them in the same frame. No Blender, no After Effects, no plugins.
The lens and the pot are geometry and materials in their documents, lit and
rendered by ultrafast, not made in a 3D app; turning the camera is one more
render of the same node, about 0.3 s.

## Speed

<img src="https://github.com/user-attachments/assets/adc8830b-2e26-4234-9801-07f08c1d253c" width="100%" alt="894 frames a second at 1920×1080 with 6-sample motion blur on one RTX 5090. Press log: launch film, 16 s, exported in 4.88 s; simulation, 15 s, in 1.06 s; class teaser, 10 s, in 1.68 s.">

The planner fuses chains of ops into one generated kernel per group, caches
what does not change, skips what cannot be seen and renders costly looks at
reduced resolution. Motion blur samples only what moves. Exports render
straight into the hardware encoder with no readbacks, and geometry that holds
still is not drawn again. No browser anywhere in the loop.

## How it works

<img src="https://github.com/user-attachments/assets/bba6bd42-7e3e-4e9f-9799-7e76ce29ac85" width="100%" alt="The pottery teaser separated into its six plates (backdrop shader, vessel shader, particles, title, details, grain), beside the six lines of the document, one node per plate.">

A frame is a stack of plates, and each plate is a node in one document. The
agent writes the document (JSON, or the MCP tools), ultrafast compiles it to
GPU kernels once, then draws and encodes every frame on the GPU: Metal on
macOS, Vulkan everywhere else. [How it works in detail](docs/ARCHITECTURE.md).

```json
"vessel": { "op": "shader", "code": "// a lathe, its profile keyed…", "u4": { "keys": [ … ] } },
"dust":   { "op": "particles", "rate": 34, "life": [6, 9] },
"title":  { "op": "text", "text": "Spin something new.", "font": "ultrafast:display", "size": 176 },
"grain":  { "op": "grain", "amount": 0.05 }
```

## Wherever your agent runs

| Where | How | |
|---|---|---|
| **MCP server** | `uf mcp`, 20 tools, on your machine | available |
| **Coding agents** | Claude Code, Codex, Cursor, Gemini CLI | available |
| **Skill and plugin** | `npx skills add ultrafastmov/ultrafast` | available |
| **Remote MCP** | `/mcp` on your own `uf serve`, one key | available |
| **SDKs** | `pip install ultrafastmov` · `npm i ultrafastmov` | available |
| **Framework starters** | Vercel AI SDK, OpenAI Agents SDK, LangGraph, Mastra ([starters](starters)) | available |
| **Self-host** | `docker run --gpus all ghcr.io/ultrafastmov/ultrafast` · [HTTP API](docs/service/API.md) | available |
| **ChatGPT app, Claude connector** | make and edit videos in a chat | coming soon |
| **ultrafast Cloud** | hosted GPUs, one API key | [waitlist](https://ultrafast.mov/cloud/) |

```sh
claude mcp add ultrafast -- uf mcp      # Claude Code
codex mcp add ultrafast -- uf mcp       # Codex
gemini extensions install https://github.com/ultrafastmov/ultrafast   # Gemini CLI
```

Cursor, Claude Desktop and the rest take `{"command": "uf", "args": ["mcp"]}`;
the Claude Code plugin is `claude plugin marketplace add ultrafastmov/ultrafast`
then `claude plugin install ultrafast@ultrafast`. Every client and tool is in
[docs/MCP.md](docs/MCP.md).

Listed on the [official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.ultrafastmov/ultrafast)
as mcp-name: io.github.ultrafastmov/ultrafast

## Install

```sh
curl -fsSL https://ultrafast.mov/install.sh | sh   # macOS (Apple silicon), Linux x86_64
brew install ultrafastmov/tap/ultrafast            # Homebrew, prebuilt
cargo install ultrafast                            # from crates.io
docker run --gpus all ghcr.io/ultrafastmov/ultrafast:latest info
```

Prebuilt archives for macOS (Apple silicon) and Linux x86_64 (glibc 2.28 and
newer) are on the [releases page](https://github.com/ultrafastmov/ultrafast/releases);
each carries the Slang libraries it loads, and the image carries everything.
`cargo install` fetches Slang once, on first use. On Linux you need your GPU's
Vulkan driver, ffmpeg for exports, and espeak-ng and tesseract for `voiceover`
and `ocr` (macOS uses its own voices and Vision). Windows runs it in WSL2
([docs/WINDOWS.md](docs/WINDOWS.md)). `uf` is the same command as `ultrafast`,
short.

## Try it

```sh
uf new vertical film.json
uf check film.json
uf sheet film.json --count 9 --out sheet.png
uf live film.json
uf review film.json
uf export film.json film.mp4
uf export film.json overlay.mov --codec prores --alpha --size 4k
uf export film.json preview.gif --quality draft --size 480p --fps 15
```

The films in [`examples/films`](examples/films) (each a short Python script
that writes the document) show the range: `ink`, `riso`, `glass`, `clay`,
`kinetic`, `chrome`, `signal_film`, `terminal`, `warp`, `pulse`, `assemble`,
`flow`, `launch`, `numbers_film`, `blocks`, `prism`, `ledger` (charts on
paper), `ship` (code typing into a live preview).

## What's in the box

**Compose anything in one graph.** Shapes, gradients, noise, images and
video; shaped text with variable fonts, glyph animators, text on paths and
counters; vector paths with strokes, dashes, trims and morphs; SVG files as
editable vector nodes; Lottie animations as editable paths and keyframes
(closely matching lottie-web, rendered hundreds of frames a second);
agent-written Slang shaders; 3D (extruded and bevelled type, glTF, primitives)
with image-based lighting, shadows, fog, depth of field and refractive glass;
particles and swarms that form type; fluid (ink, smoke) and feedback
simulations (trails, echo tunnels, reaction-diffusion), exact on export and
seekable; masks, 19 blend modes, warps, blurs; looks such as bloom, grain,
grades, halftone, CRT, glitch, glass panes, lens flares and light leaks; sound
mixed into exports, with params driven by a soundtrack's loudness.

**Every deliverable from one document.** H.264, HEVC and AV1 MP4s, ProRes
(proxy to 4444 XQ) and transparent ProRes 4444, VP9 WebM with alpha, GIFs, PNG
and EXR sequences and sound alone; rendered at any size, so 720p and a sharp
4K come from the same 1080p document; any frame rate; four quality levels from
a fast draft to a master.

**Made for agents.** Write JSON or call MCP tools. `uf check` finds mistakes
before rendering; `uf review` renders the film and reports text that is
unreadable, clipped, overlapping or on screen too briefly, and seizure-risk
flashing. `block` gives finished titles, lower thirds, quotes, stats, chapter
markers, end cards and charts (bars, lines, donuts that build themselves from
`values`); `code` types highlighted source into a window; one text node mixes
faces and colors (`"Video is *live*"`, `[300 fps]{highlight=#ff4d6d}`);
`stack` lays content out by its measured size; `captions` animates a
transcript; `uf voiceover` speaks a script with word times; `uf new` starts
from a template. Five typefaces are bundled so documents look the same
everywhere.

**Live.** `uf live` plays a document in a player while agents edit it over a
socket; parameter edits apply on the next frame without recompiling,
structural edits compile in the background, and the player outlines what an
edit touched. `uf record` films a document being edited.

## Docs

| Doc | What's in it |
|---|---|
| [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) | how to work in it (start here) |
| [docs/OPS.md](docs/OPS.md) | every op; `uf ops` prints the same as JSON |
| [docs/MCP.md](docs/MCP.md) | ultrafast as MCP tools, local and remote |
| [docs/LIVE.md](docs/LIVE.md) | the live player, edit protocol, recording |
| [docs/service/SELF_HOST.md](docs/service/SELF_HOST.md) | the render service on your GPU (`uf serve`) and its [HTTP API](docs/service/API.md) |
| [sdk/python](sdk/python), [sdk/typescript](sdk/typescript) | the SDKs; [starters](starters) for agent frameworks |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | how it works |
| [docs/LINUX_NVIDIA.md](docs/LINUX_NVIDIA.md), [docs/WINDOWS.md](docs/WINDOWS.md) | Linux with NVIDIA, Windows through WSL2 |
| [docs/RECONSTRUCTION.md](docs/RECONSTRUCTION.md) | a finished video back into an editable document |

## Your GPU today. ultrafast Cloud soon.

The engine is free under Apache-2.0 or MIT, for commercial use, at any scale:
Metal on macOS (Apple silicon), Vulkan on Linux and Windows (WSL2), with the
MCP tools, the live player and the render service in the box. ultrafast Cloud
will run the same engine and HTTP API on hosted GPUs with one API key, and the
ChatGPT app, the Claude connector and remote MCP with sign-in will run on it.
[Join the waitlist](https://ultrafast.mov/cloud/) for one email when it opens.

## Questions

<details>
<summary><b>What is ultrafast?</b></summary>

An open-source video engine built for AI agents. A video is a document of
nodes (footage, type, shapes, 3D, effects); ultrafast checks it, shows the
agent its frames and renders it on the GPU at hundreds of frames a second.
</details>

<details>
<summary><b>Do I need a GPU?</b></summary>

Yes, for now: a Mac with Apple silicon, or a computer with a Vulkan GPU on
Linux or Windows (through WSL2). ultrafast Cloud, which renders on hosted GPUs,
is coming soon: [join the waitlist](https://ultrafast.mov/cloud/).
</details>

<details>
<summary><b>Can it edit my own footage?</b></summary>

Yes. Cut, trim, speed-ramp, reframe, grade, key and caption video files, mix
in music and voiceover, and add titles, logos and charts. The
[footage examples](https://ultrafast.mov/examples/#footage) cut, caption and
grade NASA film and sound.
</details>

<details>
<summary><b>Is the 3D in the examples rendered by ultrafast?</b></summary>

Yes. The pot, the lens, the compass, the chrome ring, the Earth and the Moon
are geometry and materials written in each film's document. ultrafast lights
and renders them on the GPU every frame, in the same pass as the type. Nothing
was filmed, and nothing was made in a 3D app.
</details>

<details>
<summary><b>Which sizes and formats can it make?</b></summary>

Any size and frame rate: 9:16, 1:1, 4:5, 16:9, 21:9 or your own, up to 4K.
MP4 (H.264, HEVC, AV1), ProRes up to 4444 XQ, transparent ProRes and WebM,
GIF, PNG and EXR sequences, and sound alone.
</details>

<details>
<summary><b>What does it cost?</b></summary>

Nothing. The engine is free under Apache-2.0 or MIT, for commercial use, at
any scale.
</details>

## Building from source

- Rust (stable; `cargo build --release`)
- [Slang](https://github.com/shader-slang/slang/releases) 2026.19 or newer,
  found in this order: `ULTRAFAST_SLANG_DIR` (the folder with
  `lib/libslang.dylib` or `lib/libslang.so`); a `slang-*` folder beside the
  executable, as the release archives have; `SLANG_DIR` at build time; a copy
  fetched once into the cache (`ULTRAFAST_SLANG_FETCH=0` turns fetching off).
- ffmpeg for exports on the Vulkan backend, recordings, and media off macOS.

Releases: `packaging/` builds the archives, the Homebrew formula and the
image, and `.github/workflows/release.yml` builds, tests and publishes all
of them from a `v*` tag.

Build with `--features vulkan` to run the Vulkan backend on a Mac through
MoltenVK; every GPU test passes on both backends. On Windows with an NVIDIA
GPU, `tools/windows/build.sh` builds and installs ultrafast from WSL2
([docs/WINDOWS.md](docs/WINDOWS.md)); Linux with NVIDIA is
[docs/LINUX_NVIDIA.md](docs/LINUX_NVIDIA.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md). Report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md).

## License

Licensed under either of [Apache License, Version 2.0](LICENSE-APACHE) or
[MIT license](LICENSE-MIT), at your option. Unless you explicitly state
otherwise, any contribution intentionally submitted for inclusion in
ultrafast by you, as defined in the Apache-2.0 license, shall be dual
licensed as above, without any additional terms or conditions.

Bundled fonts are under the SIL Open Font License (see
`examples/assets/fonts/licenses`).

<br>

<a href="https://ultrafast.mov"><img src="https://github.com/user-attachments/assets/8a835882-e77a-49f2-8f10-16eef0203554" width="100%" alt="Send your agent to ultrafast.mov"></a>
