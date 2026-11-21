---
name: kinetic-type-art
description: >-
  Seventeen art-directed kinetic typography templates with exact presets: typeface strobe (one word
  through nine faces), one-word-per-beat slams, word corridor tunnel, perspective photo wall, type
  specimen grid, justified manifesto, Didone city title, scanned-sheet glitch wordmark, hyphen bridge
  wordmark, CRT decrypt, particle burst, anime command screen, photocopy explainer, echo stack over a
  halftone portrait, glyph-tracking terminal camera, bitten word and liquid art reveal. Presets cover
  beat maths (frames per beat), letter-spacing, free font pairings for Didone, condensed, grotesk and
  mono looks, riso and paper palettes in hex, 3D camera values and seeded glitch timing, from Art of
  the Title, Practical Typography, Fonts In Use and motion designers on X. Use when someone wants a
  kinetic type intro, a manifesto or lyric-style type piece, a wordmark animation or a typographic
  poster in motion. NOT for subtitles (caption-styles) or broadcast lower thirds (title-design).
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
  varg.presets: "17 templates, 54 presets"
---

# Kinetic type art: 17 art-directed typography pieces on the beat

Seventeen typography pieces where type is the picture. They share one craft: cut on the beat, hold between beats, space letters like a typographer, and keep every glitch discrete and seeded so it renders the same twice.

## Gates

- **Technique, not someone's work.** Named designers and title sequences are cited for technique; never reproduce an artist's drawings, a film's title card or a brand's wordmark.
- **Readability ceiling.** At most 20 characters per second on screen; one word per beat is safe up to about 180 BPM.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

17 templates, 54 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

