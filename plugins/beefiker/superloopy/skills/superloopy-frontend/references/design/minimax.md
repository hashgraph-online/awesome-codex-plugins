# MiniMax — Design Tokens (loopy-native)
> Category: ai-labs · Signature: airy white gallery of colorful product cards, lit by purple-tinted glow

## Signature & atmosphere
MiniMax feels like an app home screen rather than a research lab: a bright white canvas where vivid, rounded product cards sit like glowing app icons, each its own little creative tool. The chrome is light and approachable — pill-shaped nav, generous corners, near-black text — so all the color comes from the product gallery itself. The recognizable idea is white-as-structure, color-as-content: the layout is disciplined and pale, and the AI products supply every saturated hue, lifted by a faintly purple shadow that ties the whole stage together.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page background (white is the structural surface, never tinted); `#181e25` dark footer/section
- `#222222` `--fg` — primary text (near-black, warm-neutral, not pure `#000`)
- `#1456f0` `--primary` — MiniMax brand blue; brand identity and key actions
- `#3b82f6` `--accent` — standard blue action (`#2563eb` hover, `#1d4ed8` pressed, `#60a5fa` light/active)
- `#ea5ec1` `--brand-pink` — secondary brand pink; logo and decorative accents ONLY, never text/buttons
- `#45515e` `--muted` — secondary text; `#8e8e93` tertiary/labels
- `#e5e7eb` `--border` — component border; `#f2f3f5` subtle section divider; `#f0f0f0` secondary-button fill
- `#18181b` `--cta-dark` — dark CTA fill (button bg). Contrast: `#45515e` on `#fff` ≈ 7.6:1 (strong); keep pink `#ea5ec1` off text — it's decorative and fails as a label color.

## Typography
- Stack: UI `"DM Sans", "Helvetica Neue", Arial, sans-serif` (workhorse); display `"Outfit", sans-serif` (geometric headings); mid-tier `"Poppins", sans-serif`; data `"Roboto", sans-serif`. Four fonts, each a distinct job — DM Sans carries ~70%.
- Display 80px / 500 / 1.10 / 0 (Outfit or DM Sans) · Section 31px / 600 / 1.50 (Outfit) · Card title 28px / 500–600 / 1.40 (Outfit) · Sub-head 24px / 500 / 1.50 (Poppins) · Body-lg 20px / 500 / 1.50 · Body 16px / 400–500 / 1.50 · Nav 14px / 500 / 1.50 · Label 12px / 500–600 / 1.40
- Near-universal 1.50 line-height is the unifying rhythm; weight 500 is the default emphasis (600 for section titles), 700 reserved for in-body strong only — headings never go 700.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/10/16/24/32/40/64/80px; large section gaps 64–80px (gallery breathing room).
- Radius scale 8 (buttons/UI) / 13–16 (medium cards) / 20–24 (hero product cards) / 9999 (nav pills) — small UI is crisp, product cards are generously rounded.
- Depth strategy: light, low-opacity shadows; the signature is a purple-tinted glow `rgba(44,30,116,0.16) 0 0 15px` on featured cards plus neutral `rgba(0,0,0,0.08) 0 4px 6px` for standard cards. Nothing above 0.16 opacity — airiness requires restraint.
- Motion 150–250ms ease-out; gentle hover lift to the elevated `rgba(36,36,36,0.08) 0 12px 16px -4px`.

## Components (key)
- Primary CTA: bg `#18181b` / text `#ffffff` / padding 11px 20px / radius 8px / no border / hover slight lift to elevated shadow. Nav pill: `rgba(0,0,0,0.05)` fill, `#18181b` text, radius 9999px. Secondary: `#f0f0f0` fill, `#333333` text, 8px radius.
- Product card (signature): vibrant per-product gradient fill (pink/purple/orange/blue), 20–24px radius, purple glow `rgba(44,30,116,0.16) 0 0 15px`; product name in Outfit 28px/600, version + description below — each card a self-contained colorful tile on the white stage.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep white as the structural background and let product cards/gradients supply all color; use 9999px pills for nav/tabs but 8px for CTA buttons; tint featured-card shadows purple `rgba(44,30,116,...)`; keep headings at 500–600.
- Don't: tint main content sections — the wrong instinct is "add a soft brand-color background"; white is structural, color belongs to the cards. Don't put the pink `#ea5ec1` on text or buttons (decorative only). Don't go weight 700 on headings (500–600 is the range). Don't sharpen product cards to 0–4px corners or darken shadows past 0.16 — the airy, rounded feel is the brand. Don't use Roboto for headings (data/technical only).

## Example component prompts
- "Hero on `#ffffff`: headline Outfit 80px / weight 500 / line-height 1.10 in `#222222`; subhead DM Sans 16px / 400 / 1.50 in `#45515e`; dark CTA `#18181b` bg, white text, 8px radius, 11px 20px padding."
- "Product card: per-product gradient fill, 22px radius, glow `rgba(44,30,116,0.16) 0 0 15px`; name Outfit 28px/600; sits on white with 64px section gaps."
- "Nav bar: white bg, DM Sans 14px/500 links in `#18181b`, active tab pill `rgba(0,0,0,0.05)` fill 9999px radius, logo left."
- "AI product matrix: 4-col white cards, 13px radius, shadow `rgba(0,0,0,0.08) 0 4px 6px`, centered icon above DM Sans 16px/500 name."
