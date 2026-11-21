---
name: imagera-character-id
description: "Someone needs the same character to look identical across many images or videos — a reusable Character ID sheet, no training. Use when: \"Make a character sheet from these photos\", \"I need a consistent character for my series\", \"Character reference sheet, 4K\", \"character id\", \"character reference sheet\", \"soul id\", \"my digital twin\". Runs the Imagera \"Character ID\" template (one reference sheet and a 4K upscale, about a minute)."
---

# Character ID

One 4K reference sheet of the character — one face and body, held in every image and video. Reuse it as an input to any model; nothing is trained.

## When to use

Someone needs the same character to look identical across many images or videos — a reusable Character ID sheet, no training.

## How to run it

- Ask for one clear reference picture of the character, or a description when there is none: Age, build, hair, skin tone, wardrobe and the one detail you would recognise them by. To build from up to 6 pictures, create the ID on /character-id instead.
- The sheet is ONE collage — angles and details at one light and scale. It runs on the sharpest 4K image model on Pro and up; below that plan, or if that model declines, Typeset 3 makes it instead, and the Upscale step finishes it at 4K.
- To reuse it with @handle in Sandbox and the upload picker, save it as an ID on /character-id ("Use an existing sheet"), or create the ID there directly.
- Afterwards, pass the sheet as the first reference image to any edit, reference or image-to-video model (video: Imagera Warlord Pro Reference) and name it in the prompt as "reference image 1".
- Never invent a real person’s likeness from a name, and never make intimate imagery of a real person.

## Inputs

- `references` (image, optional) — a reference picture of the character
- `describe` (text, optional) — a description of the character
- `look` (text, optional) — the look you want

## Steps

1. Character Sheet
2. Upscale 4K

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "character-id"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/character-id` in Superagent, or open it from https://imagera.ai/skills.
