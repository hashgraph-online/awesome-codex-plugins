---
name: imagera-virtual-try-on
description: "Someone wants to see a specific person wearing a specific garment, as a photo. Use when: \"Show me wearing this jacket\", \"Put this dress on my model photo\", \"Virtual try-on of this shirt on this person\", \"try on\", \"try-on\", \"virtual try on\", \"wear this\". Runs the Imagera \"Virtual try-on\" template (one try-on photo, under a minute)."
---

# Virtual try-on

Dresses the person in your photo in the garment from your product photo: their face, hair, body and pose stay as they are, and the garment keeps its colour, pattern and details. A picture of the look, not a fit or size prediction.

## When to use

Someone wants to see a specific person wearing a specific garment, as a photo.

## How to run it

- Ask for a full-body photo of the person and a clear photo of the garment; where the photo is set is optional.
- Say plainly that this shows the look, not how it fits: never claim a size, fit or measurement.
- Only dress a person the user has the right to use: their own photo or a model they work with. Never put a real, named person in clothing they did not choose for a public post, and never make revealing or intimate imagery.
- For a moving version, offer the Mirror try-on video skill (/try-on-video). To keep the same model across a whole catalogue, offer the Character ID skill (/character-id) first.
- Before handing it over, check the face matches the person photo and the garment matches the product photo.

## Inputs

- `person` (image) — a full-body photo of the person
- `garment` (image) — a photo of the garment
- `setting` (text, optional) — where the photo is taken

## Steps

1. Try-on photo

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "virtual-try-on"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/virtual-try-on` in Superagent, or open it from https://imagera.ai/skills.
