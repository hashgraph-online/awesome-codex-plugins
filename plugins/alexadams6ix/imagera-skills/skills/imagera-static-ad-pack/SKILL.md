---
name: imagera-static-ad-pack
description: "Someone wants several still feed ads for one product, with their headline or offer set as real text. Use when: \"Make 4 Facebook ads for my candle with the text 20% OFF THIS WEEK\", \"Static ad creatives for my sneaker\", \"Feed ads for my product with the headline Built to last\", \"static ad\", \"static ads\", \"feed ads\", \"ad creatives\". Runs the Imagera \"Static ad pack\" template (four feed ads, about a minute)."
---

# Static ad pack

Four 3:4 feed ads built around your product photo, each a different layout: a clean hero, a lifestyle scene, a bold colour block and a close-up. The product stays as photographed, and the only words are the ones you give, spelled as you wrote them.

## When to use

Someone wants several still feed ads for one product, with their headline or offer set as real text.

## How to run it

- Ask for a product photo and the exact words; the brand look is optional.
- Set only the words given: never invent prices, discounts, ratings, dates or claims. Keep the headline short and suggest moving long details elsewhere.
- Check every ad letter by letter against their text and re-run any with a spelling slip; check the product label is unchanged.
- For a moving version, offer the Product ad video skill (/product-ad-video); to test hooks and languages, the Ad variations skill (/ad-variations).

## Inputs

- `product` (image) — a photo of your product
- `words` (text) — the exact words on the ads — a headline or an offer
- `look` (text, optional) — the brand look — colours, mood

## Steps

1. Ads ×4

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "static-ad-pack"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/static-ad-pack` in Superagent, or open it from https://imagera.ai/skills.
