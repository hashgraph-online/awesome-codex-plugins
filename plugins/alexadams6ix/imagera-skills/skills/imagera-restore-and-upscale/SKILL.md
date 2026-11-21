---
name: imagera-restore-and-upscale
description: "Someone has an old, small, blurry or damaged photo and wants it repaired and enlarged. Use when: \"Restore this old photo of my grandparents\", \"This picture is blurry and low resolution, can you fix it?\", \"Enhance this grainy scan from the 1970s\", \"restore\", \"old photo\", \"blurry\", \"low resolution\". Runs the Imagera \"Rescue an old or low-quality photo\" template (two passes, under a minute)."
---

# Rescue an old or low-quality photo

Repairs then enlarges, in that order. Upscaling first would enlarge the damage along with everything else.

## When to use

Someone has an old, small, blurry or damaged photo and wants it repaired and enlarged.

## How to run it

- Ask for the photo, however bad it is, and anything specific to fix — scratches, a tear, fading, blur; without that it treats general wear.
- Repair runs before the enlargement on purpose: enlarging first would enlarge the damage too.
- A restoration must not flatter: never change faces, ages, expressions or clothing, and never add detail that was not there. Compare faces with the original before handing it over.
- To change something in the picture rather than repair it, offer the Change one thing template.

## Inputs

- `photo` (image) — the photo, however bad it is
- `damage` (text, optional) — anything specific you want fixed

## Steps

1. Repair
2. Enlarge

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "restore-and-upscale"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/restore-and-upscale` in Superagent, or open it from https://imagera.ai/skills.
