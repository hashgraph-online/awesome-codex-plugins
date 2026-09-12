---
name: video
description: Use when a brief has to become a film. Turns a one line ask into a Claude Design prompt written in the animations-v3 engine's own language, plus the built piece.jsx and a contact sheet to look at before anyone renders. Covers reference roles, the kit, the storyboard gate, the motion floor, and the verification commands. Do not use for backend work, UI design, or marketing copy alone.
---

# Emulo video

You take a brief and hand back a film. Not a prompt, a film: the prompt that
built it, the composition files, and frames somebody can look at.

## 0. Load the profile before you write a word

1. Locate `emulo.py` two directories above this skill; fall back to `./emulo.py`
   only for a direct repo checkout.
2. Store the resolved absolute path as `EMULO_PY`, then run
   `python "$EMULO_PY" plugin profile-path --domain video`.
3. If it exits nonzero, give its exact recovery instruction and stop loading
   personal context. Never substitute a generic creative persona.
4. Read every returned path completely. First is the core working profile,
   second is the video profile. Both outrank anything below.
5. If the repo has `videos/README.md`, it routes short-form work.
   **This skill owns long-form and commercial film only.** A vertical Reel that
   is a designed film, not a screen recording, is this skill.

## 1. What you hand back

**A folder the person can upload to Claude Design and get a film.** That is the
deliverable. Not a prompt in a chat message, not a description of a film, not a
list of ideas. A folder.

Build it at `videos/_kits/<brand>/` in this exact shape, because the shape is
what makes it work:

| # | Artefact | Why it is there |
|---|---|---|
| 1 | `PROMPT.md` | the brief. One page, in the engine's language |
| 2 | `START-HERE.md` | **the upload order.** Which files, in which order, in one message. Without it the person guesses and the guess is wrong |
| 3 | `ATTACH/` | every asset the film needs, including `animations-v3.jsx` itself |
| 4 | `frames/` | reference stills whose **filenames carry the instruction** |
| 5 | `KIT.md` | the manifest: every file, its pixel size, its known defects |

Optionally, and only after the four above are finished: `build/piece.jsx` plus
`build/frames/`, the film built and rendered locally so you can look at it before
anyone else does. That is verification, not the deliverable. A kit with no local
build still ships. A local build with no kit does not.

### The three things that decide whether the folder works

**Ship the engine inside `ATTACH/`.** `animations-v3.jsx` goes in the folder with
the assets. Claude Design needs the runtime it is being asked to write against.
Leaving it out is the most common way a good prompt produces a bad film.

**Isolated parts, never a screenshot of a whole screen.** One object per file,
transparent, 1600px minimum on the long edge, plus 4K plates at the film's aspect
ratio. A whole screen dropped in is a slab and reads as broken. Claude Design
films fail on missing assets, never on prompt length.

**Put the instruction in the filename.** `REF-VERCEL_03_object-became-the-mark.png`
teaches; `ref3.png` does not. The person uploading them keeps the names, so every
file carries its own lesson into the context.

### Name what is missing. Never invent a substitute.

If an asset does not exist, say so in `PROMPT.md` under its own heading, and say
what to do instead. A brief that admits two missing assets is usable. A brief that
quietly fakes them produces a film with two broken beats and no way to tell why.

### Every prompt contains, in this order and by name

1. **the brief in the engine's language**: `OM_SCENES`, `CUES`, named `Easing`
2. **the transformation chain, as match anchors**: what becomes what
3. **the asset list**, with real filenames, so no beat is blocked on a missing part
4. **the failure conditions for this specific film**, not generic ones
5. **the verification commands**, so the claim "it works" has an output behind it

A worked example of the whole shape is `videos/_kits/claude/`: brief, upload
order, 31 assets with the official mark split into stackable layers, twelve
instruction-named frames, and two missing assets named rather than faked.

## 2. The engine

`animations-v3.jsx` is the Claude Design runtime. Read
`videos/_kits/_engine/README.md` once, then work from this table.

**Never edit `animations-v3.jsx`.** Its own header says re-running
`copy_starter_component` overwrites it. Every improvement made there is
destroyed on the next host copy. The leverage is in the brief.

| Use | Never use |
|---|---|
| `Easing.easeOutExpo` and the named curves | `cubic-bezier(...)`, any CSS string |
| `OM_SCENES` named sections with `dur` | absolute frame numbers as the structure |
| `CUES.SectionName` to key choreography | wall clock, `setTimeout`, `requestAnimationFrame` |
| `animate({from, to, start, end, ease})(T)` | `useEffect` painting anything visible |
| `interpolate([...], [...], ease)(T)` | CSS keyframes running on their own |
| `<Shot from to>` for a hard cut | conditional mounting per section |
| one `<CompositionStage>` as the only exportable root | the exportable attribute anywhere else |

