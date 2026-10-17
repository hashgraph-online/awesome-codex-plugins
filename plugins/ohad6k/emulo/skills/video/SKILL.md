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
   second is the video profile. Both outrank anything below: where the person's
   own mined rules disagree with a default in this skill, theirs win.
5. If the project has its own video docs or router, read them first and follow
   them for anything they cover.

## 1. What you hand back

**A folder the person can upload to Claude Design and get a film.** That is the
deliverable. Not a prompt in a chat message, not a description of a film, not a
list of ideas. A folder.

Build it in the project, in a folder named for the brand or the film, in this
shape:

| # | Artefact | Why it is there |
|---|---|---|
| 1 | `PROMPT.md` | the brief. One page, in the engine's language |
| 2 | `START-HERE.md` | **the upload order.** Which files, in which order, in one message. Without it the person guesses and the guess is wrong |
| 3 | `ATTACH/` | every asset the film needs, including `animations-v3.jsx` itself |
| 4 | `frames/` | reference stills whose **filenames carry the instruction** |
| 5 | `KIT.md` | the manifest: every file, its pixel size, its known defects |

Optionally, and only after the five above are finished: `build/piece.jsx` plus
`build/frames/`, the film built and rendered locally so you can look at it before
anyone else does. That is verification, not the deliverable. A kit with no local
build still ships. A local build with no kit does not.

### The three things that decide whether the folder works

**Ship the engine inside `ATTACH/`.** `animations-v3.jsx` goes in the folder with
the assets. Claude Design needs the runtime it is being asked to write against.
Leaving it out is a common way a good prompt produces a bad film.

**Isolated parts, never a screenshot of a whole screen.** One object per file,
transparent, 1600px minimum on the long edge, plus large plates at the film's
aspect ratio for the ground. A whole screen dropped in is a slab and reads as
broken. Films built this way fail on missing assets far more often than on
prompt length.

**Put the instruction in the filename.** `REF_03_object-becomes-the-mark.png`
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

## 2. The engine

`animations-v3.jsx` is the Claude Design composition runtime. Read its header
once, then work from this table.

**Never edit `animations-v3.jsx`.** Its own header says re-running
`copy_starter_component` overwrites it, so every change made there is lost on the
next host copy. The leverage is in the brief.

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
ordinary interpolation. That makes zero cuts and one object transforming across
the film the engine's defaults instead of things a brief has to fight for.

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
<script>window.OM_SCENES = '[{"name":"Strike","dur":2.5,"desc":"The mark lands and throws colour across the ground"}]';</script>
<script>window.OM_PLAYBACK = '{"mode":"loop"}';</script>
```

**Easing, the complete list.** `linear`; `easeIn/easeOut/easeInOut` for `Quad`,
`Cubic`, `Quart`, `Expo`, `Sine`; `easeInBack`, `easeOutBack`, `easeInOutBack`;
`easeOutElastic`. Back and elastic overshoot, so they belong nowhere near a logo
or an official brand file.

**Render from `T` only.** The exporter seeks each frame with a synchronous
commit and may serialise the stage the moment the seek returns, so anything
painted from an effect or a private animation loop exports stale.

**Captions only when asked.** Render `<Captions>` only when the brief or the
person's video profile asks for burned-in captions. Many people add their own
afterwards, and a burned caption ruins that. Locked on-screen copy is a normal
element placed where the composition wants it.

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
line "do not average the references" the model blends the styles into mush.

| Reference | Its one job | Never take |
|---|---|---|
| a film the person names for motion | transformation, depth, scale contrast | its palette, its brand |
| a film the person names for camera | camera and easing: the events, the hold, the settle | its colour, its product |
| the brand's own material | identity, typography, the exact mark | its interface layouts as a template |

Write it into the prompt in this shape:

```
Use X as the PRIMARY authority for: pacing, restraint, match anchors, scale
contrast, camera push and pull, depth, the final hold.
Use Y only for: monochrome identity, typography, exact logo, clarity.

