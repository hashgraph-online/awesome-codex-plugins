---
name: title-design
description: >-
  Nine title templates with broadcast-grade presets: name and place lower thirds, speaker plates
  (two-line, ticker, caption bar, title card, corner tag), a podcast or show open, headline write-on
  reveals, a channel bumper animated on twos, CRT scanline, chrome echo melt and block-glitch title
  reveals. Presets give hold time from word count, safe areas for 16:9 and 9:16, type scale by frame
  height, tracking, plate opacity and enter/exit easing, from Netflix and BBC timing rules, EBU safe
  areas, Material motion, School of Motion, Art of the Title and the Spider-Verse animators. Use when
  a video needs a lower third, a name or location super, an intro title, a chapter card or a
  glitch/CRT/chrome text reveal. NOT for subtitles (use caption-styles) or logo animation of a brand
  mark.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. No API
  key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "9 templates, 33 presets"
---

# Title design: lower thirds, show opens and title reveals by broadcast rules

Nine title templates that follow broadcast practice: information holds long enough to be read twice, sits inside the safe area, and every effect (CRT, glitch, chrome) is a transition that resolves into clean, readable type.

## Gates

- **Real names and roles.** Lower thirds use the names, titles and places the person gives you; never invent a credential.
- **Hold for two reads.** Use the hold formula in `references/title-craft-basics.md`; do not shorten holds to fit the beat.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

9 templates, 33 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

Read [`references/title-craft-basics.md`](references/title-craft-basics.md) first: it holds the numbers every template here shares.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Block glitch title** | A title that snaps in through a heavy block glitch, crashes, and settles into clean type. | On black, Transparent, Stepped | [`block-glitch-title.md`](references/block-glitch-title.md) · [`json`](assets/presets/block-glitch-title.json) |
| **Chrome echo melt** | A single chrome word that melts into stepped echoes, blurs into a grainy halo and dissolves. | Ice, Chrome, Ember, Toxic | [`chrome-echo-melt.md`](references/chrome-echo-melt.md) · [`json`](assets/presets/chrome-echo-melt.json) |
| **CRT scanline title** | A name and role that crash onto a CRT, then clear to clean type on a transparent frame. | Consumer TV, Arcade monitor, Terminal green | [`crt-scanline-title.md`](references/crt-scanline-title.md) · [`json`](assets/presets/crt-scanline-title.json) |
| **Headline write-on** | A headline that writes on letter by letter, word by word or line by line, then holds. | Display, Editorial, Chapter card, Kinetic | [`headline-write-on.md`](references/headline-write-on.md) · [`json`](assets/presets/headline-write-on.json) |
| **Name lower third** | Identify a speaker (name + role or handle) on first appearance. | Clean, Boxed, Editorial, Handle | [`name-lower-third.md`](references/name-lower-third.md) · [`json`](assets/presets/name-lower-third.json) |
| **Place and date lower third** | State where and when a scene happens: place over coordinates, a date or a local time. | Clean, Boxed, Editorial, Centered | [`place-lower-third.md`](references/place-lower-third.md) · [`json`](assets/presets/place-lower-third.json) |
| **Show open title** | Opening title for a podcast or series: show name on the beat, guest plates typed on a panel, then away. | Standard 10 s, Cold 5 s, Vertical | [`show-open-title.md`](references/show-open-title.md) · [`json`](assets/presets/show-open-title.json) |
| **Speaker plates** | A consistent plate system for talking-head videos: two-line plate, ticker, caption bar, title card, corner tag. | Two-line plate, Ticker, Caption bar, Title card, Corner tag | [`speaker-plates.md`](references/speaker-plates.md) · [`json`](assets/presets/speaker-plates.json) |
| **Stepped channel bumper** | A channel bumper animated on twos: streak panels, a name plate, a topic card with a ghosted wipe. | Classic, Sting 3 s, On threes | [`stepped-channel-bumper.md`](references/stepped-channel-bumper.md) · [`json`](assets/presets/stepped-channel-bumper.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, after the shared file, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Hold for two reads: hold = clamp(2 × max(words × 0.36, chars/20), 3, 7) s.
2. Safe areas: 16:9 graphics-safe 5% per edge, action-safe 3.5%; 9:16 text between 14% top and 35% bottom, 6% sides, clear of the right rail.
3. Enter emphasized-decelerate cubic-bezier(0.05,0.7,0.1,1); exit emphasized-accelerate cubic-bezier(0.3,0,0.8,0.15); exits ~35% shorter (0.45 s in / 0.28 s out).
4. Type by frame height: display 9–14%, chapter 6–8%, lower-third name 4.5–5.5%, role 60–70% of name, nothing under 2%.
5. Caps +0.05–0.12em tracking; display −0.01 to −0.02em; tabular figures for changing numbers.
6. Dark plates ≥60% opacity (default 75–85%); light plates ≥85% with #111 text.
7. On twos = 12 images/s at 24 fps: animate on ones, step with one global quantizer; no motion blur on stepped layers.
8. Effects are transitions; information is the destination — resolve to clean readable type that holds.
9. Digital damage in 8/16 px blocks, bursts 2–4 frames on / 3–8 off, RGB split 6–14 px decaying to 0.
10. Seek-safe: everything a function of timeline time; noise seeded by frame.

## Built from

Netflix Timed Text + BBC; EBU R95; Spider-Verse animators Jeff Panko & Geeta Basantani; Timothy Lottes (crt-lottes); Michelle Dougherty / Imaginary Forces (Art of the Title); Jason Boone (Frame.io); Chris Salters, Joey Korenman, Nol Honig (School of Motion); Material 3; GSAP; X: @jakeinmotion, @tranmautritam, @TheMirzaBeig, @komm64.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [caption-styles](../caption-styles/): subtitles and word captions.
- [kinetic-type-art](../kinetic-type-art/): art-directed type pieces and wordmarks.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
- [varg-video-edit-library](../varg-video-edit-library/): 206 named edits for existing footage (cuts, transitions, headlines, UI, numbers).
