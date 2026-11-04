# Anchors: character, product and vehicle sheets, master plates

Anchors are cheap stills made before any video. Every video run gets only the anchors of what is in its frame.

## Anchor set (make these first)

| anchor | content | locks |
|---|---|---|
| Character sheet | front, ¾, profile, back full body + a big face close-up, neutral grey background | face, hair, outfit, props |
| Product sheet | front (label to camera), ¾, side, back, top + **a hand or a person holding it** | shape, label layout, colour, product-to-hand scale |
| Vehicle sheet | front, side, back, top, ¾ **plus a person standing next to it** | design, person-to-vehicle scale |
| Antagonist sheet | the creature/rival front + profile, its minions in a separate column | look, minions |
| Master plate per location | the establishing frame of every place, in the film's look | layout, light, geography |
| Secondary cast | one still of the lead of each group | that face across shots |

Rules:
- One art style in every anchor ("1980s anime cel, hand-drawn line art, painted backgrounds" or "warm cinematic
  commercial, natural skin, 35 mm"). Run a casting test across two image models, pick one, stick to it.
- Grey or flat background on sheets; no text on sheets. For a real product, use the real packshot as the sheet and
  never ask the model to redraw the label text: logos and labels are composited in the edit if they must be legible.
- Put the important layout facts into the master plate AND the prompt: "stick at his right hand, throttle at his
  left, window behind her, the door on the left wall".
- Recurring markers carry story: a scar or crack from the first hit to the last frame, one object in every frame,
  colour = side (red enemy, brand colour = our side).
- Keep sheets modular so you can crop: minions in their own column, so a "minions only" crop is possible.
- Every ref image at least 300 px on its short side (the byteplus route rejects narrower): pad crops onto the sheet's
  background colour rather than upscaling. `build_pack.py --check` catches this.

## Master plates and first frames from the previz (geometry-locked stills)

An environment image alone still drifts: image models re-invent the layout for every camera (seen on a 3-shot
storyboard: a switch went missing, a person ended up on the wrong side, gravel became asphalt). What worked:

1. Render the previz frame of the camera you need: `?shot=<id>&k=0` in the app, or `app.exportFrame(id, t)` in
   `?export=1` mode (no HUD, no text).
2. Image edit (e.g. `gpt_image_2_5`) with that render as the FIRST file and the sheets after it: "keep the camera
   and the geometry exactly; mapping: grey mannequin = @image2 the woman, orange bottle = @image3 the product,
   grey blocks = brick buildings…".
3. Give previz people real limbs, a head and feet (the mannequin has them): blob figures come back as logs.

Use these as master plates per location and, when a run starts on a precise composition, as extra refs for that run.

## Using anchors in generations

- Close-ups are generated from the master plate as a reference ("same room, closer angle"), never from scratch.
- Give each ref a one-line role in the prompt: `@image1 is the woman's character sheet: same face, …`.
- Only refs whose content is visible in the shot; an exterior plate in an interior shot drags the exterior in.
- After a story rewrite, old stills of rewritten shots are stale: do not use them as refs.

## Still QA checklist (run on every still and every first frame)

1. Count people: exactly the people the shot names (an "over the shoulder" once drew two pilots).
2. Every visible arm is attached to a body in frame and wears that character's sleeve.
3. Scale against the sheet: the vehicle is clearly bigger than the person, the product fits the hand.
4. No letterbox: never write "keep the top fifth calm" (models draw a band); write "full-bleed, no borders".
5. No text, letters, logos drawn by the model.
6. The product's label faces the way the shot needs (the previz bottle has a white label band to check this).

## 3D stand-ins (previz objects, `js/props.js`)

- `makePerson`: a 1.8 m mannequin with named joints and a pose dictionary (`sit, phone, holdUp, talk, point, wave,
  armsCrossed, coverFace…`); eyes, mouth and an optional headset so facing and talking read from any camera.
- `makeProduct` (bottle, can, cup, box, phone) with a label band; `makeCar` 4.5 m; `makeTable`, `makeChair`.
- Build anything bigger at true scale (a ship ~5× a person, a monster hundreds of metres) with named parts
  (canopy, engines, jaw, eye lid): see `examples/space-opera/props.js`.
- Props get names and simple states (card → crumbles, orb → ignites, button → depresses).
- Match the master plate's layout in 3D, and check it: in the original project the cockpit crack sat on the front
  glass while the master showed it on the glass above and behind the pilot.