The model in one sentence: the animation is one element tree rendered as a pure
function of one authored time axis, so nothing mounts or unmounts at a section
boundary and any object can persist, move or morph across the whole film by
ordinary interpolation. That is why this engine suits the work. Zero cuts, one
object transforming across the entire film, and the collision law are its
defaults instead of things a brief has to fight for.

```jsx
<CompositionStage width={1080} height={1920} bg="#161309"
                  scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
  <Piece />          // ONE component, the whole film
</CompositionStage>
```

```js
useComposition() -> { T, CUES, time, duration, authoredTotal, playing }
```

`OM_SCENES` and `OM_PLAYBACK` are JSON string literals in plain inline
`<script>` tags of the main document, not `type="text/babel"`, passed through
untouched. Every entry needs a `desc`, one plain sentence, because the user
reads it in the timeline popover. Never hand-set `nat`.

```html
<script>window.OM_SCENES = '[{"name":"Strike","dur":2.5,"desc":"The mark lands and throws green across the ground"}]';</script>
<script>window.OM_PLAYBACK = '{"mode":"loop"}';</script>
```

**Easing, the complete list.** `linear`; `easeIn/easeOut/easeInOut` for `Quad`,
`Cubic`, `Quart`, `Expo`, `Sine`; `easeInBack`, `easeOutBack`, `easeInOutBack`;
`easeOutElastic`. Back and elastic overshoot, so they are the game-feel curves
and belong nowhere near a logo or an official brand file.

**Render from `T` only.** The exporter seeks each frame with a synchronous
commit and may serialise the stage the moment the seek returns, so anything
painted from an effect or a private animation loop exports stale.

**Never render `<Captions>`.** Ohad films the export off his phone and adds his
own Hebrew and English. A burned caption ruins that. Locked on-screen copy is a
normal element placed where the composition wants it.

**Set `bg` to the film's ground**, never the `#0b0b0e` default, and never
`#000000`. A designed world needs somewhere for light to fall off to.

Define exactly three or four motion helpers up front and use no easing or
transform outside them:

```js
MOTION.slam    Easing.easeOutExpo     arrivals and impacts
MOTION.snap    Easing.easeOutBack     chips landing, overshoot capped at 6%
MOTION.drive   Easing.easeInOutQuart  travel, light, drift
MOTION.settle  Easing.easeOutQuart    the final resolve
```

## 3. Assign the references. Never average them.

Every reference gets **one job** and an explicit do-not-copy list. Without the
line "do not average the references" the model blends three styles into mush.
This is the single cheapest fix in the whole system.

| Reference | Its one job | Never take |
|---|---|---|
| `videos/vercel-spec/vercel-spec_1920x1080_60fps.mp4` | transformation, depth, scale contrast, the zero-cut continuous composition | its palette, and never its grey placeholder chrome, which is what the no-kit build produced |
| Spotify, `videos/refnces/motion/Video-53319.mp4` | camera and easing: three events, the hold, the settle | its green, its product |
| Claude, `videos/refnces/motion/oFSdbD1WKeB9fUJJ.mp4` | monochrome identity, typography, restraint | its brand, its interface |
| `videos/_kits/duolingo/` | the logo built by assembly, and the one-object-huge-on-dark grammar | its colour, its mascot |

Write it into the prompt in this shape:

```
Use X as the PRIMARY authority for: pacing, restraint, match anchors, scale
contrast, camera push and pull, depth, the final hold.
Use Y only for: monochrome identity, typography, exact logo, clarity.

Do not copy X's design. Do not introduce X's colour. Do not average the
references.
```

### Read the source. Five films, one engine.

`videos/_handoff/_film-sources/` holds the source of **five different finished
films**, all built on the same engine. Read across them. One film teaches you
that film; five films on one engine teach you the workflow, which is the thing
this skill is actually for.

| File | The film |
|---|---|
| `vercel-film.jsx` (49 KB) | the spec commercial that got 321 upvotes on r/ClaudeAI |
| `claude-master.jsx` (68 KB) | the Claude cinematic master, 1920x1080 60fps 20.0s |
| `claude-film.jsx` (41 KB) | an earlier Claude cut, so you can diff a film against its own revision |
| `film.jsx` (62 KB) | a third long film |
| `reel.jsx` (16 KB) and `clip.jsx` (5 KB) | the same grammar at reel and clip length |

Supporting them:

| File | What it gives you |
|---|---|
| `animations-v3.jsx` (55,474 bytes) | the engine. **Byte-identical in every one of the three source archives**, verified by hash. It is a fixed substrate, not a per-film thing. Never edit it |
| `PROMPT-1.md` and `PROMPT-2.md` | the real prompt pair that produced one of these films. The storyboard-gate prompt, then the build prompt |
| `camera_keyframes.json` | real camera data from a finished film, instead of invented easing |
| `ui.jsx`, `tweaks-panel.jsx`, `support.js` | the host scaffold the films run inside |

