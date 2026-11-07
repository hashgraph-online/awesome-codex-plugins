---
name: imagera-headshot-set
description: "Someone wants professional headshots from one ordinary photo of themselves. Use when: \"Make me a LinkedIn headshot from this selfie\", \"Professional headshots from my photo\", \"I need a profile picture for work\", \"headshot\", \"headshots\", \"linkedin photo\", \"professional photo\". Runs the Imagera \"Headshots from a selfie\" template (four headshots, about a minute)."
---

# Headshots from a selfie

Four professional headshots from one clear photo: studio grey, an office window, outdoors in soft light and a dark editorial portrait. Same face every time, better light, a clean jacket or top.

## When to use

Someone wants professional headshots from one ordinary photo of themselves.

## How to run it

- Ask for one clear, front-facing photo of their own face; the wardrobe is optional.
- Only make headshots of the person asking, or someone who agreed: never of a public figure or a stranger.
- Keep the face exactly: no slimming, smoothing or changing age or features. If a result drifts from the face, re-run that one.
- For the same person in many future images, offer the Character ID skill (/character-id).

## Inputs

- `photo` (image) — a clear, front-facing photo of your face
- `wear` (text, optional) — what you wear in them

## Steps

1. Headshots ×4

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "headshot-set"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/headshot-set` in Superagent, or open it from https://imagera.ai/skills.
