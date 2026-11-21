# Camera-shake distort cut

An impact cut: the outgoing shot hops, punches in and bends (lens bulge + RGB split) into the cut; the next shot lands
already zoomed, shakes from the hit, mirror-filled at the edges, and settles. Use it on bass hits, drops, punchlines,
sports and hype edits. Works in 16:9, 9:16 and 1:1; 2 s total (0.3 s of build, the cut, ~1 s of settle).

## How the pros do it
- Shake = decaying oscillation: offset(t) = A · sin(2π f t) / e^(decay · t), started at the hit. Ebberts' defaults are
  amp 80, freq 1, decay 1 (a slow wobble); impact shakes raise frequency and decay. [10]
- Industry default frequency is fast: Sapphire S_Shake ships with frequency 8 (and slow tilt/zoom waves at 0.5); a
  common editor recipe is S_Shake at 0.7 amplitude for about 13 frames, then blur. [11][40]
- Use noise, not a pure sine, for violent hits: Unreal recommends Perlin noise for rumbles/explosions and a sine wave
  for gentle drift, each with a blend in/out. [13]
- Handheld baseline is small: wiggle(1, 25) is what School of Motion calls a subtle shake; scale the footage up so edges
  never show. [9]
- Fill edges with mirrored copies instead of over-scaling: Motion Tile output 300 % + Mirror Edges gives three mirrored
  copies across and down — this is where the "lands mirrored" look comes from. [14]
- Put a 2-frame chromatic kick on the hard cut; RGB separation of 5–25 is the plugin range shown. [41][12]
- New shot cuts in punched-in and settles: 1.52× → 1× over 1.2 s, arriving at full speed and only slowing down
  (cubic-bezier(.25,0,.11,1)). [42]
- Hide the cut inside the fastest frames, as with a whip pan: trim where the blur begins on A and where it ends on B. [6]
- Motion blur makes the shake feel physical: 180° is natural, larger angles smear; smaller angles give the staccato
  Saving Private Ryan feel. [7][15]
- Keep the core short: punch/impact moments are 0.10–0.25 s; the settle can run longer. [8]
- Cut a frame early to jolt (action); cutting late reads relaxed — editors relaying Hans Zimmer. [34]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `shake-distort-cut.bass-hit` | Hop, punch-in with bulge, cut on the kick, mirrored landing, fast decaying shake | 16:9; hop 4 f (scale 1→1.04, y −1.2 %); push 1.04→1.22 over 6 f power3.in; bulge k1 0→0.35; cut f10 (1 f before beat); B 1.18→1.0 over 0.6 s expo.out; shake A 48 px, f 10 Hz, decay 6, rot ±2°; RGB 8 px 2 f; mirror edges on; shutter 270° |
| `shake-distort-cut.handheld-snap` | Lighter: quick snap-zoom cut with handheld settle | push 1→1.12 over 5 f; B 1.12→1.0 over 0.5 s; shake 20 px, 6 Hz, decay 4, rot ±0.8°; RGB 4 px 2 f; shutter 180° |
| `shake-distort-cut.earthquake` | Long noisy rumble across the cut | Perlin noise 60 px, 14 Hz, rot ±3°, blend in 4 f / out 12 f, total 0.8 s; shutter 360°; scale 1.15 to hide edges |
| `shake-distort-cut.vertical-reel` | 9:16, vertical-biased shake for phone edits | y amplitude 1.5× x amplitude; A 40 px, 9 Hz, decay 5; B 1.25→1.0 over 0.7 s; keep captions outside the shake layer |
| `shake-distort-cut.staccato` | Crisp, stuttered war-footage hit | shutter 45°, step-hold 2 f (12 fps) during the shake, A 36 px, 12 Hz, decay 5, no bulge |

## Timing and numbers
- 2.0 s at 30 fps = 60 f (bass-hit): A normal 0–0.5 s · hop f15–f19 · push + bulge f19–f25 · cut at f25 (1 frame
  before the beat at f26) · B lands punched-in f25 · shake f25–f43 decaying · settle to < 1 px by f43 (0.6 s) ·
  hold B to f60.
- Amplitudes at 1080p: impact 24–60 px (2–5 % of frame height), rotation ±1–3°, zoom wobble ±2 %; handheld 4–12 px.
- Frequencies: impact 8–14 Hz, handheld 1–3 Hz, tilt/zoom drift 0.5 Hz.
- Decay: 4–8 for impacts (amplitude halves every 0.09–0.17 s); 1–2 for wobble.
- Bulge: lens distortion k1 +0.25…+0.40 peak at the cut, back to 0 within 6 f on B.
- Mirror fill: 300 % tile with mirrored edges; scale footage 105–115 % if not mirroring.
- RGB split: ±4–10 px horizontal for 2 frames (cut frame + 1).

