---
name: imagera-title-art
description: "Someone needs a title set in lettering that reads right, as a 16:9 thumbnail and a 2:3 poster. Use when: \"Make a YouTube thumbnail with my title spelled right\", \"I need a thumbnail and poster for my short film\", \"Design key art and a movie poster for NIGHT SHIFT\", \"thumbnail and poster\", \"youtube thumbnail\", \"video thumbnail\", \"thumbnail\". Runs the Imagera \"Thumbnail and poster\" template (two lettered images and two upscales, about a minute)."
---

# Thumbnail and poster

Sets your title two ways — a 16:9 thumbnail and a 2:3 poster — with a model built for lettering, then sharpens each for print. Type the words exactly as they should read.

## When to use

Someone needs a title set in lettering that reads right, as a 16:9 thumbnail and a 2:3 poster.

## How to run it

- Ask for the words exactly as they should read — one line is the title, a second line is a smaller subtitle — and the look: a style, a mood, a colour.
- Set only the words given: never correct, translate, or add a tagline, credits or a date the user did not type. Short titles set most reliably, so suggest trimming a long one.
- Each format is sharpened by an upscale that keeps letterforms crisp. Check the spelling on every format against the user’s text before handing them over, and re-run the one that came out wrong.
- For a poster built around an occasion rather than a title, offer the Poster skill (/poster-with-real-text).

## Inputs

- `title` (text) — the words, spelled exactly: the title, and a second line under it if you want one
- `look` (text) — the look you want — a style, a mood, a colour

## Steps

1. Thumbnail and poster ×2
2. Upscale

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "title-art"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/title-art` in Superagent, or open it from https://imagera.ai/skills.
