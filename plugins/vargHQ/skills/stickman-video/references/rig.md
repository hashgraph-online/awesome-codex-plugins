# The stickman rig

`assets/example/rig.js` (also inlined in `assets/stickman-rig.html`) defines `window.Stickman`. It has no dependencies and draws into any SVG group. Everything is a pure function of time: the same `t` gives the same pixels, so HyperFrames can seek any frame in any order.

## Skeleton

Side view, the figure faces +x before the `turn` flip. Local units, multiplied by `scale`.

| Bone | Length | Notes |
|---|---|---|
| Head | radius 36 | filled circle, no outline |
| Neck | 12 | part of the torso line |
| Torso | 124 | hip to neck base; shoulders sit 10 below the top |
| Upper arm, forearm | 70, 66 | forward kinematics from `aSh`, `aEl` |
| Thigh, shin | 86, 84 | inverse kinematics from foot targets |
| Foot | 24 | points forward, toes dip when lifted |

Standing hip height is 0.955 × (thigh + shin), so the knees are never locked. At `scale: 1.45` the figure is about 540 px tall; at 1.6 about 590 px.

Draw order: far arm and hand, far leg, torso, near leg (with outline pass), head, face, near arm and hand (with outline pass). Far limbs use the `shade` colour, which reads as depth.

## API

```js
const fig = Stickman.create(svgGroup, {
  scale: 1.45, ground: 1420,           // world px; feet stand on y = ground
  ink: "#f4f0e6", shade: "#8e97aa",    // near and far limbs
  face: "#0b0f18", outline: "#0b0f18", // eyes, brows, mouth; outline pass on near limbs
  stroke: 15, stride: 72, lift: 24, bob: 6, swing: 24, // line width, walk step, foot lift, hip bob, arm swing
  blinks: [1.15, 2.95, 4.9],           // blink centres in seconds (0.16 s each)
});
const P = Stickman.track(Object.assign({}, Stickman.DEFAULT_POSE, { x: 380 }), Stickman.LEAD);
P.move(start, duration, { channel: value, ... }, ease); // holds each channel until start, arrives at start + duration
P.set(t, { channel: value });                            // a cut
Stickman.draw(fig, P, t);                                // returns joint positions (hips, chest, head, shoulder, hands)
```

`track` is generic: the example also keys its camera with `Stickman.track({ cx, cy, cs })`.

Author `move` calls for one channel in time order. A `move` that starts before the previous one on the same channel has finished jumps; start it after.

Eases: `linear`, `inOut` (default), `out`, `in`, `snap` (fast out, for reactions), `back` (overshoot, for gestures), `walk` (15% ramp, constant speed, 15% ramp, for travel).

## Channels

| Channel | Range | Meaning |
|---|---|---|
| `x` | world px | hip position. Moving it drives the walk cycle. |
| `y` | px, negative = up | jump height (the whole figure leaves the ground; the shadow shrinks) |
| `turn` | -1 … 1 | facing. Flip over 0.16 s; it squashes through edge-on |
| `gait` | 0 or 1 | 0 switches the walk cycle off (jumps, being pushed) so the feet follow the hips |
| `hipDrop` | 0 … 85 | lowers the hips; IK bends the knees. 30 = landing, 80 = crouch |
| `lean` | -15 … 30 deg | torso tilt, + forward |
| `headTilt` | -15 … 15 deg | + chin down |
| `lookX` | -1 … 1 | eyes: 1 forward (profile), 0 at the camera, -1 over the shoulder |
| `lookY` | -1 … 1 | eyes: -1 up, 1 down |
| `eyeOpen` | 0.2 … 1.8 | 1 normal, 1.3 alarmed, 1.5–1.6 shock |
| `brow` | -1 … 1 | 0 hidden, + worried (inner ends up), - angry |
| `mouthOpen` | 0 … 1 | 0 = a line, 1 = a round O |
| `mouthCurve` | -1 … 1 | smile or frown on the line mouth |
| `aSh`, `aEl` | deg | near shoulder and elbow: 0 hangs, 90 points forward, 180 straight up, - behind; elbow + folds forward |
| `bSh`, `bEl` | deg | far arm, same convention |
| `standA`, `standB` | local px | standing foot offsets from the hips (near +16, far -14) |
| `liftA`, `liftB` | local px | lift a foot (tuck the feet in a jump) |
| `breath` | 0 … 1 | idle amplitude (breathing, weight shift) |
| `tremble` | 0 … 1.6 | fear shake on hips, arms and head |
| `wave` | 0 … 1 | elbow oscillation at 3.2 Hz for a hand wave |

`LEAD` samples some channels at a time offset: `headTilt` +0.05, `lookX`/`lookY` +0.06, `brow` +0.04 (they lead), `aSh` -0.05, `aEl` -0.07, `bSh` -0.09, `bEl` -0.11 (they follow). That one table removes most of the "everything moves at once" look.

## Layers (all inside `draw`)

