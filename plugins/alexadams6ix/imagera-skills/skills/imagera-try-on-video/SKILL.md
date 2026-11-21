---
name: imagera-try-on-video
description: "Someone wants a vertical mirror try-on video of a model wearing their garment, for a product page or a reel. Use when: \"Make a mirror try-on video of this dress\", \"Fitting room video for my new hoodie\", \"A model trying on this jacket in a mirror, for TikTok\", \"try on video\", \"try-on video\", \"mirror video\", \"outfit video\". Runs the Imagera \"Mirror try-on video\" template (a mirror still and one short clip, a few minutes)."
---

# Mirror try-on video

A model wears your garment in a bright fitting-room mirror shot built from your product photo, then turns to show the back and the fabric moving: a vertical clip for a product page or a reel. It shows the look, not a fit prediction.

## When to use

Someone wants a vertical mirror try-on video of a model wearing their garment, for a product page or a reel.

## How to run it

- Ask for a clear photo of the garment; who wears it is optional.
- Say plainly that the clip shows the look, not the fit: never claim sizes or measurements.
- The model is invented from the description; to use the same model across many garments, offer the Character ID skill (/character-id) first, and for a still on a real person, the Virtual try-on skill (/virtual-try-on).
- Before handing it over, check the garment in the clip matches the product photo: colour, pattern, buttons, logo placement.

## Inputs

- `garment` (image) — a photo of the garment
- `model` (text, optional) — who wears it

## Steps

1. Mirror still
2. Try-on clip

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "try-on-video"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/try-on-video` in Superagent, or open it from https://imagera.ai/skills.
