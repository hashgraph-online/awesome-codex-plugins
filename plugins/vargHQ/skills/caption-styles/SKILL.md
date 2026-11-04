---
name: caption-styles
description: >-
  Seventeen animated caption looks for talking heads, podcasts, ads, lyric and short-form videos
  (karaoke fill, active-word pop and colour, sliding pill, word tiles, frosted glass, neon, serif
  italic, white card, bounce and tilted word cards and more), each with presets in exact numbers: font
  (OFL), size per format, words per screen, active-word timing 1-2 frames before the voice, 9:16 safe
  box, contrast, padding and easing. The rules come from the Netflix and BBC subtitle guides, the DCMP
  Captioning Key, ITU sync tolerances, eye-tracking research and short-form editors. Use when someone
  asks for TikTok, Reels or Shorts captions, word-by-word or highlighted subtitles, karaoke captions,
  or 'captions like Hormozi / MrBeast / podcasts'. NOT for transcription itself (use WhisperX or
  ElevenLabs speech-to-text first), translation, or plain SRT delivery without styling.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. Plain
  looks also burn in with ffmpeg + ASS subtitles (libass). Needs word timestamps (WhisperX, ElevenLabs
  Scribe or any forced aligner). No API key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "burned-in mp4, transparent mov/webm caption layer, or .ass subtitles"
  varg.presets: "17 templates, 52 presets"
---

# Caption styles: 17 looks, built the way the pros set subtitles

Seventeen caption looks with presets you can apply as numbers, not adjectives. Pick how the words are chunked first (a phrase, a group of words or one word at a time), then the look. Every look ships with a plain version that is accessible, since styled word-tracking captions trade some comprehension for attention.

## Gates

- **Word timings first.** Build from word-level timestamps (WhisperX, ElevenLabs Scribe, a forced aligner on the script). Never estimate word times from text length.
- **Chunking before look.** Phrase captions by default; one word at a time only for hooks, punchlines and clips of 20 s or less.
- **Readable on a phone.** Keep text inside the 9:16 safe box and at 4.5:1 contrast against what sits behind it; the shared file has the numbers.
- **Accessible deliverable.** Offer a plain phrase SRT/VTT next to the styled render.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

17 templates, 52 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