1. **Keyed pose** from the track.
2. **Walk cycle.** The hips' travelled distance `d` (sum of |dx| over the keyed segments) sets the phase: `q = (d/scale + offset) / (2 × stride)`. Each foot is planted for half the cycle at `2·stride·(0.25 − f)` relative to the hips (so it moves back exactly as fast as the hips move forward: no sliding) and swings forward for the other half on an `inOut` curve, lifted by `sin(πg)·lift`. The far foot runs half a cycle behind. The hips bob `bob·cos(4π(q − 0.25))`, highest when one leg passes under the body. Each arm swings with the opposite leg, using the foot offset itself, so the arms can never drift out of phase. The cycle fades in with speed (full at 40 px/s) and is multiplied by `gait`.
3. **Idle.** Breathing every 3.1 s (hips 1.4 px, lean 0.9°, arms ±2°, head 1.6° slightly later), weight shift every 5.7 s (hips ±3 px with the feet planted, so the knees flex). Faded out while walking.
4. **Tremble.** Two sines at 9.1 and 13.3 Hz on hips, arms and head.
5. **Line boil.** Elbows, hands and knees jitter by up to 0.8 px from a hash of `floor(t·12)`: the drawing breathes on holds and every render matches.
6. **Blinks** from the `blinks` list: a smooth 0.16 s bump that closes the eyes to 10%.

Legs: two-bone IK from the hip to the foot target with the law of cosines; the knee always bends forward; a target out of reach is clamped to the leg's length.

## Pose values that worked in the example

| Pose | `move` values | Ease, duration |
|---|---|---|
| Settle after a walk | `lean: -3, aSh: 4, bSh: -4` | out, 0.35 |
| Look over the shoulder | `lookX: -1, headTilt: -5, lookY: -0.2` | snap, 0.28 |
| Look up | `lookX: 0.5, lookY: -0.75, headTilt: -12` | inOut, 0.3 |
| To camera, worried | `lookX: 0, lookY: 0, headTilt: 0, brow: 0.55, eyeOpen: 1.1` | snap, 0.22 |
| Point forward | `aSh: 96, aEl: 4, bSh: -14, lookY: -0.35, headTilt: -8` | back, 0.35 |
| Count (arm raised, ticks) | `aSh: 128, aEl: 6`, then dips of 8–11° on each count | back 0.3, then out 0.1 |
| Double take | `lookX: 0, eyeOpen: 1.4, brow: 0.9, mouthOpen: 0.35, lean: -5` | snap, 0.14 |
| Start to wave, then freeze | `aSh: 160, aEl: 30` + `wave: 1` (0.25), then `wave: 0` (0.06 snap) | back, 0.32 |
| Yank the arm back, hug | `aSh: 30, aEl: 95, bSh: 25, bEl: 80, lean: -7` | snap, 0.18 |
| Shock jump back | `gait: 0` first, then `y: -40, x: x − 45, aSh: 138, aEl: 30, bSh: 122, bEl: 34, eyeOpen: 1.55, mouthOpen: 1, brow: 1, lean: -12, liftA: 30, liftB: 22` | snap, 0.13 |
| Land | `y: 0, liftA: 0, liftB: 0, hipDrop: 34` | in, 0.12 |
| Crouch, cover the head | `hipDrop: 80, lean: 26, aSh: 150, aEl: 128, bSh: 138, bEl: 122, headTilt: 14, tremble: 1, eyeOpen: 1.35` | out, 0.4 |
| Peek (face visible) | `headTilt: -2, lookX: 1, aSh: 48, aEl: 70` | inOut, 0.35–0.45 |
| Stand up | `hipDrop: 0, lean: 0, headTilt: 0, aSh: 10, aEl: 22, bSh: -8, bEl: 18, tremble: 0.35` | inOut, 0.6 |
| Shrug, "your call" | `aSh: 28, aEl: 78, bSh: 22, bEl: 74, lean: -2` | back, 0.35 |

## The clock

```js
const tl = gsap.timeline({ paused: true });
const clock = { _t: 0 };
Object.defineProperty(clock, "t", { get() { return this._t; }, set(v) { this._t = v; renderScene(v); } });
tl.fromTo(clock, { t: 0 }, { t: DUR, duration: DUR, ease: "none" }, 0);
// ...HUD, rules, captions, ending card tweens on the same tl...
window.__timelines["main"] = tl;
```

GSAP assigns `clock.t` on every seek, so `renderScene(t)` redraws the set, the camera and every figure for that exact time. Keep all set animation (beams, waves, door shake, dust) inside `renderScene` as functions of `t`, with seeded hashes instead of `Math.random`.

## More figures and styles

- A second figure is another `create` plus its own `track`; give it different blink times and a different `LEAD` if it should not move like a twin. A head that only peeks (the example's face in the door window) is cheaper as a plain circle with two eyes.
- Paper-white style: `ink: "#15171c"`, `shade: "#6d7380"`, `face: "#f7f3ea"`, `outline: "#f7f3ea"` on a near-white set.
- Two-colour contrast format: two figures with different `ink` (white and yellow), the same keys shifted in time, opposite reactions.
- 16:9: same rig and scale; widen the set rather than scaling the figure down.
