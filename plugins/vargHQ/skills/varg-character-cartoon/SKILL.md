---
name: varg-character-cartoon
description: >-
  Makes original cartoon characters in famous, instantly recognisable looks on varg: the yellow
  1990s family sitcom, the 3D family feature film, hand-painted anime, paper cut-out, adult sci-fi
  cartoon, felt puppet and others, described in words instead of IP names (the names get blocked
  and do not belong in ads). Also restyles an existing character into those looks. Use when
  someone asks for a Simpsons-style, Pixar-style, Ghibli-style, South Park-style or Rick and
  Morty-style character, a cartoon version of a person or mascot, or "me as a cartoon". Part of
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

# Cartoon characters in famous looks

A loved animation look tells the viewer the genre before the first word: the Ghibli wave added 1M ChatGPT users in an hour, the figurine trend brought Gemini 13M new users in 4 days. The look is free to use; the show's characters, names, logos and catchphrases are not.

Tested on 2026-10-27: Nano Banana 2.1 **refused** "Redraw the woman as a character in The Simpsons style" and drew the same look from a description. GPT Image 2.5 and Seedream 5 Pro accepted the name, but the name still has no place in a prompt you will use for an ad, a title or a caption.

Sheet, crops and video: `varg-character-design`.

## The recipe

**Style block first, then an original character, then the guard line.**

```
Character model sheet of an original cartoon character, flat light-grey background, no text, no
labels, no logos. Top row: three full-body views at the same scale: front, side profile, back.
Bottom row: three head close-ups: <three expressions>. The same character in every panel.
STYLE: <style block>. CHARACTER: <name, age, body, hair, outfit, prop>.
Original design, no recognizable existing characters.
```

Design the character to be yours: a hair shape, an outfit and a prop that no existing character has.

## Style blocks

| Look | Style block | Model | Keep away from |
|---|---|---|---|
| Yellow family sitcom (1990s primetime) | flat 2D TV-animation look of a classic 1990s primetime family sitcom: thick uniform black outlines, flat saturated cel colors, no shading, lemon-yellow skin, large round white eyes with small black dot pupils, overbite, four-fingered hands | `nano_banana_2_1` | bald with two hairs, a blue beehive, spiky-haired kids, the town, the couch gag |
| 3D family feature film | stylised 3D CGI animated family feature-film look, soft global illumination, warm key light, subsurface scattering, big expressive eyes, simplified rounded shapes, matte materials | `nano_banana_2_1`, `gpt_image_2_5` | lookalike toys and robots, studio names |
| Hand-painted pastoral anime | hand-painted watercolor and gouache backgrounds, soft cel-shaded characters with simple faces, big summer clouds, warm nostalgic countryside light, 1990s Japanese animated feature film | `gpt_image_2_5`, `seedance_2_5` | forest-spirit lookalikes |
| Paper cut-out | crude construction-paper cut-out animation, flat shapes, visible paper texture, round heads, mitten hands, small snowy mountain town | `nano_banana_2_1` | the four boys |
| Adult sci-fi cartoon | late-night adult 2D sci-fi cartoon, wobbly thin outlines, flat colours, bulging eyes with drawn pupils, neon-green glow, garage-lab clutter | `gpt_image_2_5`, `nano_banana_2_1` | a lab-coat scientist with spiky blue-grey hair and a yellow-shirt teen |
| Clay stop-motion | clay stop-motion look, visible fingerprints and tool marks on plasticine, lumpy hand-sculpted forms, handmade miniature set | `nano_banana_2_1` | the inventor and his dog |
| Felt puppet | handmade felt and fleece hand puppet, foam head, ping-pong-ball eyes, wide hinged mouth, visible stitching, TV-studio set | `gpt_image_2_5` | a green frog, a pig diva |
| Vinyl collectible | boxed 6-inch collectible vinyl figure, matte vinyl, slightly oversized head, window box with your own brand art | `nano_banana_2_1` | the big-head box shape and logo of existing toy lines |
| 1970s Saturday-morning cartoon (video) | use the video preset | `minimax_h3_max_style_retro_toon_70s` | |

## Ready characters

| Character | Prompt seed | Result |
|---|---|---|
| Gary Pruitt (tested) | a tired 45-year-old office manager with a wild curly orange mullet, a thick unibrow and a pot belly, a green sweater vest over a pink short-sleeve shirt, brown trousers, a lanyard ID badge, a giant coffee mug; yellow sitcom look | [sheet](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_a4a9e3cae8a4.png) |
| Nonna Rosa restyled (tested) | "Redraw the woman from the character sheet as a 2D cartoon in the look of a classic 1990s primetime animated sitcom: <style block>. Keep her outfit, curlers, glasses, headscarf, leopard housecoat, red slippers and wooden spoon." with her sheet in `files` | [image](https://s3.varg.ai/files/194b94d0-58ff-4e8b-91de-4f1959d04013/file_6e0343fe7b20.png) |

## Restyling someone

Pass the person's sheet or photo (with consent) in `files` and write: "Redraw the person from the reference as <style block>. Keep <hair, glasses, outfit, signature>." Then make a new model sheet in the new style before any video: a photoreal sheet next to a cartoon prompt makes video models mix the two.

## Watch out

- Our Gary is original, but the yellow sitcom look is close to one show's trade dress; for paid ads push it further (another skin colour or eye style).
- "Pixar", "Ghibli", "LEGO", "Funko", "Muppet", "Claymation" are names and trademarks: keep them out of prompts, file names, titles and ad copy.
- Stylised characters pass video filters (Seedance, Veo) far more easily than photoreal faces.