**How to read them, and this is the point.** Do not copy one film. Open at least
three and ask what is the *same* in all of them: how a scene list is declared,
where the transformation chain is expressed, how an entrance is timed against
the thing it hits, how the last three seconds are built, what never appears.
The constants across five films are the workflow. Anything present in only one
is that film's costume, and copying it is how you get a film that looks like a
tribute instead of a piece of work.

Two ratios that hold across them:

**Motion budget, roughly 70/20/10.** Seventy percent of the movement is the
object transforming, twenty the camera pushing or pulling, ten the camera
travelling. When a film feels busy but dead, this has inverted and the camera is
doing the work the object should be doing.

**Build in stages, and gate between them.** Build the first five to eight
seconds. Render. Look at a contact sheet. Only then continue. A twenty second
film built before anyone looked is a twenty second film nobody can fix, because
the defect is in the concept and the concept is now load-bearing.

Also in the repo, for the current job rather than the general workflow:
`videos/_handoff/vercel/reel/Storyboard.dc.html` (the largest storyboard that
exists), and `videos/_kits/claude/frames/`, twelve stills whose filenames carry
the instruction.

## 4. Build the kit before you write the prompt

Films fail on missing assets, not on prompt length. The Vercel film was built
from an 8,000 word prompt with a camera scale graph, a match anchor chain, an
easing table and a frame by frame shot list, and every frame of it is grey
rectangles standing in for text and a hand drawn triangle in place of the real
mark. The prompt was not too weak. It handed the model nothing real to put in
the frame, and placeholders are the only thing a model can draw with no assets.

**Claude Code builds the kit. Claude Design animates it.** That split is the
pipeline.

1. **Measure the reference at 1:1**, one file, never a contact sheet. Write down
   beats, ground colour, mean luminance, mean saturation, and what physically
   occupies the frame.
2. **Brand intake.** Official marks live on the brand's own guidelines
   subdomain, served gzipped, mixed in with their "Please Don't" examples.
   Render a light and dark contact sheet and look before naming anything.
3. **Rebuild the product UI as live DOM carrying real strings**, then shoot it
   at 3x to 5x into flat plates with `_tools/shoot.mjs`. Interfaces are rebuilt.
   World art is rendered and composited. Nothing is faked.
4. **Cut parts, not screens.** A whole screen is a slab, and a slab cannot be
   animated, only slid. Ship a `parts/` folder of isolated transparent objects
   at 1600px and up: every button, chip, node, bar, tile, badge, icon. Plus 4K
   landscape plates for the ground.
5. **Split the mark into its own layers.** An official SVG splits into layers
   that stack back pixel perfect. Verify it: stacked against the original, the
   maximum difference on any pixel should be 1 of 255, which is antialiasing.
   Then the film **assembles** the mark instead of cutting to it.
6. **Optimise.** Every file under about 350 KB, the whole kit under about 4 MB,
   so it survives being carried into a Claude Design project.
7. **Open every file and log its defects in `KIT.md`.** Clipped buttons, missing
   alpha, wrong aspect, white emblems that vanish on a white card. Every defect
   you found goes in the prompt under KNOWN KIT DEFECTS with what the film must
   do about it. If you found none, say you opened every file and found none.

Aspect is a real defect class. Rendering 1200x800 chips into a 224x160 box
stretches every flag horizontally by 7%, which is subtle enough to survive
review and wrong in every frame.

Published artifacts run under a strict CSP that blocks every external host, so
nothing in a kit may point at a CDN. Everything is a project file or a data URI.

## 5. Write `OM_SCENES` first

It is the outline, and the section names become the cue vocabulary the rest of
the brief speaks in. Six sections is a good film. Ten is a slideshow.

The Vercel film, verbatim, as the shape to aim at:

```
The Blade 4.6 · Aperture 2.0 · Preview 2.0 · Production 2.25 ·
Everywhere 2.25 · Scale 2.25 · Convergence 2.0 · Lockup 1.75
```

Each `desc` is one sentence naming a physical event, not a mood. "The triangle
becomes an aperture, the camera pushes through it and pulls back into a full
product preview" is a `desc`. "A sense of speed and possibility" is not.

## 6. The transformation chain, as match anchors

Name the one object that carries the film and forbid breaking it.

> Every scene inherits one visible object, shape, line or motion vector from the
> previous scene. Never: scene fades out, empty background, next scene fades in.
> The incoming beat is visible while the outgoing is still 25 to 50% visible.

Worked examples from films that shipped:

- **Duolingo.** One green circle never leaves the screen: Duo's mark, then the
  lesson node, then the thing every name collapses into, then Duo again.
- **Spotify.** The track *Midnight Signal* is printed on the player bar file and
  on the phone file, so the same song moves bar to desktop to phone to lineup.
- **Emulo.** The faceless silhouette is on screen at T=0 and in all six
  sections, and the payoff is the solid robot arriving in front of it so the two
  together are exactly the shipped mark.

