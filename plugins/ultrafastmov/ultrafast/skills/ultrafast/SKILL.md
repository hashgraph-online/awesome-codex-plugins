---
name: ultrafast
description: Make and edit videos with ultrafast, a GPU video engine where a video is a JSON document. Covers social clips, explainers, titles, captions, lower thirds, charts and data videos, promos, motion graphics, 3D and shader looks, and edits of existing footage, exported as MP4, ProRes or WebM (transparent where needed), GIF, PNG or EXR sequences or sound alone, at any size from 720p to 4K. Use when someone asks for a video, an animation, motion graphics, captions burned into a clip, a GIF, a transparent overlay or an MP4/MOV/WebM export, or when you are changing an ultrafast document (a .json with "version", "format", "nodes" and "output"). Works through the ultrafast MCP tools (names start with ultrafast_) or the `uf` command line.
license: Apache-2.0 OR MIT
compatibility: Needs the ultrafast MCP server (local `uf mcp`, or a remote one over HTTP) or the `uf` CLI on a machine with a Metal or Vulkan GPU.
metadata:
  homepage: https://ultrafast.mov
  docs: https://ultrafast.mov/docs/
  version: "0.2.0"
---

# ultrafast

ultrafast renders video on the GPU from a JSON document: a `format` (size,
fps, duration), `nodes` (each an op with params, inputs and timing) and the
`output` node. You write the document, check it, look at its frames, fix
what `review` finds, then export. Never describe a video you have not
looked at.

## Pick the surface

1. **MCP tools** (`ultrafast_new`, `ultrafast_check`, `ultrafast_sheet`, ...)
   are available: use them.
   - Local server (`uf mcp`): tools take a document `path` on this machine.
     Edit with `ultrafast_edit` or by writing the file; the server reloads it.
   - Remote server (HTTP): tools take the whole `document` inline. Pass the
     document `ultrafast_edit` returns to the next call. Media inside it are
     `asset://` ids or https URLs, never local paths. `ultrafast_export`
     returns a download link.
2. **No tools, but a shell**: run `uf --version`. If it prints a version, use
   the CLI (`uf` and `ultrafast` are the same command).
3. **Neither**: tell the person how to install or connect ultrafast
   ([setup](references/setup.md)). Don't pretend to render.

## The loop

| step | MCP | CLI |
|---|---|---|
| start | `ultrafast_new` (`vertical`, `title`, `square`, `promo`, `explainer`, `product`) or write the JSON | `uf new promo film.json` |
| vocabulary | `ultrafast_ops` (all ops as Markdown), `ultrafast_ops {"ops": ["captions"]}` for full detail | `uf ops --markdown` |
| check | `ultrafast_check` | `uf check film.json` |
| look | `ultrafast_sheet` (whole film), `ultrafast_frame` (one moment) | `uf sheet film.json --count 9 --out sheet.png`, `uf render film.json --at 2.5 --out f.png` |
| find | `ultrafast_inspect` (what is on screen at `t`, and which node) | `uf inspect film.json --at 2.5` |
| change | `ultrafast_edit` (atomic edit batch) | edit the file, or `uf edit film.json edits.json` |
| review | `ultrafast_review` (`safe: "social"` for vertical video) | `uf review film.json --safe social` |
| cost | `ultrafast_estimate` with the export settings (rendered minutes, GPU seconds) | `uf estimate film.json --size 4k` |
| export | `ultrafast_export` (settings below) | `uf export film.json film.mp4 --quality high` |
| many versions | `ultrafast_batch` (one video per row of data) | `uf batch film.json --data rows.csv --out 'out/{name}.mp4'` |

Rules:

- **Read the op before you use it.** Params are exact: look up any op you
  haven't used in this session with `ultrafast_ops` (`ops: [...]`).
- **Check until clean.** Fix every error and warning `check` reports.
- **Look before you speak.** Make a contact sheet after the first draft and
  after every visual change. Compare it with what was asked: words, timing,
  framing, contrast, nothing cut off or empty.
