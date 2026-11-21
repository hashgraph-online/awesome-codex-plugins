---
name: imagera-character-consistency
description: "Someone needs one character to look the same across three different scenes, starting from a single clear photo. Use when: \"Keep the same character across three different scenes\", \"My character looks different in every image, fix it\", \"Put the same person from this photo in a café, a beach and an office\", \"same character\", \"consistent character\", \"same person\", \"looks different\". Runs the Imagera \"The same character in every shot\" template (a scene list and three images, a minute or two)."
---

# The same character in every shot

The hardest problem in AI imagery. Solved here by locking a reference and routing to models built for identity consistency, rather than by hoping a longer prompt fixes it.

## When to use

Someone needs one character to look the same across three different scenes, starting from a single clear photo.

## How to run it

- Ask for one clear, well-lit image of the character and up to three scenes; a scene list numbers them and each image is an edit of the photo.
- If they will need the character in many more images or videos, offer the Character ID skill (/character-id) first — a sheet held across shots beats a single photo. When the wardrobe must hold exactly, add the Outfit ID skill (/outfit-id).
- Setting, pose, action and light come from each scene, never from the photo; clothing stays the same unless a scene needs a change.
- Check every result for drift in the face, hair and build before handing it over, and re-run only the one that drifted.
- Never build a real person’s likeness from a name, and never make intimate imagery of a real person.

## Inputs

- `reference` (image) — a clear image of the character
- `scenes` (text) — the scenes you need them in

## Steps

1. The character in each scene ×3

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "character-consistency"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/character-consistency` in Superagent, or open it from https://imagera.ai/skills.
