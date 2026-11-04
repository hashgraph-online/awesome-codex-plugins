# Scanned-sheet glitch wordmark

A wordmark printed on a scanned sheet of paper holds still, then breaks up in short bursts of horizontal shear, smear, RGB tear and glyph flips, and settles clean. A 3-5 s logo sting or chapter card. Variants: paper, night, newsprint. 16:9, 9:16, 1:1. Works on rendered type or, with ffmpeg, on footage of a real scan.

## How the pros do it
- Glitch in bursts, not continuously: hold clean, break for a few frames, recover. Distress was added in the transfer and edit, then cut into a staccato rhythm [53].
- Keep the "accidents": the most valued artifacts are the unplanned ones from the physical process, so let some frames look broken, not designed [53].
- Glyph flip glitch: each letter cycles through `_` and two random glyphs over 0.2 s, starting 0.05 s after its neighbour [3].
- Datamosh look = motion vectors applied to old pixels (I-frame dropped, P-frames repeated); fake it with a smear that drags the previous frame along a direction [32].
- RGB split: shift red and blue in opposite directions by a few pixels only on burst frames (registry `rgb-glitch-text`, `scan-band`) [41]; ffmpeg `rgbashift` shifts each channel up to ±255 px [33].
- Paper realism: desaturate, crush levels (about 41/214), add speckle grain and a light 1-2 px blur, horizontal streaks from motion blur [31].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `scan-glitch-wordmark.paper` | Black wordmark on scanned off-white, grey grain | bg #F2EFE8, ink #111111, grain 12%, bursts at 1.0 s, 2.0 s, 2.8 s |
| `scan-glitch-wordmark.night` | Inverted scan (white on black), red/cyan tears | bg #0B0B0D, ink #F2EFE8, split R +8 px / B -8 px |
| `scan-glitch-wordmark.newsprint` | Newsprint grey, halftone, smear-heavy | bg #E9E4D8, ink #1A1A1A, halftone dots 2 px [42], smear 40-120 px |

## Timing and numbers (4 s = 120 f)
- Hold clean 0-30 f. Bursts: 3, each 3-8 f long, separated by 10-20 f of clean hold; last burst ends by 96 f; hold clean 24 f.
- Burst frame recipe (pick per frame from a seeded table): slice shear (4-12 horizontal bands, each offset ±10-80 px), RGB split ±4-12 px, smear (previous frame dragged 40-120 px with 0.6-0.8 opacity), glyph flip on 1-3 letters [3].
- Between burst frames do not interpolate: each frame is a new state (`steps(1)` per frame).
- Wordmark size: 50-70% of frame width (16:9), 80% (9:16); centred on the optical centre (2-4% above geometric centre).
- Grain: 8-15% monochrome, re-seeded every frame on bursts, every 2 f on holds.

## Build it
1. HyperFrames: `rgb-glitch-text` for the RGB copies, `scan-band` for a diagonal tear band, `glitch` block for a shader transition; paper finish from paper-shaders `paper-finish`, halftone from `halftone-overlay` [41][42].
2. Slice shear: render the wordmark N times clipped to horizontal bands (`clip-path: inset()`), translate each band by `seeded(frame, band)` on burst frames.
3. Glyph flips: per letter, replace text content on burst frames from a fixed glyph table indexed by (frame, letter, seed) [3].
4. ffmpeg for footage of a printed scan (example burst at 1.0-1.2 s):
   `-vf "format=rgb24,rgbashift=rh=8:bh=-8:enable='between(t,1.0,1.2)',tmix=frames=3:weights='1 1 2':enable='between(t,1.0,1.2)',noise=alls=12:allf=t+u,eq=contrast=1.3"` (rgbashift range ±255, tmix default 3 frames, noise strength 0-100 with temporal+uniform flags [33]).
5. A real datamosh (drop I-frames between two clips) is possible but not frame-deterministic in all players; render it once and treat it as footage [32].

## Mistakes that look amateur
- Constant glitching → no clean read of the mark; hold 70%+ of the time clean.
- Smooth tweened jitter → glitch is discrete; one state per frame.
- Huge RGB offsets on every frame → keep ±4-12 px except one hero frame.
- Glitch that ends dirty → final 0.8 s must be clean and still.
- Pristine vector edges on a "scan" → add grain, levels crush and slight blur [31].
- Wall-clock randomness → seed by frame index.

## Sources
[3] @jh3yy, glitch flip — https://x.com/jh3yy/status/1762979019446698310 — 0.2 s per letter, 0.05 s stagger
[31] Envato Tuts+, photocopy textures — https://design.tutsplus.com/tutorials/how-to-create-photocopy-and-xerox-textures--cms-109034
[32] Parker Higgins, datamoshing — https://parkerhiggins.net/2017/07/making-mosh-ups-automated-datamoshing-from-multiple-video-sources/
[33] FFmpeg filters — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, tmix, noise
[41] HyperFrames registry — https://github.com/heygen-com/hyperframes/tree/main/registry — rgb-glitch-text, scan-band, glitch
[42] varg paper-shaders — https://github.com/vargHQ/skills/tree/main/paper-shaders — paper-finish, halftone-overlay
[53] Art of the Title, Se7en — https://www.artofthetitle.com/title/se7en/ — transfer distress, accidents, staccato edit
