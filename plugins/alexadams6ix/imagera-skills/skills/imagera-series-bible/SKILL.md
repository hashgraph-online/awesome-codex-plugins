---
name: imagera-series-bible
description: "Someone is starting a series and needs the kit every later shot is generated against: lead turnarounds, empty location plates and a title card. Use when: \"I'm starting a series and need a show bible for my leads\", \"Make character turnaround sheets for my recurring cast\", \"Set up a series bible for my sci-fi show\", \"series bible\", \"show bible\", \"character bible\", \"turnaround sheet\". Runs the Imagera \"Set your show up once\" template (up to six images and about five minutes. The only part of a series you do not pay for again next episode.)."
---

# Set your show up once

The assets a series reuses: a four-panel turnaround for each lead, an empty plate of every recurring location, and a title card. Nothing here is a shot — it is the kit every later shot is generated against. A character described in words drifts between episodes; a character with a sheet does not. Run this before the script, not after.

## When to use

Someone is starting a series and needs the kit every later shot is generated against: lead turnarounds, empty location plates and a title card.

## How to run it

- Ask what the show is, a line per lead (age, build, hair, wardrobe and the one detail you would recognise them by), the places the story keeps returning to (a line each), and the title; a photo of anyone they already have a face for is optional. Pass leads and places one per line: each line is one sheet or plate.
- Run this before any shots: a character described in words drifts between episodes, and a character with a sheet does not.
- For a lead, product, place or outfit that must stay identical everywhere, offer the Character ID (/character-id), Object ID (/object-id), Location ID (/location-id) or Outfit ID (/outfit-id) skill — each sheet is saved once and reused as an ID.
- Never build a real actor’s likeness from a name. The plates carry no people, text or signage, and the title card carries only the title.
- Next, the A teaser for your series and The next shot, matching the last templates take these sheets and plates as references.

## Inputs

- `show` (text) — what the show is — the world, the tone, and who it is about
- `leads` (text) — your leads, a line each: age, build, hair, wardrobe, and the one detail you would recognise them by
- `places` (text) — the places the story keeps coming back to, one per line, up to three
- `title` (text) — the title of the show
- `reference` (image, optional) — a photo of anyone you already have a face for

## Steps

1. A turnaround sheet per lead ×2
2. An empty plate per location ×3
3. Title card

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "series-bible"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/series-bible` in Superagent, or open it from https://imagera.ai/skills.