Read [`references/shared-type-craft.md`](references/shared-type-craft.md) first: it holds the numbers every template here shares.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Anime command screen title** | A compressed serif title card inside a fictional command screen with counters, glow and scanlines | Alert, Monitor, Title card only | [`anime-command-screen.md`](references/anime-command-screen.md) · [`json`](assets/presets/anime-command-screen.json) |
| **Bitten word title** | A word eaten letter by letter, one scalloped bite per beat | Lemon, Orange, Lime, Strawberry | [`bitten-word-title.md`](references/bitten-word-title.md) · [`json`](assets/presets/bitten-word-title.json) |
| **CRT decrypt title** | Two rows of glowing type decrypt on a side-angle CRT among dim labels | Amber, Green, Serif | [`crt-decrypt-title.md`](references/crt-decrypt-title.md) · [`json`](assets/presets/crt-decrypt-title.json) |
| **Didone city title** | Two-word place name in traced Didone caps that holds, then springs wide | Ink, Night, Big stretch | [`didone-city-title.md`](references/didone-city-title.md) · [`json`](assets/presets/didone-city-title.json) |
| **Echo stack over halftone portrait** | Two words in stacked echoes over a dot-screened portrait, torn away to a moire contour face | Mono, Riso, Night | [`echo-halftone-portrait.md`](references/echo-halftone-portrait.md) · [`json`](assets/presets/echo-halftone-portrait.json) |
| **Glyph-tracking terminal camera** | A virtual camera tracks the newest glyphs of an agent terminal across beat-timed shots | Dark, Light, Tilt | [`glyph-tracking-terminal.md`](references/glyph-tracking-terminal.md) · [`json`](assets/presets/glyph-tracking-terminal.json) |
| **Hyphen bridge wordmark** | Two words joined by a hyphen that grows, stands up and shrinks back | Paper, Night, Riso | [`hyphen-bridge-wordmark.md`](references/hyphen-bridge-wordmark.md) · [`json`](assets/presets/hyphen-bridge-wordmark.json) |
| **Justified manifesto column** | A manifesto set word by word into one justified column, photos opening in gaps | Dark, Light, Caps poster | [`justified-manifesto.md`](references/justified-manifesto.md) · [`json`](assets/presets/justified-manifesto.json) |
| **Liquid artwork reveal** | An artwork appears through a liquid distortion that settles, then the title resolves | Ripple, Marble, Reeded glass | [`liquid-art-reveal.md`](references/liquid-art-reveal.md) · [`json`](assets/presets/liquid-art-reveal.json) |
| **Dot-burst particle title** | Typed titles where dots gather into one and burst into a coloured particle field | Meadow, Evening, Monochrome, Electric | [`particle-burst-title.md`](references/particle-burst-title.md) · [`json`](assets/presets/particle-burst-title.json) |
| **Perspective photo wall** | Masonry wall of photos and captions tilted back, sliding toward camera in a seamless loop | Gallery, Night, Floor | [`perspective-photo-wall.md`](references/perspective-photo-wall.md) · [`json`](assets/presets/perspective-photo-wall.json) |
| **Photocopy explainer** | Explainer graphics in photocopied paper and toner: question to number grid, or a clipping under a highlighter | Explainer, Article, Riso zine | [`photocopy-explainer.md`](references/photocopy-explainer.md) · [`json`](assets/presets/photocopy-explainer.json) |
| **One-word-per-beat red slam** | Big condensed words, one per beat, full frame on red | Slam, Punch, Riso, Invert accent | [`red-beat-words.md`](references/red-beat-words.md) · [`json`](assets/presets/red-beat-words.json) |
| **Scanned-sheet glitch wordmark** | A wordmark on a scanned sheet that holds, breaks up in short glitch bursts, and settles clean | Paper, Night, Newsprint | [`scan-glitch-wordmark.md`](references/scan-glitch-wordmark.md) · [`json`](assets/presets/scan-glitch-wordmark.json) |
| **Type specimen grid** | One word set many ways on a ruled Swiss grid, intercut with photos | Swiss, Riso, Serif waterfall | [`type-specimen-grid.md`](references/type-specimen-grid.md) · [`json`](assets/presets/type-specimen-grid.json) |
| **Typeface strobe** | One word cut through many typefaces on a fast beat, landing on the brand face | Per beat, Strobe, Colour pairs | [`typeface-strobe.md`](references/typeface-strobe.md) · [`json`](assets/presets/typeface-strobe.json) |
| **Repeating word corridor** | A word repeated on four walls of a corridor rushing toward camera | Paper, Night, Riso | [`word-corridor.md`](references/word-corridor.md) · [`json`](assets/presets/word-corridor.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, after the shared file, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Beat lock: frames per beat = 60/BPM × fps; tempos landing on whole frames at 30 fps: 90, 100, 120, 150 BPM; compute events from absolute time.
2. Cut on the beat, hold between: swaps are hard cuts on frame 0 of a beat; moves start 1–2 frames early; end on a 1–1.5 s hold.
3. Readability ceiling 20 characters/s; one word per beat safe to ~180 BPM.
4. Caps +0.05 to +0.12em; never letterspace lowercase; condensed slam caps 0 to +0.02em.
5. Glitch/decrypt discrete and seeded from (frame, glyph, seed); bursts 3–8 frames inside long clean holds; letter flips 0.2 s, 0.05 s stagger.
6. Real 3D CSS and real text for depth: perspective on the scene, linear travel for tunnels/walls.
7. Anime title cards: heavy Mincho serif squeezed to 0.55–0.75 width, not a condensed font.
8. Didones only big, at the large optical size.
9. Riso: #FF48B0, #3255A4, #FFE800 multiply, 1–3 px misregistration. Photocopy: desaturate, Levels 41/214, speckle grain, 1.7 px blur, horizontal streaks.
10. Screens serve the message: one huge title, one visual system, counters change on story beats.

## Built from

Tom Kan (Art of the Title) + Fonts In Use; Matthew Butterick (Practical Typography); Jhey Tompkins (@jh3yy); Peiran Tan; John LePore & David Sheldon-Hicks (Pushing Pixels); Kyle Cooper (Se7en); crt-pi; Envato Tuts+; @natAndrewson, @_chenglou, @ilovetypography.

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [title-design](../title-design/): lower thirds, show opens, CRT and glitch title reveals.
- [motion-formats](../motion-formats/): kinetic lyric video and wave wordmark formats.
- [paper-shaders](../paper-shaders/): paper, halftone and grain backgrounds.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
