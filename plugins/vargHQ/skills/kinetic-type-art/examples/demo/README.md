# kinetic-type-art preview

A 15.5 s HyperFrames film (1920x1080, 30 fps, silent) that cuts through four templates of the skill on one 120 BPM grid: 1 beat = 0.5 s = 15 frames, and every scene starts and ends on a beat. A small label in the bottom-left corner names the template and preset on screen.

| # | Time | Beats | Preset | Shows |
|---|---|---|---|---|
| 1 | 0.0–3.0 s | 6 | `typeface-strobe.frames` | "TYPE" through nine OFL faces with a fixed baseline and the same cap height in every face. Frames 0–5 show the anchor (Anton). Then comes the preset's strobe mix, 3 f x 6, 2 f x 12 and 3 f x 4 (54 f), with wide/narrow and serif/sans faces alternating. It lands on the anchor on frame 60 (beat 4) and holds it for 30 f. The background stays black the whole time |
| 2 | 3.0–7.0 s | 8 | `red-beat-words.slam` + `.punch` + `.invert` | six Anton words on #E4002B, each a hard cut on frame 0 of its beat. Each word punches from 112% to 100% in 3 f (`expo.out`) with a ±1.5° rotation that alternates. An 8 px shake decays over 4 f. Word 4 (beat 4) inverts to red on white. The last word holds for 2 beats over a 14 px black bar |
| 3 | 7.0–11.0 s | 8 | `word-corridor.night` | "DEEPER" in real text on four CSS 3D walls, with perspective 450 px. Each wall is 5x the frame width deep. Cap height is 60% of the wall, tracking +0.05em and the gap 0.6em. The words travel one word pitch per beat (linear) and double speed for the 2-beat drop. Fog starts at 60% of the depth, and the far end glows #FF5A1F at 30%. The scene fades in from the background over 15 f, then match-cuts on beat 6 to the flat word and holds for 30 f |
| 4 | 11.0–15.5 s | 9 | `photocopy-explainer.zine` (explainer timings) | a question card, then a number grid, then an answer stamp, in the two riso inks #3255A4 and #FF48B0 (multiply, with pink misregistered by 2 px) on #F4F1EA paper. Cards slide in over 12 f (`power3.out`) with 0.5–1.5° of rotation and a 4 px shadow. The highlighter takes 15 f (`power2.inOut`), grid cells fill one every 2 f, and the stamp lands in 4 f (1.3 to 1, `back.out(2)`) with a 2 f smear. Toner jitter of ±1 px every 2 f comes with ±3% flicker, plus one copier band of 21 f at 15%. Seeded speckle grain runs on top, and the type stays sharp |

The values come from `assets/presets/*.json` and from the "Timing and numbers" section of each reference: BPM, frames per face and word, cap-height ranges, fit widths, hexes, perspective, depth, fog, eases and frame counts. Every swap is computed from absolute beat time (`round(i * 15)`), never by adding rounded frames.

## Render

```bash
cd kinetic-type-art/examples/demo
npx --yes hyperframes@0.8.206 check
npx --yes hyperframes@0.8.206 snapshot --at 1,4.6,8.6,14.9
npx --yes hyperframes@0.8.206 render --fps 30 --crf 22 --output kinetic-type-art.mp4
```

HyperFrames needs Node 22 and ffmpeg. The render takes about a minute on a laptop and writes a file of about 6 MB.

## Deviations and notes

- **Strobe cap height.** The preset allows a cap height of 28–35% of the frame. The demo targets 30% and lowers it only if the widest face (Michroma or Rubik Mono One) would leave the 86% width box, so that all nine faces keep the same cap height. Blackletter and script are set in title case ("Type"), because all-caps Fraktur does not read.
- **Strobe lead-in.** Frames 0–5 hold the anchor so that the 54 f strobe lands exactly on beat 4. The preset does not specify a lead-in.
- **Red slam palette.** The scene combines three presets: the slam palette and size, the punch motion and the invert accent. The black accent bar sits under the last word only.
- **Corridor length.** The reference describes a 7 s piece. Here it is cut to 4 s (8 beats), with the drop moved to beats 3–4 and the flat-word hold set to 30 f (the reference allows 20–30 f; the JSON default is 24 f), so that the cut lands on the beat. The corridor uses the paper preset's base values (Anton caps, depth 5x, 0.6em gap, 60% cap) with the night overrides.
- **Zine piece.** The scene uses the `explainer` preset's card, grid and stamp timings with the `zine` preset's inks and paper. The paper fibre comes from an SVG `feTurbulence` filter and the speckle from seeded canvas noise, both in place of the paper-shaders `paper-finish` texture. The 17 px corner label is under the 28 px reading floor on purpose: it is a quiet credit, not reading text.
- **Photosensitivity.** In the strobe, only the type changes. The background never flashes.

## Credits

All type and shapes are drawn in code. The words and the question are invented, and no footage, music, logos or real publications are used. The fonts are all under the SIL Open Font License and are kept as small `.woff2` files in `assets/fonts/`: Anton, Bodoni Moda, UnifrakturMaguntia, Big Shoulders Stencil, Alfa Slab One, Michroma, Monoton, Rubik Mono One and Pacifico. HyperFrames bundles Inter, Space Mono and JetBrains Mono.