**The colour rule that comes with this.** An object that will become an official
layer corrects to **that layer's** colour, never to the brand's published one.
Duolingo's `duo-01-field.svg` is filled `#50C800` while Feather Green `#58CC02`
is the guidelines and product value. Correcting to the published green would
have stepped colour on the exact frame that must be invisible. The file wins
over the guidelines page.

## 7. The prompt

Fill this. Delete nothing structural. A brief that is long and contains no
filenames is the wrong brief.

```text
You are directing a <N> second <vertical|landscape> spec commercial for <BRAND>,
built on the animations-v3 composition engine. Cinematic. Few objects, large, lit.

FORMAT. WRITE IT LITERALLY.

  <CompositionStage width={<W>} height={<H>} bg="<ground hex>"
                    scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>

<W> wide by <H> tall. If your composition is <wider than it is tall | not
<W>x<H>> you have failed before anything else is judged.

THE ONE LAW

Every object on screen is a file from the list below. The timeline never draws a
<BRAND> screen, never draws the mark, never stands text in with a grey
rectangle, never approximates imagery with a gradient. It places, masks, crops,
lights and moves those files.

If a beat needs an object the kit does not contain, say so and stop. Do not
substitute a div. If you cannot resolve the paths, tell me before building
anything rather than drawing replacements.

REFERENCES

<one job per reference, with a do-not-copy list. Then: do not average them.>

THE ASSETS

  <every file, its pixel size, and one line on what it is for. Name which
   element level parts exist and what they are meant to do on their own.>

THE BAR, AND WHAT IT RULES OUT

<the genre exclusions, not craft notes. Genre exclusions are what the model
already understands: six disconnected slides, a SaaS product tour, a dashboard
montage, a conference presentation, a developer tutorial, a browser screen
recording, a wall of technology logos, a generic futuristic AI advertisement.>

- no paragraphs, no terminal dumps, no reports, no lists of findings. If a frame
  needs more than about eight words to be understood, the frame is wrong
- no charts, no graphs, no dashboards, no code editors
- no neon, no glow, no purple, no gradient meshes, no particle fields

At most ONE object carries text in any frame, and that object is a real thing
with edges, not a caption floating in space.

GROUND AND LIGHT

Measured off the reference film, not chosen:

  frame average sits between <hex> and <hex>, <channel> dominant
  mean luminance <n> of 255
  mean saturation <n>

The base is <hex> and never pure black. One warm key light, <position>, fixed.
Every object carries a contact shadow and a cast shadow. Depth is blur and
scale. Bloom on <named elements> only. One grain pass at low opacity.

LOCKED COPY

  <three or four lines, nothing else>

No feature list, no metric, no URL, no invented tagline, no subtitle under the
logo. Set in <typeface, and say plainly if it stands in for a licensed brand
font>. Revealed through a horizontal mask, never typed letter by letter.

THE ENGINE

<script>window.OM_SCENES = '[
 {"name":"<Name>","dur":<s>,"desc":"<one plain sentence>"},
 ...
]';</script>
<script>window.OM_PLAYBACK = '{"mode":"loop"}';</script>

Key everything to T from useComposition() against those cues. One continuous
composition, zero cuts.

  MOTION.slam    Easing.easeOutExpo     arrivals and impacts
  MOTION.snap    Easing.easeOutBack     landings, overshoot capped at 6%
  MOTION.drive   Easing.easeInOutQuart  travel, light, drift
  MOTION.settle  Easing.easeOutQuart    the final resolve

Nothing eases outside those four. No elastic, no Back curve on an official brand
file, no setTimeout, no requestAnimationFrame, no useEffect painting, no wall
clock, no random, no CSS keyframes running on their own. Render everything from
T so any seek reproduces its frame. Never render <Captions>. Never edit
animations-v3.jsx.

THE ANCHOR

<the one object physically present across beats that carries the film. Name it
and forbid breaking it.>

THE SECTIONS

<one block per OM_SCENES entry. Each block carries:
   what is on screen and which file
   coverage as a percentage of frame width for every hero object
   what causes the next thing to happen
   a "Do not:" line specific to this beat>

CAMERA

<N> events and nothing else moving the frame:

  1. <cue range>   <what>
  2. <cue range>   <what>

Between them the camera holds and the objects do the work. No drifting, no
breathing zoom, no shake, no orbit, no continuous parallax.

Motion budget:
  60% local object and geometric transformation
  20% surface, lighting, parallax, environment
  20% camera scale and reframing

WHERE THE COLOUR COMES FROM

<name the objects allowed to be saturated, and say the ground picks up their
colour. Forbid coloured light with no object making it.>

MOTION SHAPE, MEASURED

<the numbers from §8. State the reference figures and the floor this film must
clear.>

KNOWN KIT DEFECTS

  <every defect you found opening the files, and what the film must do about it>

FAILURE CONDITIONS

<15 to 25 lines, each a specific observable defect for THIS film. §10.>

BEFORE YOU BUILD, RETURN AND STOP

1. the CompositionStage line, so I can see the dimensions
2. the OM_SCENES literal
3. a <N> frame storyboard, and per frame: which asset, its coverage as a
   percentage of frame width, how many elements are moving, and the WORD COUNT
   on screen. Any frame over eight words is a defect, tell me and fix it
4. your impact list with times
5. confirmation the anchor object is on screen in every section
6. anything you cannot verify

Do not animate until I approve.
```

