---
name: varg-character-design
description: >-
  How to make AI characters people remember, on varg: define the character (premise, archetype,
  contrast), write the details (face, body, age, flaws, one signature detail), dress them
  (garment by garment, materials, fit, one loud colour), pick a category recipe, then lock the
  look in a character sheet and reuse it in later images and videos (Nano Banana, Seedream, GPT
  Image, Kling 4, Seedance 2.5, Wan 3). Use when someone asks to create, design or describe a
  character, an AI influencer or persona, a mascot, a character sheet or turnaround, or the same
  character in new scenes or videos. Category recipes: varg-character-grandma,
  varg-character-big-guy, varg-character-cringe, varg-character-beautiful-woman,
  varg-character-fitness, varg-character-absurd, varg-character-cartoon. Not for multi-scene ads
  from real actor photos (varg-consistent-characters), a speaker on a stage
  (varg-character-keynote) or two-person podcasts (varg-podcast-video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    requires:
      anyBins:
        - curl
    homepage: https://varg.ai
compatibility: >-
  Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY with curl (see the
  varg-ai skill). Cropping a sheet locally uses ffmpeg; without it, use varg's ffmpeg tool.
allowed-tools: Bash(curl:*) Bash(jq:*) Bash(ffmpeg:*) Bash(ffprobe:*) Read Write Edit
---

# varg character design

How to make a character people remember, and keep it the same in every later image and video. Generation runs on varg: the MCP server (`https://mcp.varg.ai/mcp`, `call_tool`) or `POST https://api.varg.ai/v2/tools/{image|video}/call`. Quote prices in credits. Facts marked **Tested** were run on varg on 2026-10-27.

A default request ("make a beautiful woman", "make a funny old man") gets the model's average person: pleasant, symmetrical, forgettable. Characters that spread have a **gap between what people expect and what they see**, written in exact, visible details. The prompt is the whole craft: who they are, what their face and body look like, what they wear.

## 1. Define the character

One line of premise + one archetype + one contrast.

| Part | Example |
|---|---|
| Premise | "84-year-old Sicilian grandmother who solves everything with a wooden spoon" |
| Archetype | very old · big guy · cringe deadpan · beautiful woman · fitness · absurd hybrid · cartoon |
| Contrast | age vs behaviour (a granny on a scooter), size vs job (a 160 kg florist in a tiny pink apron), seriousness vs costume (a deadpan man on roller skates), object vs life (a T-rex made of bread) |

Pick the category recipe; each has the details, clothing and ready characters for its type:

| Category | Skill | Example |
|---|---|---|
| Grandmas and grandpas | `varg-character-grandma` | Nonna Rosa, 84, leopard housecoat, gold tooth |
| Big guys | `varg-character-big-guy` | Bruno, 48, 160 kg florist in a tiny pink apron |
| Cringe deadpan characters | `varg-character-cringe` | Gérard, 61, 2 m tall, mustard corduroy suit, roller skates |
| Very beautiful women | `varg-character-beautiful-woman` | model looks, real skin, fashion or swimwear editorial |
| Fitness characters | `varg-character-fitness` | Mara, 31, CrossFit coach, lime sports bra |
| Absurd characters and mascots | `varg-character-absurd` | Baguettosaurus, Señor Pincho the cactus, Hector the sheep |
| Cartoon sitcom characters | `varg-character-cartoon` | Gary Pruitt in the yellow 2D sitcom look |

Numbers behind these archetypes (what spread on X and Instagram in 2025–2026, and why): [references/archetypes.md](references/archetypes.md).

## 2. Write the details

The face and body carry identity. Write them as things a camera can see, in this order:

1. **Age as a number** ("84-year-old", not "old"; "26-year-old", not "young").
2. **Body with visible cues.** Numbers alone are under-rendered (Tested: "about 160 kg" came out much lighter until the prompt said "wide round belly that pushes the apron forward, double chin, the apron looks too small on him"). Height needs proportions ("arms hang to mid-thigh, small head for his height") or something to compare in the scene.
3. **Face, feature by feature**: face shape, eyes (shape, colour), brows, nose, lips, jaw, skin tone and texture.
4. **One signature detail readable at phone size**: a gold front tooth, a scar through one eyebrow, curlers under a lace headscarf, a curled moustache. Write it twice (face line and close-ups) and check it: Tested, only Nano Banana 2.1, Seedream 5 Pro and Krea 3 kept a single gold tooth on a sheet; GPT Image 2.5 and FLUX 3 dropped it, Grok made every tooth gold.
5. **Hair**: length, colour, texture, parting, silhouette (hair is the second identity carrier).
6. **Skin that reads as skin** for photoreal people: "visible pores, fine peach fuzz, natural texture, no retouching". See [references/realism.md](references/realism.md).
7. **Expression and posture**: deadpan, suspicious squint, shy half-smile; hands on hips, stooped, ramrod straight.

Ban list: "beautiful" or "perfect" as quality words, "8k masterpiece", "flawless", a celebrity's name.

## 3. Dress them

Clothes are the fastest read after the silhouette, and they are what drifts first between shots.

- **Garment by garment**, with cut, colour, material and fit: "leopard-print quilted housecoat over a plain black dress, beige compression stockings, fluffy red slippers".
- **One loud colour** against calm pieces (red slippers, lime sports bra, mustard corduroy), with hex codes in the card.
- **Fit tells the joke**: an apron a size too small, trousers too short showing white socks, a suit too formal for the place.
- **One outfit per character.** It becomes their uniform in every post; a second look gets its own sheet.
- **Unbranded.** Brand words draw logos (Tested: "Vespa" put the Vespa wordmark on the scooter; a short gym prompt came back with a real activewear logo). Write "unbranded, no logos".
- **For swimwear and sportswear, name the garment exactly** ("high-support sports bra and high-waisted 7/8 leggings", "one-piece swimsuit with a high leg cut"): it is also what gets the prompt past filters ([references/moderation.md](references/moderation.md)).

## 4. Keep it in a character card

```json
{
  "id": "nonna-rosa",
  "premise": "84-year-old Sicilian grandmother who solves everything with a wooden spoon",
  "body": "150 cm, sturdy round build",
  "face": "deeply wrinkled tanned skin, age spots, one gold front tooth, thick black cat-eye glasses",
  "hair": "silver hair in pink foam curlers under a black lace headscarf",
  "wardrobe": "leopard-print quilted housecoat over a plain black dress, beige compression stockings, fluffy red slippers",
  "signature": "gold front tooth + wooden spoon",
  "palette": ["#B08850", "#111111", "#E8C9A8", "#C8102E", "#F2A7C3"],
  "style": "photoreal, natural skin texture",
  "never_change": ["gold tooth", "cat-eye glasses", "curlers", "leopard housecoat", "red slippers"],
  "sheet": { "model_sheet": "<url>", "face": "<url>", "body": "<url>" }
}
```

Build every prompt from the card, word for word, so the description never drifts.

## 5. Lock the look in a sheet

```
Character reference sheet for AI video, flat light-grey studio background, even soft studio light,
no text, no labels, no logos. Top row: three full-body views at the same scale on one ground line:
front, side profile, back, arms relaxed, empty hands. Bottom row: three large head-and-shoulders
close-ups: front, three-quarter, side profile. The same <person> in every panel: identical face,
hair, body, outfit and proportions. CHARACTER: <details>. WARDROBE: <clothing>. <STYLE>.
```

| Character | Model | Credits |
|---|---|---|
| Photoreal person | `seedream_5_pro` (native 2K, best skin) | 7 |
| 3D, cartoon, clay, creature | `nano_banana_2_1` | 6 |
| Labelled sheet for a client | `gpt_image_2_5` or `nano_banana_2_1` | 24 / 6 |

Swap the bottom row for expressions when the character has to act. More layouts (from photos, expression, outfit, prop, labelled bible): [references/sheet-prompts.md](references/sheet-prompts.md).

Then cut two crops: a face close-up and a full-body front (`ffmpeg -i sheet.jpg -vf "crop=iw/3:ih/2:0:ih/2" face.png` and `crop=iw/3:ih/2:0:0` for the body), upload them (`create_upload`), and keep the URLs in the card.

## 6. Reuse it

- **New images**: pass the crops (or the whole sheet) in `files` to `nano_banana_2_1` and describe only what changes: "First reference image is Nonna Rosa's face, second is her full outfit. Show this exact woman riding a red vintage scooter through a narrow Palermo street, wooden spoon raised." Tested: both the sheet and the crops kept her identity.
- **Video, safest**: make the scene still first (6 credits), approve it, then animate that one still with `kling_v4` (Tested: most faithful, 83 credits for 5 s). Never pass the sheet itself as a first frame.
- **Video, reference mode**: `seedance_2_5` with `@image1` = face crop, `@image2` = body crop gave the steadiest face (203 credits for 5 s with audio). Add: "Use the references for identity only. Do not copy the sheet layout, labels or grey backdrop. No grid, no picture-in-picture, no on-screen text."

Per-model reference fields (Kling elements, Wan 3, Vidu, Omni Flash, MiniMax H3, Recast), route pinning and drift fixes: [references/downstream.md](references/downstream.md).

## 7. Moderation and famous looks, in short

- Filters react to **words**. "Girl", "bikini", "tight", "sexy" get blocked on GPT Image 2.5, FLUX 3 and Grok; a catalog prompt (adult age, named garments, an activity, the brand purpose) passed on all six image models we tried. Blocks are random: retry once, rephrase, then route. Full log and swaps: [references/moderation.md](references/moderation.md).
- **Describe famous looks, never name them.** Nano Banana 2.1 refused "The Simpsons style" and drew the same look from a description. Style blocks and the legal line: [references/styles.md](references/styles.md).
- Label AI characters as AI on social platforms, and never present one as a real customer in an ad.

## References

- [references/archetypes.md](references/archetypes.md): archetypes that spread, with numbers and sources
- [references/sheet-prompts.md](references/sheet-prompts.md): sheet layouts and templates
- [references/downstream.md](references/downstream.md): reusing the sheet in each image and video model
- [references/moderation.md](references/moderation.md): test log, safe phrasing, routing
- [references/realism.md](references/realism.md): real skin, unusual bodies, upscalers
- [references/styles.md](references/styles.md): famous looks without IP names
- [references/sources.md](references/sources.md): creators, guides and posts
