---
name: imagera-poster-with-real-text
description: "Someone needs a poster, flyer, banner or sign whose words must be spelled exactly right. Use when: \"Make a poster for my bakery's grand opening with the words spelled right\", \"Design a flyer for Saturday's yoga class\", \"I need a banner that says SUMMER SALE 50% OFF\", \"poster\", \"flyer\", \"title card\", \"headline\". Runs the Imagera \"A poster whose words are spelled right\" template (a poster and a sharpening pass, under a minute)."
---

# A poster whose words are spelled right

Routes to the models built for typography rather than the ones that merely score well on pictures, then reads the result back and fixes what came out wrong. Most image models cannot spell; the two that can are unremarkable at everything else, which is why this is its own job.

## When to use

Someone needs a poster, flyer, banner or sign whose words must be spelled exactly right.

## How to run it

- Ask what the poster is for and the exact words that must appear, spelled as they want them; the look is optional.
- Keep the headline short — the shorter the string, the likelier it renders — and suggest moving long details such as addresses or schedules to a second, simpler line.
- Never invent dates, prices, venues, phone numbers or links: the poster states only the words given. Check the result letter by letter against their text before handing it over, and re-run it if anything is off.
- For a video thumbnail and a matching film poster of one title, offer the Thumbnail and poster skill (/title-art).

## Inputs

- `occasion` (text) — what the poster is for
- `words` (text) — the exact words that must appear, spelled as you want them
- `look` (text, optional) — the look you want — a style, a mood, a colour

## Steps

1. The poster
2. Sharpen for print

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "poster-with-real-text"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/poster-with-real-text` in Superagent, or open it from https://imagera.ai/skills.