Read [`references/_shared-caption-craft.md`](references/_shared-caption-craft.md) first: it holds the numbers every template here shares.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Active word colour captions** | White outlined text, a few words at a time, where only the colour of the spoken word changes: no scale, no box. | Blue outline, Yellow outline, Calm phrase (accessible) | [`active-word-color-captions.md`](references/active-word-color-captions.md) · [`json`](assets/presets/active-word-color-captions.json) |
| **Active word pop captions** | White outlined words where the word being spoken turns blue and pops a little larger, then settles back. | Blue pop, Subtle pop, Spring pop | [`active-word-pop-captions.md`](references/active-word-pop-captions.md) · [`json`](assets/presets/active-word-pop-captions.json) |
| **Bouncing single-word pill** | One uppercase word at a time bounces up inside a coloured pill (purple by default) near the centre of the frame. | Purple spring, Lime spring, Soft rise (no overshoot) | [`bounce-word-pill.md`](references/bounce-word-pill.md) · [`json`](assets/presets/bounce-word-pill.json) |
| **Frosted panel captions** | White text on a blurred, frosted-glass panel; inactive words are dimmed and the spoken word is full white. | Clear glass with dim, Thick glass for bright footage, Light glass | [`frosted-panel-captions.md`](references/frosted-panel-captions.md) · [`json`](assets/presets/frosted-panel-captions.json) |
| **Gradient-fill word captions** | The spoken word fills with a two-colour gradient (blue to pink by default) inside a dark rounded box while the other words stay white. | Blue to pink on dark box, Sunset, Sweep fill | [`gradient-word-captions.md`](references/gradient-word-captions.md) · [`json`](assets/presets/gradient-word-captions.json) |
| **Grow-in highlight box captions** | White words inside a dark rounded box; the spoken word turns yellow and grows into place while the box adjusts its width. | Yellow grow, Green grow, Reveal grow | [`grow-highlight-captions.md`](references/grow-highlight-captions.md) · [`json`](assets/presets/grow-highlight-captions.json) |
| **Karaoke fill captions** | Each word fills with yellow as it is sung or spoken, with a short bar under the current word. | Classic yellow sweep, Two-line preview, Speech (instant fill) | [`karaoke-fill-captions.md`](references/karaoke-fill-captions.md) · [`json`](assets/presets/karaoke-fill-captions.json) |
| **Line-hugging rounded box captions** | Bold dark text on a white box whose rounded corners follow each line's own width, the native look of in-app text on vertical platforms. | White box classic, Black box inverse, Navy pill rise, Brand tint | [`line-hug-box-captions.md`](references/line-hug-box-captions.md) · [`json`](assets/presets/line-hug-box-captions.json) |
| **Neon tube captions** | Words glow like neon tubes (hot pink by default) inside a dark box with a glowing border. | Hot pink, Cyan ice, Pulse only (no flicker) | [`neon-tube-captions.md`](references/neon-tube-captions.md) · [`json`](assets/presets/neon-tube-captions.json) |
| **Outlined spring-word captions** | White words with a thick black outline; the spoken word turns cyan and springs up a few pixels, then settles. | Cyan spring, Gaming condensed, Clean outline | [`outline-spring-captions.md`](references/outline-spring-captions.md) · [`json`](assets/presets/outline-spring-captions.json) |
| **Serif italic emphasis captions** | Large serif text with a soft shadow and no box; the spoken word flips to italic. | Instrument italic, Playfair warm, Fraunces soft | [`serif-italic-captions.md`](references/serif-italic-captions.md) · [`json`](assets/presets/serif-italic-captions.json) |
| **Shadow-only minimal captions** | White text with a soft shadow and no box; the spoken word is just a little brighter than the rest. | Soft shadow, Cinema lower, Bright-footage guard | [`shadow-minimal-captions.md`](references/shadow-minimal-captions.md) · [`json`](assets/presets/shadow-minimal-captions.json) |
| **Sliding pill word tracker** | A coloured pill slides from word to word behind white outlined text, marking the word being spoken while the text stays still. | Electric blue, Brand pill, Soft pill | [`sliding-pill-captions.md`](references/sliding-pill-captions.md) · [`json`](assets/presets/sliding-pill-captions.json) |
| **Tilted card word pops** | One uppercase word at a time springs in on a slightly rotated sticker-like card, alternating white and lime. | White / lime alternating, Sticker with hard shadow, Calm tilt | [`tilted-card-word-pop.md`](references/tilted-card-word-pop.md) · [`json`](assets/presets/tilted-card-word-pop.json) |
| **Translucent box subtitles** | Plain white sentence-case text on a semi-transparent dark box, one phrase or sentence at a time, cut on and cut off with no motion. | Broadcast 16:9, Vertical 9:16, Soft off-black | [`translucent-box-subtitles.md`](references/translucent-box-subtitles.md) · [`json`](assets/presets/translucent-box-subtitles.json) |
| **White card captions** | Dark text on a clean white card with a soft shadow; the spoken word turns a strong blue. | Corporate blue, Warm paper, Vertical card | [`white-card-captions.md`](references/white-card-captions.md) · [`json`](assets/presets/white-card-captions.json) |
| **Word tile captions** | Every word sits on its own dark rounded tile; the spoken word's tile turns orange. | Orange active, Stagger in, Mono tiles | [`word-tile-captions.md`](references/word-tile-captions.md) · [`json`](assets/presets/word-tile-captions.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, after the shared file, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Choose chunking first: phrase (5–12 words), group (2–5), single word only for hooks/punchlines/≤20 s clips (word-for-word: ~90% gaze on text, lower comprehension — Romero-Fresco; Meryl Evans).
2. Active word switches 1–2 frames before audio onset (late noticed from ~45 ms, early unnoticed to ~125 ms — ITU-R BT.1359). Karaoke: line leads 10–20 f (≤1.5 s), fill follows voice (\kf).
3. Per-word motion done within ~6 f at 30 fps; scale via transforms, never font-size.
4. 9:16 safe box: top 288, bottom 672, left 120, right 192 px on 1080x1920; max width 696 px, block centre ~60% height.
5. Contrast ≥4.5:1 against what is behind; black box ≥60% opacity on white footage.
6. Netflix/BBC/DCMP line breaks; 42 cpl 16:9; 2 lines (3 in 9:16); 160–180 wpm; 0.83–7 s per caption; 2-frame gaps.
7. Sentence case; caps only for single-word cards; OFL faces only.
8. Ship a plain phrase version as the accessible deliverable.

## Built from

BBC Subtitle Guidelines; Netflix Timed Text Style Guide; Meryl K. Evans (@merylkevans); DCMP Captioning Key; ITU-R BT.1359; Romero-Fresco; WCAG; X: @wayofzorro, @finnardley, @mws, @yt_igm, @tigerjvideo.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- `remotion-captions`, `iart-caption-animation`, `cinematic-caption-audrey` on varg how to: caption engines these presets can drive.
- [short-form-ffmpeg-cookbook](../short-form-ffmpeg-cookbook/): burn SRT/ASS with ffmpeg.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
- [varg-video-edit-library](../varg-video-edit-library/): 206 named edits for existing footage (cuts, transitions, headlines, UI, numbers).
