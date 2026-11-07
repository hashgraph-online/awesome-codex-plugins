---
name: imagera-carousel-post
description: "Someone wants an Instagram or LinkedIn carousel whose slide text is spelled exactly right. Use when: \"Make an Instagram carousel about 3 tips for better sleep\", \"LinkedIn carousel slides for my launch\", \"A 4-slide carousel with my headline and points\", \"carousel\", \"carousel post\", \"slides post\", \"instagram carousel\". Runs the Imagera \"Carousel post\" template (four slides, about a minute)."
---

# Carousel post

Four 3:4 carousel slides in one look: a cover, two point slides and a closing slide, each setting only the words you give, spelled as you wrote them.

## When to use

Someone wants an Instagram or LinkedIn carousel whose slide text is spelled exactly right.

## How to run it

- Ask for the cover headline, two short points and a closing line; the look is optional. Help them shorten long lines before running.
- Set only the words they give: never invent statistics, quotes, names or claims.
- Check every slide letter by letter and re-run any slide with a slip.
- For a single poster, offer the Poster skill (/poster-with-real-text); for a week of image posts, the Social set skill (/social-set).

## Inputs

- `cover` (text) — the cover headline
- `point1` (text) — the first point, one short line
- `point2` (text) — the second point, one short line
- `close` (text) — the closing line or call to action
- `look` (text, optional) — the look — colours, type, mood

## Steps

1. Cover slide
2. Point slide 1
3. Point slide 2
4. Closing slide

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "carousel-post"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/carousel-post` in Superagent, or open it from https://imagera.ai/skills.
