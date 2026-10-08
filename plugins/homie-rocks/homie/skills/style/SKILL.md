---
name: style
description: "A game's look as a set of decisions that fit together — render style, palette, shape language, proportions, materials, light, camera, fonts and effects; then the cast, its library family, scale and phone budgets — each picked automatically from the person's words with a one-line why, which the person can steer (\"warmer\", \"closer\"), lock, or explore on a style board of three directions drawn by the game engine itself (free; a painted mood image only on their own fal account). Locked and pinned decisions keep every asset coherent: change one and the blast radius lists exactly what went stale and what remaking it would cost, and nothing is remade without a yes. Use when someone talks about a game's look or style, \"make it look like…\", \"show me other looks\", \"keep that palette\", \"darker\", \"the art doesn't fit together\", or before making any models or art for a game."
compatibility: Node 22 and Chrome. The style board is free; a painted mood image uses the creator's own fal account (FAL_KEY), through the models skill.
metadata:
  providers: fal
---

# The look of a game: decisions, the board, locks

A game's art direction lives in `games/<id>/codex/decisions.json` (private, like the codex) and is drawn in
the Game Codex's **Art direction** tab: every decision with its value, its why, and its state. It is the style
bible. Everything made for the game (models, textures, covers, title cards) is made under it and records the
revision it was made under, so the game stays one game.

| State | Meaning | Who changes it |
| --- | --- | --- |
| **auto** | your pick, with its why | you, freely |
| **steered** | the person nudged it ("warmer") | you may refine within the nudge, never undo it |
| **pinned** | the first asset built on it pinned it (locked by use) | you only while nothing paid or published depends on it; else ask |
| **locked** | the person froze it | only the person: unlock needs their reason, after they saw the blast radius |

A lock protects taste, not money: no signed approval, but you never change a locked value on your own, and you
record their words when you lock for them.

## The automatic path (the default: no questions)

```sh
npx --no-install homie-studio style init <id> --prompt "<the person's own words about the game>"
```

It fills about thirty decisions from their words, the codex and the genre, writes `style.json` (the palette,
fonts, light and camera the game draws with) and redraws the codex. Say ONE line: "Look: flat low-poly,
autumn grove palette, golden hour, high three-quarter camera; open the codex to change anything." Then build
with free routes only (the engine and the starter library: the `models` skill) unless the plan set an art
budget. The first asset you add pins the decisions it was made under.

## The hands-on path

When the person wants to steer the look closely (the plan asks once), show the **style board**:

```sh
npx --no-install homie-studio style board <id>
```

(In an app with Homie's cards: `style_explore`; the card has Pick, Mix, Steer and Lock.) Three coherent
directions, each **drawn by the game's own engine**: its palette on a ground and a sky, its light and fog, its
camera, its material model (flat, toon with ink outlines, painted, PBR, pixel), a character stand-in at the
decided proportions, and the starter library family's own pieces re-tinted into the palette, with the title in
its display font. Free, about 20 seconds, saved under `games/<id>/codex/board/`. Look at all three yourself
before you show them (file_read), and say in one line each what is different.

- **Pick**: `style pick <id> b`. **Mix**: `style pick <id> --mix style.palette=b,style.camera=c`.
- **Steer**: `style steer <id> style.palette "warmer"` (warmer, cooler, less saturated, darker, lighter, a hex
  colour with its job; light: golden hour, night, harder shadows; camera: closer, further, higher, top-down;
  shape: chunkier, sharper; materials: add outlines). Words it does not know are recorded; refine the value
  with `style set` within them.
- **Lock** when the person says so: `style lock <id> style.palette --words "<what they said>"`, or the whole
  style: `style lock <id> style --words "…"`.
- **A painted mood image** per direction is optional and PAID (about US$0.035 each, the person's own fal
  account, `models.mjs mood`): a picture the engine cannot draw is a target, never a promise, and the card says
  so. Offer it only when the engine's swatches leave the person unsure.
- **Golden images**: once the style is locked, two to six approved pictures (a chosen mood image, a concept they
  loved, their own art) become the references of every generated concept: `style golden <id> add <image>`.

## The characters: the cast card

`cast_plan` (or `npx --no-install homie-studio cast <id>`) shows the decisions that shape characters together:
proportions (heads tall, metres), the shape language and its silhouette rule (every character readable black on white
at 64 px: the lineup checks it), the palette, the library family, the skeleton family (`rig.skeleton`) and where rigs
come from; then every character made or planned, with its source, skeleton, bones, triangles and clips. A library
character comes in free (`asset_add`); a generated one through the `models` skill's `character` (paid, priced first);
their clips and feel are the `animate` skill's. A starter game's own `style.json` is what `style init` starts from:
it never repaints a working game behind its back.

## Changing a locked decision: the blast radius first

When the person wants a locked or pinned decision changed, never just change it:

```sh
npx --no-install homie-studio style blast <id> style.palette            # what goes stale, and the cost
npx --no-install homie-studio style set <id> style.palette <value> --unlock --reason "<their words>"          # shows it again, changes nothing
npx --no-install homie-studio style set <id> style.palette <value> --unlock --reason "<their words>" --confirm  # after their yes
```

Tell them the list in plain words: which assets go stale, which are fixed for free (a palette re-tint of
flat-coloured models, another library match, a procedural one regenerated) and what remaking the generated ones
would cost. Nothing is remade by itself: remaking is a new, priced job they approve (the `models` skill).

## One look end to end

- The game draws with `games/<id>/style.json` (palette, fonts, light, camera): read it rather than hard-coding
  colours, so a change of the palette reaches the HUD and the world.
- The codex wears a steered or locked palette and fonts; the landing and the trailer's title cards use them too
  (a game with no `landing.theme` takes its accent and glow from `style.json`).
- `style prompt <id>` is the derived style prompt (about 80 words: medium, shape, palette hexes, light, framing)
  every generated picture starts from. It is computed, never edited by hand.

## Never

- Never change a locked decision without the person's yes after the blast radius; never remake anything by
  yourself; never lock on your own.
- Never present a painted mood image as what the game looks like.
- Never name a living artist in a style ("in the style of …"): describe the look in words.
- Never "upgrade" a game whose procedural look is its strength to generated meshes without the owner's ask.
