---
name: varg-character-absurd
description: >-
  Makes absurd AI characters and mascots people share, on varg: hybrids of a food or object, an
  animal and one human detail (a T-rex made of bread in a beret, a grumpy cactus mail carrier, a
  nervous sheep accountant), in a 3D family-film, clay stop-motion or photoreal look, as a
  turnaround sheet ready for scenes and video. The Italian-brainrot format with original
  characters. Use when someone asks for an absurd, funny, weird or brainrot character, a creature,
  a talking animal or object, a food character, or a brand mascot. Part of varg-character-design
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

# Absurd characters and mascots

The fastest-growing AI characters: Italian brainrot (Tralalero Tralala, a shark in sneakers; Ballerina Cappuccina, 55M+ TikTok views in half a year) turned into a Roblox game with 25.4M concurrent players; Fruit Love Island got 3M followers in 9 days. Mascots carry the best brand evidence: Coca-Cola's AI holiday ad scored the maximum on System1. Non-human characters also pass video filters far more easily than photoreal people and have no uncanny valley.

Use the **format**, not the famous characters: who owns the named brainrot characters is being fought in court.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Formula**: a food, plant or object + an animal (or a body plan) + one human detail + a job or a mood.

| Food / object | Animal / body | Human detail | Job or mood |
|---|---|---|---|
| baguette, croissant, avocado, espresso cup, cactus, sock | T-rex, shark, pigeon, frog, sheep | a beret, a postal cap, tiny sneakers, glasses, a tweed waistcoat | mail carrier, accountant, lifeguard, opera singer; grumpy, nervous, proud |

**Details**: one unambiguous noun per feature ("two antennae", not "ears or antennae"); big expressive eyes; the material written like a texture ("crusty golden crust with flour-dusted scoring marks", "fluffy wool made of rolled clay coils", "soft spines as a moustache"); a clear silhouette.

**Look** (put the style block first):

- 3D family film: "stylised 3D CGI animated family feature-film look, soft global illumination, warm key light, subsurface scattering, simplified rounded shapes, matte materials, clear silhouette"
- Clay stop-motion: "clay stop-motion look, visible fingerprints and tool marks on plasticine, slightly lumpy hand-sculpted forms, handmade miniature feel" (say "clay stop-motion", not "Claymation", which is a trademark)
- Photoreal creature: "photoreal, natural light, documentary wildlife photo"

## Ready characters (tested, `nano_banana_2_1`, 6 credits each)

| Character | Prompt seed | Sheet |
|---|---|---|
| Baguettosaurus | a small T-rex whose whole body is a crusty golden French baguette with flour-dusted scoring marks, tiny arms, big round googly eyes, a red-and-white striped knitted scarf, a black beret, stubby legs in tiny white sneakers; 3D family-film look | [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_3356a6c5b5c1.png) |
| Señor Pincho | a grumpy tall saguaro cactus who works as a desert mail carrier: two cactus arms, a bushy white moustache made of soft spines, big expressive eyes under heavy brows, a tiny blue postal cap, a worn leather mailbag, one small pink flower on his head; 3D family-film look | [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_844b46a7a45d.png) |
| Hector | a nervous sheep who works as an accountant: cream-coloured long face, long floppy ears, large buck teeth, big round tortoiseshell glasses, fluffy white wool made of rolled clay coils, a tiny brown tweed waistcoat, an abacus under one arm; clay stop-motion look | [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_eb98a40764c2.png) |

## Sheet

```
Character turnaround sheet of an original creature, flat light-grey background, even soft light,
no text, no labels, no logos. Top row: three full-body views at the same scale: front, side
profile, back. Bottom row: three large head close-ups: <three expressions>. The same creature in
every panel. CHARACTER: <seed>. STYLE: <style block>. Original design, no recognizable existing
characters.
```

Model: `nano_banana_2_1` (holds stylised designs; 6 credits).

## Formats that work

- A fake-Italian (or fake-anything) name and a chant, one creature per post, collectible lore.
- A micro-drama cast (fruits, cats) with cliffhangers; one sheet per cast member, one set.
- A mascot with an expression sheet, then the same mascot in every ad and as merch (a boxed vinyl figure from the sheet works in one `nano_banana_2_1` call).
- Myth creatures doing mundane influencer things (vlogging, complaining, a selfie stick).

## Watch out

- Don't reuse named brainrot characters, Stormtroopers or studio mascots: original creatures only.
- Absurd series grow fast but pay poorly as pages (Fruit Love Island quit citing no revenue). They pay as brand mascots, toys and kids' series.
