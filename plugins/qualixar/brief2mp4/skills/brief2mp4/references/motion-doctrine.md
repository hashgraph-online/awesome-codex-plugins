# Motion doctrine: the rules behind motion that looks finished

Read this before animating anything, and again when a render "works but feels cheap". These are working rules with numbers, not laws: break one on purpose and write the reason in SPEC.md. Times are seconds; "scene" means one beat of the film.

## 1. Smooth beats bouncy

Default to a long-tail deceleration: GSAP `power3.out` or `expo.out` for arrivals. `back`, `bounce` and `elastic` eases overshoot and wobble; they read as playful and cheap when used on everything. Use one only for a moment the brief wants to feel playful (a sticker landing, a mascot), and then use it for that moment alone. When the brief says "snappy", it means a short duration with a strong ease-out, not an overshoot.

Why: overshoot draws the eye to the motion instead of the thing that moved. A smooth arrival lets the viewer's attention land on the content.

## 2. Easing is direction

- **Arrivals ease out** (fast start, soft landing). **Exits ease in** (soft start, fast departure). **Moves between two resting places ease in-out.** Linear only for constant spins and turntables.
- **Exits are shorter than entrances.** Entrance about 0.4 s, exit about 0.25 s. Camera moves 1.5-3 s, ease in-out.
- **Mirror the ease across a cut or transition:** `power3.in` on the way out, `power3.out` on the way in, so the speed matches.
- The most common first-draft fault is motion faster than a viewer can read. Slow the first draft one notch before judging it.

## 3. Vary on purpose

If every element enters the same way, the result reads as a template.

- No more than two independent tweens with the same ease in one scene.
- The slowest scene is about 3x the duration of the fastest.
- Not every element from the same direction; a different stagger per scene.
- The first animation starts 0.1-0.3 s after the scene begins, never at exactly 0.
- Stagger the whole group within about 0.5 s however many items it has; ten items at 0.2 s apart is a 2 s wait.
- The most important element moves first.

## 4. Build, breathe, resolve

Shape every scene in three parts. In the first 30% the elements enter, staggered. From 30% to 70% the content sits readable, with at most one ambient motion. In the last 30% it resolves or exits. Do not dump everything in the first quarter and then leave the screen to idle.

## 5. Reveal on the cue

When there is narration, introduce each line, card or heading when the voice mentions it, spread over the later half of the scene. Fewer things, each arriving on its own beat, beat a full screen at t = 0. Word-timed camera keys are arrival times: hold on key i and move only in the window before key i+1.

## 6. Stillness beats bad motion

No lazy scale-breathing loop and no slow push-in on the back half of a text scene. The sanctioned signs of life during a hold are a subtle jitter or one living detail. A mid-video hold that must stay still gets 1-2% drift so it does not read as frozen; a key readout gets a full 1 s hold. A pause that is a reading hold may still move at rest (an idle bob on a parked mascot) so long as it ends at rest.

## 7. Overlap and follow-through

Start the next move before the last one ends. Secondary parts trail the lead by 2-5 frames. If everything starts and stops together, it reads as a slideshow.

## 8. Ration effects

- One glint per shot, on the hero, clipped inside its rounded corners.
- Whole-frame impacts (shake, flash, scale pump): about three per video at most, at least 16 beats apart, on the strongest hit.
- One flood, one whip and one title-entrance style per video (two at most).
- One transition style per seam.

## 9. Camera

Stable by default. No handheld shake in a clean UI or explainer film. Text-dense shots face the camera straight on. Move the camera for a reason (to follow an event, to reveal), not to keep the frame busy.

## 10. Transitions carry meaning

| Transition | What it says to the viewer |
|---|---|
| Hard cut | "Wake up": a new thing, a new place |
| Crossfade | "This continues" |
| Slow dissolve | "Drift with me": time passing, a reflective beat |
| Zoom-through | A change of state |
| Inverse zoom-through | An arrival, a payoff |

Crossfading everything is a tell. A transition that demonstrates the product feature is better than one that only replaces a card. Never start a new headline in the same spot while the old one is still fading; the two overlap as unreadable text.

**Velocity-matched cuts.** Cut at the peak of a move, with the same direction and speed on both sides. If an object leaves frame going right at speed, the next shot's object arrives going right at the same speed.

**Blur scales with the subject.** About 10 px peak on text-sized subjects (20 px smears letterforms), 18-20 px on full-frame surfaces, the same value on both sides of the seam, applied to the wrapper and not to each child.

**Never hard-cut through a flash while the next element's words still start at opacity 0.** Start the incoming words under the cover and dissolve the cover over them.

**Narrated cuts:** hard cuts with about 0.35 s of silence between voice clips usually beat crossfading the picture and the audio.

## 11. Springs for UI motion

For UI shots, drive positions and scales from closed-form springs written as pure functions of `t`, one spring per change, summed when several changes hit the same value. Any frame then renders alone, which parallel render workers need. Keep GSAP for sequencing. UI presets may overshoot about 4.6%; type never overshoots.

## 12. Numbers and charts

Counters never reflow: tabular numerals, fixed width, the final value exact. When a spoken number is counted up, compute the schedule from the voice's word timings so the number on screen equals the number heard. A number needs a visual with weight (a fill bar, a ring, a shape). Successive stats of one idea stay in the same visual space and only the value changes. Avoid pie charts, multi-axis charts, six-panel dashboards, gridlines, tick marks and legends in motion work.

## 13. Retention pacing by format

| Format | A new visual idea | A pattern interrupt (hard cut, colour flip, scale jump, sound change) | Hook |
|---|---|---|---|
| Short, Reel, promo | every 1.5-3 s | every 3-5 s | in the first 1.5 s |
| Long-form | every 8-15 s | at each chapter boundary | in the first 1-3 s |

- The first frame is a complete image, motion is under way by frame one, and the opening works on mute. No logo sting, no "welcome".
- Re-hook at least every 30 s on long-form with something real (a loop, a reveal, a stake), never a filler question. Put the strongest visual moves in the weakest windows: the minute after a strong cold open, a digression after the payoff, a triple ending.
- Budget the beats from the reading time. At 0.4 s per word plus 0.5 s and at most 7 words per card, a hook, five cycles, a montage and an end card cost about 90 s. To fit 75-85 s, use fewer beats, not faster text.
- Narrate in plain order: what was done, what to expect, what you are looking at, then the result. Define each number and term at the shot where it first appears.

## 14. Check it

Motion rules are checked on the rendered file, not on the timeline: `scripts/check_seams.py` (flicker, pops, freezes), `scripts/check_clutter.py` (layout), and the second-reader pass in `references/review-checklist.md`. Render traps that make a timeline look right and the file look wrong are in `references/render-traps.md`.
