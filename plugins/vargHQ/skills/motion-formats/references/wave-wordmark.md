# Wave-through wordmark

A crest of motion runs through a wordmark letter by letter: each glyph lifts (or thickens, or tips the whole word like a seesaw) as the wave passes, then everything settles back to the exact logo. It is a 2 s logo sting, intro or outro button, or loopable idle in 16:9, 9:16 or 1:1. It works on any wordmark set as live text or split SVG glyphs.

## How the pros do it
- **Drive every letter from one wave with a per-letter delay; don't keyframe letters by hand.** Each character gets a peak time `delay + (index − 0.5) × individualDelay` and a response that eases from full to zero as the distance from its peak grows. [27]
- **Make the falloff window about 2× the per-letter delay,** so neighbouring letters are partly lifted at the same time. Without the overlap you get a "one letter at a time" stair-step instead of a wave. The reference values are individualDelay 0.15 s with a falloff window of 0.30 s. [27]
- **For snappy brand motion, think in frames:** about 2 frames of stagger per letter, about 12% overshoot past the target, and a settle within 6 frames. Put these in one config so "snappier" becomes numbers. [29]
- **Stagger with `each`, not `amount`,** when the delay between letters must stay fixed whatever the word length. With `amount`, a 4-letter and a 12-letter wordmark take the same total time, so the wave speed changes. [26]
- **`from` sets where the wave starts:** "start", "center", "edges", "end" or an index. Nested `repeat`/`yoyo` inside the stagger object makes each letter loop independently, which is the right tool for a continuous idle wave. [26]
- **Settle with a decaying sine, not a single ease:** `amp · sin(2π·freq·t) / e^(decay·t)`. The frequency stays constant while the amplitude dies, which reads as a physical spring for the seesaw tilt. Defaults to start from: amp 80, freq 1, decay 1; raise freq and decay for a short sting. [28]
- **A weight wave is the variable-font alternative to a position wave.** Swell `wght` from rest to black and lean `slnt` forward as the crest passes, with a crest about 4 characters wide. Driving the font axes keeps the baseline and logo lock-up perfectly still. [30]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `wave-wordmark.lift` | Letters rise and fall as a crest travels left to right | lift 30% of cap height; 3 frames (0.1 s) per letter at 30 fps; pulse width 0.4 s (window = 2× delay on each side); `sine.inOut`; ends on the exact rest pose |
| `wave-wordmark.seesaw` | The whole word tips toward the crest like a seesaw, then rocks to rest | lift 20% of cap height; tilt = 3° × (crestX − centre)/halfWidth about the centre of the baseline; settle by decaying sine (amp 3°, freq 2.5 Hz, decay 5) |
| `wave-wordmark.weight` | A crest of boldness passes through | Recursive variable font: `wght` 400 → 1000, `slnt` 0 → −15 at the crest; crest 4 characters wide; one sweep in 1.0 s |
| `wave-wordmark.snap` | Short, punchy UI-brand version | 2 frames per letter, scaleY overshoot 12%, settle in 6 frames, total ≤ 1.2 s |
| `wave-wordmark.idle-loop` | A continuous subtle ripple for a held logo | lift 8–12% of cap height; each letter loops `yoyo` at a 1.0 s period with `stagger.each` 0.08 s; seamless 2.0 s loop |

## Timing and numbers
- **Beat structure (2.0 s, 30 fps = 60 frames; 60 fps works too, double all frame counts):**
  - 0.00–0.20 s (6 f): the logo at rest, so viewers read it first.
  - 0.20 s → (0.20 + (N−1)·0.10) s: the crest travels. For an 8-letter wordmark the last peak is at 0.90 s, and the tail clears by 1.10 s.
  - 1.10–1.60 s: settle. Seesaw rocking or overshoot dies out; the decaying sine with decay 5 falls below 1% within about 0.9 s, so start it at the moment the crest leaves the centre letter.
  - 1.60–2.00 s (12 f): hold the exact rest pose. The last frame matches the first, so the sting loops.
- **Per-letter response** (Ebberts-style, seek-safe):

  ```
  peak_i = t0 + i·d
  y_i(t) = −A · ease(clamp(|t − peak_i| / (2d), 0, 1))
  ```

  - `ease(u) = 0.5·(1 + cos(π·u))`: a raised cosine, 1 at the peak and 0 at the edge.
  - d = 0.10 s, so the full pulse width is 4d = 0.4 s and about 4 letters move at once, matching a 4-character crest. [27][30]
