---
name: imagera-explainer-with-voice
description: "Someone needs to explain something without being on camera: their script read aloud in a natural voice, with a picture for each beat. Use when: \"Make an explainer with a voiceover from my script\", \"I need a tutorial narrated over pictures, I don't want to be on camera\", \"Turn my presentation notes into narration with visuals\", \"explainer\", \"voiceover\", \"narration\", \"tutorial\". Runs the Imagera \"Explainer with a voiceover\" template (a voiceover and three visuals)."
---

# Explainer with a voiceover

Writes nothing you did not say — it takes your script, reads it in a natural voice, and renders a visual for each beat so there is something to watch.

## When to use

Someone needs to explain something without being on camera: their script read aloud in a natural voice, with a picture for each beat.

## How to run it

- Ask for the script in their own words and the kind of voice: warm and conversational, crisp and professional, or calm and slow.
- The voice reads the script exactly as written, so never add, rewrite or pad it; offer edits only as suggestions. Spell out numbers, dates and abbreviations the way they should be said.
- The visuals illustrate the opening, middle and close of the script in one consistent style, with no words in them; for a slide that must carry exact text, offer the Poster skill (/poster-with-real-text).
- For music under the finished piece, offer the Music for something you already made template.

## Inputs

- `script` (text) — what you want said — your own words are best
- `voice` (one of: warm and conversational, crisp and professional, calm and slow) — the kind of voice you want

## Steps

1. Voiceover
2. A visual per beat ×3

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "explainer-with-voice"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/explainer-with-voice` in Superagent, or open it from https://imagera.ai/skills.
