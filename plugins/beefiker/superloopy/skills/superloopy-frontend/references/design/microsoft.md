# Microsoft — Design Tokens (loopy-native)
> Category: consumer · Signature: Fluent neutrals, acrylic blur depth, one confident blue, square-ish corners

## Signature & atmosphere
Microsoft (Fluent) feels like frosted glass over light gray: surfaces stack with translucent "acrylic" blur and soft layered shadows, so depth comes from material rather than borders. The one recognizable idea is the confident communication blue paired with cool neutral grays — calm, enterprise-trustworthy, and slightly square in its geometry. The four-color logo grid signals brand; the product itself is restrained, legible, and built for long working sessions.

## Color (hex · --var · role)
- `#ffffff` `--bg` — canvas; `#faf9f8` `--bg-2` — app background (warm-cool off-white); `#242424` `--fg` — text (near-black, not `#000`)
- `#0078d4` `--primary` — communication blue; primary CTA, links, selected (hover `#106ebe`, pressed `#005a9e`)
- `#2b88d8` `--accent` — lighter blue tint for fills on dark / hover wash
- `#605e5c` `--muted` — secondary text; `#a19f9d` tertiary/disabled
- `#d2d0ce` `--border` — control outline (`#8a8886` stronger input stroke); `#f3f2f1` `--card` — neutral layer fill
- `#a4262c` `--destructive` — error red; `#107c10` success green; `#ffb900` warning amber (also a logo hue)
- Logo grid: `#f25022` red · `#7fba00` green · `#00a4ef` blue · `#ffb900` yellow — brand mark only, not UI fills.
- Contrast: `--muted #605e5c` on white ≈ 5.7:1. Blue `#0078d4` is the single action color.

## Typography
- Stack: `"Segoe UI Variable", "Segoe UI", system-ui, sans-serif`; substitute Inter or system-ui. Clear, neutral, humanist — engineered for legibility at small sizes.
- Display 40px / 600 / 1.20 · Title 28px / 600 / 1.25 · Subtitle 20px / 600 / 1.30 · Body-strong 14px / 600 · Body 14px / 400 / 1.43 · Caption 12px / 400 / 1.33
- Signature: hierarchy is carried by semibold (600) headings over a 14px regular body — a tight, businesslike ramp. Segoe's even color and open counters keep dense UI readable; no light-weight display moment.

## Spacing, radius, depth, motion
- Base 4px; scale 4 · 8 · 12 · 16 · 20 · 24 · 32 · 40; comfortable but information-efficient.
- Radius: 2px small controls · 4px buttons/inputs · 8px cards/dialogs · 50% personas. Fluent is gently rounded but stays square-ish (4px is the workhorse) — not pill-soft.
- Depth = acrylic blur + layered neutral shadows: surfaces use `backdrop-filter: blur(30px)` over a translucent `rgba(255,255,255,0.6)` tint; elevation shadows `0 1.6px 3.6px rgba(0,0,0,0.13), 0 0.3px 0.9px rgba(0,0,0,0.11)` (card) up to `0 6.4px 14.4px rgba(0,0,0,0.13), 0 1.2px 3.6px rgba(0,0,0,0.11)` (dialog). Reveal highlight on hover for large surfaces.
- Motion: 167–267ms with Fluent easing `cubic-bezier(0.33, 0, 0.67, 1)`; subtle, purposeful.

## Components (key)
- Primary CTA (filled): bg `#0078d4` / text `#fff` / padding 5px 20px, min-height 32px / radius 4px / hover `#106ebe` / pressed `#005a9e` / focus 2px `#0078d4` ring offset + 1px inner stroke. Default (secondary): white fill, 1px `#8a8886` border, `#242424` text.
- Acrylic flyout / command surface: translucent `rgba(255,255,255,0.7)` + `backdrop-filter: blur(30px)`, radius 8px, shadow `0 6.4px 14.4px rgba(0,0,0,0.13)`; subtle 1px `rgba(0,0,0,0.05)` stroke to define the edge over busy backgrounds.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build depth with acrylic blur + layered neutral shadows; keep the body at 14px with 600 semibold headings; use one communication blue for all actions; keep radius small (4px).
- Don't: round buttons into full pills — Fluent stays square-ish at 4px, the pill instinct is wrong. Don't pull the brand logo's red/green/yellow into the UI as accent fills — they live in the logo only; blue is the action color. Don't replace acrylic translucency with flat opaque cards when the design calls for material depth. Don't go below 14px for primary body in dense apps.

## Example component prompts
- "Fluent primary button: `#0078d4` fill, white label Segoe UI 14px/600, radius 4px, padding 5px 20px, min-height 32px; hover `#106ebe`, pressed `#005a9e`, 2px focus ring. Secondary: white fill, 1px `#8a8886` border, `#242424` text."
- "Acrylic command flyout: translucent `rgba(255,255,255,.7)` + backdrop-blur 30px, radius 8px, shadow `0 6.4px 14.4px rgba(0,0,0,.13)`, 1px `rgba(0,0,0,.05)` edge; items 14px/400 `#242424`, hover fill `#f3f2f1`."
- "Card on `#faf9f8`: white surface, radius 8px, shadow `0 1.6px 3.6px rgba(0,0,0,.13), 0 .3px .9px rgba(0,0,0,.11)`; title 20px/600 `#242424`, body 14px/400 `#605e5c`."
