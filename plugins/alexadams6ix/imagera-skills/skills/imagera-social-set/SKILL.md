---
name: imagera-social-set
description: "Someone needs a batch of social posts that share one palette, light and framing, so a profile grid reads as one set. Use when: \"Make a week of posts for my bakery in one look\", \"I need matching posts for my Instagram grid\", \"Plan a content calendar of images for my yoga studio\", \"content calendar\", \"week of posts\", \"batch\", \"series\". Runs the Imagera \"A week of posts, one look\" template (one image per topic, up to five, about a minute)."
---

# A week of posts, one look

Generates up to five posts, one per topic, that share palette, lighting and framing, so a profile grid reads as deliberate rather than as a pile of unrelated images. A shorter list makes, and buys, fewer posts.

## When to use

Someone needs a batch of social posts that share one palette, light and framing, so a profile grid reads as one set.

## How to run it

- Ask for the post topics, one per line, up to five with one image each, and the look they share in a sentence. Pass the topics one per line: each line is one post.
- Consistency beats any single image: palette, light direction and framing stay fixed and only the subject changes, so push back on a look that asks for a different style per post.
- Never put claims, prices or handles into the images unless the user gave the exact words; lettering that must read right belongs to the Poster skill (/poster-with-real-text).
- If they want several different looks to test rather than one, offer Ad variations (/ad-variations).

## Inputs

- `topics` (text) — the posts you need, one topic per line, up to five
- `look` (text) — the look they should share

## Steps

1. A matched set ×5

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "social-set"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/social-set` in Superagent, or open it from https://imagera.ai/skills.
