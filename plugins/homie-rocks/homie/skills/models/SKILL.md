---
name: models
description: Give a game real 3D models that fit together and run on a phone — free CC0 models from Homie's starter library (Kenney, KayKit, Poly Haven, ambientCG) copied in with their licence, the person's own files checked and made phone-sized, and generated props (a concept image in the game's locked style, then Tripo P1 image-to-3D) and generated rigged characters (an A-pose concept, then Meshy 7.1 with its auto-rig, the library's clips retargeted onto it) on the person's OWN fal account under a hard budget with a receipt per call — every asset recorded with its provenance and licence (RIGHTS.md, the credits page), checked against phone budgets, shown in a lineup at true scale, and loaded through one safe loader. Use when someone wants 3D models, props, characters, scenery or "free assets" for a game, asks where a model came from or whether it may be used, or says the models look like they are from different games.
compatibility: Node 22. Generated props use Tripo's models, and generated characters Meshy's, on the creator's own fal account (FAL_KEY); fal's own MCP server (https://mcp.fal.ai/mcp-relay) reads schemas and prices.
metadata:
  providers: fal tripo
---

# Models for a game: free first, everything licensed, one look

Read the `style` skill first: a game's models are made under its decisions (render style, palette, scale,
budgets). Routes, cheapest coherent one first:

1. **The engine** (free): procedural geometry, tinted from the palette. The house's best looks are procedural;
   never replace one with generated meshes without the owner's ask.
2. **The starter library** (free, CC0): `assets find`, then `assets add`.
3. **The person's own files**: `assets add --file … --license …` (ask whose it is).
4. **Generated** (paid, their own fal account, under a budget): a concept, then a mesh: props, and rigged characters
   (below). A character's rig, clips and feel are the `animate` skill's.

Commands run from inside the studio: `npx --no-install homie-studio assets …` (free) and this skill's script for
the paid route: `node "${CLAUDE_PLUGIN_ROOT}/skills/models/scripts/models.mjs" <command>` (in an app with Homie's
tools: `assets_find`, `asset_add`, `asset_make`, `asset_check`, `asset_lineup`, `asset_rights`).

## The starter library (free)

```sh
npx --no-install homie-studio assets find "fox"                    # CC0 items, phone-sized, with triangles and size
npx --no-install homie-studio assets find "pine tree" --family kenney
npx --no-install homie-studio assets add <id> kenney-cube-pets/animal-fox --height 0.7 --card "Characters/Fox"
```

One library family per game (`cast.family`): mixing Kenney with KayKit shows. An added item is COPIED into
`games/<id>/public/models/` (never loaded from homie.rocks at runtime), recorded in `assets/manifest.json` with its
pack, origin and SHA-256, and its pack is credited on the landing's credits page (kindly: CC0 needs no credit).
`HOMIE_LIBRARY` points at another copy of the library (a folder or an address).

## The person's own files

```sh
npx --no-install homie-studio assets add <id> --file /path/to/lantern.glb --license own --as lantern --height 0.6
```

Ask whose it is and under what licence: `own`, `cc0`, `cc-by-4.0` (with `--attribution "<who, where>"`),
`eula:<store>`, `market:<listing>`, `other` (with `--notes`). The file is refused before anything reads it when it
loads anything from an address (an external URI), declares a buffer over the import cap, or is over 64 MB; a
.gltf may bring its .bin and pictures from its own folder only. Then it is made phone-sized (its tier's
triangles and picture size, the pivot at the bottom centre, its height in metres, meshopt geometry, WebP
pictures); the raw file stays in `art/<slug>/raw/` (git-ignored; the studio's R2 with `media move` once it has
storage), never shipped and never committed. FBX, OBJ and .blend: export a .glb first (Blender: File > Export >
glTF 2.0, binary).

## Generated props (paid): price, budget, look, then the mesh

```sh
node <models.mjs> check                                  # the fal key (a free check) and the registry
node <models.mjs> quote <id> --count 3                   # concept + mesh, priced live (about US$0.54 a prop)
node <models.mjs> budget <id> --cap 3                    # the cap the person agreed to, for this game's models
node <models.mjs> prop <id> lantern --card "Items/Ember Lantern" --what "an iron lantern with a warm ember inside" --height 0.6 --dry-run
node <models.mjs> prop <id> lantern --card "Items/Ember Lantern" --what "…" --height 0.6 --yes     # the concept only
#   LOOK at art/lantern/concept.*: the thing, whole, in the game's style, on a plain background?
node <models.mjs> prop <id> lantern --mesh --yes          # Tripo P1, textured, face_limit 1500; then optimised and recorded
npx --no-install homie-studio assets lineup <id>         # true scale, silhouettes, palette drift
```

- Tell the person the price first and agree a cap; `prop` refuses with no budget, refuses past the cap, and asks
  again without `--yes`. The receipt is written the moment fal accepts the job (`art/receipts.jsonl`, the
  game's `art/<id>-models/budget.json`); running the same step again resumes it and never pays twice.
- The concept starts from the derived style prompt (`homie-studio style prompt <id>`) with the golden images as
  references, on a plain background with even light (baked light is the top quality problem of image-to-3D).
- **Never a loop.** Look at the concept before the mesh, and at the model in the lineup before the next one. A
  bad concept: change the words and `--concept-again` once. Spend the riskiest prop first.
- `references/models.json` is the dated registry of endpoints, prices and schemas. Endpoints retire and reprice
  monthly: `node <models.mjs> registry` reads every price again for free; update the registry (`--write`) when one
  moved, and never hard-code an endpoint anywhere else. fal's own MCP server (`get_model_schema`, `get_pricing`,
  `search_models` for a newer Tripo version; the `art` skill says how to connect it) reads the same facts; a paid
  run still goes through `models.mjs`, never the MCP's `run_model`.
