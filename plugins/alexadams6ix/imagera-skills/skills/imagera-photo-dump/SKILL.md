---
name: imagera-photo-dump
description: "Someone wants a set of casual, phone-style photos of one person (often an AI influencer) to post together. Use when: \"Make a photo dump of my AI influencer\", \"Four casual Instagram photos of this person\", \"Candid phone photos of my character for a carousel\", \"photo dump\", \"photodump\", \"casual photos\", \"instagram dump\". Runs the Imagera \"Photo dump\" template (four photos, about a minute)."
---

# Photo dump

Four casual, phone-shot photos of the person in your photo, the kind posted together as a photo dump: a café table, a golden-hour street, a mirror selfie and a beach walk. Same face and style in each, ordinary light, nothing posed.

## When to use

Someone wants a set of casual, phone-style photos of one person (often an AI influencer) to post together.

## How to run it

- Ask for one clear photo of the person; the vibe of the set is optional.
- Only for the user themself, someone who agreed, or an invented character: never a real public figure, and never revealing or intimate imagery.
- For an account that posts often, offer the Character ID skill (/character-id) first so every set keeps the same face.
- Check every photo for drift in the face before handing it over, and re-run only the one that drifted.

## Inputs

- `photo` (image) — a clear photo of the person
- `vibe` (text, optional) — the vibe of the week

## Steps

1. Photos ×4

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "photo-dump"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/photo-dump` in Superagent, or open it from https://imagera.ai/skills.