Then `PROMPT-2.md`, the approval:

```text
Approved. Before you build, confirm these four:

  <four checks specific to this film, each one a thing that was measured off the
   reference and could quietly go missing>

Now build it from the approved storyboard. Deterministic, keyed to T, kit files
only. When it is running, show me <the cue boundaries> at full size before
anything else.
```

## 8. The motion floor, measured

Zero cuts alone reads dead. Cut rate and energy are two separate specifications
and a brief has to carry both.

Frame to frame motion energy, sampled at 15fps:

| Film | mean | peak | frames above 4.0 | near-still | cuts |
|---|---|---|---|---|---|
| Vercel, the reference | 2.378 | 13.005 | 22.0% | 26.2% | zero |
| Duolingo v1 | 6.557 | | 40.2% | | zero |
| Duolingo v2, rejected | 2.565 | 76.545 | 13.6% | **50.2%** | zero |

Read the v2 row. Half of that film is frozen. The mean looks acceptable only
because a handful of enormous transitions drag it up, and the peak is six times
the reference. That is the signature of a slideshow with big transitions between
static cards. A motion designer produces the opposite shape: a lower peak and
far less stillness, because something is always moving.

The floor to write into a prompt:

- near-still frames below 26%
- no single frame above 25 energy
- frames above 4.0 above 22%
- at least two elements mid-transformation at every moment that is not a hold
- a growing hero gains at least 35% of frame width per 0.5s
- holds are named and counted. Two or three in a film, plus the final lockup

**The freeze test.** If a frame's motion would survive freezing every gradient
in it, the motion is real. A continuously drifting pool or breathing gradient
lowers the near-still number without adding one frame of real motion. That is
the metric moving, not the film, and we have shipped a bad video that exact way
before by optimising the measurement instead of the thing it measured.

**Luminance is one film or two.** Measured on a rejected build: greetings 19.9,
transition 75.1, UI middle 226.2, outro 180.4. A 19.9 to 226.2 span is not a
grade change, it is a different film glued between two designed worlds. Name one
ground for the whole piece and a ceiling for the brightest section.

**Coverage stops things coming out tiny.** Hero object 25% to 45% of frame width
as a floor, and higher on payoff beats. In the rejected middle the nodes sat at
roughly 6%, which is why nothing read and nothing felt like it was moving.

**The source material never leaves the middle.** Measured on two boards that came
back: the product was off screen for 72% and 68% of running time. Both opened on
the real product, spent the middle on coloured rectangles, and returned for a
closing beat. That is a template reel with a product bookend, and it is the
single reason both read as cheap. State a floor as a percentage of frame area and
put "any beat takes place on a bare ground" in the failure conditions.

The rule is about **chrome**, not content. Name the product's own components off
the screenshot, the sidebar, the tab strip, the chip row, the player bar, and
require them present by name. The strongest form: let the product's own controls
cause the film. A chip being struck is what recolours the page. Then collision,
causality and real product behaviour are the same move, and the film cannot be
described without naming the product.

## 9. What physically happens in the beat

Everything in section 8 can be green on a film that comes back rejected. The
verbatim verdict on one that was: "its just boring words with ok animations
instead of showing crazy animation crazy things happening with animation like
you did with the hook with the puppet inside the chatbox ui." That build cleared
the structure, the coverage floors and the energy floors. It was still a
sequence of phrases arriving over a lit ground.

Read `videos/_handoff/_film-sources/ITERATION-LOG.md` before you write a brief.
It is the only file that records what was rejected, in his words, next to what
replaced it. Finished code cannot tell you the words were there first.

### The per-beat test

For every `OM_SCENES` entry, write three lines before anything is built. If line
2 is empty, the beat is a card, and a card reads as boring however it eases in.

1. the phrase on screen
2. **a body** doing something, named with a verb: dives, hammers, hops, is pulled off its feet
3. the surface it does it to, named as a kit file or a rebuilt UI part

**A body is a character or an object with mass. A word is not a body.** Letters
that hammer, shatter or fly are still kinetic typography, which is the exact
thing that got rejected. If line 2 names the phrase itself, the test fails.