- **Review before export.** Fix every finding and review again until it
  reports none. Each finding names a node, a time span and a fix. If you
  keep one deliberately, say which one and why.
- **Report what you made**: the file or link, size, duration and the review
  result. Show a frame or the sheet when the person can see images.
- **Many variants** (a name, a price, a language per file): make one
  document, review it, then batch it with one row per video, instead of
  writing many documents. Each row sets `node.param` keys (and
  `format.width`, `format.height` for another shape); every row is checked
  before anything renders. Another *resolution* of the same shape is an
  export setting (`size`), not another document.

## Export

The format follows the output's extension; the settings are the same in
`ultrafast_export`, `uf export` flags (`--quality high`) and the HTTP API.

| want | settings |
|---|---|
| a quick look at the motion | `quality: "draft"` (no motion blur, fastest), often with `size: "720p"` |
| the deliverable | the defaults: H.264 MP4, `quality: "standard"` |
| an upload that gets re-encoded (YouTube, social) | `quality: "high"`, and `size: "4k"` when it should be 4K |
| a master for editing or archiving | `.mov` with `codec: "prores"` (`prores_profile: "hq"` by default), `quality: "master"` |
| a transparent overlay for an editor | `.mov`, `codec: "prores"`, `alpha: true` (ProRes 4444) |
| a transparent video for a web page | `.webm`, `alpha: true` (VP9) |
| compositing (Nuke, After Effects) | a PNG or EXR sequence: `out` a folder (`frames/`) or `frames/{frame:05}.exr`, `alpha: true`; the sound lands beside it as `audio.wav` |
| a GIF | `.gif` with `size: "480p"` and `fps: 15` (it gets large fast); `loops: 0` plays once |
| a smaller modern file | `codec: "hevc"`, or `codec: "av1"` (MP4 or WebM) |
| the sound alone | `.wav`, `.mp3`, `.m4a`, `.flac` or `.opus` |

- `size` (`720p`, `1080p`, `1440p`, `4k`, or `WxH` of the same shape) renders
  at that size, sharp; it is not an upscale. `720p` means the short side, so
  a vertical film stays vertical. `scale: 2` doubles it.
- `fps` changes the frame rate; the film plays at the same speed.
- Transparency needs a document without a full-frame background: drop the
  `bg` node (or make it transparent), and check a frame.
- Settings that don't go together (alpha in an MP4, ProRes in an MP4, a GIF
  at 60 fps) are refused before anything renders, with the fix in the
  message.
- Estimate with the same settings first when the render is big:
  `ultrafast_estimate {"size": "4k", "quality": "high"}`.

## The document

```json
{
  "version": 1,
  "format": { "width": 1080, "height": 1920, "fps": 30, "duration": 8,
              "motion_blur": { "samples": 6, "shutter": 0.5 } },
  "nodes": {
    "bg":     { "op": "gradient", "params": { "kind": "radial", "a": "#2b2250", "b": "#0b0a12" } },
    "title":  { "op": "block", "params": { "kind": "title", "kicker": "SATURDAYS", "title": "Learn the wheel" },
                "timing": { "offset": 0.3 } },
    "comp":   { "op": "over", "inputs": { "fg": "title", "bg": "bg" } },
    "finish": { "op": "grain", "inputs": { "source": "comp" }, "params": { "amount": 0.06 } }
  },
  "output": "finish"
}
```

- `nodes` is a map of id to node. A node is `op`, `params`, `inputs` (other
  node ids on named ports) and optional `timing`. `output` names the last
  node.
- Composite with `over` (`fg` over `bg`); effects take a `source`; cut
  between shots with `transition` (`a`, `b`, `at`, `duration`, `kind`).
- Any param can be animated:
  `{"keys": [{"t": 0, "v": 0, "ease": "out_expo"}, {"t": 0.8, "v": 1}]}`,
  `{"wiggle": ...}`, `{"oscillate": ...}`, `{"audio": ...}` or
  `{"expr": "0.5 + 0.5 * sin(t * 3)"}`.
