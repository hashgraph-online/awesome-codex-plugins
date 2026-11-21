<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Btike/bulk-bg-remove/main/assets/logo-dark.svg">
    <img src="https://raw.githubusercontent.com/Btike/bulk-bg-remove/main/assets/logo-light.svg" width="200" alt="bulk-bg-remove logo: a pixel-art monitor showing a green vase with a pink tulip on a transparency checkerboard">
  </picture>
</p>

<h1 align="center">bulk-bg-remove</h1>

<p align="center"><em>Every photo in the folder. No background. Nothing leaves your machine.</em></p>

<p align="center">
  <img alt="works with" src="https://img.shields.io/badge/works%20with-Claude%20Code%20·%20Codex%20·%20any%20agent-0d1117?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0d1117?style=flat-square">
  <a href="https://pypi.org/project/bulk-bg-remove/"><img alt="PyPI" src="https://img.shields.io/pypi/v/bulk-bg-remove?style=flat-square&color=0d1117&label=pypi"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Btike/bulk-bg-remove/main/assets/demo.webp" width="880" alt="Demo: an agent is asked to remove the background from every photo in a folder; a bottle of olive oil loses its background, a reviewer catches background left by a cat's ear and keeps the redone cut-out, the products switch between white, mint and rose backgrounds and land in an online store">
</p>

<p align="center"><strong>Other skills run a model. This one checks every cut-out and redoes the bad ones.</strong></p>

<p align="center">
  <strong>11 models benchmarked on 80 hard images, judged blind at zoom.</strong><br>
  The default scored <strong>8.6/10 on real product catalogue photos</strong>, the best of the 11, at <strong>3.2 s per photo</strong> on a laptop CPU.<br>
  <sub>Apple M5, CPU only, one worker. Method, every score and the RAM numbers: <a href="https://github.com/Btike/bulk-bg-remove/blob/main/BENCHMARK.md">BENCHMARK.md</a>.</sub>
</p>

## What it is

An agent skill plus the engine behind it. Ask your coding agent to *"remove the
background from every photo in this folder"* and it:

1. installs the engine (one `uv tool install`, ~500 MB with Python),
2. checks your machine (free RAM, formats) and plans the run,
3. looks at a sample, picks the best model that fits your free RAM (BiRefNet when there is
   room), and cuts out every image in a queue or in parallel depending on RAM and CPU,
4. has a second agent, with fresh eyes, review the cut-outs on black and on white,
   redo the bad ones with a better setting and keep whichever version is better
   (clean product shots that pass a strict chroma-key check skip this review),
5. tells you what worked, what failed and why.

Output goes to a new `<name>-no-bg/` folder next to the input. Originals are never
touched, and the subject's pixels are copied bit for bit: only the alpha channel is new.

Selling online? `--shop` puts every product on white, square, 2000 px and ready to
upload; `--background "#E6F6EA"` uses your brand colour instead.

<p align="center">
  <img src="https://raw.githubusercontent.com/Btike/bulk-bg-remove/main/assets/showcase.webp" width="880" alt="Four before-and-after pairs: three friends by train tracks, a black camera on black, a bottle of olive oil, and a white bicycle against a wall, each cut out onto a transparency checkerboard">
</p>

Reads JPG, PNG, HEIC, WebP, AVIF, TIFF and BMP (by content, not extension), follows
EXIF rotation, and handles CMYK, 16-bit and 45 MP photos.

## Install

