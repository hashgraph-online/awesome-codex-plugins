---
name: imagera-clay-explainer
description: "Someone wants a playful clay-animation clip in which their product, as a clay character, shows one idea. Use when: \"Make a claymation ad for my vitamin bottle\", \"Stop-motion clay video explaining my app\", \"Clay animation of my coffee bag waking someone up\", \"claymation\", \"clay animation\", \"stop motion\", \"clay ad\". Runs the Imagera \"Claymation explainer\" template (a clay scene and one short clip with sound, a few minutes)."
---

# Claymation explainer

Your product rebuilt as a handmade clay-animation character in a small clay world, showing the idea you describe in one short scene, with gentle stop-motion sounds. Stylised on purpose, which is why these ads keep running.

## When to use

Someone wants a playful clay-animation clip in which their product, as a clay character, shows one idea.

## How to run it

- Ask for a product photo and the one idea the clip shows (what the product does, or the problem it solves).
- One scene, one action: offer a second run for a second idea rather than cramming two in.
- Never show medical, health or before/after results; keep the idea about what the product is or does.
- Before handing it over, check the clay product is still recognisably theirs: shape and colours.

## Inputs

- `product` (image) — a photo of your product
- `idea` (text) — the one idea the clip shows

## Steps

1. Clay scene
2. Clay clip

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "clay-explainer"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/clay-explainer` in Superagent, or open it from https://imagera.ai/skills.
