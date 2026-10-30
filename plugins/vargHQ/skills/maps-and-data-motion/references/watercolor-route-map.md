# Watercolor travel route

A hand-painted map on paper: soft watercolour land and sea, a dashed hand-drawn route that inks itself between two
places, handwritten labels and small stamps. Use it for travel vlogs, honeymoon and holiday recaps, "our journey"
brand stories, wedding films. Formats 16:9, 9:16 and 1:1; typical length 6–8 s (preset default 7 s).

## How the pros do it
- **Paint the shapes, don't filter a photo.** Tyler Hobbs' watercolour method: deform each polygon by recursive
  midpoint displacement (~7 rounds for a base shape), then stack 30–100 layers, each deformed 4–5 more rounds and drawn
  at about 4% opacity, with per-segment variance so some edges stay crisp and some bleed. Bake this once into a texture;
  never re-simulate per frame. [32]
- **Mask each layer with texture.** Hobbs masks every layer with a different scatter of ~1000 small circles to get
  pigment granulation; a paper texture multiplied on top finishes it. [32]
- **Wobble edges with displacement, gently.** SVG `feTurbulence` + `feDisplacementMap` displaces pixels by
  `scale·(C−0.5)`; MDN's demo (baseFrequency 0.05, numOctaves 2, scale 50) is a strong wobble; for borders and the route
  at 1080p use scale 3–8 and keep the seed fixed so frames do not boil (unless you want a deliberate "boil" every
  2–3 frames). [33]
- **Start from public-domain shapes.** Natural Earth coastlines and borders are public domain, so the painted base is
  yours to use commercially. [24]
- **Ready-made watercolour tiles exist but carry credits:** Stamen Watercolor via Stadia needs "© Stadia Maps
  © Stamen Design © OpenStreetMap" and has gaps above zoom 16; check the plan for commercial video. [31]
- **Ink the route with a mask, keep the dashes still.** Animating `stroke-dashoffset` on a dashed line makes the dashes
  slide. Instead draw a solid mask path with DrawSVG and reveal a static dashed path through it, so the pen appears to lay
  dashes down. [34]
- **Let the traveller ride the tip** with `motionPath` + `autoRotate` (a paper plane or a car doodle). [35]
- **Keep ambient motion subtle:** paper grain shift, a 1–2 px boil on the route, a slow 1–2% push-in. [8]
- **Make it SVG/vector so labels and stamps can animate independently.** [5]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `watercolor-route-map.journal` | Travel-journal page: cream paper, soft blue sea, sage land, red ink route | paper #F4ECD8, sea wash #8FB8C9, land wash #B9C7A1, route #C0392B 4 px dashes 14/10 round caps, labels Caveat 700 |
| `watercolor-route-map.bold-wash` | Saturated poster washes, thick navy route, stamp badges | paper #FBF7EE, sea #4F9FD1, land #F2C14E, route #1F2A44 6 px dashes 18/12, labels Patrick Hand, stamps rotate ±6° |
| `watercolor-route-map.antique` | Sepia antique chart with vignette | paper #E9DCC0, ink #5B4636, sea #B8C4B0 at 60%, vignette 35%, labels IM Fell English, compass rose fades in at 0.8 s |

## Timing and numbers
Default 7 s = 210 frames at 30 fps.

| Beat | Time (s) | Frames | Motion | Ease |
|---|---|---|---|---|
| Paper + washes bloom | 0.0–1.2 | 0–36 | washes fade 0→1 through a radial "wet" mask that grows from the centre | `power2.out` |
| Start pin + label | 1.2–1.6 | 36–48 | pin drop, label writes on (clip reveal 0.4 s) | `back.out(1.4)` |
| Route inks | 1.6–5.2 | 48–156 | mask path draws, traveller rides tip | easeInOutSine `cubic-bezier(0.37,0,0.63,1)` [53] |
| Arrive | 5.2–5.8 | 156–174 | end stamp slaps in: scale 1.4→1, rotate −6°, 0.25 s | `power3.out` |
| Hold | 5.8–7.0 | 174–210 | 1.5% slow push-in, paper grain drift | linear |

- Route: 4–6 px at 1080p, dash 14–18 px, gap 10–12 px, `stroke-linecap:round`; hand jitter via displacement scale 3–6 [33].
- Wash layers if generated: 30–60 layers at 3–5% opacity [32]; bake to PNG at 2× output size.
- Labels: 3–3.6% of frame height in Caveat/Patrick Hand; titles 6–7%; write-on reveal 0.35–0.5 s per word.
- Push-in on hold: ≤ 2% scale over the hold (from 1.00 to 1.02).
- 9:16: route must sit inside the middle 60% of height; rotate the map composition rather than shrinking it.

## Build it
1. Pre-bake the painted basemap: project Natural Earth land/borders for your region with d3, rasterise, and run a
   Hobbs-style layering pass (Python/Canvas, offline) → `basemap.png` + `paper.jpg` (multiply). [24][32]
2. Compose in HyperFrames: basemap and paper as images; route as two SVG paths (solid mask path + dashed visible path
   inside `<mask>`); labels as HTML text with handwriting fonts.
3. Timeline: `tl.fromTo(maskPath, {drawSVG:"0%"}, {drawSVG:"100%", duration:3.6, ease:"sine.inOut"}, 1.6)` and the
   traveller on the same position with `motionPath`. [34][35]
4. Wobble: one `<filter>` with `feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="7"` and
   `feDisplacementMap scale="4"`; for a hand-drawn boil, swap the seed on every third frame from the timeline (seek-safe:
   seed = floor(frame/3) mod 4). [33]
5. Starting blocks: the HyperFrames `svg-stroke-trace` and `offset-path-traveler` components for the line and icon.

## Mistakes that look amateur
- Sliding dashes (animating dashoffset on a dashed stroke) → reveal a static dashed path through a drawn mask. [34]
- Photoshop "watercolor" filter over a satellite map → paint flat shapes with layered low-opacity washes. [32]
- Boiling edges at every frame (noise reseeded per frame) → fixed seed, or boil on 2s/3s. [33]
- Script font for long text → handwriting only for 1–3 word labels; body in a clean serif.
- Saturated washes behind labels → keep 4.5:1 label contrast with a paper-colour halo. [43]
- Watercolour tiles without their credit line → Stadia/Stamen/OSM credit, or paint your own from Natural Earth. [24][31]

## Sources
[5] Joshua Stevens — SVG tip — https://x.com/jscarto/status/2114826779596599409
[8] John Nelson — subtle map animation — https://x.com/John_M_Nelson/status/2027406545420493180
[24] Natural Earth — Terms — https://www.naturalearthdata.com/about/terms-of-use/ — public domain base shapes
[31] Stadia Maps — Stamen Watercolor — https://docs.stadiamaps.com/map-styles/stamen-watercolor/ — credit, z16 cap
[32] Tyler Hobbs — Simulating watercolor paint — https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art — layering numbers
[33] MDN — feDisplacementMap — https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/feDisplacementMap — wobble
[34] GSAP — DrawSVGPlugin — https://gsap.com/docs/v3/Plugins/DrawSVGPlugin/
[35] GSAP — MotionPathPlugin — https://gsap.com/docs/v3/Plugins/MotionPathPlugin/
[43] Lisa Charlotte Muth — colours in style guides — https://www.datawrapper.de/blog/colors-for-data-vis-style-guides — contrast
[53] easings.net — https://github.com/ai/easings.net/blob/master/src/easings.yml
