---
name: imagera-ad-variations
description: "Someone wants several genuinely different executions of one ad concept to test against each other. Use when: \"Give me four ad variations I can A/B test\", \"I need different versions of my sneaker ad to test\", \"Make test creative for my coffee brand's Instagram campaign\", \"variations\", \"a/b test\", \"ab test\", \"options\". Runs the Imagera \"Ad variations to test\" template (four images, under a minute)."
---

# Ad variations to test

Takes one concept and produces genuinely different executions — not the same image four times. Different angles, settings and moods, so an A/B test actually tests something.

## When to use

Someone wants several genuinely different executions of one ad concept to test against each other.

## How to run it

- Ask what the ad is for and who it is aimed at; a product or brand image is optional and keeps the product recognisable.
- The executions differ on purpose — a close product hero, the product in use, a graphic flat-lay from above and a moody night scene — so a test compares setting, angle and mood rather than small details.
- Never put claims, prices or copy into the images unless the user gave the exact words; for lettering that must read right, offer the Poster skill (/poster-with-real-text).
- For a moving ad, offer the Product ad video skill (/product-ad-video); for posts that should look alike rather than differ, offer A week of posts (/social-set).

## Inputs

- `concept` (text) — what the ad is for and who it is aimed at
- `photo` (image, optional) — a product or brand image, if you have one

## Steps

1. Product hero
2. Three more executions ×3

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "ad-variations"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/ad-variations` in Superagent, or open it from https://imagera.ai/skills.
