# caption-styles preview

A 15.6 s HyperFrames film (1920x1080, 30 fps, silent) that plays four caption looks one after another on the same invented line, *"Say less, show more, let it breathe."*. Each look runs for 3.9 s inside a centred 9:16 panel over a calm sunrise backdrop that is drawn in code. A small label in the bottom-left corner names the preset on screen.

| # | Time | Preset | Shows |
|---|---|---|---|
| 1 | 0.0–3.9 s | `karaoke-fill-captions.classic-yellow` | line mode: each page goes up 15 f before its first word, the yellow sweep follows each word's duration (starts onset −1 f), and the underline slides 4 f between words on a line and jumps between lines |
| 2 | 3.9–7.8 s | `sliding-pill-captions.electric-blue` | one #1F5BFF pill slides 5 f between words on a line; it jumps in 2 f after a word shorter than 6 f ("let"), and fades out and scales back in (0.8 to 1) across a line change |
| 3 | 7.8–11.7 s | `active-word-pop-captions.blue-pop` | the active word turns #4DA3FF and pops 1 → 1.12 (4 f, `back.out(1.7)`), settles to 1.06 (4 f), and releases to 1.0 (3 f) at the next onset |
| 4 | 11.7–15.6 s | `frosted-panel-captions.clear-dim` | the glass comes in over 8 f (opacity, scale 0.96 → 1, blur 0 → 20 px). It resizes in 6 f between pages, and the active word goes from 70% to 100% with a glow in 2 f |

Fonts, sizes, strokes, colours, padding, radii, eases and frame counts are taken from `assets/presets/*.json` and the "Timing and numbers" section of each reference: Poppins 800 at 84 px, Montserrat 900 at 84 and 88 px, and Inter 700 at 80 px. All of them are OFL and bundled with HyperFrames.

## Render

```bash
cd caption-styles/examples/demo
npx --yes hyperframes@0.8.206 check
npx --yes hyperframes@0.8.206 snapshot --at 1.5,5.2,10,13.3
npx --yes hyperframes@0.8.206 render --fps 30 --crf 20 --output caption-styles.mp4
```

HyperFrames needs Node 22 and ffmpeg. The render takes about 35 s on a laptop and writes a file of about 0.9 MB.

## Deviations and notes

- **9:16 inside 16:9.** The captions are laid out on a real 1080x1920 stage that is scaled to 50% into a 540x960 panel in the middle of the 16:9 frame. Every px value is applied on the 1080x1920 stage, so the panel shows exactly what a vertical render would show, at half size.
- **Word timings are illustrative.** There is no audio. The seven word times in `index.html` (`WORDS`) are set by hand at about 150 wpm, with a comma pause and a longer pause between the two pages. Real captions must come from word timestamps (see the skill's gates).
- **Paging.** Group looks use two pages, "Say less, / show more," and "let it breathe.". Each page goes up on onset −1 f and leaves 2 f before the next one. The karaoke look shows the same two pages as lines, each going up 15 f ahead of the voice.
- **Lyric marker.** The karaoke preset names a `♫` marker for sung lines. It is left out so that all four looks show the identical line.
- **Frosted panel width.** The preset's `max_width_px` is 760, which is wider than the shared 9:16 centred maximum of 696 px (safe box x 120–888). The demo keeps the glass inside 696 px, so the text column is 600 px.
- **Look length.** Each look is shown for 3.9 s to fit four looks into one short card. That is shorter than a real caption track and is not a timing recommendation.

## Credits

All imagery is drawn in code (SVG gradients). The line is invented and no footage, music or logos are used. Fonts: Poppins, Montserrat, Inter and JetBrains Mono, all under the SIL Open Font License.
