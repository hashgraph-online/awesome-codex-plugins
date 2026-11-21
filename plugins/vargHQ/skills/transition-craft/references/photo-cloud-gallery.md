# 3D photo cloud gallery

The viewer's photos hang in a deep 3D cloud on a white (or dark) void; the camera swings through them while the far
ones dissolve into fog, then flies into one hero photo, which becomes the next shot. Use it for portfolios, event
recaps, "memories" montages and product galleries. Works in 16:9, 9:16 and 1:1; 4 s default (3–6 s).

## How the pros do it
- Fog colour must equal the background colour, so distant photos melt into the void instead of greying out. Use
  exponential-squared fog: factor = 1 − exp(−density² · depth²), which keeps the near field clear and thickens fast with
  distance; linear fog is smoothstep(near, far, depth). [31]
- Recycle or cull planes exactly at the fog far distance, so anything that appears is already fully fogged — no pop-in.
  HyperFrames' tunnel block ties its recycle boundary to the fog distance for this reason. [33]
- Drive the camera from timeline time: in Remotion use `useCurrentFrame` inside ThreeCanvas, never `useFrame`; in
  HyperFrames tween a driver value on the paused GSAP timeline. [32][33]
- Fly through depth at a constant perceived speed — exponential dolly toward the hero (equal scale change per second),
  same rule as any zoom. [16]
- Use depth of field to pick a subject: Abrams' photo-montage camera uses DOF at f/1.4 with high blurriness; a depth
  pass driving defocus can hold two or more focus points if two photos matter. [29][50]
- Keep motion blur modest (90–180° shutter) — a smeared gallery reads as a glitch. [7][15]
- Land on the hero photo where the viewer is already looking (frame centre) and let it fill the frame as the cut. [1]
- The landing is a zoom-through transition: the photo is a screen into the next shot, the same logic as a match cut on
  shape. [5]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `photo-cloud-gallery.white-fog-swing` | Bright paper-white void, photos fade into fog, camera arcs 30° and lands on a hero | bg + fog #F4F3EF, FogExp2 density = 1.73 / farDepth, 80 photos, plane 1.6 × 1.0 units, cloud 12 × 7 × 24 units, FOV 50, yaw 30° + dolly 16 units over 3.2 s power2.inOut, land 0.8 s expo.out |
| `photo-cloud-gallery.dark-void` | Black void, photos glow slightly, deeper fog | bg + fog #0B0B0D, linear fog near 4 far 20, emissive 0.15 on photos, FOV 60 |
| `photo-cloud-gallery.vertical-column` | 9:16 tall column of photos, camera rises and turns | cloud 6 × 20 × 14, FOV 60, camera rises 10 units, yaw 45°, photos 1.0 × 1.25 (4:5) |
| `photo-cloud-gallery.slow-drift-loop` | No landing; endless gentle drift for a background | speed 0.6 units/s, recycle at fog far, yaw ±8° sine at 0.1 Hz, 6 s loop |

## Timing and numbers
- 4.0 s at 30 fps = 120 f: drift/establish 0–0.6 s · swing + dolly 0.6–3.2 s · hero lands 3.2–4.0 s (fills frame at
  f120, cut to the hero's video on the beat).
- FogExp2 density for 95 % fog at depth D: density = sqrt(−ln 0.05) / D ≈ 1.73 / D (D = 18 → 0.096).
- Photo count: 40–120. Minimum spacing between photo centres ≥ 1.2 × plane width; reject-sample positions with a
  seeded PRNG.
- Photo yaw: billboard toward camera ± 10–15° random so edges catch light; roll ±3°.
- Photo borders: 2 % white frame on dark void, 1 px #00000020 hairline on white void; soft shadow only on white.
- DOF: focus distance = hero distance, blur max 6–10 px at 1080p for planes 2× farther than the hero.
- Camera path: Catmull-Rom through 3–4 points; yaw change ≤ 35° per 2 s to avoid nausea.

## Build it
- HyperFrames: `gallery-tunnel` (panels receding into fog, FOV 75, speed in segments/s, fog distance parameter) is the
  closest block; reuse its fog-and-recycle logic and swap the tunnel layout for a random cloud. `camera-rig-depth-stack`
  and `ui-3d-reveal` for CSS-3D versions. `npx hyperframes add gallery-tunnel`.
1. Three.js scene: `scene.background = scene.fog.color = new Color('#F4F3EF')`, `scene.fog = new FogExp2(bg, density)`,
   `MeshBasicMaterial({ map, fog: true })` per photo (basic material keeps photos true-colour).
2. Place planes from a seeded PRNG inside the cloud box; mark one hero near the end of the path at camera height.
3. Animate a single `driver.t` 0 → 1 on the paused timeline; each frame compute camera position from the spline at t,
   look-at a point 3 units ahead, and for the last 20 % blend look-at to the hero centre.
4. Final 0.8 s: exponential dolly toward the hero until it fills the frame, then cut to the hero's full-res video.
- Remotion: `<ThreeCanvas>` + `useCurrentFrame()`; `useMemo` for positions; set the GL renderer to `angle`. [32]
- CSS-only fallback (no WebGL): `perspective: 1200px` stage, photos with translate3d, opacity = 1 − fogFactor(depth).

## Mistakes that look amateur
- Grey fog on a white background → photos turn muddy; fog colour = background colour.
- Photos popping in at the far plane → recycle exactly at fog far.
- Even grid of photos → reads as a wall, not a cloud; seeded random with spacing.
- Camera moving on `requestAnimationFrame` or `useFrame` → non-deterministic renders; drive from frame/timeline time.
- Fast yaw with heavy motion blur → nausea and smear; ≤ 35° per 2 s, 90–180° shutter.
- Hero photo low-resolution → it fills the frame at the end; use the full-res still or video.
- Lit/standard materials with harsh lights on photos → colours shift; use unlit materials.

## Sources
[1] Filmdaft — Murch's Rule of Six — https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ — eye-trace on the landing
[5] Logan Baker, PremiumBeat — Match cuts — https://www.premiumbeat.com/blog/match-cuts-for-video-editors/ — shape match carries the cut
[7] StudioBinder — 180° shutter — https://www.studiobinder.com/blog/what-is-the-180-degree-shutter-rule/
[15] Remotion — CameraMotionBlur — https://www.remotion.dev/docs/motion-blur/camera-motion-blur
[16] Reach & North (van Wijk & Nuij) — https://ar5iv.labs.arxiv.org/html/1801.09358 — exponential zoom/dolly
[29] Evan Abrams, PremiumBeat — Falling Polaroids — https://www.premiumbeat.com/blog/after-effects-photo-montage-tutorial — DOF camera
[31] three.js — FogExp2.js / fog_fragment.glsl.js — https://raw.githubusercontent.com/mrdoob/three.js/dev/src/renderers/shaders/ShaderChunk/fog_fragment.glsl.js — fog formulas
[32] Remotion — @remotion/three — https://www.remotion.dev/docs/three — useCurrentFrame, angle renderer
[33] HyperFrames registry — gallery-tunnel — https://github.com/heygen-com/hyperframes/tree/main/registry — fog-tied recycling, FOV 75
[50] plugin3d (@plugin3d) — https://x.com/plugin3d/status/2079216930615927190 — depth pass + defocus, multiple focus points