## Build it
- HyperFrames: `camera-shake` (nine measured handheld/tele/wide profiles, closed-form and seek-safe; set `profile` and a
  frequency multiplier), `whip-pan-cut` for the matched-velocity seam, `motion-blur` (shutter angle, phase, samples),
  `chromatic-aberration-wipe` or `caption-glitch-rgb` for the kick, `transitions-distortion` for the bend.
  `npx hyperframes add camera-shake motion-blur transitions-distortion`.
1. Wrap A and B in one rig div. Build the hop and push on the paused timeline (power3.in into the cut).
2. Add the decaying shake as a function of `t − hitTime` (closed form, so any frame can be rendered alone):
   `x = A·sin(2π f t + φx)·exp(−d t)`, `y = 0.8·A·sin(2π f·1.13 t + φy)·exp(−d t)`, `rot = R·sin(2π f·0.7 t)·exp(−d t)`.
3. Mirror edges: render B inside a 3×3 grid of mirrored copies (`scaleX(-1)`/`scaleY(-1)` neighbours) so translation
   and rotation never expose black.
4. Bulge: SVG `feDisplacementMap` or a small WebGL pass with k1 tweened; RGB split as three offset layers with
   `mix-blend-mode: screen` for 2 frames.
5. Wrap the rig with `motion-blur` (shutter 180–270°, 6–8 samples).
- Remotion: same closed-form shake in `useCurrentFrame()`; `<CameraMotionBlur shutterAngle={270} samples={6}>`. [15]
- ffmpeg on footage (B side shown):
  `scale=iw*1.15:-1,crop=iw/1.15:ih/1.15:x='(iw-ow)/2+48*sin(2*PI*10*t)*exp(-6*t)':y='(ih-oh)/2+38*sin(2*PI*11.3*t)*exp(-6*t)',lenscorrection=k1=0.12:k2=0.02,rgbashift=rh=-8:bh=8:enable='lt(t,0.067)',tmix=frames=3:weights='1 2 1'`;
  use `fillborders=mode=mirror` instead of the 1.15 overscale when you want mirrored edges; `hflip` only if the brief
  wants B literally mirrored.

## Mistakes that look amateur
- Constant-amplitude wiggle across the cut → reads as an earthquake filter; decay it from the hit.
- Black edges visible during the shake → mirror-fill or scale up 10–15 %.
- Shake on the caption/UI layer → text unreadable; shake only the footage rig.
- Shake starts before the beat → the hit feels late; hit on the beat or 1 f early.
- Same shake preset on every cut → wallpaper; reserve it for 1 hit in 5–8 cuts.
- Heavy RGB split for more than 2–3 frames → looks like a broken file; 2 frames.
- Pure sine at 1–2 Hz for an impact → looks like a boat; use 8–14 Hz with noise.

## Sources
[6] No Film School — whip pan in 5 steps — https://nofilmschool.com/2017/09/5-steps-create-perfect-whip-pan-transition — cut inside the blur
[7] StudioBinder — 180° shutter — https://www.studiobinder.com/blog/what-is-the-180-degree-shutter-rule/ — blur vs staccato
[8] Zaid Alkuheli, OverseerOS — https://www.overseeros.com/blog/how-long-should-video-transitions-be — impact 0.10–0.25 s
[9] Jason Boone, School of Motion — https://schoolofmotion.com/blog/how-to-simulate-camera-shake-adobe-after-effects — wiggle(1,25), scale up
[10] Dan Ebberts, MotionScript — http://www.motionscript.com/articles/bounce-and-overshoot.html — decaying sine expression
[11] Boris FX — Sapphire S_Shake — https://borisfx.com/documentation/sapphire/ae/shake — default frequency 8, wave freq 0.5
[12] Maxon Universe — Camera Shake Transition — https://help.maxon.net/rg/en-us/Content/html/Transitions_camera-shake-transition.html.md — RGB separation 5–25
[13] Epic Games — Camera Shakes in Unreal Engine — https://dev.epicgames.com/documentation/unreal-engine/camera-shakes-in-unreal-engine — Perlin vs sine, blend in/out
[14] Rick Gerard, Adobe Community — Motion Tile mirror edges — https://community.adobe.com/t5/after-effects-discussions/mirror-edges-not-working/m-p/11946450 — 300 %
[15] Remotion — CameraMotionBlur — https://www.remotion.dev/docs/motion-blur/camera-motion-blur
[34] EOSHD forum — cutting on/before/after the beat — https://www.eoshd.com/comments/topic/46696-editing/ — a frame early jolts
[40] goop (@goopsoup_) — https://x.com/goopsoup_/status/2114615971826827569 — S_Shake 0.7 for 13 frames, then blur
[41] Yaori (@Pashoke1) — https://x.com/Pashoke1/status/2115041115590037582 — 2-frame chromatic kick
[42] Raptor (@RajAdonis) — https://x.com/RajAdonis/status/2113906813020344579 — 1.52× → 1× over 1.2 s, bezier
