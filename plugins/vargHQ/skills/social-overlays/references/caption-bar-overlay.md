# Story caption bar

The full-width translucent caption strip from Snapchat-style stories (white text on a see-through dark bar), plus the "big text" style: large bold free-floating words with an outline. Gives UGC and creator ads a raw, phone-native feel. 9:16 first, also 1:1 and 16:9; about 5 s.

## How the pros do it
- The classic look: white text on a semi-transparent grey/dark bar that stretches the full width; in the app this default bar cannot be resized, only moved up and down [19]. Recreate exactly that: full width, one line, fixed text size, vertical position as the only free variable.
- The second look is free-floating text in a bigger font that can be moved, scaled and rotated, with an optional dark outline (the "Aa" toggle) [19]. Our "big text" preset = large bold centred words with a dark stroke, no bar.
- Snapchat's own font isn't public; Public Sans (OFL) and Arimo (OFL) are close free alternatives [19][41]; Avenir is a commercial match, so don't ship it.
- Snap ad safe zone: keep the top 150 px and bottom 330 px of 1080×1920 clear (382 px with Offer Details) [6]. If the video also goes to TikTok/Reels/Shorts, keep the bar within y 288–1248 [1][4][5].
- Caption craft for Snap Spotlight: ≤ 40 characters per line, 2–3 lines max, contrast ≥ 4.5:1, about 1 s per 5 words, final caption can carry a 5–8-word CTA [20]. The bar style is 1 line, so split longer text into consecutive bars.
- The bar is a "typed by a person" signal: no animated word-by-word karaoke inside the bar; swap whole lines on cuts.
- Snap's ghost logo and the name are Snap's trademarks; their guidelines say to use only the official Ghost logo [18]. Don't add it to the bar.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `caption-bar-overlay.classic` | Full-width bar, black @55% (house), white centred one-line text | bar height 76 px, Public Sans 500 40 px, y default 62% of height |
| `caption-bar-overlay.big-text` | Large bold white words, 4 px black outline, centred, no bar | Arimo 700 or Public Sans 800, 88 px, stroke 4 px #000000, tilt 0° |
| `caption-bar-overlay.classic-multi` | Consecutive one-line bars, one per beat | 1 line per bar, 1 s per 5 words, hard cut swaps |
| `caption-bar-overlay.light-bar` | Light translucent bar with dark text for dark footage | bar #FFFFFF @70% (house), text #000000 |

(55%/70% bar opacities and sizes are house starting values; no source published exact values. Tune against a current app screenshot.)

## Timing and numbers (5 s = 150 f)
- Appear: hard cut in (0 frames), or a 3-frame (0.1 s) fade; the native bar does not fly in. Big text: 0.2 s scale 0.9→1 `power2.out` (house).
- Duration per bar: max(1.2 s, words / 5 s) [20], swap on picture cuts where possible.
- Out: hard cut, or 0.1 s fade.
- Bar geometry at 1080×1920: full width 1080 px, height 76 px (≈4% of height), text 40 px/500, single line, ≤ 40 characters [20]. Default bar centre y = 1190 (62%) when cross-posting; Snap-only can go to y ≤ 1590 [6].
- Contrast check: white on black @55% over mid-grey footage is ≥ 4.5:1 in most frames; raise to 65% on bright footage [20].
- Big text: 80–96 px bold, max 2 lines, line-height 1.1, stroke 4 px (paint-order: stroke fill) [19].
- 16:9: bar full width, 60 px tall, text 32 px, centre y = 78% of height. 1:1: bar 68 px, text 36 px.

## Build it
1. HyperFrames: plain HTML div: `position:absolute; left:0; right:0; height:76px; background:rgba(0,0,0,.55); display:flex; align-items:center; justify-content:center;` Text in `<span>` with `white-space:nowrap`. For multi-bar captions, the `caption-pill-karaoke` component's timing data structure can be reused with karaoke off [40].
2. Swap lines with `tl.set(span, {textContent: line}, t)` (seek-safe `set`), not with timeouts.
3. Big text: `-webkit-text-stroke: 4px #000; paint-order: stroke fill;` check one rendered frame for stroke support; fallback = 8-direction text-shadow 2 px.
4. Remotion: an array of `{from, to, text}` and `frame` comparisons; `<AbsoluteFill>` with the bar.
5. Params: `lines[] {text, from, to}`, `style`, `y`, `font`.

## Mistakes that look amateur
- Bar with rounded corners and margins → native bar is edge to edge [19].
- Two lines in the bar → one line per bar; split text.
- Word-by-word karaoke inside the bar → whole-line swaps.
- Bar in the bottom 330 px of a Snap ad → covered by Snap UI [6].
- Using Snap's actual font file or ghost logo → Public Sans/Arimo, no logo [18][19].
- Text at 28 px to fit a long sentence → shorten to ≤ 40 characters [20].

## Sources
[1] TikTok safe-zone template · [4] Meta Reels specs · [5] Google vertical safe zone · [6] Snapchat Business Help safe zone · [18] Snap brand guidelines · [19] Kapwing: Snapchat text fonts · [20] OpusClip: Snapchat Spotlight captions · [40] HyperFrames registry · [41] Google Fonts licences.
