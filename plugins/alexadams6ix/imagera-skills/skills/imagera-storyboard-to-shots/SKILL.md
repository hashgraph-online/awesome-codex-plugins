---
name: imagera-storyboard-to-shots
description: "Someone has a scene idea and wants to see it as four framed shots, then as clips joined into one cut. Use when: \"Storyboard a scene where a detective finds a letter in the rain\", \"I need previz for a short film opening\", \"Turn my scene idea into a shot list with clips\", \"storyboard\", \"scene\", \"short film\", \"previz\". Runs the Imagera \"Storyboard to shots\" template (a shot list, four frames, four eight-second clips and one joined cut)."
---

# Storyboard to shots

Breaks an idea into four shots, renders each as a frame, animates each frame and joins the clips into one cut. The frames come first deliberately — it is far cheaper to reject a composition as a still than as a clip.

## When to use

Someone has a scene idea and wants to see it as four framed shots, then as clips joined into one cut.

## How to run it

- Ask who is in the scene, where it is and what happens; the look is optional, and a character photo is optional but keeps the person consistent.
- The shot list plans a wide establishing shot, a medium shot, a close shot and an insert detail; every frame after the first is an edit of it, so palette and light hold, and each becomes an eight-second clip.
- If a person or place must hold across this and later scenes, offer the Character ID skill (/character-id) or the Location ID skill (/location-id) first and use the sheet as the character photo.
- Keep one action per shot and no on-screen text. Check the frames before relying on the clips: a composition is far cheaper to reject as a still than as a clip.
- For a whole story with a character and shot sheet, offer the AI Director skill (/ai-director) instead.

## Inputs

- `scene` (text) — the scene you have in mind — who, where, what happens
- `look` (text, optional) — the look you want
- `reference` (image, optional) — a photo of the character, if you have one

## Steps

1. Storyboard frames ×4
2. Animate the chosen frames ×4

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "storyboard-to-shots"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/storyboard-to-shots` in Superagent, or open it from https://imagera.ai/skills.
