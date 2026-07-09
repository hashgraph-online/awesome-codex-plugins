# MongoDB — Design Tokens (loopy-native)
> Category: dev-tools · Signature: forest-black canvas with one bioluminescent green and a serif headline

## Signature & atmosphere
MongoDB feels like a database glimpsed at night in a forest — the canvas is the deepest teal-black (`#001e2b`), never space-black, and a single electric green (`#00ed64`) glows against it like something alive growing in the dark. The unexpected move is an editorial serif at hero scale, which makes a developer database read as an institution rather than a startup. Even shadows are tinted teal, so depth stays inside the brand's color world.

## Color (hex · --var · role)
- `#001e2b` `--bg` — forest-black canvas (never `#000`); `#ffffff` `--bg-light` — light content sections
- `#ffffff` `--fg` on dark / `#001e2b` text on light; `#e8edeb` `--fg-soft` — input/body text on dark
- `#00ed64` `--accent` — electric MongoDB green; underlines, highlights, glows (accent only, never large fills)
- `#00684a` `--primary` — muted functional green; CTA fill + link text on light, button borders
- `#006cfa` `--link` — action blue; hover transitions to `#3860be`; `#1eaedb` teal active/hover
- `#5c6c75` `--muted` — secondary text on dark; `#1c2d38` deep-teal secondary surface
- `#b8c4c2` `--border-light` — hairline on white; `#3d4f58` `--border-dark` — hairline on dark
- Contrast: white on `#001e2b` is strong; the neon `#00ed64` is for accents/underlines on dark only — too acidic as body text or a page fill.

## Typography
- Stack: display serif `"MongoDB Value Serif", Georgia, "Times New Roman", serif`; UI `"Euclid Circular A", Akzidenz-Grotesk, system-ui, sans-serif`; code/labels `"Source Code Pro", ui-monospace, monospace`. Serif = authority, geometric sans = workhorse, mono = the database-field label voice.
- Display 96px/400/1.2/0 (serif) · Display-2 64px/400/1.0 (serif) · Section 36px/500/1.33 (sans) · Sub 24px/500/1.33 · Body 18px/400/1.33 · Body-light 16px/300/1.5 · Code-label 14px/400–500/1.14/+1–2px UPPERCASE
- Four-weight sans range (300/400/500/700) — weight 300 is the distinctive airy body voice. Source Code Pro uppercase with wide 1–3px tracking is the signature technical label.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 (plus organic 7/10/14/15 micro-values).
- Radius: 4px inputs/small buttons · 8px links · 16px standard cards · 24px large panels · 30–32px image containers · 100px pill buttons.
- Depth strategy = teal-tinted shadows. Primary card elevation `rgba(0,30,43,0.12) 0 26px 44px, rgba(0,0,0,0.13) 0 7px 13px`; subtle lift `rgba(0,0,0,0.1) 0 2px 4px`. Even on white, shadows carry the forest color rather than neutral black.
- Motion 150–250ms ease; pill buttons hover with `translateX(5px)` and scale micro-presses.

## Components (key)
- Primary CTA (pill): bg `#00684a` / text `#000000` / radius 100px / `1px solid #00684a` / shadow `rgba(0,0,0,0.06) 0 1px 6px` / hover scale 1.1, active scale 0.85.
- Dark teal button: bg `#1c2d38` / text `#5c6c75` / `1px solid #3d4f58` / radius 100px / hover bg `#1eaedb`, white text, `translateX(5px)`.
- Green accent underline: bottom-border `2px solid #00ed64` (or `#006cfa` variant) under feature headings — the signature decorative element.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use forest-black `#001e2b` for dark canvases and keep shadows teal-tinted (`rgba(0,30,43,…)`) so depth stays in the brand world.
- Don't: use pure `#000` for dark backgrounds or neutral-gray shadows — the cool teal cast IS the identity.
- Don't: pour the neon `#00ed64` into large fills or body text — it is an accent/underline on dark; large surfaces use the muted `#00684a`.
- Don't: set body text in the serif or default to weight 400 — the serif is hero-only and weight 300 is the airy reading voice; narrow tracking on the mono labels also kills them.

## Example component prompts
- "Hero on `#001e2b`: headline 96px MongoDB Value Serif weight 400, line-height 1.2, white with one word in `#00ed64`; subtitle 18px Euclid Circular A weight 400. Green pill CTA `#00684a` 100px radius, black text; neon-green gradient glow behind the product screenshot."
- "Card on white: `1px solid #b8c4c2`, 16px radius, teal shadow `rgba(0,30,43,0.12) 0 26px 44px`. Source Code Pro 14px uppercase label, +2px tracking, above a 24px/500 Euclid title; body 16px/300; green underline `2px solid #00ed64` on the heading."
