---
name: imagera-cinematic-website
description: "a website or landing page for one brand, product, person or project, where one continuous film can carry the opening Use when: \"build me a landing page for my coffee brand\", \"I need a website for my architecture studio\", \"make an animated website for my yacht shipyard\", \"landing page\", \"website builder\", \"build a website\", \"website for\". Runs the Imagera \"Cinematic Website\" template (one 2K frame, one 8 s 720p film, and a finished page; by tier: Lite 3 pictures and 1 cut-out, Standard 5 pictures and 2 cut-outs, Premium 8 pictures and 3 cut-outs)."
---

# Cinematic Website

Writes the page copy and picks its type, renders the opening frame, films one continuous shot that plays as the visitor scrolls, adds section pictures and builds a ready-to-publish page.

## When to use

a website or landing page for one brand, product, person or project, where one continuous film can carry the opening

## How to run it

- Ask what the site is for, who it is for, and the ONE action a visitor should take (and its link, if they have one). Ask for a product or portrait photo when the subject is a real product or person.
- If the story travels between distinct places or stages (a voyage, a tour, a making-of), offer the Journey Website instead; for one physical product with a photo, offer the Product Film Website.
- Never invent facts, prices, numbers, testimonials, awards or links: the page states only what the user gave, and every claim is checked against their brief before the page is built.
- A website is built as ONE job — copy, film, pictures and page together — with its price shown before it starts. Do not generate its steps one by one here: once you have what it needs, tell the user to run it from /templates → Websites (or the website studio), with their brief ready to paste.
- When it is done: the Website preview plays the film as you scroll; Download ZIP exports the whole site to host anywhere; Refine takes plain-language changes to the text.

## Inputs

- `brief` (text) — what the website is for — product, brand or project, and who it is for
- `photo` (image, optional) — a product or portrait photo to feature
- `tier` (one of: Lite, Standard, Premium, optional) — Lite — a focused page: fewer sections, pictures and one floating cut-out; Standard — a full page: more sections and pictures, two floating cut-outs; Premium — a long, rich page: three scroll films, the subject as a real 3D model, a signature effect of its own and the most sections
- `look` (text, optional) — the look you want
- `changes` (text, optional) — any specific changes to apply to the finished page
- `title` (one of: No — set the type on the page, Yes — sculpt one word in the scene, optional) — whether to sculpt the brand's word into the film

## Steps

1. Write the page
2. Film frame
3. Film ×3
4. Section images ×5

## Run it through Imagera

Connect the Imagera MCP server (https://mcp.imagera.ai/mcp, sign in with your Imagera account), then:

1. `run_skill` with `skill_id: "cinematic-website"` and the inputs above, `confirm: false` — this returns the price in credits and starts nothing.
2. Show the price. Only after the person agrees, call `run_skill` again with `confirm: true`.
3. Poll `check_skill_run` with the returned `run_id` until it finishes; hand over the result URLs.
4. Pictures of a saved Character, Object, Location or Outfit ID: `list_identities` returns each ID's sheet URL to pass as a reference image.

In Imagera itself, type `/cinematic-website` in Superagent, or open it from https://imagera.ai/skills.
