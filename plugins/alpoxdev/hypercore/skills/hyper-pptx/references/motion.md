# Motion

Read this when a deck should not appear all at once: a transition between pages, an entrance on the argument, or a question about why an animation name was rejected.

## Contents

- What motion costs
- A transition belongs to the slide
- An animation belongs to shapes
- The nine effects and what they write
- Roles and targets
- Ids inside the timing tree
- What is deliberately not supported
- What was verified and what was not

## What Motion Costs

Motion is the one part of the package that fails quietly. A wrong transition name or a duplicated time-node id does not stop the file from opening; PowerPoint shows a repair prompt, and after the repair the slides are gone. Playback cannot be checked here because PowerPoint is not installed, so every rule below exists to keep the writer inside what the schema guarantees rather than what it hopes.

Two consequences run through the rest of the skill:

- Every name is checked against a closed list at layout time. An unknown name is an error, never a near-match.
- The animation target is a shape id that the layout pass assigns. Nothing is written from a name an author guessed.

The default is no motion. A deck with no `transition` and no `animation` produces exactly the bytes it produced before motion existed.

## A Transition Belongs to the Slide

```json
{ "transition": "fade" }
{ "transition": { "effect": "push", "speed": "fast" } }
{ "transition": false }
```

`transition` on the deck sets the default for every slide; a slide may override it. `false` and `"none"` both mean this slide has no transition. The resolved element is one direct child of `p:transition`, which itself is one direct child of `p:sld`:

```xml
<p:transition spd="med"><p:fade/></p:transition>
```

| Effect | What it does |
|---|---|
| `fade` | cross-fades the page |
| `cut` | no blend; the page swaps |
| `dissolve` | random-pixel dissolve |
| `push` | the new page slides in from `dir` |
| `wipe` | the new page is revealed along `dir` |
| `cover` | the new page covers the old one |
| `split` | the page opens from the centre outward |
| `strips` | vertical strips swap |
| `zoom` | the new page grows in |
| `plus` | the page opens along both axes |
| `pull` | the old page is pulled away on `dir` |
| `randomBar` | bars in random order |
| `checker` | squares |
| `blinds` | horizontal blinds |
| `diamond` | diamond wipe |
| `circle` | circle wipe |
| `wedge` | wedge wipe |
| `wheel` | one spoke |
| `random` | random effect |
| `comb` | comb wipe |
| `newsflash` | the page appears and shrinks |
| `morph` | PowerPoint 2019+ object morph |
| `none` | no transition |

Directions are not a field. Each effect that takes one has a fixed value in the schema (`p:push` is `dir="u"`), so a direction the author sets would be ignored by PowerPoint and the deck would animate differently than described. The writer emits the value the schema expects for the effect.

`spd` is `slow`, `med`, or `fast`. `morph` also carries `p14:dur` in milliseconds, because the modern attribute is what PowerPoint 2019 reads; `spd` is kept for older readers.

## Morph Is the One Wrapped Effect

`morph` is not an ECMA-376 element. It is a Microsoft extension from the `p159` namespace, so it is written inside `mc:AlternateContent`: a `Choice` that requires `p159` holds the morph, and a `Fallback` holds a plain fade. A reader that does not know the extension takes the fallback and shows a fade rather than refusing the file.

That is the only place in this package where markup-compatibility is used. Every other transition is a plain element, because wrapping them would add a namespace declaration PowerPoint does not need.

## An Animation Belongs to Shapes

```json
{ "animation": [
    { "effect": "fade", "target": "title", "trigger": "on-click" },
    { "effect": "fly", "target": "body", "direction": "up", "delay": 100 },
    { "effect": "grow", "target": "chart", "trigger": "after-previous" }
] }
```

| Field | Default | Meaning |
|---|---|---|
| `effect` | `fade` | one of the nine below |
| `target` | `all` | a role, a shape id, or an array of either |
| `trigger` | `on-click` | `on-click`, `with-previous`, `after-previous` |
| `direction` | `up` | `up`, `down`, `left`, `right`; used by `fly` and `wipe` |
| `duration` | `500` | milliseconds |
| `delay` | `0` | milliseconds after the trigger |

## The Nine Effects and What They Write

