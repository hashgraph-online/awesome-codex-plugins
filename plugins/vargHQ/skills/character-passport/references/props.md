# Props: materials, wear, motion, sound

A hero prop gets the same treatment as a character: a passport, its own sheet, its own reference slot in every shot
where it matters.

Tested 2026-11-03: the umbrella's prop sheet kept every wear detail (lacquer worn to pale wood where the thumb
rests, the bent front rib, faded top panels, rain beads). In the shots, where only the character sheet was attached,
the worn handle came out right 0 of 22 times (two blind AI judges). A prop holds only when its own sheet goes in.

## Which objects need a passport

Any object the camera lingers on, a character touches twice, or the story turns on. Everything else is set dressing
and lives in the location prompt.

## Prop passport

```text
<Whose> <object>: <type and size>, <main material and finish> <colour, hex if it matters>, <second material>,
<the wear: what, where, why>, <one defect with its side>. Unbranded, no logos.
```

Rules:

1. **Materials as the camera sees them:** finish (matte, satin, gloss), what light does on it (chrome mirrors the
   street, nylon glows when backlit, wet lacquer shines, worn wood goes pale and dull).
2. **Wear follows use and has a reason:** hands polish and darken grips; edges chip; corners round; sun fades the
   top; water and salt mark the bottom; things carried in a bag scuff on one side. Write where and why.
3. **One defect** makes it this object, not a stock photo: a bent rib, a dent, a tape repair, a missing screw.
4. **No brand names** (they draw logos). "Unbranded, no logos."
5. **A colour that must survive gets a hex, and so does its faded version.** "Faded paler" became salmon-orange.
6. **Size against the body:** "about the length of her forearm", "fits in one palm". Scale drifts otherwise.

## Motion block (video prompts only)

```motion
<Weight in kg or "heavy for its size">. <How it starts: snap, swing, slide>. <How it stops: settles, bounces, clatters>.
<What lags behind: fabric, straps, liquid, cables, and how>. <What the environment does to it: wind, rain, light>.
<Its sound>.
```

Example (umbrella):

```motion
Heavy for its size, about 0.6 kg. Opens with a hard snap and a short shudder of the canopy. In a gust the canopy dents inward on the windward side and the bent rib flutters. Rain drums loudly on the taut nylon; water runs off the rib tips in thin streams. Closing takes one shake that throws a fan of drops; the furled canopy drips from the tip for a few seconds.
```

Video models make objects weightless by default. A stated weight, a start, a stop and one lagging part are the
cheapest fix: they are the animation principles of follow-through and overlapping action, written as a prompt.

## Sheet

```text
Prop reference sheet of one object, in the look of the film it is in: <texture, key, fill>, plain <hex> backdrop,
every panel lit the same way, no hands, no text, no labels, no logos. Five views of the same <object> at the same
scale: <three-quarter from above>; <side>; <closed or at rest>; a close-up of <the wear>; a close-up of <the defect>.
THE OBJECT: <prop passport>. Photoreal, real material texture: <materials>.
```

For real products (a client's bottle, a phone), start from real photos, not a generated sheet: varg-product-lock.
For exact geometry, build it in code (three.js primitives or a CC0 model from Poly Haven / Sketchfab) and dress
it with an image edit: `code.md`.

## In shots

Image 2 = the prop sheet (or its wear close-up) whenever the prop is in frame and matters, named: "Image 2 is the
umbrella: the object only." Then the prop passport after the character passport; the motion block only in video
prompts (`scripts/prompt.py build --video`). Keep detailed props still and large in frame when they must read;
small, moving props blur first.

## From people with finished work (verbatim in x-evidence.md)

- Heavy things take longer to start and to stop; show weight through grip changes and mechanical play
  ([@RobertAnim8er](https://x.com/RobertAnim8er/status/1922835836518928445)).
- Say which hand moves the prop, or it floats on its own ([@reidhannaford](https://x.com/reidhannaford/status/2069482804824420651)).
- Product sheet: all angles plus a scale reference (a hand holding it); a separate "fix sheet" for the detail that
  breaks, e.g. the label unwrapped flat ([@invideoOfficial](https://x.com/invideoOfficial/status/2078155212192412101)).
- Material rule in the prompt: rigid parts rotate, flexible parts bend or stretch; forbid invented accessories
  ([@aimikoda](https://x.com/aimikoda/status/2100258742059069739)).
- Design props from construction, material rendering and a story clue ([@visignacademy](https://x.com/visignacademy/status/2013665451079868866)).
- For a phone screen, record the real screen and attach it as a reference ([@second_bassoon](https://x.com/second_bassoon/status/2094846379688386861)).

## Evidence (sources and quotes in craft-evidence.md)

- Non-metals reflect about 4% of light head-on, bare metals 70-100%; rust, paint and dirt on metal behave like
  non-metal ([Adobe PBR guide](https://www.adobe.com/learn/substance-3d-designer/web/the-pbr-guide-part-2)). Real
  base colours and roughness: [physicallybased.info](https://physicallybased.info/) (CC0).
- Wear = contact + exposure + time: knocked edges, grime in crevices, polish where hands touch, fading on the sun
  side, sticker residue. "Dirty a prop too much, and then try to clean it as best as you can" (Adam Savage, via
  [PremiumBeat](https://www.premiumbeat.com/blog/how-to-weather-and-age-props)).
- Films keep several copies of a prop at different levels of wear; keep one approved image per state (new, used,
  damaged) and never mix states in a scene.
- Sound: material on material + action + space ("steel keys on a glass desk, quick drop, small room").
