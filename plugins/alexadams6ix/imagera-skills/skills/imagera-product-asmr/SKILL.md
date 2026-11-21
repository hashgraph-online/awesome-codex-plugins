---
name: imagera-product-asmr
description: "Someone wants a slow, satisfying ASMR-style close-up of their product with crisp sound. Use when: \"Make an ASMR video of my lipstick\", \"Satisfying close-up clip of my drink can with sound\", \"ASMR ad for my skincare jar\", \"asmr\", \"satisfying video\", \"asmr ad\", \"product asmr\". Runs the Imagera \"Product ASMR clip\" template (a macro still and one short clip with sound, a few minutes)."
---

# Product ASMR clip

A slow macro clip of your product with crisp, close sounds: a cap clicking, liquid pouring, a surface tapped or poured over. Built from your product photo; the sound comes with the clip, no music.

## When to use

Someone wants a slow, satisfying ASMR-style close-up of their product with crisp sound.

## How to run it

- Ask for a product photo; what happens in the clip (and so what it sounds like) is optional.
- Keep to one simple action per clip: pour, drip, click, tap, slide. Several actions in one short clip look rushed.
- The sound comes from the video model with the picture; there is no separate sound step, so say so if they ask for a specific track.
- Before handing it over, check the product stays unchanged through the clip.

## Inputs

- `product` (image) — a photo of your product
- `action` (text, optional) — what happens in the clip

## Steps

1. Macro still
2. ASMR clip

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "product-asmr"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/product-asmr` in Superagent, or open it from https://imagera.ai/skills.
