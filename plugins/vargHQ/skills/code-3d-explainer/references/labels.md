# Labels, text and the scale bar

Labels are HTML over the WebGL canvas (sharp at any size, real fonts, no texture atlas), positioned every
frame from the projected 3D anchor. `lib/explainer.js` does all of this from `story.json`; this page is the
rulebook and the numbers behind it. `scripts/check_labels.ts` enforces most of it on the real render.

## Anatomy (measured at 1920×1080)

```
  02                         <- index, JetBrains Mono 28 px, orange #ff6a33
  Nucleus                    <- name, Inter 650, 64 px
  Holds nearly all the cell's DNA   <- fact, Inter 450, 40 px, #b4d6d2, wraps at 760 px
  ───────────────────────    <- rule under the text; the leader joins its near end
      ╲
       ◉                     <- anchor: orange ring 10 px + white dot, on the part's surface
```

- A soft radial scrim behind each label (`.label::before`, rgba(3,7,9,0.6) fading out) keeps text readable
  over bright parts without a visible box.
- End-card tags (`"small": true`): name only, 46 px, no index, no build-in animation.
- Titles: 124 px; end title 64 px; the caveat lines 44 px, near-white (34 px grey was ~7 px on a phone: the frame critic flagged it).

## Phone legibility

A 1080p frame shown full-width in a portrait phone feed is ~390 px wide: everything shrinks to 0.2×.
`check_labels.ts` fails a primary line (name, tag, title) under 9 px there (= 46 px at 1080p) and any other
line under 6.5 px (= 32 px). Our first end tags at 40 px failed (8.1 px); 46 px passed. Look at
`qa/phone.png` (`bun scripts/sheet.ts master.mp4 qa/phone.png --phone`) at 100% before you sign off.

## Placement

- **Anchor-following** (beats): label = anchor + `offset` (default ±190, −150 px), `side` left or right,
  clamped to the safe area (96 px sides, 80 top, 96 bottom). The leader draws from the anchor to the rule.
- **Alternate sides** between consecutive beats (right, left, right…): the outgoing and incoming labels
  overlap in time by ~0.5 s and must not overlap in space.
- **Columns** (end card): `"column": "left" | "right"` stacks tags in a column at `story.columns[side]` px,
  **sorted by the anchor's screen height** so leaders do not cross, ≥ 26 px apart. All tags of a column are
  laid out from the start, even before they fade in; laying out only the visible ones made the Golgi tag
  jump when its neighbours arrived.
- Never let a label cover its own anchor (`check_labels.ts` warns). The membrane label sat right of an
  anchor near the frame edge, got clamped back over it; we moved the anchor to the other side of the cell.
- Anchor choice: on the thing itself, never between things (our ribosome anchor sat on the empty axis of
  the polysome helix; the critic caught it) and never where something else hides it (the cytoskeleton dot
  landed on a mitochondrion in front of the microtubule). Print positions with
  `capture.ts --eval "__film.project('lyso3', 20.5)"` to choose.
- Anchor placement: a point on the part's surface that faces the camera during its beat; for the end card,
  points on the cut faces or on parts that stay outside the removed wedge (an anchor inside the wedge
  points at nothing).

## Timing

- Build-in: ring pops (0.25 s), leader draws (0.1–0.4 s), name slides up (0.15–0.45 s), fact fades in
  (0.25–0.55 s). Out: 0.35 s fade.
- **Reading time**: each label must be readable (opacity ≥ 0.5) for ≥ 0.3 s + words / 4.5 s. A 2-word
  name + 6-word fact needs 2.08 s. With 9 labelled parts in ~21 s this is the binding constraint: it set
  the camera holds (`build-and-camera.md`). Our first cut gave the ER label 1.5 s; the check caught it.
- **Leader vs text**: when the anchor leaves the frame the leader fades at once; the text lingers only
  while the anchor was on screen within the last 0.25 s (computed from the camera pose at t − 0.25, so it
  is still a pure function of t). A 0.5 s linger (and before that, keeping the text to its out time) left
  "Golgi apparatus" over a shot of mitochondria: the frame critic called it a mislabel, an accuracy bug.
  Shorter linger = longer camera holds to keep reading time.
- Sync to narration when there is a voiceover (`narration.md`): label `in` = the word's start time − 0.2 s.

## Focus dimming

While a part's label is up, every other part dims to ~45% (`uDim`), the membrane to 60%. It tells the eye
what the label is about without moving anything.

## The scale bar

`scaleBar(camera, lookAt)` measures true length at the look-at depth: world units per pixel =
2·d·tan(fov/2)/H, then picks the largest of 10 nm…1 mm (1-2-5 steps) that is ≥ 150 px. It changes value as
the camera zooms, which sells the "zoom through scales" idea for free ("5 µm" → "500 nm").

It is only true for geometry drawn at real size. **Hide it where parts are enlarged** (`scaleBar.hide`
windows in `story.json`): our critic caught that the ribosome close-up would have shown a 500 nm bar next to
120 nm ribosomes while the label said 25–30 nm.

## What the checker checks (`bun scripts/check_labels.ts qa/labels.json`)

| check | rule | severity |
|---|---|---|
| overlap | any two text boxes intersect (4 px margin), opacity ≥ 0.15 | FAIL |
| safe | a box closer than 64 px to the left/right edge or 48 px to top/bottom | FAIL |
| anchor | a label covers its own anchor | WARN |
| phone | primary < 9 px, other < 6.5 px at 390 px wide | FAIL |
| reading | readable time < 0.3 + words / 4.5 s | FAIL |

The boxes come from the real DOM of every rendered frame (`capture.ts --labels`), not from the story.
