# title-design preview

A 16 s HyperFrames film (1920x1080, 30 fps, silent) that plays four title presets one after another over a calm, graded backdrop drawn in code: a defocused teal and amber "studio" with drifting bokeh and a slow push-in. All four share one system (Inter, a single #FFD23F accent and the #0E0F12 plate). A small label in the top-right corner names the preset on screen.

| # | Time | Preset | Shows |
|---|---|---|---|
| 1 | 0–4 s | `headline-write-on.display` | "The Quiet Hour": Inter 800 at 130 px (12% H), −0.02em. Characters rise from y 60% with opacity over 0.55 s `expo.out`, staggered 0.04 s from 0.2 s, then drop out with `power2.in` (0.3 s, stagger 0.02 s) |
| 2 | 4–8 s | `name-lower-third.boxed` | "Mara Lindqvist / Head of Research, Lumen Labs" at x 144 with the block bottom at y 945. A #0E0F12 α 0.85 name bar wipes in over 0.45 s `cubic-bezier(0.05,0.7,0.1,1)`, with the text +0.1 s and the #FFD23F role bar +0.12 s. Padding is 18/28 px, the name is 54 px and the role 32 px. Everything leaves together in 0.28 s `cubic-bezier(0.3,0,0.8,0.15)` |
| 3 | 8–12 s | `block-glitch-title.transparent` | "CLEAR SIGNAL" in JetBrains Mono 800 caps at 130 px, +0.04em, #F5F5F5. Two lone-band flickers (frames 4 and 9) lead into the heavy section (0.4–1.3 s): bursts of 2–4 f on and 3–8 f off, 3–7 shifted bands of 16/32/48/64 px moved ±24–160 px, an RGB split of 4–10 px in #FF0040 / #00E5FF, and one frame of 8 px noise cells. A 2-frame crash follows, then a 12 f settle (split 6 → 0, `expo.out`, residual bands at 1.50 and 1.63 s), a clean hold with one micro-glitch, and a 3-frame exit burst. Every value comes from `mulberry32(seed + frame)` |
| 4 | 12–16 s | `speaker-plates.ticker` + `speaker-plates.corner-tag` | A ticker bar 70 px high (6.5% H) on the 5% graphics-safe line, 96 px from each side, with an 18% #FFD23F label block and a #0E0F12 α 0.9 text area. The bar wipes in over 0.4 s and the Inter 38 px crawl runs linearly at 420 px/s. The corner tag sits at x 96, y 54: Inter 600 24 px caps, +0.08em, α 0.9, in over 0.4 s |

## Render

```bash
cd title-design/examples/demo
npx --yes hyperframes@0.8.206 check
npx --yes hyperframes@0.8.206 snapshot --at 2.5,6,9.4,14
npx --yes hyperframes@0.8.206 render --fps 30 --crf 20 --output title-design.mp4
```

HyperFrames needs Node 22 and ffmpeg. The render takes about 30 s and writes a file of about 1.4 MB.

## Deviations and notes

- **Holds are shortened to fit a 16 s card.** The lower third holds for 3.05 s, the 3 s minimum, where the skill's formula gives about 5 s for this name and role. The glitch title holds clean for 1.8 s in a 3.7 s run instead of 6 s, so the phases shift: the exit burst is at 3.6 s, not 5.5 s. The headline hold of 2.1 s meets its 1.8 s minimum. Use the full holds in real work.
- **Glitch font.** The block-glitch preset JSON names Space Grotesk 700. The reference allows JetBrains Mono 800, which HyperFrames bundles, so the demo uses that and needs no font file.
- **Transparent variant over a backdrop.** The preset is meant for alpha output over footage. Here it plays over the drawn backdrop, which follows the same rules: bands and noise stay inside the type's box + 15%, and there is no full-frame invert.
- **Ticker start.** The crawl is already running when the bar wipes in, with its head at 30% of the text area, so a 4 s look shows a full ticker. Its speed stays a constant 420 px/s.
- **Lower-third role font.** The `boxed` preset gives sizes but no faces. The demo uses Inter 700 for the name and Inter 600 for the role, as in `clean`.
- All names, the show, "Lumen Labs" and "Northwind" are invented.

## Credits

All imagery is drawn in code (CSS gradients). No footage, music or logos are used. Fonts: Inter and JetBrains Mono, both under the SIL Open Font License.
