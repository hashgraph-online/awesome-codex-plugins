# Photo collage burst

Dozens to hundreds of photos (or flat shapes, or words) are thrown in from the frame edges and pile into a collage that
keeps churning; once the pile covers every pixel, the next shot is cut underneath and revealed. Use it to open a recap,
a "year in photos", a product drop or a chapter change. Works in 16:9, 9:16 and 1:1; 3–5 s (4 s default), of which the
transition core (full coverage → reveal) is 0.4–0.7 s.

## How the pros do it
- Stack by order, not at random: each new card sits on top of the last. In 3D, offset every card's Z by its index
  (Abrams subtracts index × 4 px); in 2D, z-index = spawn order. [29]
- Give each card its own random rotation from a seeded random: Abrams uses Z rotation in a ±45° range for photos
  thrown in. Let them settle to a smaller angle (±6–12°) so the pile reads as a table, not a tornado. [29]
- Spawn on a distribution, not a fixed gap: use GSAP `stagger.amount` (total spawn time) so changing the card count
  never changes the length, and put an ease on the distribution — `power2.in` starts sparse and gets dense, which is
  exactly the "pile-up" build. [21]
- Throw from the edges: `stagger.from: "edges"` (or a custom origin per card outside the frame) so the pile grows
  inward; for "random" scatter use `from: "random"`. [21]
- Cards arrive at full speed and only slow down — ease-out entrances such as cubic-bezier(.25,0,.11,1) or expo.out,
  never ease-in-out on a thrown object. [42]
- Paper physicality: a cast shadow at about 50 % darkness and a thin white paper edge (white drop shadow or border)
  sell the cut-out; "lift" a card by animating scale and shadow distance together. [29][30]
- For the handmade variants (shapes, words) posterize to 12 fps so the collage moves in stop-motion steps. [30]
- Depth of field separates layers: Abrams turns on camera DOF (blurriness 200 at f/1.4); in 2D blur cards that are
  more than 10 layers below the top by 2–6 px. [29]
- The pile is an object wiping the frame — Kon's trick of "use objects to wipe the frame" — so hide the hard cut at the
  frame where no background pixel is visible, then let the pile blow outward or zoom into one card. [4]
- Keep the eye in one place across the cut: the last card (or the gap that opens) sits where the next shot's subject
  will be; eye-trace is the 4th of Murch's six criteria. [1]
- After the pile settles, keep it alive with a low-frequency wiggle on a few cards: SoM calls wiggle(1, 25) a subtle
  shake; for churn use frequency 0.5–1 Hz and 4–12 px. [9]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `photo-collage-burst.photos` | Real photos with white borders thrown from all edges, pile, then the last photo zooms to full frame as the next shot | 80 cards, card width 24–34 % of frame width, border 3 % of card, rotation in ±45° → settle ±10°, entry 0.45 s expo.out, spawn amount 2.0 s ease power2.in from edges, full cover at 2.6 s, reveal 0.5 s |
| `photo-collage-burst.shapes` | Flat paper shapes in a 4-colour palette, stop-motion | 120 shapes 6–18 % of frame height, posterize 12 fps, rotation ±30°, entry 0.3 s, amount 1.8 s |
| `photo-collage-burst.words` | Bold words pile up like stickers | 60 words, Anton 4–12 % of frame height, black/white/one accent, rotation ±12°, entry 0.35 s back.out(1.4) |
| `photo-collage-burst.mixed` | Photos + shapes + words, editorial scrapbook | 50 photos / 40 shapes / 20 words, tape strips on 30 % of photos, 12 fps on shapes only |
| `photo-collage-burst.polaroid-drop` | Slower 3D drop from above onto a table, perspective camera | 24 polaroids 350×425 px frame / 300×312 px photo, 10-frame cadence, Z start −2700 px, shadow 50 %, DOF blur 6 px on lower layers |

## Timing and numbers
- 4.0 s at 30 fps = 120 f: spawn 0–2.2 s (66 f) · pile complete and covering 2.2–2.6 s · hidden cut at 2.6 s (f78) on
  the downbeat · reveal 2.6–3.1 s · next shot settles 3.1–4.0 s.
- Each card: 0.30–0.50 s (9–15 f) flight; overshoot on landing ≤ 4 % scale (back.out(1.4) for stickers only).
- Spawn density: with amount 2.0 s and 80 cards the average gap is 0.75 f; with `power2.in` the first cards are
  ~3 f apart and the last ones < 0.5 f apart.
