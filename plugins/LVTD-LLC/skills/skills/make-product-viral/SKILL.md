---
name: make-product-viral
description: Make a product, landing page, pricing page, launch page, free tool, or social preview easier to understand, buy, remember, and share using Marc Lou-inspired viral product patterns.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Make Product Viral
  category: Marketing
  tags: marketing,launch,cro,pricing,copywriting,shareability
---

# Make Product Viral

Use this skill to improve a product surface so people can understand it quickly,
trust it before paying, remember it after leaving, and share it without needing
to decode the whole page first.

## Attribution

This skill is inspired by Marc Lou's "32 Principles of a Viral Product" post on
X: https://x.com/marclou/status/2065385672991752210

Use the source as a set of strong defaults from startup building experience, not
as universal rules. See `references/source-and-caveats.md` for attribution,
ethical guardrails, and adaptation notes.

## Core Lens

A viral product is not just a product with social sharing. It has a simple
promise, visible product proof, low cognitive load, a clear buying path, and a
memorable reason to talk about it.

Optimize in this order:

1. Can people understand it in seconds?
2. Can they see or try the product before reading a long explanation?
3. Is the desired outcome concrete, emotional, and memorable?
4. Is there one obvious next action?
5. Is trust visible before the user is asked to pay?
6. Is the page easy to share, including its final impression and social preview?

## Resource Routing

Load only the files needed for the task:

| Need | Read |
| --- | --- |
| Full audit sequence for a product, landing page, pricing page, launch page, free tool, app-store surface, or OG image | `workflows/audit-product-surface.md` |
| Attribution, caveats, and ethical guardrails | `references/source-and-caveats.md` |

## Fast Workflow

1. Write the product in one clear sentence before making lower-level changes.
2. Check whether the first viewport can sell alone: what it is, who it is for,
   the result, why to believe it, and what happens on click.
3. Move visible product proof before long explanatory copy.
4. Remove mixed-message sections so each screen or section carries one idea.
5. Make the primary CTA specific to the next action.
6. Check trust, pricing clarity, and paywall fit before recommending launch
   traffic.
7. Review the social preview and final impression as shareable artifacts.

## Output Format

When using this skill, respond with:

1. **Viral diagnosis:** the main reason this is or is not likely to spread.
2. **Highest-leverage fixes:** 3 to 7 changes, ordered by impact.
3. **Hero rewrite:** headline, subhead, CTA, and proof or demo suggestion.
4. **Shareability pass:** OG image, footer or final impression, and one-line
   description.
5. **Pricing or paywall note:** only if relevant.
6. **Validation plan:** what to check before launch.

Keep recommendations concrete. Prefer replacement copy, section order, product
proof, pricing structure, and specific UI/content changes over abstract advice.
