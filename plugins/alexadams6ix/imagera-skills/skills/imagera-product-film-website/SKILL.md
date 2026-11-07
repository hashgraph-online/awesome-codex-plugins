---
name: imagera-product-film-website
description: "a product page where one physical product, from the user's own photo, turns on a studio set as the visitor scrolls Use when: \"a product page where my perfume bottle rotates as you scroll\", \"make a product launch page for our new energy drink can\", \"turntable website for my sneaker\", \"product website\", \"product page\", \"product launch page\", \"turntable website\". Runs the Imagera \"Product Film Website\" template (one 2K product frame, one 8 s 720p film, and a finished page; by tier: Lite 3 pictures and 1 cut-out, Standard 5 pictures and 2 cut-outs, Premium 8 pictures and 3 cut-outs)."
---

# Product Film Website

Places your exact product on a studio set, films a slow orbit around it that turns with the visitor's scroll, adds detail pictures and builds a ready-to-publish product page.

## When to use

a product page where one physical product, from the user's own photo, turns on a studio set as the visitor scrolls

## How to run it

- Ask what the site is for, who it is for, and the ONE action a visitor should take (and its link, if they have one). Ask for a product or portrait photo when the subject is a real product or person.
- This skill needs a clear photo of the product itself; without one, offer the Cinematic Website, which can film the product from a description.
- Never invent facts, prices, numbers, testimonials, awards or links: the page states only what the user gave, and every claim is checked against their brief before the page is built.
- A website is built as ONE job — copy, film, pictures and page together — with its price shown before it starts. Do not generate its steps one by one here: once you have what it needs, tell the user to run it from /templates → Websites (or the website studio), with their brief ready to paste.
- When it is done: the Website preview plays the film as you scroll; Download ZIP exports the whole site to host anywhere; Refine takes plain-language changes to the text.

## Inputs

- `brief` (text) — the product, what it is for and who it is for
- `photo` (image) — a clear photo of the product
- `tier` (one of: Lite, Standard, Premium, optional) — Lite — a focused page: fewer sections, pictures and one floating cut-out; Standard — a full page: more sections and pictures, two floating cut-outs; Premium — a long, rich page: three scroll films, the subject as a real 3D model, a signature effect of its own and the most sections
- `look` (text, optional) — the look you want
- `changes` (text, optional) — any specific changes to apply to the finished page
- `title` (one of: No — set the type on the page, Yes — sculpt one word in the scene, optional) — whether to sculpt the brand's word into the film

## Steps

1. Write the page
2. Product frame
3. Product film ×3
4. Detail images ×5

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "product-film-website"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/product-film-website` in Superagent, or open it from https://imagera.ai/skills.