- Card sizes at 1080p: photos 460–650 px wide in 16:9; in 9:16 use 45–70 % of frame width so photos stay legible.
- Rotation: flight ±45°, settled ±6–12°; never 0° on more than 10 % of cards.
- Shadow: `0 12px 30px rgba(0,0,0,0.35)` plus a 1 px `rgba(0,0,0,0.15)` contact edge; white border `#FAFAF7`.
- Motion blur on flying cards: 180° shutter, 5–10 samples. [7][15]
- Coverage check before the cut: 100 % of pixels covered for at least 2 frames.

## Build it
- HyperFrames: start from `paper-collage-reveal` (torn scraps that scatter away — run it in reverse for the pile-up,
  forward for the reveal), `grid-card-assemble` for an ordered variant, `motion-blur` wrapped around the card layer.
  `npx hyperframes add paper-collage-reveal motion-blur`.
1. Pre-compute every card from a seeded PRNG (e.g. mulberry32(seed + i)): start point outside the frame (pick an edge,
   then a point 10–20 % beyond it), end point inside, start/end rotation, scale, delay. Never call `Math.random()`
   inside the render loop.
2. One paused GSAP timeline: `tl.from(cards, { x, y, rotation, duration: 0.45, ease: "expo.out",
   stagger: { amount: 2.0, from: "edges", ease: "power2.in" } })`; z-index = index.
3. Add a churn tween for 8 % of cards after they land (seeded noise, 0.5–1 Hz, 4–12 px), all driven by timeline time.
4. At the cover frame, swap the background layer to the next shot (hard cut under the pile), then either tween the
   pile outward (`from: "center"`, 0.5 s power3.in) or scale one hero card to full frame using an exponential scale.
- Remotion: `random("card-" + i)` for deterministic values, `interpolate` + `Easing.bezier(.25,0,.11,1)` per card,
  `<CameraMotionBlur shutterAngle={180} samples={6}>` around the flying layer.
- ffmpeg fallback for footage-only edits: `xfade=transition=pixelize:duration=0.5` is the cheap "breaks into pieces"
  cousin; it is not this effect.

## Mistakes that look amateur
- Every card the same size and angle → vary size ±20 % and rotation per card from a seed.
- Even spawn rhythm (metronome feel) → put an ease on the stagger distribution so it accelerates.
- Background showing through at the cut frame → only cut when coverage is 100 % for 2+ frames.
- `Math.random()` per frame → cards jump on every re-render; seed everything.
- Cards entering with ease-in-out (floaty) → ease-out, arrive fast.
- Pile churning for 3+ s after it lands → keep churn ≤ 1 s or on < 10 % of cards; the next shot is the payoff.
- No shadow/border on photos on a busy pile → photos merge into mush; add border + shadow.
- Faces cut by later cards on the hero photo → keep the hero card on top and its face area clear.

## Sources
[1] Filmdaft — Murch's Rule of Six — https://filmdaft.com/walter-murchs-rule-of-six-the-editors-formula-for-choosing-the-right-cut/ — eye-trace across the cut
[4] Tony Zhou, Every Frame a Painting — Satoshi Kon: Editing Space & Time (transcript) — https://voicetube.com/videos/32481 — objects wiping the frame as a transition
[7] StudioBinder — 180-degree shutter rule — https://www.studiobinder.com/blog/what-is-the-180-degree-shutter-rule/ — blur amount
[9] Jason Boone, School of Motion — camera shake — https://schoolofmotion.com/blog/how-to-simulate-camera-shake-adobe-after-effects — wiggle(1, 25) as subtle
[15] Remotion — CameraMotionBlur — https://www.remotion.dev/docs/motion-blur/camera-motion-blur — 180°, 5–10 samples
[21] GSAP — Staggers — https://gsap.com/docs/v3/Staggers/ — amount, from, ease on distribution
[29] Evan Abrams, PremiumBeat — Falling Polaroids — https://www.premiumbeat.com/blog/after-effects-photo-montage-tutorial — rotation range, z stacking, shadows, DOF, polaroid sizes
[30] Tom Graham, Envato Tuts+ — Collage animation in After Effects — https://photography.tutsplus.com/articles/collage-animation-in-after-effects--cms-93666 — 12 fps, paper edge, lift
[42] Raptor (@RajAdonis) on X — https://x.com/RajAdonis/status/2113906813020344579 — arrive at full speed, then slow; exact bezier
