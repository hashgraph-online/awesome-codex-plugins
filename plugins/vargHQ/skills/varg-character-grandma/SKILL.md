---
name: varg-character-grandma
description: >-
  Makes very old AI characters people remember, on varg: grandmas and grandpas (80+) with a
  contrast between age and behaviour, real wrinkles and age spots, a loud signature outfit and
  one prop, as a character sheet ready for scenes and video. Use when someone asks for an AI
  granny or grandpa, an old lady or old man character, a babushka, nonna or abuela, an elderly
  influencer, or an old character for an ad. Part of varg-character-design (definition, sheet,
  reuse in video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY (see varg-ai).
allowed-tools: Bash(curl:*) Read Write Edit
---

# Grandma and grandpa characters

Old characters have the strongest money evidence of any AI archetype: Granny Spills (an AI grandmother in a pink suit) reached 1M Instagram followers in about a month and 2.1M by mid-2026, with brand deals (Kurt Geiger, Papi Steak); a wordless cosy-granny-and-cat page reached 16M views. They work because of **age versus behaviour**: a granny who rides a scooter, fans cash, lifts weights, gives brutal advice. Buyers are mostly women 38–65; grannies sell books, beauty, food and home products.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Definition**: exact age (80–100) + nationality or place + one behaviour that does not fit the age.

**Details** (write all that apply):

- Skin: "deeply wrinkled skin with visible pores, age spots on the cheeks and hands, visible veins on the hands", "no airbrushed skin, no professional makeup"
- Body: height in cm, build ("sturdy round build", "tiny and bird-like", "slightly stooped")
- Hair: silver, thinning, a set perm, curlers, a bun under a headscarf, a blue rinse
- Teeth: a gold tooth, a gap, dentures with a too-white smile
- Eyes: thick glasses (cat-eye, bottle-bottom, tinted aviators), a sharp suspicious squint
- **One signature detail**: gold tooth, a giant hearing aid, a cigarette holder, false lashes

**Clothing** (one loud piece, the rest plain):

- Loud: leopard or zebra housecoat, a shiny purple track suit, a pink fur coat, a neon windbreaker, a sequined cardigan
- Plain under it: a black dress, a cardigan, compression stockings
- Shoes that tell the story: fluffy slippers, orthopaedic sandals, chunky trainers
- One prop: a wooden spoon, a cane she does not need, a shopping trolley, a fat purse

**Expression**: deadpan, suspicious, unimpressed; she has never laughed in her life, or she laughs with every tooth.

## Ready characters

| Character | Prompt seed |
|---|---|
| Nonna Rosa (tested) | 84-year-old Sicilian grandmother, 150 cm, sturdy round build, deeply wrinkled tanned skin, age spots, one gold front tooth, thick black cat-eye glasses, silver hair in pink foam curlers under a black lace headscarf; leopard-print quilted housecoat over a plain black dress, beige compression stockings, fluffy red slippers, worn wooden spoon |
| Babushka Zina | 79-year-old Russian grandmother, short and round, gold teeth, permed copper-red hair, a flowered headscarf; shiny purple track suit, unbranded, white chunky trainers, a bag of sunflower seeds, completely unimpressed |
| Abuela Carmen | 91-year-old Mexican grandmother, tiny and stooped, deep laugh lines, silver braid, huge tinted glasses; black lace dress, a neon-pink windbreaker over it, a cane with stickers, a phone on a lanyard |
| Grandpa Walt | 88-year-old ex-biker, tall and thin, long white beard in a braid, forearm tattoos faded to blue, a leather vest over a hospital-style cardigan, slippers, a tiny dog in a bag |

Nonna Rosa: [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7d8641db61c3.jpg) (Seedream 5 Pro, 7 credits) · [new scene](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_958a5a187e1e.png) · [Seedance clip](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_6489606dc55b.mp4) · [as a vinyl figure](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_3c2e14641686.png)

## Sheet

```
Character reference sheet of one original character on a clean light-grey studio background,
landscape, flat even lighting, photorealistic. Character: <seed>. Layout: left two thirds: four
full-body views at the same scale standing on one ground line: front, three-quarter, side
profile, back. Right third: a 2x2 grid of head-and-shoulders close-ups: neutral, laughing,
suspicious squint, shouting. Bottom strip: five colour swatches and the props. The same face,
hair, outfit and proportions in every panel.
```

Model: `seedream_5_pro` (best wrinkles and attitude, 7 credits). Tested: on this prompt only Seedream 5 Pro, Nano Banana 2.1 and Krea 3 kept the single gold tooth. For video input, use the label-free sheet from `varg-character-design`.

## Formats that work

- A cosy wordless routine (granny, cat, rain, soup): no words, travels to every country.
- The impossible feat: granny breaks a bundle of bats, outruns a teenager, rides through Palermo.
- Brutal advice to camera, one line, deadpan (`varg-character-keynote` puts her on a stage).
- Merch: the same granny as a boxed vinyl figure or a colouring-book cover.

## Watch out

- Models smooth old skin; repeat "deep wrinkles, visible pores, age spots, no airbrushing".
- Veo blocked a wholesome grandparent-and-grandchild ad on its child-safety codes; keep grandchildren out or use `kling_v4` / `seedance_2_5`.
- An AI granny recommending a supplement as if she used it is a fake testimonial (FTC). She is a character, not a customer; label the account as AI.
