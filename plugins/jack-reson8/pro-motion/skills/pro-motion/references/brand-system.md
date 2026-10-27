# Brand system: plan and execute one coherent brand fast

Read when the user asks for branding, a brand upgrade, a launch kit, or when a site/film/poster/store set must feel like one thing. Output, before any asset is made: `docs/brand-system.md` with the five blocks below filled. Each asset then cites the block it uses. Built from the Tutti site (2026-10-25): what made it feel coherent was not a logo but one verb repeated at every touchpoint.

## 1 · Core (one screen, no adjectives)
- **Verb**: the one action the product performs (Tutti: flash → a great shot). Every touchpoint shows the verb happening, not a description of it.
- **Material**: what the brand is "made of" (Tutti: the visitor's own photo + huge warped type + grain). No material = it will look like a template.
- **Protagonist**: who/what appears everywhere (Tutti: a real person cut out in front of the type; later the visitor).
- **Proof**: the artefact that travels (Tutti: the 6-character code on every export).
- **Line**: two-beat slogan in each market's language, from the product's own strings (Tutti: 出片，从未如此简单。/ Great shots, made easy.).

## 2 · Tokens (copyable values, one file shared by app, site, film)
States table (ground / ink / glow per state, ≤6 states); type per language (display, UI, annotation; subset per page); texture (grain amount, flash duration); motion (spring, kick, auto-advance interval); voice rules (two-beat, no slogan endings, renhua). Store as CSS variables + a JSON the app and film can read.

## 3 · Touchpoint matrix (fill every row before making assets)
| Touchpoint | Shows the verb how | Uses material | Carries the proof | Status |
|---|---|---|---|---|
| App icon · store screenshots · site hero · OG/share card · export/watermark · code page · code-only poster · 404/error · waitlist + invite card · social avatar & first 9 posts · launch film · email (confirm, invite) · physical (sticker, cup sleeve) |
A row that can't show the verb is redesigned or dropped; a row that shows no proof loses the growth loop.

## 4 · Unexpected, but easy (Jack: "耳目一新…不用什么都按传统的来，但是要让用户感到容易理解并且有趣")
- One familiar control per screen (tap, scroll, drag); the surprise is what that control *does* (a tap is a camera flash), never a new gesture to learn.
- Each touchpoint gets one deliberate break from convention (404 that "breaks" then fixes itself; a poster with only a code) and nothing else unusual.
- Check with a 15–25 user's eyes: understood in 3 s without text? fun to do twice?

## 5 · Execution order (parallel where independent)
1. Core + tokens (this file) → 2. hero touchpoint built to `web-craft.md` (it proves the system) → 3. derive the share card, code page, poster, 404 from the same engine (same tokens, same verb) → 4. store screenshots and launch film reuse the hero's states (film method in SKILL.md) → 5. social kit (post skill) and copy (renhua) → 6. audit: lay all touchpoints on one board; any that could belong to another brand is redone.
Process for finding the core: `creative-process.md` moves 1–2 and 7.
