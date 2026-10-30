# Photo wall loop

A wall of photo or screenshot cards in columns that scroll at different speeds (alternating directions optional) and loop without a seam: UGC wall, "wall of love", customer photos, creator portfolio, product range. Vertical, square and landscape; about 16 s, designed to loop.

## How the pros do it
- Loop by math, not by luck: GSAP's seamless-loop helpers move each item to the wrap point and re-enter it from the opposite side, using percentages so it survives size changes; there is a vertical version (`verticalLoop`, yPercent/offsetTop/paddingBottom) [29]. Its default speed is ~100 px/s at `speed: 1` [29].
- For a video that must loop end-to-start, choose each column's speed so it travels a whole number of set heights in the clip length: `speed_px_s = k × H / D` (H = one set of cards incl. gaps, D = duration, k = 1, 2, 3…). Then frame 0 equals frame D exactly.
- Different speeds per column create depth: e.g. k = 1, 2, 1 for three columns; reversing the middle column reads as "wall in motion" (opposing marquee).
- Cards should be the people's real photos/screenshots used with permission; if they are customer reviews or posts, the FTC rule on fake reviews and testimonials applies [21].
- In 9:16 the wall can run behind platform UI because it is texture, but the headline or CTA on top must be inside the universal box (x 120–888, y 288–1248) [1][4][5].
- Keep text on top readable: put a 40–60% dark scrim or a blurred band behind the headline; contrast ≥ 4.5:1 for normal text [42].
- On-screen text speed limit still applies to any words placed over the wall: 5–10 words/s [3].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `photo-wall-loop.three-column` | 3 columns, k = 1/2/1, all upward | 9:16, card 300×400 px, gap 20 px, radius 24 px |
| `photo-wall-loop.opposing` | Middle column runs down, outer up | k = 1/−1/1, card 300×420 |
| `photo-wall-loop.tilted` | Whole wall rotated −12° with perspective, 4 columns | rotateZ −12°, scale 1.25 to cover corners, perspective 1600 px |
| `photo-wall-loop.landscape-rows` | 16:9 rows moving horizontally, alternating | 3 rows, card 420×300, k = 1/2/1 |

## Timing and numbers (16 s = 480 f)
- Default D = 16 s; H for 9:16 three-column = 6 cards × (400 + 20) = 2,520 px → k = 1 speed = 157.5 px/s (5.25 px/frame), k = 2 = 315 px/s.
- Keep per-frame motion ≤ ~12 px/frame at 30 fps for crisp cards without motion blur (house limit); above that, add slight `filter: blur(0.5px)` or lower k.
- Grid at 1080×1920: 3 columns × 300 px + 2 gaps of 20 px = 940 px, margins 70 px; or 4 columns × 236 px for denser walls. 1:1: 4 columns. 16:9: 5–6 columns or 3 rows.
- Card styling: radius 24 px, 1 px white @12% border, shadow 0 8px 24px rgba(0,0,0,.3); images `object-fit: cover`.
- Intro (optional, not looped): cards fade in with 0.03 s stagger over 0.6 s; skip it when the clip must loop.
- Overlay headline: Inter 800, 72–88 px, centred at y ≈ 760–900 inside the safe box, scrim #000000 @50%.

## Build it
1. HyperFrames: `perspective-marquee` (tilted 3D marquee), `logo-wall`, `grid-card-assemble`, `dynamic-grid` [40]; varg cards `tilted-screenshot-wall`, `opposing-marquee-rows`, `wall-of-love-marquee` already exist.
2. Duplicate each column's card set enough times to cover the viewport plus one set (usually 2–3 copies).
3. Position per frame: `y = -(((t / D) * k * H) % H)`; for reversed columns `y = -H + (((t / D) * k * H) % H)`. Drive `t` from the timeline (a paused GSAP tween on a proxy from 0→D with `ease:"none"`), so seeking any frame is exact. Alternatively use GSAP `verticalLoop(items, {paused:true, speed})` and set `tl.time()` from the master timeline [29].
4. Remotion: `const t = frame / fps; translateY = -((t / D * k * H) % H)`.
5. Pre-load and decode all images before render; a missing image shows as a gap in the loop.
6. Params: `images[]`, `columns`, `k[]`, `direction[]`, `tilt`, `D`, `headline?`.

## Mistakes that look amateur
- Jump at the loop point → speeds must be k × H / D [29].
- Same speed for every column → vary k for depth.
- Using random cards order that repeats a photo side-by-side → shuffle with a fixed seed and check neighbours.
- Customer posts used without consent or faked "UGC" → real, permissioned content [21].
- Headline floating over busy cards with no scrim → 50% scrim or blur band [42].
- 25 px/frame scroll strobing → keep ≤ ~12 px/frame.

## Sources
[1] TikTok safe-zone template · [3] TikTok creative best practices · [4] Meta Reels specs · [5] Google vertical safe zone · [21] FTC rule · [29] GSAP seamlessLoop helper · [40] HyperFrames registry · [42] WCAG 2.1 contrast.
