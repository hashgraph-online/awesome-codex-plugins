---
name: imagera-location-id
description: "Someone needs the same location to look identical across many images or videos — a reusable Location ID sheet, no training. Use when: \"Make a location sheet from these photos\", \"I need a consistent location for my series\", \"Location reference sheet, 4K\", \"location id\", \"location reference sheet\". Runs the Imagera \"Location ID\" template (one reference sheet and a 4K upscale, about a minute)."
---

# Location ID

One 4K reference sheet of the location — a place that keeps its layout, light and mood across shots. Reuse it as an input to any model; nothing is trained.

## When to use

Someone needs the same location to look identical across many images or videos — a reusable Location ID sheet, no training.

## How to run it

- Ask for one clear reference picture of the location, or a description when there is none: The place, its layout, materials, time of day and where the light comes from. To build from up to 6 pictures, create the ID on /character-id instead.
- The sheet is ONE collage — angles and details at one light and scale. It runs on the sharpest 4K image model on Pro and up; below that plan, or if that model declines, Typeset 3 makes it instead, and the Upscale step finishes it at 4K.
- To reuse it with @handle in Sandbox and the upload picker, save it as an ID on /character-id ("Use an existing sheet"), or create the ID there directly.
- Afterwards, pass the sheet as the first reference image to any edit, reference or image-to-video model (video: Imagera Warlord Pro Reference) and name it in the prompt as "reference image 1".
- Never invent a real person’s likeness from a name, and never make intimate imagery of a real person.

## Inputs

- `references` (image, optional) — a reference picture of the location
- `describe` (text, optional) — a description of the location
- `look` (text, optional) — the look you want

## Steps

1. Location Sheet
2. Upscale 4K

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "location-id"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/location-id` in Superagent, or open it from https://imagera.ai/skills.
