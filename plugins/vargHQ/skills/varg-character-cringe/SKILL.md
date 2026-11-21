---
name: varg-character-cringe
description: >-
  Makes cringe, deadpan, odd-looking AI characters people argue about, on varg: a photoreal,
  bizarre-but-believable person (strange haircut, wrong suit, absurd shoes) who takes himself
  completely seriously and repeats one action in a new place every post: the "Jean Phil" format
  of late 2026. Builds the character sheet and the posting format. Use when someone asks for a
  weird, cringe, odd, awkward or deadpan character, a strange AI influencer, a "is he real?"
  persona, or a character like Jean Phil. Part of varg-character-design (definition, sheet,
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

# Cringe deadpan characters

The late-2026 meta. Jean Phil (blonde bob, curled moustache, brown houndstooth suit, shadowboxing around Paris) reached 244K Instagram followers from 12 posts, one clip at 35.9M views; Bill Smith (burgundy suit, platinum bangs) 18.3M on one clip. They work because they are **bizarre but believable**: people scroll past 90 real humans to argue in the comments whether this one is real, and that argument is the distribution.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Definition**: a real-looking adult (35–65) + a look that is slightly wrong everywhere + one repeated action, done with total seriousness.

**Details** (the face must look like a real person, not a cartoon):

- One strange haircut: a blonde bob on a middle-aged man, a ginger comb-over, platinum bangs, a bowl cut, a mullet with a perm
- One strange face feature: a curled or droopy moustache, huge tinted aviators, a unibrow, a long neck with a prominent Adam's apple
- A body that is a little extreme: very tall and thin, very short and wide (show it with proportions: "arms hang to mid-thigh, small head for his height")
- Skin: real, "visible pores, natural skin texture, no retouching"
- **Expression: completely serious.** "Deadpan, he never smiles, he never explains himself."

**Clothing: one silhouette readable in one frame.**

- A suit in a colour or fabric nobody wears: mustard corduroy, brown houndstooth, burgundy velvet, mint polyester
- Something wrong at the edges: trousers too short with white socks, a knitted tie, a fur collar
- Absurd footwear or one accessory: white roller skates, cowboy boots, a fanny pack, a gold chain
- The same outfit in every post, forever

## Ready characters

| Character | Prompt seed |
|---|---|
| Gérard (tested) | 61-year-old Belgian man, extremely tall and lanky: very long thin legs, arms that hang to mid-thigh, narrow sloping shoulders, a long thin neck with a prominent Adam's apple, a small head for his height; thin ginger comb-over, huge tinted aviator glasses, droopy ginger moustache, completely serious; mustard-yellow corduroy three-piece suit with trousers slightly too short showing white socks, brown knitted tie, white quad roller skates with orange wheels |
| Dieter | 52-year-old German accountant, short and wide, blonde bowl cut, thin rimless glasses, a pencil moustache; a mint-green polyester leisure suit, a fanny pack, socks with sandals; power-walks everywhere with a stopwatch |
| Rex | 44-year-old Australian, wiry, a sun-bleached mullet with a perm, a gold chain, wraparound sunglasses on top of his head; a burgundy velvet tracksuit, unbranded, white cowboy boots; slow-motion karate kata in public places |

Gérard: [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_8252d5cfde30.jpg) (Seedream 5 Pro, 7 credits).

## Sheet

The model sheet from `varg-character-design`, model `seedream_5_pro`. Tested: height is invisible on a plain sheet even with proportions; Gérard reads as "tall" only in a scene with something to compare (a doorway, a car roof, a normal-height person). Put the scale in the scene prompts.

## The format

1. Same character, same outfit, one repeated action (shadowboxing, skating, power-walking, kata).
2. A new, very normal place every post: a supermarket, a metro platform, a wedding, a dentist's waiting room.
3. Motion from real footage you own or licensed: Kling motion control, Seedance "replace the person in @video1 with the character from @image1", or `minimax_h3_max_recast` with one clean full-body photo of him.
4. No dialogue, no explanation, no winking at the camera.

## Watch out

- Keep it original: copying Jean Phil's exact look is copying someone's character.
- Swap only footage you shot or licensed; never someone else's viral clip with a real person in it.
- The comedy is the costume and the situation, not ethnicity or disability.
- Label the account as AI (Instagram cuts reach of unlabelled AI-person accounts since 2026-08-31); the ambiguity can live in the content, not in hiding it.