Any agent ([skills CLI](https://github.com/vercel-labs/skills), needs Node.js 22.20 or newer):

```bash
npx skills add Btike/bulk-bg-remove
```

<details>
<summary>Claude Code</summary>

```
/plugin marketplace add Btike/bulk-bg-remove
```
```
/plugin install bulk-bg-remove@bulk-bg-remove
```
</details>

<details>
<summary>Codex</summary>

```bash
codex plugin marketplace add Btike/bulk-bg-remove
codex plugin add bulk-bg-remove@bulk-bg-remove
```
</details>

<details>
<summary>Just the command, no agent</summary>

```bash
uv tool install bulk-bg-remove
bulk-bg-remove ~/Pictures/products          # → ~/Pictures/products-no-bg/
bulk-bg-remove                              # opens a drag-and-drop page in your browser
```
</details>

## Use it in your browser

No agent needed: the engine has a local page for people.

```bash
uvx bulk-bg-remove                          # or `bulk-bg-remove` once installed
bulk-bg-remove ~/Pictures/products --ui     # open it with a folder already loaded
```

Drop photos or a folder (or type a path), pick a model and press **Start**. You watch each
photo go from the queue to its own progress bar, then the results split into **Passed**
(the automatic check proved the cut-out clean), **Check by eye** and **Failed**. Open any
result to compare it with the original on black, white or a checkerboard, zoom in on the
edges, and **Try again** with other settings if it needs it.

The page runs on `127.0.0.1` only and nothing is uploaded. Press Ctrl+C in the terminal to
stop it; `--no-browser` prints the address instead of opening it.

## Which model it picks

You do not choose: the agent looks at a few of your photos, tells the engine
what kind they are, and the engine takes the best model for that kind that
fits in your free RAM. Scores are from a [blind-judged benchmark](https://github.com/Btike/bulk-bg-remove/blob/main/BENCHMARK.md) (0–10):

| Your photos | Best model | With little RAM (~4 GB free) |
|---|---|---|
| Products, objects | `birefnet-general-lite` 8.6 | `silueta` 8.1, used on its own |
| Hair, fur, plants, wires | `birefnet-general` 7.6 | `silueta` 5.2, only if you say yes |
| People | `birefnet-general` 7.8 | `silueta` 5.8, only if you say yes |
| Busy scenes | `birefnet-general` 6.3 | `silueta` 4.0, only if you say yes |
| Drawings, anime | `isnet-anime` 9.0 | needs ~5 GB free |

## Options

| Flag | What it does |
|---|---|
| `--profile uniform\|complex\|people\|scene\|drawing` | what the photos are; the model follows |
| `--model NAME` | force a model instead of `auto` |
| `--format webp\|jpg` | smaller lossless files (PNG by default); JPEG only with a background |
| `--shop` | ready for a shop: white, square, product filling ~85%, 2000 px, JPEG |
| `--background white\|#RRGGBB` | a solid colour behind the subject |
| `--square` · `--pad PCT` · `--size PX` | square canvas · margin around the subject · longest side |
| `--clean-edges` | remove the old background's colour halo from hair and fur edges |
| `--fast-edges` | skip edge matting: faster, coarser hair |
| `--review-sheets` | sheets and close-ups for reviewing the cut-outs that need it |
| `--review-all` | with `--review-sheets`: also sheet the ones the chroma-key check certified |
| `--only FILE` | redo just some images, keeping their output names |
| `--max-megapixels MP` | leave larger photos for another run (short on RAM) |
| `--dry-run --json` | scan and plan only; one JSON event per line for agents |
| `doctor` | check the machine, and what `auto` would pick right now |

## Requirements

- Tested on macOS (Apple silicon), Linux and Windows, with a real-model run on each in CI
  (Python 3.11–3.13). Runs on the CPU. GPU support (CUDA, DirectML) is planned; installing
  `onnxruntime-gpu` by hand is not supported.
- **3.5 GB of free RAM** is enough for product photos: the engine picks the best
  model that fits (about 12 GB gets the best ones). For hair, fur and plants a
  light model is clearly worse, so the agent asks before using one.
- The first run downloads about 350 MB (the engine, ~125 MB, and the default model, ~225 MB)
  and takes about 700 MB on disk. After that everything runs offline.

## Help wanted

Early project, one maintainer. These would help most:

- **A GPU to test on.** It runs on the CPU today. GPU support is planned: NVIDIA (CUDA) on
  Linux and Windows, any card on Windows (DirectML), picked automatically with a fall-back to
  the CPU. If you have one and can run a few commands, open an issue.
- **Cut-outs that came out wrong.** Use the
  [Bad cut-out](https://github.com/Btike/bulk-bg-remove/issues/new/choose) form; hard cases
  you are allowed to share can join the public benchmark.
- **Other agents.** Tried it in Cursor, Gemini CLI or another agent? Say how it went
  (the Agent / skill behaviour form).

Planned, in rough order: a retouch brush in the viewer (erase or restore by hand without
touching the subject's pixels), a smaller install (edge matting without numba, about 150 MB
less on disk), GPU support, and certifying more photos automatically (shadows, busy
backgrounds), only once it is measured never to pass a bad cut-out. See
[CONTRIBUTING.md](https://github.com/Btike/bulk-bg-remove/blob/main/CONTRIBUTING.md) to
send code.

## Credits

Built on [rembg](https://github.com/danielgatis/rembg) and
[BiRefNet](https://github.com/ZhengPeng7/BiRefNet). Showcase and demo photos (CC0, via
Wikimedia Commons): Priscilla Du Preez, Dennis Klein, margenauer, Natasza Remesz,
Mona Magnussen, Tiko Giorgadze, Dmitry Ratushny. The demo film is drawn in code (GSAP, rendered frame by
frame in headless Chromium) from the engine's real output.

Built with Claude Code as a coding partner; the design, the benchmark runs and every
number in this README and in BENCHMARK.md were checked by the author.

## License

MIT — see [LICENSE](https://github.com/Btike/bulk-bg-remove/blob/main/LICENSE).
