# Stepped channel bumper

A channel bumper animated on twos: colored streak panels whip across, a plate reveals the channel name, then a
topic card arrives with a ghosted wipe. The stepped frame rate gives it a hand-made, comic-panel feel. Between
segments, before a topic, or as a channel sting. 16:9, 9:16, 1:1; 5–7 s.

## How the pros do it
- "On twos" means every image is held for two frames: at 24 fps, 12 new images per second [41][32]. It changes
  smoothness, not timing — a move still takes the same seconds [42].
- Animate smoothly on ones first, then step it: Spider-Verse animators found posing directly on twos looked
  artificial, so they animated on ones, baked, removed every second key and stepped it [32].
- No motion blur on stepped motion; the film used stepped "shifting" echoes instead of blur, which reads sharper [32].
- Keep secondary simulations on ones (hair/cloth there; grain, particles and texture here) when stepping them makes
  them jump [32] — or deliberately step texture "boil" at a slower rate for the stop-motion look [19].
- Editors use posterized time widely for a choppy, crafted look; around 14–16 fps is a popular sweet spot on live
  footage [43], and pairing it with stylized glitch or texture gives an anime feel [40][45].
- Bumpers are short: 2–3 s for a pure sting, under ~8 s with a topic card [20].
- Keep easing inside the stepped motion — stepping removes frames, not the ease; strong ease-outs read as
  "snap and settle" in 2–3 steps [17].
- Vary panel timings so it is not one repeated curve [33].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `stepped-channel-bumper.classic` | 3 diagonal streak panels, name plate, topic card with ghost wipe | render 24 fps, step 12 fps; panels 0.0–1.2 s; plate 1.2–3.2 s; topic 3.4–6.4 s; out 6.4–7.0 s |
| `stepped-channel-bumper.sting-3s` | Panels + name only | 24 fps on twos, 3.0 s total, name hold 1.4 s |
| `stepped-channel-bumper.threes` | Rougher, more hand-made | step 8 fps (hold 3 frames at 24), boil every 3 frames, grain 10% |

## Timing and numbers
- Frame rate: author and render at 24 fps; quantize the stepped layer with `tq = floor(t × 12) / 12` [41]. If the
  delivery is 30 fps, either deliver 24 fps or accept 3,2,3,2 holds; never mix 15 fps and 12 fps steps in one piece.
- Streak panels (classic): 3 panels at −14° angle, widths 38%/24%/12% of the diagonal, colors #FF4D2E, #FFD23F, #1E1E24;
  each crosses the frame in 0.5–0.7 s with `expo.out`, starts staggered 0.12/0.2 s (deliberately uneven).
- Name plate: a #1E1E24 plate wipes 0.4 s from the panel edge; name Archivo Black caps 13% H, +0.02em; on twos the
  name "settles" in 3 steps (overshoot scale 1.06 → 0.99 → 1.0, one step each).
- Topic card ghost wipe: card wipes left→right in 0.5 s; 2 ghost copies trail by 1 and 2 steps at 50% and 25% opacity
  (stepped echoes instead of blur [32]); kicker mono caps 2.2% H +0.12em; topic Inter 800 8% H.
- Texture: paper/grain overlay boils every 2 frames at 6–8% opacity [19]; optional 1 px position jitter per step.
- Sound: hits on panel arrivals; music on 120 BPM puts beats every 12 frames at 24 fps — land the plate and topic on beats.

## Build it
- HyperFrames: `stop-motion-cadence` (one driver that quantizes time and feeds all motion), `rubber-band-bumper`
  (panel tension → snap), `directional-wipe` / `swipe-rail` (streaks), `grain-overlay`.
- GSAP: build the whole bumper as a normal smooth timeline `inner`, then drive it from a stepped master:
  `master.eventCallback('onUpdate', () => inner.seek(Math.floor(master.time() * 12) / 12))` — or in HyperFrames
  set the composition to 24 fps and seek `inner` to the quantized time in the seek hook. Do not put `steps()` on every tween [11].