- Tripo's models run **on fal** here (`tripo3d/...` endpoints): one account, prices read live, the receipts above.
  Tripo's own CLI and MCP server (`tripo-cli`, `tripo mcp`) bill a separate Tripo account in Tripo credits, outside
  this skill's budget and receipts, and a free Tripo plan makes its outputs public under CC BY 4.0
  (`references/RIGHTS.md`): keep a game's models on the fal route. The Homie mod (Claude Code) and Homie's hooks (Codex)
  hold a `tripo` generating command or a Tripo MCP tool as a call whose cost cannot be read first.
- A painted mood image for the style board: `node <models.mjs> mood <id> b --yes` (about US$0.035; a target).

## Generated characters (paid): an A-pose concept, then a rigged mesh

Library characters first (`assets find "knight" --kind character`: KayKit's adventurers and skeletons, Kenney's mini
and blocky characters, all CC0 and animated). For one the library cannot cover:

```sh
node <models.mjs> character <id> ranger --card "Players/Ranger" --what "a forest ranger: green hooded cloak, leather tunic, a bow on the back" --height 1.45 --like kaykit-adventurers/rogue --dry-run
node <models.mjs> character <id> ranger --card "Players/Ranger" --what "…" --height 1.45 --like kaykit-adventurers/rogue --yes   # the concept only
#   LOOK at art/ranger/concept.*: one character, whole, in an A-pose, in the game's style, on a plain background?
node <models.mjs> character <id> ranger --mesh --yes     # Meshy 7.1 + auto-rig, about US$1.40; then free: optimised, rig mapped, clips retargeted
npx --no-install homie-studio anim preview <id> --asset ranger   # LOOK at the preview sheet
```

`--like` takes a library character's own thumbnail as the style reference (so a generated hero stands beside the
library's in one look); golden images, when the game has them, come first. The concept is a full body in an A-pose,
front view, plain background (what auto-rigging needs). Humanoids with clear limbs only. The quote reads fal's pricing
API and the model page's add-ons (textures, rigging) and takes the higher. The raw rigged file stays in
`art/<asset>/raw/`; the shipped character is phone-sized with its skeleton mapped to the standard and the library's
CC0 clips (idle, run, jump, attack, hit, die, ...) retargeted onto it, recorded with both receipts.

## Check, lineup, rights

```sh
npx --no-install homie-studio assets check <id>    # phone budgets, the glTF-Validator, licences, staleness, big files
npx --no-install homie-studio assets lineup <id>   # pictures in .studio/art/<id>/; look at them
npx --no-install homie-studio assets rights <id>   # games/<id>/assets/RIGHTS.md and the credits
npx --no-install homie-studio assets redo <id> <asset>   # made again from its kept raw file, free
```

`assets redo` runs only the free steps again (today's budgets and render style, from `art/<slug>/raw/`). A model
drawn black in the game is metal with nothing to reflect: every style but `pbr` makes models non-metal, and a redo
applies it to one made before. A palette or shape change needs a new concept and mesh (paid), not a redo.

Phone budgets (per asset): a prop 1,500 triangles and 512 px pictures, a hero 8,000 and 1,024 px, one material;
the scene: about 100 draw calls, 150,000 triangles, 48 MB of picture memory, 5 MB to download before the first
round. `assets check` holds the game to them; the `perf` skill is the real gate on a phone.

After the lineup, have a FRESH reviewer (the `playtest` skill's blind review: a new agent that never saw your
reasoning) look at the style board, the golden images and the lineup pictures and score "does every model look
like one game?" from 1 to 10, naming outliers; record it: `assets review <id> --score <n> --outliers a,b`.
Under 7, or any outlier, those assets need another look.

## Loading them in the game

Every model loads through `@homie-rocks/studio/assets`:

```ts
import { createModels } from '@homie-rocks/studio/assets';
const models = createModels();
const fox = await models.instance('./models/fox.glb').catch(() => models.placeholder({ x: 0.5, y: 0.7, z: 0.8 }));
```

It refuses an unsafe or oversized file (an external URI, a buffer over the cap, an extension three.js cannot
read) before parsing it, decodes meshopt geometry, clones skinned models properly, and warns in development
when a model is over its budget. Draw each loaded model the way the decisions say, once, before copying it:
`stylize((await models.load(url)).scene, style)` with the game's `style.json` (its material model and ink outline,
as the style board drew them). The `gem-rush-3d` starter shows the whole pattern.

## Licences, plainly

- `references/RIGHTS.md` keeps what the providers' terms say, with read dates. Read the live pages again before
  anything commercial is published (`registry` re-reads prices; terms you read by hand).
- A public game may contain only assets whose licence lets them sit in a public source: CC0, CC BY with credit,
  the studio's own, and generated ones. Anything else is `remix: none` (remixers get a grey placeholder) and the
  studio's repository must stay private while it holds the raw file. `publish` refuses a game with an asset that
  has no licence record.
- Never fetch from Poly Pizza or ShareTextures by script, never use Quaternius, Mixamo, Synty, Fab, Unity Asset
  Store or TurboSquid files in a public game's repository, never use a model or dataset under non-commercial
  terms.

## Never

- Never spend without a budget, past it, or without a receipt; never run paid generation in a loop; never print
  or store a key.
- Never ship a raw provider file, never commit one, never ship an asset with no licence record.
- Never replace a model the person made without asking.