- `timing`: `in`/`out` (when it shows), `offset` (where its time zero sits),
  `speed`, `loop`. Outside its window a node costs nothing.
- Times are seconds; positions and sizes are pixels in the frame; colours
  are hex (`#rrggbb` or `#rrggbbaa`).
- Files (footage, images, fonts, audio, SVG) are relative to the document.

Details: [references/document.md](references/document.md).

## Making it look good

- **Blocks first.** `block` gives a finished, animated `title`,
  `lower_third`, `quote`, `stat`, `chapter`, `end_card`, `bar_chart`,
  `line_chart` or `donut` in one node. Place it in time with
  `timing.offset`, and restyle it with `ink`, `accent`, `display_font` and
  `scale`.
- **Lay out with `stack`**, not hand-computed positions. It measures what it
  holds.
- **Type**: any Google Font by family name; `*word*` in `text` takes the
  `em_` params (colour, font) for accent words. Variable fonts animate their
  axes.
- **Cuts**: `transition` nodes (crossfade, dip, wipe, push, slide, iris,
  zoom, dissolve, glitch, blur), and land them on the beat (`ultrafast_beats`).
- **Finish**: `grain` (0.05 to 0.09) on almost everything; often `bloom`
  and `vignette`; `grade` for footage.
- **Motion**: ease arrivals with `out_expo` or `{"bezier": [0.16, 1, 0.3, 1]}`;
  use `spring` or `out_back` for things that land with weight. Turn on
  `motion_blur` in the format for anything that moves fast.

More patterns, each one checked and reviewed:
[references/recipes.md](references/recipes.md). Whole documents to start
from: [examples/](examples/).

## Footage, sound and captions

- `video` plays footage (`src`, `fit: "cover"`, `start`, `speed`, `rect`);
  `image` shows stills and sequences; `svg` and `lottie` stay vector.
- `clip_camera` turns a landscape talking-head clip into a framed vertical
  one: it tracks faces in the footage and follows the speaker with eased
  pans and cuts (`src`, `start`, `duration`).
- `audio` mixes sound into the export (`src`, `start`, `gain`, `from`).
  Footage plays silent unless an `audio` node uses the same file.
- `captions` animates word timings (`src`: Whisper-style JSON, `.srt` or
  `.vtt`; or inline `words` as lines of `start end word`). Use `style`
  karaoke, pop, reveal or plain. They stay clear of the social apps' buttons
  on vertical frames by default (`safe: "auto"`).
  Over footage, give captions a `background` (e.g. `#000000b0`) or a
  `stroke_outline`, or review will flag them as unreadable.
- `ultrafast_voiceover` speaks a script to WAV and writes word timings for
  `audio` + `captions` (local server).

## Mistakes to avoid

- Blocks use light type by default. On light backgrounds set `ink` (and
  `accent`), or they vanish.
- Long values in a `stat` block, or long labels, run off a vertical frame.
  Keep them short; review catches it.
- Generators (`solid`, `gradient`, `noise`, shaders) fill the whole frame.
  Crop or transform them to make panels.
- On 9:16, keep text out of the bottom 20% and right 12% (the apps'
  buttons). `review` with `safe: "social"` checks this.
- Don't invent params: unknown or misspelled ones are reported by `check`,
  with suggestions.
- Node ids are unique; an edit batch applies all or nothing.

## References

- [references/document.md](references/document.md): the document format in full.
- [references/recipes.md](references/recipes.md): tested patterns (vertical promo, captions over footage, explainer with a chart, beat cuts, voiceover).
- [references/setup.md](references/setup.md): install `uf` and connect Claude Code, Claude Desktop, Codex, Cursor, Gemini CLI or a remote server.
- The full op list comes from `ultrafast_ops` or `uf ops --markdown`. The JSON Schema comes from `uf schema` and is published at https://ultrafast.mov/schema/v1.json.
