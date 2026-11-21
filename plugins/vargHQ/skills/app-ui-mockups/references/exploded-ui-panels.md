# Exploded UI panels

An app screen split into its layers (background, sidebar, cards, modal, toasts) that float apart in 3D depth while the camera orbits, then slide home and lock into the finished flat screen. Shows "everything that goes into" a product in one shot; a classic launch-film opener or feature-section transition. 16:9 native; 1:1 works; 9:16 suits a phone-app screen. Typical length 4–6 s.

## How the pros do it
- Design the UI first, as a complete believable screen (a "fake UI" for a product that may not exist yet); the explode only works if every layer is clean on its own. [3]
- Rebuild instead of recording: build the panels as real layers (Figma → motion tool, or HTML), styled to the product's design system, then animate. [48][4]
- Start from a known projection: true isometric is 45° around the vertical axis then ≈35.264° around the horizontal; for UI, a softer three-quarter view (rotateX 50–58°, rotateZ −30 to −45°) keeps text legible while showing depth. [43]
- Separate on z by role, not evenly: background deepest, content mid, floating UI (modals, toasts, cursors) highest; leave 2–3× more gap above the main card than between minor layers so the hierarchy reads.
- Stagger the layers when they separate and when they come home (60–90 ms), and use ease-out into rest; the final lock should be dead still, with no spring wobble. [2][44]
- The return to flat must stabilize quickly because the viewer is about to read the screen. [45]
- Keep the screen the hero: screen graphics should support the story, not hijack it; decide what each panel says before styling it. [42]
- Reference for the look: product motion designers post "custom 3D UI reveal" shots that resolve into the logo or the finished screen. [5]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `exploded-ui-panels.orbit-collapse` | Layers apart in a three-quarter view, 25° orbit, collapse to flat | rotateX 55°, rotateZ −35°, z gap 90 px (minor) / 220 px (hero card), orbit rotateZ −35° → −10°, collapse 1.1 s power3.inOut, stagger 0.07 s |
| `exploded-ui-panels.iso-stack` | Strict isometric plates with labels beside each layer | rotateX 54.736° (= 90° − 35.264°), rotateZ −45°, z gap 120 px, labels Inter 600 2.2% of frame height |
| `exploded-ui-panels.phone-layers` | Phone app screen exploding toward camera in 9:16 | rotateY −24°, rotateX 12°, z gap 70 px, 5 layers, collapse 0.9 s |

## Timing and numbers
- 4 s clip (120 frames): 0–0.4 s flat screen visible (or fade in, scale 0.95→1); 0.4–1.4 s tilt to the three-quarter view and explode (layers z 0 → target, power3.out, stagger 0.07 s bottom → top); 1.4–2.6 s hold + slow orbit (rotateZ +25°, sine.inOut); 2.6–3.7 s collapse (z → 0, power3.inOut, stagger 0.06 s top → bottom) and untilt to 0°; 3.7–4.0 s dead-still final screen. [2][44][45]
- Perspective 1800–2600 px at 1080p; `transform-style: preserve-3d` on the stage only.
- Z separation: 4–7 layers; minor gap 70–110 px, hero card gap 180–240 px, total stack depth ≤ 60% of frame height.
- Each layer gets its own shadow that grows with height: offset y = 0.12 × z, blur = 0.35 × z, opacity 0.25 → 0.12.
- Panel corner radius 12–16 px, 1 px border rgba(255,255,255,.08) on dark UIs so edges read in depth.
- Background: neutral, low-contrast (e.g. #0B0D10 → #15181D radial), 10–15% darker than the UI's own background.
- Fonts inside the UI: Inter (OFL-1.1) 400/500/600; labels the same family. [49]

## Build it
1. Start from HyperFrames `exploded-stack` (isometric plates explode with a label per layer, hold, collapse back) or `ui-3d-reveal` (perspective 3D reveal of UI elements); `transitions-3d` for the hand-off. `npx hyperframes add exploded-stack ui-3d-reveal`.
2. Build the finished screen as nested divs, one div per layer, each `position:absolute` in a shared stage; record each layer's flat rect.
3. One paused timeline: tween stage `rotateX/rotateZ` and each layer's `z` (translateZ) with staggers; orbit on the stage only. Never animate layout properties, only transform and opacity. [44]
4. Shadows: a blurred div under each layer driven by the same z value (so it seeks exactly).
5. Remotion: `interpolate` per layer with `Easing.bezier(0.65, 0, 0.35, 1)` (≈ power3.inOut) and staggered start frames.

## Mistakes that look amateur
- Layers as flat sibling divs with a top-to-bottom collapse stagger: the card layer passes over the content layer and hides it for a few frames → nest the layers, each z relative to its parent, so the stack collapses in order.
- All layers equally spaced → space by hierarchy, hero card highest.
- Text upside down or edge-on during the orbit → limit rotateZ to ±45° from the start view and rotateX ≤ 60°.
- A spring wobble when the panels lock home → power3.inOut into a still frame. [2]
- Animating `top/left/width` → transform and opacity only. [44]
- Busy wallpaper behind floating panels → flat dark gradient.
- Exploding a real third-party app's UI → your own designed UI. [3]

## Sources
[2] Emil Kowalski (@emilkowalski) — ease-out, matched durations — https://x.com/emilkowalski/status/1970144111261868487 , https://x.com/emilkowalski/status/2102798004281635184
[3] Steve Schoger (@steveschoger) — full fake UI for marketing — https://x.com/steveschoger/status/1795585777864184025
[4] Om Patel (@om_patel5) — https://x.com/om_patel5/status/2110398086438584391
[5] Bohdan Motion (@bohdanmotion) — 3D UI reveal + logo — https://x.com/bohdanmotion/status/2106544538231640442
[42] Pushing Pixels, David Sheldon-Hicks (Territory Studio) — https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html
[43] Wikipedia, Isometric projection — https://en.wikipedia.org/wiki/Isometric_projection
[44] Emil Kowalski, Great animations — https://emilkowal.ski/ui/great-animations
[45] Screen Studio guide, Animations — https://screen.studio/guide/animations
[48] Steve Lemuel, Raycast spec teaser — https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion
[49] Google Fonts metadata — https://github.com/google/fonts
