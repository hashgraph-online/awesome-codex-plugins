# Bokeh light-spot transition

The outgoing shot drops out of focus until its highlights bloom into giant bokeh discs, the cut happens under the
blur, and the next shot resolves from the same discs into focus. Use it for night/city/party footage, emotional beats,
music videos and soft chapter changes. Works in 16:9, 9:16 and 1:1; about 1 s (0.8–1.2 s).

## How the pros do it
- Structure it as defocus A → hard cut at maximum blur → refocus B; transition plugins build exactly this from the
  transition length and give separate ease-in, mid and ease-out controls. [26]
- Bokeh comes from highlights only: build a matte of the brightest values (matte position near 100 = highlights) and
  blur/shape that, then add it back with Screen or Add so highlights stay hot. [26]
- Push highlight gain during the transition — Maxon's bokeh transition defaults Highlight Boost to 60 on a −100…100
  scale. [25]
- Use a real iris shape: polygons come from aperture blades (Sapphire defaults to 7 sides), curvature/roundness 100 is a
  perfect circle, and a squeeze ratio stretches discs into anamorphic ovals (50 = round, lower = vertical). [25][26][27]
- Give discs a size spread, not one size: Sapphire's defaults are 30 lights, size 0.3, vary size 0.2, softness 0.01,
  colour fringing 0. [27]
- Size discs like a lens would: a background point at infinity blurs to c = f²/(N(S₁−f)). A 50 mm at f/1.4 focused at
  0.5 m gives a ~4 mm disc on a 24 mm-tall sensor (≈ 16 % of frame height); focused at 2 m, ≈ 4 %. "Giant bokeh" is
  therefore 12–25 % of frame height. [28]
- Blur amounts are large: plugin examples run at 150 and 600 on their blur slider; a timid 20 px Gaussian is not bokeh. [25]
- Match brightness at the cut, as for any hidden cut: the brightest region of A's last frame and B's first frame should
  overlap. [6][1]
- The fast-blur family sits at 0.20–0.40 s for the blur itself; this transition spends the extra time on the resolve,
  which is the payoff. [8]
- Defocus transitions are a stock editor move (tutorial accounts post them weekly); the highlight discs and the matched
  bright spot are what make it look shot, not plugged in. [46]
- If it looks like a filter, halve gain and disc count. [41]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `bokeh-light-spot.warm-night` | City lights bloom into big warm heptagons, cut, resolve | 1.0 s; blur ramp 0.40 s power2.in, cut at 0.43 s, resolve 0.57 s expo.out; discs 14–22 % of frame height, 7 sides, roundness 0.3, threshold luma 0.78, gain 1.7, tint #FFB86B, 24 discs |
| `bokeh-light-spot.clean-circle` | Modern lens, round discs, neutral | 0.8 s; circle (curvature 100), discs 10–16 %, threshold 0.82, gain 1.4, no tint, fringing 0 |
| `bokeh-light-spot.flash-through` | Discs swell to a near-white flash for 2 frames at the cut | 0.9 s; at cut white overlay 85 % for 2 f, discs 20–30 %, gain 2.0 |
| `bokeh-light-spot.anamorphic-oval` | Vertical oval discs, slight blue fringe | 1.0 s; squeeze ratio 35 (vertical oval), fringing 0.03, tint #9CC8FF, 6–10 discs at 20–28 % |
| `bokeh-light-spot.vertical-soft` | 9:16 phone footage, smaller discs, gentle | 1.1 s; discs 8–14 % of frame height, 18 discs, threshold 0.75, gain 1.3 |

## Timing and numbers
- 1.0 s at 30 fps = 30 f: A blur 0 → max over f0–f12 (power2.in) · cut at f13 (maximum blur, on the beat) · B blur
  max → 0 over f13–f30 (expo.out, so focus "snaps" in the last 5 f).