Do not copy X's design. Do not introduce X's colour. Do not average the
references.
```

If the person has several finished films on the same engine, read at least three
and ask what is the *same* in all of them: how a scene list is declared, where
the transformation chain is expressed, how an entrance is timed against the
thing it hits, how the last three seconds are built. The constants are the
workflow. Anything present in only one is that film's costume.

**Build in stages, and gate between them.** Build the first five to eight
seconds. Render. Look at a contact sheet. Only then continue. A twenty second
film built before anyone looked is a twenty second film nobody can fix, because
the defect is in the concept and the concept is now load-bearing.

## 4. Build the kit before you write the prompt

A long, detailed prompt with no real assets still comes back as grey rectangles
standing in for text and a hand-drawn shape in place of the real mark, because
placeholders are the only thing a model can draw with nothing real to place.

**Claude Code builds the kit. Claude Design animates it.** That split is the
pipeline.

1. **Measure the reference at 1:1**, one file, never a contact sheet. Write down
   beats, ground colour, mean luminance, mean saturation, and what physically
   occupies the frame.
2. **Brand intake.** Official marks usually live on the brand's own guidelines
   or press page, mixed in with their "don't do this" examples. Render a light
   and dark contact sheet and look before naming anything.
3. **Rebuild the product UI as live DOM carrying real strings**, then shoot it
   at 3x to 5x into flat plates with a headless browser. Interfaces are rebuilt.
   World art is rendered and composited. Nothing is faked.
4. **Cut parts, not screens.** A whole screen is a slab, and a slab cannot be
   animated, only slid. Ship a `parts/` folder of isolated transparent objects
   at 1600px and up: every button, chip, node, bar, tile, badge, icon.
5. **Split the mark into its own layers.** An official SVG splits into layers
   that stack back pixel perfect. Verify it: stacked against the original, the
   maximum difference on any pixel should be about 1 of 255, which is
   antialiasing. Then the film **assembles** the mark instead of cutting to it.
6. **Optimise.** Keep each file small (a few hundred KB) and the whole kit a few
   MB, so it survives being carried into a Claude Design project.
7. **Open every file and log its defects in `KIT.md`.** Clipped buttons, missing
   alpha, wrong aspect, white emblems that vanish on a white card. Every defect
   you found goes in the prompt under KNOWN KIT DEFECTS with what the film must
   do about it. If you found none, say you opened every file and found none.

Aspect is a real defect class. Rendering 1200x800 chips into a 224x160 box
stretches every one horizontally by 7%, which is subtle enough to survive review
and wrong in every frame.

Published artifacts may run under a strict CSP that blocks external hosts, so
nothing in a kit should point at a CDN. Everything is a project file or a data URI.

## 5. Write `OM_SCENES` first

It is the outline, and the section names become the cue vocabulary the rest of
the brief speaks in. Six sections is a good film. Ten is a slideshow.

Each `desc` is one sentence naming a physical event, not a mood. "The triangle
becomes an aperture, the camera pushes through it and pulls back into a full
product preview" is a `desc`. "A sense of speed and possibility" is not.

## 6. The transformation chain, as match anchors

Name the one object that carries the film and forbid breaking it.

> Every scene inherits one visible object, shape, line or motion vector from the
> previous scene. Never: scene fades out, empty background, next scene fades in.
> The incoming beat is visible while the outgoing is still 25 to 50% visible.

For example, one coloured circle that is the brand mark, then a lesson node, then
the thing every name collapses into, then the mark again. Or one track title
printed on every product surface, so the same song moves from bar to desktop to
phone.

**The colour rule that comes with this.** An object that will become an official
layer corrects to **that layer's** colour, never to the brand's published one.
Brand files and brand guideline pages often disagree by a few values, and
correcting to the guideline value steps the colour on exactly the frame that
must be invisible. The file wins over the guidelines page.

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
- no neon, no glow, no gradient meshes, no particle fields

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
T so any seek reproduces its frame. Never edit animations-v3.jsx.

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

<the numbers from section 8, measured off the reference. State them and the floor
this film must clear.>

KNOWN KIT DEFECTS

  <every defect you found opening the files, and what the film must do about it>

FAILURE CONDITIONS

<15 to 25 lines, each a specific observable defect for THIS film. Section 11.>

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

Zero cuts alone reads dead. Cut rate and motion energy are two separate
specifications and a brief has to carry both.

Measure frame to frame motion energy on the reference, sampled at a fixed rate
(15fps is enough): the mean, the peak, the share of frames above a threshold, and
the share of near-still frames. Then measure your own build the same way.

A mean that looks fine can hide a slideshow: a handful of enormous transitions
drags the mean up while half the film is frozen. That shape, a peak far above the
reference and a large near-still share, is static cards with big transitions
between them. A motion designer produces the opposite: a lower peak and far less
stillness, because something is always moving.

Floors to write into a prompt, set against the reference's own numbers:

- near-still frames no higher than the reference's share
- no single frame far above the reference's peak
- frames above the threshold at least the reference's share
- at least two elements mid-transformation at every moment that is not a hold
- a growing hero gains a large share of frame width per half second
- holds are named and counted. Two or three in a film, plus the final lockup

**The freeze test.** If a frame's motion would survive freezing every gradient
in it, the motion is real. A continuously drifting pool or breathing gradient
lowers the near-still number without adding one frame of real motion. That is
the metric moving, not the film.

**Luminance is one film or two.** A build that goes from a very dark section to a
nearly white one and back is not a grade change, it is a different film glued
between two designed worlds. Name one ground for the whole piece and a ceiling
for the brightest section.

**Coverage stops things coming out tiny.** Hero object 25% to 45% of frame width
as a floor, and higher on payoff beats. Nodes at a few percent of the frame do
not read and do not feel like they move.

**The source material never leaves the middle.** A film that opens on the real
product, spends the middle on coloured rectangles, and returns for a closing beat
is a template reel with a product bookend. State a floor for how much of the
running time the product is on screen, as a percentage of frame area, and put
"any beat takes place on a bare ground" in the failure conditions.

The rule is about **chrome**, not content. Name the product's own components off
the screenshot, the sidebar, the tab strip, the chip row, the player bar, and
require them present by name. The strongest form: let the product's own controls
cause the film. A chip being struck is what recolours the page.

## 9. What physically happens in the beat

Everything in section 8 can be green on a film that is still boring: a sequence
of phrases arriving over a lit ground clears structure, coverage and energy
floors and still reads as words with animation.

### The per-beat test

For every `OM_SCENES` entry, write three lines before anything is built. If line
2 is empty, the beat is a card, and a card reads as boring however it eases in.

1. the phrase on screen
2. **a body** doing something, named with a verb: dives, hammers, hops, is pulled off its feet
3. the surface it does it to, named as a kit file or a rebuilt UI part

**A body is a character or an object with mass. A word is not a body.** Letters
that hammer, shatter or fly are still kinetic typography. If line 2 names the
phrase itself, the test fails.

### Ban grow-in-place

Fixed `left` and `top` with `width`, `height` or `opacity` animating inside the
object's own bounding box is what a model writes by default, because it is safe
and can never collide. Every hero entrance carries position, rotation, blur and
scale at once, and starts **at least 0.35 of stage width outside where it
lands**. Express every distance as a fraction of stage width, never in raw
pixels, so a figure survives a change of stage size.

An object that travelled has a before-state the viewer never saw, so its arrival
carries information. An object that grew was always there.

### Attach a character to real geometry

Derive the body's transform from the target object's live animated values every
frame, including rotation, rather than from a separate expression that happens to
use the same progress variable. Two expressions off one clock drift apart the
first time anything is retimed, and the body reads as a sticker. Couple to the
object, not to a shared clock.

### Simulated UI, operated at speed

When a film has a product in it, carry at least one operated-UI beat. **Never draw
a grey rectangle standing in for a product screen. Rebuild the UI as live DOM,
one element per part, and operate it.**

- **Rebuild, do not screenshot.** A screenshot can only be pushed and cropped. A
  DOM rebuild lets one card lift.
- **The cursor is an object with momentum.** Key its path with a comment on each
  key saying what it is about to do. Use one ease-out across a span and let
  friction decelerate; easing in and out on every key makes it stop and restart.
- **Sample the path, then derive everything from one number.** Speed from the
  sampled path feeds squash, heading, motion blur and trail opacity. Hand-keying
  those separately is how a fast move ends up mismatched.
- **Every UI state change is caused by an impact**, and the impact and state
  tables share timestamps. A screen that assembles on a schedule is a slideshow.
  A screen that answers a few hundred milliseconds after something hits it is
  alive.
- **One impact function drives shake, camera bump and blur together.**
- **A control being operated reads its value off the cursor**, it is not keyed
  alongside it. Two objects keyed in parallel drift a few pixels and the shot
  reads fake.
- **A click is three asymmetric ramps**: fast down, a brief hold, slower up, with
  the button swelling slightly just before contact. A symmetric press reads as a
  CSS demo.
- **Passing near a thing knocks it, by distance not by keyframe**, so the
  reaction survives retiming.
- **Dim the interface under the copy, never cut away from it.** The app stays
  visibly running behind the words.

### Keep the edges quiet

The fix for a boring beat is more happening in the middle of the frame and less
at the edges: no giant background words, no word storms, no decorative hairlines,
no ambient panels behind the hero.

### Occupied holds

Section 13 law 5 fixes the camera to a few moves. This is its other half: **fill
every camera lock with a body doing something.** When the frame holds, the
content earns the motion.

### Gate the weakest beat, not only the opening

The eight-second gate in the next section catches a bad opening. It cannot catch
a strong opening followed by three flat beats. So after the opening passes,
render the middle stretch and look at that too. Do not self-grade it. Put the
contact sheet in front of the person who asked for the film and ask which seconds
are the worst. Their answer is the list. Rebuild those beats against the per-beat
test above, and only then build the rest.

## 10. Build it, look at it, then continue

Do not build the whole film and then find out.

1. **Build the first 5 to 8 seconds only.** Wire `build/index.html` and
   `build/piece.jsx` against the kit:

```html
<script>window.OM_SCENES = '[...]';</script>
<script>window.OM_PLAYBACK = '{"mode":"loop"}';</script>

