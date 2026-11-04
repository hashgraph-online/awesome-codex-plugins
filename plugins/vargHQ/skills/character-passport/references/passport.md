# The passport

One paragraph that names everything a camera can see, in a fixed order, pasted unchanged into every image and
video prompt. It is the text half of identity; the sheet is the picture half. Both go into every shot.

Tested 2026-11-03 (Nano Banana 2.1, four shots of one film): the moodboard's one-line subject ("a woman, 30,
shoulder-length black hair, charcoal wool coat to mid-calf, black boots, red umbrella") gave four different women.
The passport with no reference image gave the same woman in every shot.

## Rules

1. **Fixed order:** who (name, age as a number, origin, job) → height, build, posture → face top to bottom (shape,
   eyes, brows, nose, mouth, marks) → skin → hair → clothes outer to inner, top to bottom → hands. A fixed order
   lets you diff two versions and see a dropped detail at once.
2. **Only what a camera sees.** "Tired" is invisible; "grey shadows under deep-set eyes" is not. "Kind" is
   invisible; "laugh lines at the outer eyes" is not.
3. **Side and size for every mark:** "a 2 cm pale scar across the left side of her chin", "tucked behind her right
   ear only", "a jade bangle on the LEFT wrist". Unanchored details wander and mirror.
4. **Every garment: colour, material, fit, one sign of wear.** Wear is history: a missing button, pilled cuffs, salt
   marks, a shiny seat on trousers, a collar softened by washing. Brand-new clothing is a slop tell.
5. **One signature detail readable at phone size.** Brows, a gold tooth, a scar, curlers, a colour. Write it in the
   passport and check it on every still.
6. **Posture from history:** "a slight forward stoop after a 12-hour shift", "a rower's wide back", "stands with
   weight on the left leg". Posture is what makes a body look lived in.
7. **No value words** (beautiful, perfect, stunning, flawless, attractive, cinematic), **no real people's names**
   (they pull towards the model's average face or a lookalike), **no brands** (they draw logos). Search every invented
   full name on the web before use: our first surname for Vesna belonged to a real writer.
8. **Under ~900 characters,** so passport + prop passport + look block + shot fit a 2,000-character image prompt.
9. **Versioned, never paraphrased.** The agent pastes it from `cast/<id>.md` with `scripts/prompt.py`; any change
   is `v2` with a new sheet. `prompt.py check` fails any prompt where the passport drifted.

What stays out: light, palette, film stock (the look block); action, emotion, camera (the shot line). A passport
that says "lit by a neon sign" puts that neon sign in every shot.

## Template

```text
<Name>, a <age>-year-old <origin> <job>, <height> cm, <build>, <posture that comes from the job or history>.
<Face shape>, <eyes: set, colour, what is around them>, <brows>, <nose>, <mouth and lips>, <one mark: size, colour, side>.
<Skin: tone, texture, freckles or lines>, <makeup or none>.
<Hair: length, colour, cut, texture, which side it is tucked or parted>.
<Outer garment: colour, material, length, one sign of wear>; <what shows underneath>; <accessory>; <footwear with wear>.
<Hands: nails, marks, rings>.
```

For a stylised or non-human character, keep the order and add the medium as part of the body: "a 12 cm
stop-motion mouse made of matte grey plasticine with visible thumbprints", "a 2D flat-colour character with 3 px
black outlines". The medium is identity, not style, when the character is made of it.

## Examples

Photoreal (LAST BUS, tested; 884 characters):

```passport
Vesna Doric, a 30-year-old Croatian ICU nurse, 168 cm, narrow shoulders, long neck, a slight forward stoop after a 12-hour shift, weight on her left leg. Long oval face, deep-set dark brown eyes with grey shadows under them, thick straight black brows that almost meet, a strong straight nose with a small bump on the bridge, a wide mouth with a thin upper lip, a 2 cm pale scar across the left side of her chin. Olive skin with visible pores, a few freckles across the nose, no makeup. Shoulder-length black hair in a grown-out blunt cut, frizzy from rain, tucked behind her right ear only. Charcoal wool coat to mid-calf, single-breasted, the second button from the top missing, pilled cuffs; a navy V-neck scrub top showing at the collar; a black jersey scarf; worn black leather ankle boots with white salt marks. Short unpolished nails, a beige plaster on her right index finger.
```

Older man (untested example of the same form):

```passport
Teodor Balan, a 71-year-old Romanian retired tram driver, 174 cm, heavy shoulders, a belly that pushes his cardigan open, walks with his left knee kept straight. Broad square face, small pale grey eyes under hooded lids, bushy grey brows longer at the outer ends, a wide flat nose with broken veins, a thin mouth turned down at the corners, a deep vertical crease between the brows. Ruddy weathered skin, liver spots on the forehead, white stubble two days old. Thin white hair combed straight back, yellowed at the front from smoking. Brown wool cardigan with leather buttons, the right pocket stretched out of shape; a checked flannel shirt buttoned to the top; grey trousers shiny at the knees; black lace-up shoes, heels worn down on the outside. Thick fingers, a wedding ring that no longer comes off, nicotine stain on the right index finger.
```

Stylised (untested example):

```passport
Mops, a stop-motion field mouse puppet about 12 cm tall, made of matte warm-grey plasticine with visible thumbprints and slightly lumpy edges, pear-shaped body, a slight hunch. Round head, two black glass-bead eyes set wide apart, the left eye a little higher, a pink felt nose, no visible mouth until he speaks, two large thin ears, the right ear torn at the top edge. Short wool-thread whiskers, three on each side, the bottom left one bent. A mustard knitted scarf, hand-knit with uneven stitches, wound twice and tied on the right; a red button sewn on his chest as a badge, its thread loose. Four-fingered hands, the plasticine shiny at the fingertips from handling.
```

## Prompt order for every later shot

`[reference roles]` → shot (size, lens, height, action) → `SUBJECT:` passport → prop passports → look block →
(video only) prop motion blocks. `scripts/prompt.py build` writes exactly this order.
