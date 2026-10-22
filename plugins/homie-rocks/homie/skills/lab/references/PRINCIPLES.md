# The principles of feel this skill works from

Use the names below with the person, and describe what each does in the take you are both looking at. They are
old, well-documented ideas; say where they come from when it helps, in your own words.

## Sources worth naming

- **The twelve principles of animation**, from Frank Thomas and Ollie Johnston's *The Illusion of Life: Disney
  Animation* (1981): squash and stretch, anticipation, staging, follow-through and overlapping action, slow in and
  slow out, arcs, secondary action, timing, exaggeration, solid drawing, appeal, straight-ahead and pose-to-pose.
- **Game feel**: Steve Swink's book *Game Feel* (2008): real-time control, the response to input, polish effects.
- **Juice**: Martin Jonasson and Petri Purho's talk "Juice it or lose it" (2012), and Jan Willem Nijman's talk "The
  Art of Screenshake" (2013): small effects that make actions read (hit-stop, shake, particles, knockback).
- **Jumps**: Kyle Pittman's GDC talk "Math for Game Programmers: Building a Better Jump" (2016): a jump designed by
  its height and time to the apex, and a different fall.

Never quote frame counts or tuning values as another game's unless you measured them yourself and say how.

## The principles, as the lab shows them

| Principle | What it looks like in a take | What usually shapes it |
| --- | --- | --- |
| Anticipation | A short wind-up the opposite way before the action (COIL). For player input keep it visual or very short: a delay the player feels is lag. | wind-up ms, how far back |
| Hit-stop (hit pause) | On contact both sides hold for a few frames, so the hit reads. Short for light hits, longer for heavy ones. | hit-stop ms |
| Impact frame | The struck thing flashes, squashes against the hit, shakes in place. | flash ms, squash |
| Squash and stretch | Stretched along fast motion, squashed on a stop or a landing; the volume stays about the same (sx · sy ≈ 1). | squash amount |
| Slow in, slow out (easing) | Spacing on the arcs overlay: dots far apart are fast, close are slow. An ease-out leaves fast and arrives soft. | ease power, duration |
| No creep, no pop | An exponential slide never quite stops (a creep), then control snaps back (a pop). A curve that ends at rest has neither. | distance, duration |
| Follow-through and overlap | Things keep going a little after the main action stops (a wobble, a trailing smear) and settle at different times. | settle ms, wobble |
| Arcs | Natural motion travels on curves; the arcs overlay shows the path. | |
| Smears | A fast motion leaves a trail (a swipe's crescent, a stretched body) so the eye can follow it between frames. | smear length |
| Camera kick | The camera reacts to the player's own hits, briefly, a few pixels; never to everything. | shake px, ms |
| Secondary action | Particles, dust, numbers: they support the main action and never hide it. | count, life |
| Timing | Frames per phase: the lab's timeline is a timing chart. Try 30, 15 and 12 fps: a good move reads at each. | |

## Recipes (phases first, then the numbers that shape them)

- **A hit or bump**: HIT-STOP → LAUNCH → SLIDE → SETTLE (→ RECOVER when control comes back). Hit-stop 50 to 100 ms;
  launch stretched; an ease-out slide of a fixed distance; a squash and a dying wobble.
- **A strike or swing**: (WIND-UP) → IMPACT → FOLLOW → RECOVER. Damage on the press (responsive); the swipe's smear
  carries through; the target freezes white, is pushed, wobbles; a step into the strike keeps a combo in reach.
- **A jump**: COIL → RISE → HANG → FALL → LAND → RECOVER. Height and time to the apex as the tunables (gravity follows);
  a lighter gravity near the apex (hang); a faster fall; a landing squash; coyote time and a buffered press for
  fairness.
- **A dash**: WIND-UP → BURST → GLIDE → BRAKE. A burst of speed eased out over a fixed distance; a smear; a short
  brake squash.
- **A drift**: ENTRY → SLIP → HOLD → EXIT. Grip that falls off with the slip angle; a counter-steer window; a boost on
  exit sized by the hold.