- **Amplitude:**
  - lift: 30% of cap height; seesaw: 20%; idle: 8–12%.
  - On a 1080p wordmark with a 160 px cap height, 30% is 48 px.
  - Keep the lift inside the title-safe area; the 9:16 format needs 10% of height of clear space above the word.
- **Seesaw tilt:**
  - θ(t) = 3° × (crestX(t) − cx) / (W/2) while the crest is inside the word.
  - Then θ(t) = θ_exit · sin(2π·2.5·τ + φ) / e^(5τ), with τ the time since the crest left.
  - Pivot at the baseline centre (`transform-origin: 50% 100%`). Never exceed 4°, or the word reads as falling over. [28]
- **Squash on landing** (optional, the snap preset): scaleY 1 → 1.12 at the crest → 0.96 → 1.0 within 6 frames. [29]
- **Fonts (free for commercial video):**
  - Recursive (OFL-1.1; variable `wght` 300–1000, `slnt` −15–0) for the weight preset.
  - Inter (OFL-1.1) or Space Grotesk (OFL-1.1) for lift and seesaw on a typeset wordmark.
  - A brand SVG logo works too: split it into one `<g>` per glyph.
- **Colours:** inherit the brand. For a contrast crest, tint the letter at its peak with an accent (e.g. a #FFD400 overlay at peak only, mapped from the same `ease` value).

## Build it
1. **Split** the wordmark into per-glyph spans (GSAP SplitText, or manual `<span>`s with `display:inline-block`) or per-glyph SVG groups. Keep kerning by measuring before splitting, and never re-layout during the animation.
2. **One paused timeline.** Either:
   - `gsap.to(chars, { y: -A, duration: 2*d, ease: "sine.inOut", yoyo: true, repeat: 1, stagger: { each: d, from: "start" } })`, or
   - a single `onUpdate` that computes `y_i(t)` with the formula above from `tl.time()`. Both are seek-safe. [26]
3. **Seesaw:** tween the parent's `rotation` from the crest position, then add the decaying sine as a custom ease, or compute it in `onUpdate` from the time since exit. [28]
4. **Weight wave:** start from the registry block `weight-wave` (Recursive, crestWidth 4 chars default, sweepSpeed, weightFrom/weightTo variables). [30] Related blocks: `variable-font-flex` (axes flex with per-character stagger), `wordmark-tiles` (a wordmark resolving through a GSAP wave), `pendulum-swing` (gravity-damped settle for the seesaw feel), `logo-sting` and `logo-outro` for the surrounding lock-up.
5. **Remotion:** drive `y_i` from `useCurrentFrame()/fps` with the same formula, and use `spring()` only for the snap preset's overshoot.

## Mistakes that look amateur
- No overlap between letters, so they pop one at a time → falloff window ≥ 2× the per-letter delay. [27]
- Stagger by `amount`, so long wordmarks wave faster than short ones → use `each` for a constant wave speed. [26]
- The wave never returns to the exact logo pose (drift, rounding, leftover rotation) → end every channel at 0 and hold 0.4 s; the last frame must equal the first.
- Too much amplitude (letters jumping a full cap height) → 20–30% for a sting, 8–12% for an idle.
- A linear back-and-forth tilt for the seesaw → a decaying sine with constant frequency reads as weight. [28]
- Animating `font-weight` on a static font (which jumps between instances) → use a variable font with a continuous `wght` axis. [30]
- Kerning breaking when the text is split → measure glyph positions first and lock them.

## Sources
[26] GSAP docs — "Staggers" — https://gsap.com/resources/getting-started/Staggers/ — each vs amount, from, grid, nested repeat/yoyo, stagger ease
[27] Dan Ebberts (After Effects expression author, MotionScript; Creative COW answer) — "Mexican wave" expression selector — https://creativecow.net/forums/thread/mexican-wave-expression-selector/ — per-letter peak time, 0.15 s delay, 2× falloff window
[28] Dan Ebberts — "Realistic Bounce and Overshoot" (MotionScript) — http://www.motionscript.com/articles/bounce-and-overshoot.html — decaying sine with amp, freq and decay
[29] Asteri (@Asteri_eth; kinetic-type builder on X) — https://x.com/Asteri_eth/status/2115126932291436649 — 2 frames per letter, 12% overshoot, settle in 6 frames, one config file
[30] HyperFrames registry — `weight-wave` block (OFL-1.1, Recursive) — https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry/blocks/weight-wave/registry-item.json — wght/slnt crest, crest width 4 chars
[31] Google Fonts repository — license files for Recursive, Inter, Space Grotesk (OFL) — https://github.com/google/fonts/tree/main/ofl