<script src="<path to react.development.js>"></script>
<script src="<path to react-dom.development.js>"></script>
<script src="<path to @babel/standalone babel.js>"></script>
<script type="text/babel" src="../ATTACH/animations-v3.jsx"></script>
<script type="text/babel" src="./piece.jsx"></script>

<script type="text/babel">
  /* ?still=1 freezes the transport so a capture script can seek
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

2. **Shoot it and look.** Snapshots cost seconds, renders cost many minutes. Open
   `build/index.html?still=1` in a headless browser, seek the stage to a list of
   times, and save a frame at each. Print the stage size, the duration, and every
   page error. A single `Failed to load resource` means the film is drawing
   nothing where an asset should be, and it is blocking. Fix `BASE` or the kit
   path before you judge a single frame.

   Dispatch the seek on the **stage element**, not on `document`; on `document`
   it silently does nothing and every frame comes back identical. The stage
   autoplays, so seek before you shoot.
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
- the film cuts, or captions are burned in when nobody asked for them
- `animations-v3.jsx` was edited
- it reads as a product tour rather than a film

## 12. Verify, with output

A green command is not visual approval. Report the numbers, do not estimate
them.

Capture frames as in section 10: stage dimensions, duration, and the frames
themselves. Wrong aspect fails here.

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,bit_rate,duration -of default=nw=1 <export>.mp4
```
check resolution, frame rate and bitrate against what the brief asked for.

```bash
ffmpeg -i <export>.mp4 -vf "select='gt(scene,0.2)',showinfo" -f null - 2>&1 | grep -c showinfo
```
cut count. A zero-cut promo should return zero. `scene_score` measures nothing
else on a zero-cut film, so it is a cut detector and never a motion metric.

Motion energy, near-still percentage, peak and per-section mean luminance are
measured off the export, not estimated, and reported next to the floors from
section 8.

Browser frames carry zero motion blur, so an export can read as stop-motion next
to the preview. Rendering at a multiple of the target frame rate and blending
down (for example 240fps with `tmix=frames=4` to 60) adds it back. Smoothness and
sharpness are separate problems: check for duplicate frames, BT.601 versus BT.709
colour, chroma subsampling and pixel ratio before changing encoder tuning.

For a vertical film posted to a feed that crops the top of the frame, keep
anything load-bearing out of that band.

## 13. The laws

1. **Reference roles are assigned, never averaged.** Write "do not average the
   references" verbatim.
2. **Build the first 5 to 8 seconds and gate on quality before continuing.**
3. **Never fix a concept problem with easing.** If a transition reads as a cut,
   the thing you animate and the thing you land on are two different objects.
   No curve repairs that. Split the mark into layers and assemble it.
4. **A flash cannot replace geometry in a transition.** Brightness that hides a
   missing seam is a defect. Every luminance jump names the object state,
   evidence or medium change it accompanies.
5. **The camera moves a few times, at the moments that matter.** Around three
   events in a 12 second film, and nothing else moving the frame. Between them
   the camera holds and the objects do the work.
6. **Objects must exceed the frame.** Everything safely centred reads as
   scaling, not as camera movement.
7. **Zero cuts alone reads dead.** Energy is specified separately from cut rate,
   with the numbers from section 8.
8. **Pictures are real or rendered, never faked.** A gradient is not album art,
   a triangle you drew is not the mark, a div is not a product screen unless it is
   a real rebuild of one. If the kit does not have it, stop and say so.
9. **Nothing fades in.** Every entrance hits something and the impact causes the
   next beat. A particle that is not consumed by the thing it belongs to is
   litter, not a cause.
10. **2D, not 3D.** The cinematic look is flat layer compositing. The camera
    push is `scale()` on a container and depth is blur plus scale. 3D scenes
    tend to produce a game look and lag. Flat compositing is not flat lighting:
    name a light source with a position, give grounds a falloff, give every
    object a contact shadow and a cast shadow.
11. **Every number on screen is a real published figure**, read on a stated date
    and hardcoded. Never invent one, round one, animate a count up from zero, or
    turn it into a chart.
12. **Do not open a prompt with an essay about why the last attempt failed.**
    These prompts do not apologise or narrate history. They specify. Do not
    describe a mood where a number will do. Do not write a scene without a
    coverage percentage.
