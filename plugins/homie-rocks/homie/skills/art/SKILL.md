---
name: art
description: Make a studio's game look like something at build time — a cover from a real frame of the game (free), painted covers, backdrops, textures and character plates from image models through the creator's OWN fal account under a hard budget with a receipt for every call, checked (does the texture tile, is the file small enough for a phone, does the cover promise only what the game contains) and loaded by the game — plus the art-direction method (a style sheet and paintovers of real frames as the target the game's own rendering is changed to reach). Use when someone asks for cover art, key art, a thumbnail, a hero image, backgrounds, textures, sprites, or says the game looks rough, flat or unfinished.
compatibility: Node 22, ffmpeg and Chrome. Generated images use the creator's own fal account (FAL_KEY); fal's own MCP server (https://mcp.fal.ai/mcp-relay) finds models and reads prices.
metadata:
  providers: fal
---

# Art for a studio's game

**Build time, never a frame of play.** Everything here happens once, before anybody plays, and costs
nothing at runtime: never call an image model from a game's loop or from anything a person waits on.
If you want one there, you want a baked asset instead.

One script: `scripts/art.mjs` in this skill's folder (Claude Code:
`node "${CLAUDE_PLUGIN_ROOT}/skills/art/scripts/art.mjs" <command>`), from inside the studio. Node 22,
ffmpeg and Chrome; `--json` on every command. Art jobs live in `art/<slug>/` (the images, the
`budget.json`, the `.request` and `.json` receipts beside each generated file); every paid call is
also a line in `art/receipts.jsonl`.

```sh
node <art.mjs> check      # ffmpeg, Chrome, the studio; the fal key checked for free (only generated images need it)
```

## 1. The cover, first, always

The cover is what a stranger sees before pressing anything: the studio's game page, the directory
card, a link preview. Start from the game itself:

```sh
npm run dev                                                       # background task
node <art.mjs> frame <game> --url http://127.0.0.1:8787           # frames of the big screen playing, the busiest picked
node <art.mjs> cover <game> --from art/frames/frame-04.png [--focus 0.6,0.4]
```

`frame` films the game's big screen (bots playing in a live room) with the platform's own furniture
hidden (the join QR, the status chip, result cards) and keeps the frame with the most visible detail.
`cover` crops it to 16:9 around the focus, writes `cover.jpg` (1600x900, under 400 KB) into the game
and names it in `game.json` (`"cover": "cover.jpg"`): the site and the directory use it until the game's
landing has a still of its own (`hero/wide.jpg`), which then is its picture everywhere.

**Open the cover and look.** A cover is a picture of the GAME: no QR code, no share panel, no debug
text, not the waiting screen (a picture of nothing happening). Dark or featureless frames get a
warning: a black card on a page reads as a black box.

**A painted cover** from that frame, when the person wants one (paid, below): write the prompt from
the game you just played, never from its title. Describe what is on screen: the palette, the time of
day, what the player is doing, the shapes. A cover that promises something the game does not contain
is the one failure here that matters: a person presses Play expecting that picture and meets
something else. Use the real frame as the image reference (`"@file:art/frames/frame-04.png"` in the
input) so the painting keeps the game's layout.

## 2. Paid images: price, budget, one call at a time

Generated images come from fal through the person's own account: they create a key at
https://fal.ai/dashboard/keys and set `FAL_KEY` in the environment Claude or Codex runs in (never
pasted into the chat, never written into the studio). **fal's own MCP server** is how you find a
model and read its input schema and price (`search_models`, `recommend_model`, `get_model_schema`,
`get_pricing`): use it rather than memory, because endpoints retire and reprice. Not connected? Offer
it, and the person signs in on fal's own page (no key): in Claude Code `claude mcp add --transport http
--scope user fal https://mcp.fal.ai/mcp-relay`, then `/mcp`; in Codex `codex mcp add fal --url
https://mcp.fal.ai/mcp-relay`, then `codex mcp login fal`. **Paid calls go through `art.mjs gen`,
never the MCP's `run_model` or `submit_job`**: `gen` prices, caps, receipts and resumes; the MCP's run
does none of that (the Homie mod in Claude Code, and Homie's hooks in Codex, hold one as a call whose cost cannot be read first).

```sh
node <art.mjs> price --model fal-ai/flux/dev --input art/cover/input.json    # free: fal's unit price x this input
node <art.mjs> budget cover --cap <dollars the person agreed to>
node <art.mjs> gen cover --model fal-ai/flux/dev --input art/cover/input.json --out cover-painted.jpg --dry-run
node <art.mjs> gen cover --model fal-ai/flux/dev --input art/cover/input.json --out cover-painted.jpg --yes
```

- Tell the person the price and ask for a cap before the first call. `gen` refuses with no budget,
  refuses past the cap, and asks again without `--yes`.
- The receipt is written the moment fal accepts the job. Running the same `gen` again resumes it from
  `<out>.request`: it never pays twice. A cut-off call is resumed, not re-sent.
- **Never run paid generation in a loop** to "try until it is good". Look at what came back, change
  the prompt, run it once more. Spend the riskiest image first.
- No real people, no real brands, no copyrighted characters, no "in the style of" a living artist, in
  prompts or references.
- **Every prompt starts from the game's derived style prompt** (`homie-studio style prompt <id>`: medium,
  shape, palette hexes, light, framing; computed from the decisions, never edited by hand) and uses the golden
  images as references on a multi-reference model. A picture made under an older palette is listed stale when
  the palette changes (the `style` skill's blast radius).
- What the provider's terms say about the pictures, with read dates: `references/RIGHTS.md`. Read the live page
  again before anything commercial is published.
- 3D models (props, characters) are the `models` skill's; mood images for the style board are too
  (`models.mjs mood`).

## 3. Backdrops, textures, plates

A procedural gradient sky is the tell that a game was generated; a painted one costs one image at build
time and loads like any other asset. Good candidates: a skybox or far matte, a ground or wall texture,
a character plate, a title card. Bad: anything the game generates procedurally for a reason.

```sh
node <art.mjs> tile art/floor/floor.png                                      # does it tile? seam numbers and a 2x2 preview
node <art.mjs> fit art/floor/floor.png --out games/<id>/public/art/floor.jpg --width 1024 --max-kb 250
node <art.mjs> sheet art/floor                                               # everything in a job, labelled, to look at
```

- **Models are bad at tiling.** Ask for a texture, then check it: a seam over 2 shows as a grid of
  lines in the game. Mirror-blend the edges or make it tile yourself before it ships.
- **Size is a feature.** A phone downloads every byte before the first round. Fit backdrops to the
  size they are drawn at, JPEG (or WebP where ffmpeg has it) for pictures, PNG only for hard-edged
  sprites with transparency. Then play it again: the `playtest` skill's first row times the load; an
  asset that doubled the load time made the game worse.
- Put art where the game's own build puts assets (`games/<id>/public/` for a bundled game, the
  game's folder for a static one) and load it with a relative path.

## 4. Art direction: paintovers, then change the game

Images do not fix a game that looks unfinished; the best-loved browser games often ship no texture
files at all. What makes a frame look finished is light, contrast between the subject and the ground,
detail at more than one scale, and a clear horizon or depth. The method:

1. **The style bible is the game's decisions** (the `style` skill): render style, palette with its jobs,
   light, shape language, camera, fonts, drawn in the codex's Art direction tab. An older studio's
   `art/STYLE.md` retires into it: carry what it says into `style set` / `style steer`, then keep only the
   decisions. Paint with the LOCKED palette and light.
2. **Paintovers**: real frames of the game (`frame`), painted over by an image model with the derived style
   prompt (`npx --no-install homie-studio style prompt <id>`) and the frame as the reference, plus the golden
   images (`style golden`) where there are any. These are the TARGET, never shipped as the game.
3. **Change the game's own rendering** (lights, materials, fog, the floor, the camera) until frames of
   the running game match the paintover; compare them side by side.
4. **Judge blind**: frames of the old build, the new one and a reference game the person admires,
   shuffled under random labels, scored by a fresh reviewer before the labels are revealed (the
   `playtest` skill's review). A reference is a bar, not a template.

## Tell the person

What was made and where it is used, the file sizes, what it cost (from the receipts) against the cap,
what is a real frame and what is generated, and the pictures themselves.

## Never

- Never ship generated art as a screenshot of gameplay, or a cover that shows what the game does not have.
- Never spend without a budget, past it, or without a receipt; never print or store a key.
- Never replace art a person made without asking.