Rejected: "Create completely" over a fixed box at `left: 1090, top: 224,
width: 470, height: 630`, whose children only widen in place
(`claude-film.jsx:530-537`). Approved: nine blocks fly in from
`left: tx + Math.cos(a) * 1000 * (1 - p)`, each carrying `blur(6 * (1 - p))` and
`rotate((1-p) * 26deg) scale(.7 + .3*p)` on a 52ms stagger, while a body hammers
alongside and squashes on every landing (`claude-master.jsx:1012-1044`).

Note what separates them, because it is not the count of pieces. Nine flying
rectangles with no body beside them is still the rejected beat with more parts.

### Ban grow-in-place

Fixed `left` and `top` with `width`, `height` or `opacity` animating inside the
object's own bounding box is what a model writes by default, because it is safe
and can never collide. Every hero entrance carries position, rotation, blur and
scale at once, and starts **at least 0.35 of stage width outside where it
lands**. Express every distance as a fraction of stage width, never in raw
pixels: the films are authored at 1920x1080 and the rebuilt UI at 2560x1600, so
a pixel figure copied between them is wrong by a third.

An object that travelled has a before-state the viewer never saw, so its arrival
carries information. An object that grew was always there.

### The character must be attached to real geometry

Derive the body's transform from the target object's live animated values every
frame, including rotation:

```
const rad = bars[0].rot * Math.PI / 180;
cx0 = bars[0].x - Math.cos(rad) * bars[0].w / 2;
cy0 = bars[0].y - Math.sin(rad) * bars[0].w / 2 - 34;
rotc = bars[0].rot - 90;
```

That expression is the tip of the rotated bar, and `rot - 90` keeps the body
standing perpendicular on it (`claude-master.jsx:833-838`). Generate paths from
the target's own data too, so a climb right to left is an emergent property of
the chart rather than an authored path that happens to match.

**The reference film also gets this wrong, and you should see where.** In the
research dive the source cards compute `cy = -180 + 1460 * easeInOutCubic(rDive)`
while the critter three lines below is `y = -200 + 1500 * easeInOutCubic(rDive)`.
Two independent expressions off one progress variable, 20px apart at the start
and 60px at the end. Delete the critter and every card lights exactly the same.
It reads acceptably and it is still a sticker, and it will drift the first time
anything is retimed. Couple to the object, not to a shared clock.

### Simulated UI, operated at speed

He asked for this by name: "i want like in the reference video when it shows like
a mimic ui fast paced doing on it with the mouse and text and stuff." Section 7
bans faking a screen as static art. It does not ban rebuilding one. **Never draw
a grey rectangle standing in for a product screen. Rebuild the UI as live DOM,
one element per part, and operate it.** When a film has a product in it, it must
carry at least one operated-UI beat.

- **Rebuild, do not screenshot.** `ui.jsx` builds sidebar, top bar, greeting, six
  shortcut tiles and a six-card carousel as separate positioned divs. A
  screenshot can only be pushed and cropped. A DOM rebuild lets one card lift.
- **The cursor is an object with momentum**, and every key carries its intent in
  a comment. `film.jsx` BALL_RAW is 39 keyframes: `{ t: 2.80, x: 812, y: 872 }`
  grabs the progress knob, `{ t: 3.86, x: 960, y: 836 }` punches play. A failure
  is recorded in the same file: easeInOut on consecutive keys made the roll stop
  and restart at every card. Use one ease-out across the span and let friction
  decelerate.
- **Sample the path, then derive everything from one number.**
  `const bPrev = ballAt(T - 0.022); const speed = Math.hypot(vx, vy)` feeds
  squash `clamp(speed/5200, 0, .46)`, heading `Math.atan2`, motion blur
  `clamp(speed/900, 0, 9)`, trail opacity and audio gain. Hand-keying five of
  those separately is how a fast move ends up mismatched.
- **Every UI state change is caused by an impact**, and the two tables share
  timestamps: `IMP = [0.30, 2.62, 3.86, 4.24, ...]` against
  `HOME_TRIG = [4.24, 4.52, 4.80, 5.08, ...]`, each region a 40ms staggered
  cascade off its own hit. A screen that assembles on a schedule is a slideshow.
  A screen that answers 300ms after something hits it is alive.
- **One impact function drives shake, camera bump and blur together**, sign
  flipping on alternate hits: `Math.pow(1 - d/.34, 2.1) * Math.sin(d*108) *
  (i % 2 ? 1 : -1)`, consumed as `cam.s *= 1 + sh*.022`, `shakeX = sh*11`,
  `mBlur = min(abs(sh)*4, 7)`. Fifteen hits in sixteen seconds, none of them
  feeling repeated.
- **A control being operated reads its value off the cursor**, it is not keyed
  alongside it: `scrubF = clamp((b.x - TR0)/(TR1 - TR0), 0, 1)`. Two objects
  keyed in parallel drift a few pixels and the shot reads fake.
