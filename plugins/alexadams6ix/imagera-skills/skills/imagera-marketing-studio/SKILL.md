---
name: imagera-marketing-studio
description: "Someone wants one polished marketing image of their own product in a known style (studio, lifestyle, ad, poster, marketplace listing). Use when: \"Studio white shot of this bottle\", \"Make a marketplace image of my bag\", \"A bold poster for these headphones\", \"marketing studio\", \"product shot\", \"marketplace image\", \"product poster\". Runs the Imagera \"Marketing Studio\" template (one image, under a minute)."
---

# Marketing Studio

One marketing visual of your product in a chosen style (22 styles: product shots, ads, posters, marketplace), the product kept exact from its photo.

## When to use

Someone wants one polished marketing image of their own product in a known style (studio, lifestyle, ad, poster, marketplace listing).

## How to run it

- Ask for a clear product photo and which style; offer the style names from the template.
- For creator videos or product motion, send them to /app/marketing-studio (video templates run Warlord Pro from a first frame).
- Check the product is unchanged and any printed words are spelled as given.

## Inputs

- `photo` (image) — a clear photo of the product
- `style` (one of: Studio white, Color pop, Water splash, Stone plinth, In hand, Lifestyle table, Bold claim, Problem → solution, Feature callouts, Native post, Offer, Editorial, Bold type, Retro print, Gallery, Launch banner, Cut-paper collage, Clean white, Three angles, In use, Dark premium, Pastel set) — which style
- `product` (text, optional) — what the product is called
- `words` (text, optional) — any headline or call to action to print

## Steps

1. Shot
2. Visual

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "marketing-studio"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/marketing-studio` in Superagent, or open it from https://imagera.ai/skills.