- Base image blur at peak: Gaussian σ ≈ 2.5–4 % of frame height (27–43 px at 1080p) under the discs.
- Disc count: 12–30; size spread ±30 %; opacity 40–90 %; edge softness 1–2 px with a slightly brighter rim
  (rim +10 %).
- Disc positions: sampled from A's brightest pixels (top 2–5 % luma) for the first half, B's for the second half;
  cross-fade disc sets over the 4 f around the cut.
- Colour: keep each disc's colour from its source pixel, saturation +10–20 %; optional global tint at 15 %.
- Fringing 0–0.05 (red/blue offset of 1–3 px at the disc rim).

## Build it
- HyperFrames: `transitions-blur`, `focus-blur-resolve`, `rack-focus`/`focus-rack` for the focus pull, `light-leak` or
  `transitions-light` for the flash variant. `npx hyperframes add focus-blur-resolve transitions-light`.
1. Two video layers (A, B). On A, tween CSS `filter: blur()` 0 → 36 px (power2.in); at the cut frame set A hidden, B
   visible at 36 px; tween B to 0 (expo.out). All on one paused timeline.
2. Bokeh layer: pre-analyse the last frame of A and first frame of B (canvas `getImageData`, done once at build time)
   to pick the brightest points; render discs as SVG polygons/circles with radial-gradient fill and Screen blend.
3. Scale discs 0.2 → 1 with the blur, cross-fade A-discs to B-discs around the cut, then shrink and fade with the
   refocus.
4. Optional: 2-frame white flash at the cut (flash-through).
- Remotion: same structure; `interpolate(frame, [0, 12], [0, 36], {easing: Easing.in(Easing.quad)})` for blur.
- ffmpeg (footage only, no discs): split at the cut and ramp blur with `gblur=sigma=…` via `sendcmd`, or the cheap
  `xfade=transition=hblur:duration=0.6`. For real discs, render the bokeh overlay in HyperFrames and composite it with
  `blend=all_mode=screen`.

## Mistakes that look amateur
- Gaussian blur only, no discs → it is a soft dissolve, not bokeh; shape the highlights.
- Discs on dark areas or on every pixel → matte the highlights only.
- All discs the same size and opacity → vary ±30 %.
- Cutting before maximum blur → the cut shows; cut at the peak.
- Refocus with ease-in → B "drifts" into focus; ease-out so focus snaps at the end.
- Hexagons on a "modern phone" look → match the iris to the story (round for modern, 6–7 blades for vintage).
- Bright spot of A at top-left and B's subject at bottom-right → the eye jumps; align them.

## Sources
[1] Filmdaft — Murch's Rule of Six — https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ — eye-trace
[6] No Film School — whip pan in 5 steps — https://nofilmschool.com/2017/09/5-steps-create-perfect-whip-pan-transition — match brightness at the cut
[8] Zaid Alkuheli, OverseerOS — https://www.overseeros.com/blog/how-long-should-video-transitions-be — fast blur 0.20–0.40 s
[25] Maxon Universe — Bokeh Transition — https://help.maxon.net/rg/en-us/Content/html/Transitions_bokeh-transition.html.md — highlight boost 60, shapes, ratio, blur examples
[26] Boris FX — BCC+ Rack Focus Dissolve — https://borisfx.com/documentation/continuum/bcc-plus-rack-focus-dissolve/ — highlight matte, curvature, Screen blend, ease controls
[27] Boris FX — Sapphire BokehLights — https://borisfx.com/documentation/sapphire/ae/bokehlights — default counts and sizes
[28] Wikipedia — Circle of confusion — https://en.wikipedia.org/wiki/Circle_of_confusion — blur-disc formula
[41] Yaori (@Pashoke1) — https://x.com/Pashoke1/status/2115041115590037582 — halve values if it looks like a filter
[46] After Effects Tricks (@jesiccaesthetic) — https://x.com/jesiccaesthetic/status/1925128197424951329 — defocus transition as a stock move
