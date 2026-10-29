---
name: varg-character-fitness
description: >-
  Makes AI fitness characters on varg (coaches, gym creators, athletes, bodybuilders) with real
  muscle and skin, a locked signature outfit and colour, and catalog-style wording that gets
  sports bras, leggings and shirtless athletes past false moderation blocks. Builds the character
  sheet ready for workout scenes and video. Use when someone asks for a fitness influencer, gym
  girl or gym guy, a trainer for an app, an athlete for an activewear or supplement ad, or a
  character in a sports bra that keeps getting blocked. Part of varg-character-design
  (definition, sheet, reuse in video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY (see varg-ai).
allowed-tools: Bash(curl:*) Read Write Edit
---

# Fitness characters

The natural home for activewear, supplements and fitness apps. "This fitness coach doesn't exist" (the post claims 8M views) locked one look: grey tee, dark joggers, **lime wristbands**. Contrast versions spread further: a skinny kid lifting heavy (every reel above 892K), an 80s bodybuilder with a mullet (9.1M).

The hard part is moderation: a woman in a sports bra at the gym is ordinary content, but short prompts get blocked. The catalog wording below passed on all six image models we tested.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Definition**: adult age as a number + a role (CrossFit coach, yoga teacher, powerlifter, runner, physio) + one signature colour.

**Details**:

- Build, specific: "athletic muscular build", "lean runner's build", "powerlifter build, thick legs and back"
- Real muscle and skin: "real muscle definition, visible skin texture, light post-workout sheen, chalk on her hands", "no retouching"
- Face and hair: a buzz cut, a high ponytail, braids; one mark (a scar through an eyebrow, a gap tooth, freckles)

**Clothing, named like a product listing** (this is also what passes filters):

- Women: "high-support <colour> sports bra and high-waisted black 7/8 leggings", "seamless crop top and bike shorts, athletic fit"
- Men: "fitted training T-shirt", "tank top", or for shirtless: "competitive bodybuilder on stage, posing trunks, competition tan, contest number"
- Gear: a lifting belt, wrist wraps, chalk, training shoes
- One loud colour (lime, safety orange, cobalt) that is in every post
- "Unbranded, no logos" (Tested: a short gym prompt came back with a real activewear brand's logo on the top)

**Activity, always**: mid-set of kettlebell swings, deadlift lockout, a plank, stretching after a run. An activity reads as fitness; standing and posing reads as something else.

## Ready characters

| Character | Prompt seed |
|---|---|
| Mara (tested) | 31-year-old adult woman, CrossFit coach, 172 cm, athletic muscular build, light-brown skin, short bleached buzz cut, a small scar through her left eyebrow, wide friendly smile; high-support lime-green sports bra, high-waisted black 7/8 leggings, black training shoes, black lifting belt, chalk on her hands |
| Theo | 27-year-old marathon runner, 180 cm, lean, curly red hair, freckles, a gap-tooth grin; cobalt singlet, black split shorts, white running shoes, a race bib, sweat |
| Big Sam | 45-year-old powerlifter, 185 cm, about 140 kg, grey beard, bald; black singlet, knee sleeves, a worn leather belt, chalk cloud around his hands |

Mara: [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_00d1bc4f1c02.jpg) (Seedream 5 Pro, 7 credits).

## The prompt that passes

```
Activewear brand catalog photo of a <age>-year-old adult woman with an athletic build, wearing a
high-support <colour> sports bra and high-waisted <colour> leggings, unbranded, mid-workout in a
sunlit concrete gym, holding a kettlebell at chest height, light sweat on her forehead, focused
expression. Natural skin texture with visible pores, real muscle definition. Shot on 35mm,
fitness magazine editorial.
```

Tested on `nano_banana_2_1`, `gpt_image_2_5`, `seedream_5_pro`, `flux_3_image`, `soul` and `grok_imagine_image_2`: passed on all six, and all six looked like real athletes. "Beautiful girl in a sports bra at the gym" was blocked on GPT Image 2.5; "hot sexy girl in a tight sports bra … big booty" was blocked on GPT Image 2.5 and FLUX 3 and came back as a plastic "AI girl" elsewhere.

| Instead of | Write |
|---|---|
| girl, fitness girl | woman, 31 / coach, 31 |
| tight, skin-tight | athletic fit, compression fit |
| booty, glutes shot | hips and thighs, or the exercise: "mid glute-bridge rep" |
| sweaty, oiled, wet | light post-workout sheen, towel over one shoulder |
| posing in a sports bra | mid-set of <exercise> |

## Video

Make each workout as an approved still, then animate it with `kling_v4` (creators use Kling for gym motion). Veo blocks more fitness clips; Seedance strict tiers reject photoreal face references, so for Seedance use the stills, not a face sheet. Looping exercise demos for an app: see the "Exercise demo loops" use case on skills.varg.ai.
