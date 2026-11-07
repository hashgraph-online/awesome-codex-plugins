---
name: imagera-brand-studio
description: "Someone wants several finished static ads (image + headline + call to action) for a product, to test on Meta, TikTok or Google. Use when: \"Make ads for my candle brand from this photo\", \"I need 6 static ads to test for this sneaker\", \"Brand ads for my coffee bag\", \"ad batch\", \"ads studio\", \"static ads\", \"brand ads\". Runs the Imagera \"Marketing Brand Studio\" template (6 ad images, about a minute)."
---

# Marketing Brand Studio

6 finished static ads — picture, headline and call to action — each testing a different angle, with your product kept exact from its photo.

## When to use

Someone wants several finished static ads (image + headline + call to action) for a product, to test on Meta, TikTok or Google.

## How to run it

- Ask for one clear product photo and the brand in a sentence or two (name, what it sells, colours, tone). Never invent prices, reviews or statistics for them.
- This run makes 6 ads in Portrait 4:5, each a different angle. For more, other formats, or a brand kit read from their website, send them to /app/brand-studio.
- Before handing over, check each ad keeps the product exactly and that the headline is spelled as planned.

## Inputs

- `photo` (image) — a clear photo of the product
- `brand` (text) — the brand: its name, what it sells, its colours and how it sounds
- `direction` (text, optional) — any direction for these ads

## Steps

1. Ad plan
2. Ads ×6

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "brand-studio"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/brand-studio` in Superagent, or open it from https://imagera.ai/skills.
