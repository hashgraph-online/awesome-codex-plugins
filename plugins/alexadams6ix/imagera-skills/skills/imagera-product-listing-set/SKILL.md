---
name: imagera-product-listing-set
description: "Someone has a photo of a product and needs marketplace-ready listing images: a clean hero on white plus lifestyle shots. Use when: \"My Shopify listing photos look amateur, can you fix them?\", \"Make a clean product shot on a white background from this phone photo\", \"I need Amazon listing images for my water bottle\", \"product photo\", \"listing\", \"ecommerce\", \"e-commerce\". Runs the Imagera \"Product listing photos\" template (about five images, a couple of minutes)."
---

# Product listing photos

Turns a single phone photo into a clean catalogue hero on white, plus lifestyle shots that show it in use. The hero is what a marketplace wants; the lifestyle shots are what makes someone want it.

## When to use

Someone has a photo of a product and needs marketplace-ready listing images: a clean hero on white plus lifestyle shots.

## How to run it

- Ask for one in-focus photo of the product and what it is in a few words; where the lifestyle shots are set is optional and defaults to wherever it would naturally be used.
- The hero keeps the product exactly as photographed on pure white and is the image upscaled for zoom and print; the lifestyle shots are a wide view, the product in use and a close view in hand.
- If the same product must look identical across many later images or videos, offer the Object ID skill (/object-id) first — a sheet held across shots beats a single photo.
- Never invent labels, claims, certifications or packaging text the photo does not show. Check the hero for changed colours, markings or proportions before handing it over.
- For a video ad of the same product, offer the Product ad video skill (/product-ad-video) next.

## Inputs

- `photo` (image) — a photo of your product — a phone shot is fine, just keep it in focus
- `what` (text) — what the product is, in a few words
- `setting` (text, optional) — where you want the lifestyle shots set

## Steps

1. Clean hero on white
2. Lifestyle shots ×3
3. Upscale for print and zoom

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "product-listing-set"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/product-listing-set` in Superagent, or open it from https://imagera.ai/skills.