- **A click is three asymmetric ramps**: 80ms down, 20ms held, 120ms up, with the
  button swelling 12% starting 160ms before contact. Symmetric press animation
  reads as a CSS demo.
- **Passing near a thing knocks it, by distance not by keyframe**:
  `knock = rolling * max(0, 1 - abs(b.x - CARD_CX(i))/120)`. Hand-authored
  reaction windows break the moment you retime the roll. A falloff survives it.
- **Dim the interface under the copy, never cut away from it.** `DIM` keys
  brightness across the whole UI, 1.0 down to 0.42 then 0.26, plus a corner
  scrim. The app stays visibly running behind the words.

### Delete these from the background

The fix for a boring beat is more happening in the middle of the frame and less
at the edges. Deleted from the approved build: giant background words, the
word-storm, decorative hairlines, ambient panels behind the hero, and the light
field cut to a single soft wash. `STORM` is still declared empty at
`claude-master.jsx:192-193` with its renderer live, which is what deleting it
properly looks like.

### Occupied holds

Section 12 law 5 fixes the camera to three moves. This is its other half: **fill
every camera lock with a body doing something.** All three locks in the approved
film are occupied, and the longest one is the busiest stretch in the picture.
When the frame holds, the content earns the motion.

### Gate the weakest beat, not only the opening

The eight-second gate in the next section catches a bad opening. It cannot catch
a strong opening followed by three flat beats, which is exactly what was rejected
here: "the intro very strong... the only parts i dont like is the think create
handoff."

So after the opening passes, render the **capability stretch** and look at that
too. Do not self-grade it. Put the contact sheet in front of the person who asked
for the film and ask which seconds are the worst. Their answer is the list.
Rebuild those beats against the per-beat test above, and only then build the rest.


## 10. Build it, look at it, then continue

Do not build the whole film and then find out.

1. **Build the first 5 to 8 seconds only.** Wire `build/index.html` and
   `build/piece.jsx` against the kit. The host scaffold is fixed, and
   `videos/_kits/duolingo/build/` is the working copy to clone:

```html
<script>window.OM_SCENES = '[...]';</script>
<script>window.OM_PLAYBACK = '{"mode":"loop"}';</script>

<script src="../../node_modules/react/umd/react.development.js"></script>
<script src="../../node_modules/react-dom/umd/react-dom.development.js"></script>
<script src="../../node_modules/@babel/standalone/babel.js"></script>
<script type="text/babel" src="../../_engine/animations-v3.jsx"></script>
<script type="text/babel" src="./piece.jsx"></script>

<script type="text/babel">
  /* ?still=1 freezes the transport so the capture harness can seek
     deterministically. The shipped composition autoplays as normal. */
  const still = new URLSearchParams(location.search).has('still');
  ReactDOM.createRoot(document.getElementById('root')).render(
    <CompositionStage width={1080} height={1920} bg="#06120A"
                      autoplay={still ? 'false' : 'true'}
                      loop={still ? 'false' : 'true'}
                      scenes={window.OM_SCENES} playback={window.OM_PLAYBACK}>
      <Piece />
    </CompositionStage>
  );
</script>
```

   `piece.jsx` opens with one path constant and the four motion helpers, and
   nothing else in the file knows where the kit lives:

```js
const BASE = '../ATTACH/';   // the ONLY line that changes when assets move

const MOTION = {
  slam:   (o) => animate(Object.assign({ ease: Easing.easeOutExpo },    o)),
  snap:   (o) => animate(Object.assign({ ease: Easing.easeOutBack },    o)),
  drive:  (o) => animate(Object.assign({ ease: Easing.easeInOutQuart }, o)),
  settle: (o) => animate(Object.assign({ ease: Easing.easeOutQuart },   o)),
};
```

2. **Shoot it and look.** Snapshots cost seconds, renders cost 25 minutes.

```bash
node videos/_kits/_tools/frames.mjs <project> 0,0.6,1.4,2.2,3.0,4.1,5.2,6.4,7.6
```

   The tool prints the stage size and duration, flags a wrong aspect, and prints
   every page error under `PAGE ERRORS:`. A single
   `Failed to load resource: net::ERR_FILE_NOT_FOUND` means the film is drawing
   nothing where an asset should be, and it is blocking. Fix `BASE` or the kit
   path before you judge a single frame.

   The seek listener is on the **stage element**, not on `document`; dispatching
   on `document` silently does nothing and every frame comes back identical.
   The stage autoplays, so seek before you shoot.
3. **Gate on quality before continuing.** Open the frames at 1:1, not as a
   contact sheet. If the first 8 seconds are not the level, nothing after them
   will be, and every hour spent on the back half is spent twice.
4. Only then build the rest.
5. **Diff the template against the generated file** whenever another tool has
   touched the project.

## 11. Failure conditions

Generic failure conditions catch nothing. Write 15 to 25 lines, each a specific
observable defect for **this** film. These are the ones that recur, as a
starting set to specialise:

- the composition is not `<W>x<H>`
- any object on screen was drawn rather than placed
- the ground is pure black anywhere
- a frame is empty between beats, or a beat takes place on a bare ground
- any frame contains a paragraph, a report, a terminal dump, or a list
- more than one object carries text in the same frame
- a frame needs more than eight words to be understood
- the anchor object is absent from any section
- the mark or lockup is stretched, skewed, rotated, glowed, recoloured, extruded
  or animated
- a gradient stands in for real imagery
- the camera moves outside its named events
- the final hold is shorter than 1.5 seconds, or the mark is still moving on the
  final frame
- the film cuts, or `<Captions>` is rendered
- `animations-v3.jsx` was edited
- it reads as a product tour rather than a film

## 12. Verify, with output

A green command is not visual approval. Report the numbers, do not estimate
them.

```bash
node videos/_kits/_tools/frames.mjs <project>
```
stage dimensions, duration, and the contact sheet. Wrong aspect fails here.

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,bit_rate,duration -of default=nw=1 <export>.mp4
```
the floor for a landscape film is 1920x1080, 60fps, 4.69 Mbps.

```bash
ffmpeg -i <export>.mp4 -vf "select='gt(scene,0.2)',showinfo" -f null - 2>&1 | grep -c showinfo
```
cut count. A promo should return zero. `scene_score` measures nothing else on a
zero-cut film, so it is a cut detector and never a motion metric.

Motion energy, near-still percentage, peak and per-section mean luminance are
measured off the export, not estimated, and reported next to the floors in §8.

Browser frames carry zero motion blur, so an export reads as stop-motion next to
the preview. Render at 240fps and `tmix=frames=4` down to 60. Smoothness and
sharpness are separate problems: duplicate frames, BT.601 versus BT.709, chroma
and pixel ratio are the measured causes, and `-tune animation`, `-tune grain`
and `gradfun` are all wrong advice.

For a vertical film the Instagram feed crops the top 285 px, so nothing load
bearing goes there.

## 13. The laws that cost real renders

Each of these was paid for once. None of them is a preference.

1. **Reference roles are assigned, never averaged.** Vercel for transformation
   and depth. Spotify for camera and easing. Write "do not average the
   references" verbatim.
2. **Build the first 5 to 8 seconds and gate on quality before continuing.**
3. **Never fix a concept problem with easing.** If a transition reads as a cut,
   the thing you animate and the thing you land on are two different objects.
   No curve repairs that. Split the mark into layers and assemble it.
4. **A flash cannot replace geometry in a transition.** Brightness that hides a
   missing seam is a defect. Every luminance jump names the object state,
   evidence or medium change it accompanies.
5. **The camera moves once, at the moment that matters.** Three events in a 12
   second film, and nothing else moving the frame. Between them the camera holds
   and the objects do the work.
6. **Objects must exceed the frame.** Everything safely centred reads as
   scaling, not as camera movement. The player bar at its peak is wider than the
   frame. The screen fills past its edges.
7. **Zero cuts alone reads dead.** Energy is specified separately from cut rate,
   with the numbers in §8.
8. **Rendered assets, not browser-drawn shapes.** A div is not a card, a
   gradient is not album art, a triangle you drew is not the mark. If the kit
   does not have it, stop and say so.
9. **Nothing fades in.** Every entrance hits something and the impact causes the
   next beat. A particle that is not consumed by the letter it belongs to is
   litter, not a cause. Either it causes the thing or it is not there.
10. **2D, never 3D.** The cinematic look is flat layer compositing. The camera
    push is `scale()` on a container and depth is blur plus scale. 3D scenes are
    what produce the game look and the lag. Flat compositing is not flat
    lighting: name a light source with a position, give grounds a falloff, give
    every object a contact shadow and a cast shadow.
11. **Every number on screen is a real published figure**, read on a stated date
    and hardcoded. Never invent one, round one, animate a count up from zero, or
    turn it into a chart.
12. **Do not open a prompt with an essay about why the last attempt failed.**
    These prompts do not apologise or narrate history. They specify. Do not
    describe a mood where a number will do. Do not write a scene without a
    coverage percentage.

## 14. Working files

| What | Where |
|---|---|
| the engine and its contract | `videos/_kits/_engine/` |
| kit split, brief template, tools | `videos/_kits/README.md`, `_BRIEF-TEMPLATE.md`, `_tools/` |
| the 26 section anatomy and the two gates | `docs/MASTER-PROMPT-STANDARD.md` |
| worked prompts that shipped | `videos/_kits/{spotify,duolingo,emulo}/PROMPT-*.md` |
| the correction rounds, which is where the lessons are | `videos/_kits/duolingo/PROMPT-IMPROVE*.md`, `PROMPT-V3*.md` |
| the reference film | `videos/vercel-spec/` |
| short-form, a different job | `videos/README.md` and its router |
