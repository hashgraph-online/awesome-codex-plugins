# Replicate — Design Tokens (loopy-native)
> Category: ai-creative · Signature: a developer launchpad that shouts with joy

## Signature & atmosphere
Replicate feels like a festival poster wearing a developer playground — an explosive orange-to-magenta gradient hero up top, then a clean white canvas where model galleries and code snippets do the talking. Two extreme choices define it: display type that goes genuinely huge (up to 128px) in a heavy face, and a geometry that is pill-shaped on absolutely everything. The energy is participatory and community-powered, not corporate.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page body background; `#202020` `--fg` — primary text and dark surface (a warm near-black, not pure `#000`)
- `#ea2804` `--primary` — the brand red-orange; used in the hero gradient and accent borders, never as a flat fill background
- `#dd4425` `--primary-hover` — warmer variant for button borders and link hover
- `#2b9a66` `--success` — operational/"running" status badges
- `#24292e` `--code-bg` — blue-tinted dark for code blocks
- `#646464` `--muted` — secondary text; `#8d8d8d` `--muted-2` — footnotes; `#bbbbbb` `--decoration` — the dotted-underline link color
- `#000000` `--border-strong` — max-emphasis borders. Contrast: `--primary` `#ea2804` on white ~4.0:1 — fine for large/bold text and icons, not 14px body.

## Typography
- Stack: display `"rb-freigeist-neue", ui-sans-serif, system-ui` · body `"basier-square", ui-sans-serif, system-ui` · code `"JetBrains Mono", ui-monospace, monospace`
- Display-mega 128px / 700 / 1.00 / 0 (closing manifesto) · Display 72px / 700 / 1.00 / -1.8px · H2 48px / 700 / 1.00 / 0
- H3 30px / 600 / 1.20 / 0 · Body-lg 20px / 400 / 1.40 · Body 16px / 400–600 / 1.50
- Caption 14px / 400–600 / 1.43 · Tag 12px / 400 / 1.33 lowercase (text-transform: lowercase is the signature) · Code 14px / 400 / 1.43

## Spacing, radius, depth, motion
- Base 8px; scale 4·8·12·16·24·32·48·64·96·160·192; section gaps very generous (96–192px)
- Radius: `9999px` on EVERYTHING — buttons, images, badges, containers. There is no other radius value in the system
- Depth strategy: borders + background color, not shadows. `1px solid #202020` is the workhorse container; `1px solid #ea2804` marks featured items
- Motion: 150–200ms ease on hover; dotted underline and badge color shifts, no elaborate transitions

## Components (key)
- Primary CTA: `#202020` bg / `#fcfcfc` text / pill radius / generous horizontal padding / hover dims slightly / active presses / focus ring. Secondary is white bg + `1px solid #202020` outlined pill
- Manifesto block: "Imagine what you can build." at 128px / 700 / 1.0 on `#202020`, with small AI-generated images embedded between the words — the emotional climax of the page

## Do / Don't (anti-convention — name the wrong instinct)
- Do: commit to one radius — `9999px` everywhere, including image containers
- Don't: reach for a tasteful 8–12px corner. The wrong instinct here is "moderate rounding"; Replicate is all-pill or it's not Replicate
- Don't: paint surfaces in `#ea2804`. The brand red lives in gradients and accent borders only — a full red panel breaks the system
- Don't: use solid underlines on links — dotted `#bbbbbb` is the developer-notebook signature; and don't shrink display type below 48px on desktop

## Example component prompts
- "Hero: full-width orange→red→magenta→pink gradient; headline `rb-freigeist-neue` 72px weight 700 letter-spacing -1.8px in white; a dark pill CTA (`#202020` bg, `#fcfcfc` text) beside a white outlined pill (`1px solid #202020`)."
- "Model card: pill image container (`9999px`), name `basier-square` 16px/600, run count 14px in `#646464`, `1px solid #202020` border, no shadow."
- "Status badge: pill, `#2b9a66` bg, white `basier-square` 14px text."
- "Code block: `#24292e` bg, `JetBrains Mono` 14px white text, pill container."
