---
name: varg-character-big-guy
description: >-
  Makes big, heavy AI characters people remember, on varg: very large men (and women) whose size
  is shown with visible cues instead of numbers, dressed so the contrast tells the joke (a 160 kg
  florist in a tiny pink apron), played straight and never mocked, as a character sheet ready for
  scenes and video. Use when someone asks for a fat, big, heavy, chubby or plus-size character, a
  big guy, a gentle giant, a huge man in a small job, or a strongman. Part of
  varg-character-design (definition, sheet, reuse in video).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
  openclaw:
    homepage: https://varg.ai
compatibility: Needs the varg MCP connection (https://mcp.varg.ai/mcp) or a VARG_API_KEY (see varg-ai).
allowed-tools: Bash(curl:*) Read Write Edit
---

# Big guy characters

Extreme bodies played straight are one of the most shared AI character types of late 2026: a 280-lb clown lifting cars reached 14.6M views on one reel, an 80s bodybuilder with a mullet 9.1M, a 6'7", 154 lb gym guy 4.6M. "Chubby" the fat orange AI cat had a video with 136M views in 4 days. Size is a silhouette you read in one frame, and physical comedy needs no words.

**The rule:** the joke is the **contrast** (size against job, outfit or skill), never the body itself. He is good at what he does and completely serious about it.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Definition**: age + size + a job or hobby that is small, delicate or unexpected (florist, ballet teacher, barista with latte art, model-train collector, yoga instructor).

**Details: show the size, don't just state it.** Tested on Seedream 5 Pro: "178 cm and about 160 kg" came out as a merely heavy-set man ([v1](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_33b0d3a66e95.jpg)); the version below got the size right ([v2](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_7715698a084a.jpg)).

- Belly: "wide round belly that pushes the apron far forward and hangs over his waistband"
- Neck and face: "thick neck, full round cheeks and a double chin"
- Arms and legs: "thick upper arms and forearms", "thick legs"
- Shoulders: "broad heavy shoulders"
- Always: "realistic weight distribution, not slimmed", full-length framing
- Face: a beard, small glasses, a shaved head or a tiny man-bun, a gentle or deadly serious look
- For women: "plus-size adult woman, US size 22, 165 cm, full upper arms, soft belly, wide hips, full face", confident

**Clothing: fit tells the joke.**

- Something too small or too delicate: a tiny pastel apron, a ballet wrap cardigan, a child-size backpack, a cycling jersey a size too small
- Something true to size underneath: a black crew-neck T-shirt that fits, work trousers
- One prop that is small in his hands: a bouquet of tulips, an espresso cup, a pencil behind his ear, a tiny dog

## Ready characters

| Character | Prompt seed |
|---|---|
| Bruno (tested) | 48-year-old Italian-American florist, a very large heavyweight man of about 160 kg: wide round belly that pushes the apron far forward and hangs over his waistband, broad heavy shoulders, thick neck, full cheeks and a double chin, thick tattooed forearms, shaved head, bushy salt-and-pepper beard, small round gold-rimmed glasses, gentle shy half-smile; a tiny pastel-pink canvas apron that looks too small on him, black crew-neck T-shirt true to size, grey work trousers, white clogs, a pencil behind his ear |
| Big Lou | 35-year-old ex-powerlifter who now teaches ballet to adults, 190 cm, about 150 kg, huge round belly and arms, buzz cut, thick black beard; black leotard over grey sweatpants, pale pink ballet slippers, deadly serious |
| Tiny Tony | 40-year-old barista, 185 cm, about 170 kg, round face, waxed handlebar moustache, slicked-back hair; a too-small denim apron, rolled sleeves, makes perfect latte art with a tiny steel jug |

## Sheet

Use the model sheet from `varg-character-design` with the details above. Model: `seedream_5_pro` (7 credits). Ask for **full-body panels that fill the frame**: models quietly shrink bigger bodies with loose clothes, tight crops and angled poses.

## Formats that work

- One delicate skill done perfectly (arranging flowers, a pirouette, latte art), deadpan.
- The strongman: lifting something absurd (a car, a horse, a vending machine), no comment.
- Same character, a new small job every post.

## Watch out

- "Curvy", "chubby", "fat" alone are read inconsistently; describe what the camera sees.
- No body-shaming jokes, no food-as-punchline. Brands avoid it, and the archetype works without it.
- Shirtless strongman content passes better with a sport context: "strongman competitor at a contest, lifting belt, chalk".
