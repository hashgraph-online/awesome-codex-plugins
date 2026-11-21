---
name: imagera-photo-to-reel
description: "Someone has a good photo and wants it moving as a vertical eight-second clip with music under it, for social. Use when: \"Turn this photo into a reel for Instagram\", \"Animate my beach photo for TikTok\", \"Photo to video for my stories, please\", \"reel\", \"tiktok\", \"animate\", \"make it move\". Runs the Imagera \"Reel from a photo\" template (a reframed still, one eight-second clip, a music bed and a dub — a few minutes)."
---

# Reel from a photo

Recomposes a photo as a vertical frame, moves it with the motion you pick — the photo stays the picture that moves — and lays an instrumental bed under it. The move is the whole point: a static image posted as video looks broken.

## When to use

Someone has a good photo and wants it moving as a vertical eight-second clip with music under it, for social.

## How to run it

- Ask for the photo and how it should move — a slow forward drift, a turn toward the camera, a slow orbit, or the scene coming alive; the music is optional and defaults to a calm instrumental bed.
- Reframe first recomposes the photo as 9:16, keeping the subject, face, colours and light; for a photo that is already vertical, the Canvas can wire it straight into Image to Video.
- One move per clip: if they describe several actions, pick the strongest and say so. The bed is instrumental, so offer the Music video skill (/music-video) when they want a sung song.
- Before handing it over, check the subject still matches the photo and the motion runs at real-world speed, not slow motion.

## Inputs

- `photo` (image) — the photo you want to animate
- `move` (one of: the subject moves naturally as the camera drifts slowly forward, the subject turns and looks toward the camera, a slow orbit around the subject, the scene comes alive: wind, water and light move) — how the picture should move
- `music` (text, optional) — the music under the clip

## Steps

1. Reframe
2. Vertical clip with the chosen move
3. Music
4. Dub

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "photo-to-reel"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/photo-to-reel` in Superagent, or open it from https://imagera.ai/skills.
