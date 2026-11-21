---
name: imagera-ai-director
description: "Someone has a story and wants a character and shot sheet plus a film shot from it: 8 seconds, 3 cuts. Use when: \"AI director: turn my short story into a film\", \"Make a character sheet and film from my story\", \"Give me a shot sheet and a finished film for my samurai story\", \"ai director\", \"director sheet\", \"character sheet and film\", \"story to film\". Runs the Imagera \"AI Director\" template (one 4K character sheet and one 8-second film with 3 cuts)."
---

# AI Director

Writes a character and shot sheet from your story, renders it, then shoots a multi-shot film from that sheet. Download both together.

## When to use

Someone has a story and wants a character and shot sheet plus a film shot from it: 8 seconds, 3 cuts.

## How to run it

- Ask for the story or idea; a photo of the lead is optional (without one the sheet draws them from words), and the look defaults to cinematic live action.
- The sheet comes first and the film is shot from what the sheet shows, so check the sheet’s face, wardrobe and shot strip before relying on the film; both are delivered and download together as one ZIP.
- If the lead must stay identical across several films, offer the Character ID skill (/character-id) first and give its sheet as the lead photo; for a recurring place, the Location ID skill (/location-id).
- The film has no dialogue or narration. Never build a real person’s likeness from a name, and never write a real name in as the lead.
- For a single scene broken into separate frames and clips, offer the Storyboard to shots skill (/storyboard-to-shots) instead.

## Inputs

- `story` (text) — the story or idea for your film
- `character` (image, optional) — a photo of your lead character
- `look` (text, optional) — the look you want

## Steps

1. Write the sheet
2. Character sheet
3. Write the film
4. Final film

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "ai-director"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/ai-director` in Superagent, or open it from https://imagera.ai/skills.
