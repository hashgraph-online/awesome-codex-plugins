---
name: imagera-unboxing-video
description: "Someone wants a first-person unboxing clip of their product, with sound, for social or a product page. Use when: \"Make an unboxing video of my perfume\", \"POV unboxing clip for my sneakers\", \"Hands unboxing my product, for TikTok\", \"unboxing\", \"unbox\", \"unboxing video\", \"pov unboxing\". Runs the Imagera \"Unboxing video\" template (an unboxing still and one short clip with sound, a few minutes)."
---

# Unboxing video

A first-person unboxing: hands open a box on a table and lift your product out of the tissue, built from your product photo, with the soft sounds of the box and paper. A vertical clip for reels and product pages.

## When to use

Someone wants a first-person unboxing clip of their product, with sound, for social or a product page.

## How to run it

- Ask for a clear product photo; where it is unboxed is optional.
- Hands using a real product can warp: keep the action simple (lift out, turn to camera) and say so if they ask for more.
- Never add reactions, ratings or claims in words; the clip has room sound only.
- Before handing it over, check the product matches the photo through the whole clip.

## Inputs

- `product` (image) — a photo of your product
- `setting` (text, optional) — where it is unboxed

## Steps

1. Unboxing still
2. Unboxing clip

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "unboxing-video"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/unboxing-video` in Superagent, or open it from https://imagera.ai/skills.