| Effect | Class | Writes |
|---|---|---|
| `appear` | entrance | a `p:set` on `style.visibility` |
| `fade` | entrance | that `p:set` plus `p:animEffect filter="fade"` |
| `wipe` | entrance | `p:animEffect filter="wipe(dir)"` |
| `split` | entrance | `p:animEffect filter="barn(inVertical)"` |
| `fly` | entrance | a `p:anim` on `ppt_x` or `ppt_y` from outside the slide |
| `zoom` | entrance | two `p:anim` nodes, width and height from zero |
| `grow` | emphasis | `p:animScale by="150000,150000"` |
| `spin` | emphasis | `p:animRot by="21600000"`, one full turn |
| `exitFade` | exit | `p:animEffect filter="fade"` out, then a `p:set` to hidden |

An entrance starts hidden because the `p:set` to `visible` runs first: without it the shape is on screen from the moment the slide appears, and the entrance has nothing to reveal. An exit does the reverse, and its `p:set` to hidden is delayed by `duration - 1` milliseconds so the shape does not vanish before its fade ends.

Preset ids make the effects appear in the animation pane under their own names instead of as custom animation: `appear` 1, `fly` 2, `grow` 6, `spin` 8, `fade` 10, `split` 16, `wipe` 22, `zoom` 23.

## Roles and Targets

An author writes a name; a slide has ids. Both resolve to the same shape ids in the layout pass:

| Target | Matches |
|---|---|
| `all` | every content shape; decoration and page furniture are skipped |
| `title`, `body`, `kicker`, `table`, `chart`, `image`, `decor` | shapes carrying that role |
| `s1` … `i1` … | the shape id the layout assigned |

`all` skipping decoration is deliberate. A rule under the title, a background block, a page number — if those animate, the page looks like it is assembling itself in front of the audience, which reads as a mistake rather than a style.

A shape with no declared role still has one: text is `body`, anything else is `decor`. Without that default an author would have to know the ids before the deck exists.

A target that matches nothing is `ANIMATION_TARGET_EMPTY`. A timing tree with no target still opens, and the symptom is a shape that never fades in, discovered live.

## Ids Inside the Timing Tree

Time-node ids are unique within a slide, not within the deck. Each animated row reserves four ids (the row, the visibility set, and up to two behaviour nodes) and each click-group wrapper takes one, so the counter advances by four per target and one per group. `pp_check_motion` re-reads the written XML and fails the render on three conditions:

| Condition | Code |
|---|---|
| more than one `p:timing` on a slide | `MOTION_INVALID` |
| a `p:cTn id` that repeats within the slide | `MOTION_INVALID` |
| a `p:spTgt spid` naming a shape not on the slide | `MOTION_INVALID` |

Those three are the failure modes that open with a repair prompt or silently do nothing. The check was verified by injecting a duplicate id and a missing target into a rendered deck and confirming both were reported.

## What Is Deliberately Not Supported

- No motion paths. `p:animMotion` needs a hand-authored path, and a wrong path is invisible until playback.
- No `p:media` or trigger-on-media.
- No per-character or per-word text build. Splitting a text box into animated sub-runs changes its runs, and the run structure is what `edit-deck.sh` searches.
- No sound.
- No animation on the master or the layout, so a slide's motion never inherits.

An author who needs one of these should build it in PowerPoint rather than have this package write XML nothing here can check.

## What Was Verified and What Was Not

Verified here, on 2026-11-14:

- All 23 transitions and 9 effects render without a layout error, with the expected element and attribute in `ppt/slides/slideN.xml`.
- Every `p:spTgt` names a `p:cNvPr` id that exists on the same slide.
- No slide has a duplicate `p:cTn id`.
- `pp_check_motion` catches an injected duplicate id and an injected missing target.

Not verified: playback. PowerPoint is not installed on this machine, so "does the morph look right on a projector" has no answer here. The XML matches the schema and the reference implementation; treat the first real presentation as the test.

## Sources

> Checked 2026-11-14.

| Claim | Source |
|---|---|
| `p:transition` is a child of `p:sld` and holds one effect element | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.slide> |
| Transition effect elements and their direction attributes | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.transition> |
| `p:timing` builds a tree of `p:cTn` nodes with targets in `p:spTgt` | <https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.presentation.timing> |
| Animation preset ids correspond to the named effects in the pane | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |
| Morph is a `p159` extension and needs `mc:AlternateContent` | <https://learn.microsoft.com/en-us/office/open-xml/presentation/working-with-presentations> |

### Evidence grade

`LOCAL` — the element, attribute, and id rules were read from the writer and confirmed against the rendered XML in `ppt/slides/`. Playback is specification-based; PowerPoint is not available on this machine.