- Remotion: `<Composition fps={24}/>`; `const f = useCurrentFrame(); const stepped = Math.floor(f / 2) * 2;` and pass
  `stepped` to every `interpolate` call of the stepped layers; pass the raw `f` to grain if it should stay on ones.
- ffmpeg on finished footage: `fps=12,fps=24` (drop then duplicate) or `framestep=2` + `setpts` for a choppier
  look; keep audio untouched [22].

## Mistakes that look amateur
- Motion blur on stepped frames → turn blur off; use 1–2 stepped echoes for speed [32].
- Each tween with its own `steps()` so elements step out of phase → one global time quantizer [11].
- Stepping posed keyframes directly → animate on ones, then step [32].
- Same speed and ease for every panel → stagger and vary durations [33].
- A 15 s bumper → 3 s sting or ≤ 7 s with topic card [20].
- Grain stepped at a different rate in random places → texture on ones or on a fixed boil rate [19][32].

## Sources
[11] GSAP docs — SteppedEase (GreenSock animation platform documentation) — https://gsap.com/docs/v3/Eases/SteppedEase — steps(n) ease syntax for ticking properties.
[17] Joey Korenman — Kinetic typography in After Effects, part 1 (School of Motion) (Founder of School of Motion) — https://schoolofmotion.com/blog/kinetic-typography-after-effects-part-1 — Sync markers, ghost copies 50% two frames early, nudge 2-3 frames earlier, lingering ease-out.
[19] Lesterbanks — Ben Marriott's paper cut-out stop-motion look in AE (Write-up of a tutorial by Ben Marriott, motion designer and educator) — https://lesterbanks.com/2020/02/an-easy-way-to-get-a-paper-cutout-stop-motion-look-in-ae/ — Posterized wiggle (boil) at a low frame rate for a stop-motion feel.
[20] Hadiyah Woods — How long should a YouTube intro be? (Marmoset) (Marmoset music licensing journal) — https://www.marmosetmusic.com/journal/how-long-should-a-youtube-intro-be/ — Intro under 8 s (5-15 s range), bumper 2-3 s, 30 s too long.
[22] FFmpeg Filters Documentation (FFmpeg project) — https://ffmpeg.org/ffmpeg-filters.html — rgbashift, chromashift, noise, gblur, geq, tmix, lagfun options.
[32] CG Spectrum — Spider-Man: Into the Spider-Verse, how they got that look (Interviews with supervising animator Jeff Panko and lead lighting/comp artist Geeta Basantani) — https://cgspectrum.com/blog/spider-man-into-the-spider-verse-how-they-got-that-mind-blowing-look — Animate on ones then step to twos; no motion blur, stepped echoes; sims on ones.
[33] @jakeinmotion (Jake Bartlett) (Motion designer and kinetic-type instructor (Skillshare), maker of the AE tools Type Jazz and Railcut) — https://x.com/jakeinmotion/status/2104022458865218019 — AI motion fails with 60 fps, flat fast pacing and repeated easing.
[40] @ohey_official (OHEY | Top Effects) (After Effects effects/template creator) — https://x.com/ohey_official/status/1846868254595469793 — Pop glitch text + posterize time for an anime feel.
[41] @TrevElViz (Trev El. Viz) (Frame-by-frame animator) — https://x.com/TrevElViz/status/1833544353991516503 — On twos = 12 fps, each drawing held 2 frames at 24 fps.
[42] @HoodyPisDed (HoodyP) (Animator; post with 100k views and 250 bookmarks) — https://x.com/HoodyPisDed/status/2099406048742588424 — Twos/threes change smoothness, not timing.
[43] @_TyRogers_ (Ty Rogers) (Video creator) — https://x.com/_TyRogers_/status/1178882014675701761 — Posterize time 14-16 fps sweet spot for a choppy look on live footage.
[45] @niqteh (niqte) (Motion designer posting AE tutorials) — https://x.com/niqteh/status/2079011658467266574 — Photocopy texture chain: noise, blur, threshold, tint, posterize time.
