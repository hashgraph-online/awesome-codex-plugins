# GitLab — Design Tokens (loopy-native)
> Category: dev-tools · Signature: tanuki orange gradient against clean Pajamas neutrals

## Signature & atmosphere
GitLab feels like a single confident orange burst lighting up an otherwise sober, document-clean interface. The recognizable idea is the two-tone brand gradient — the fox-orange runs from a hot `#fc6d26` into a deeper `#e24329`, used on the logo, hero accents, and one primary action per view. Around that warmth everything is restrained Pajamas-system gray-on-white, so the orange always lands as the loudest thing on the page.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page/cards; `#fafafa` `--bg-subtle` — alternating section tint
- `#1f1e24` `--fg` — primary text (near-black, faint warm cast); `#28272d` heading variant
- `#e24329` `--primary` — tanuki red-orange; primary CTA fill + brand signal
- `#fc6d26` `--accent` — bright orange; gradient top-stop, hover lift, icon highlights
- `#1068bf` `--link` — action blue; links and informational accents (cool counterweight to the orange)
- `#737278` `--muted` — secondary text; `#89888d` tertiary/placeholder
- `#dcdcde` `--border` — default hairline; `#ececef` subtle divider
- `#dd2b0e` `--destructive` — danger red; `#108548` success green; `#c17d10` warning
- Contrast: muted `#737278` on white ≈ 4.6:1 (AA body); white text on `#e24329` passes for CTAs. The orange gradient is decoration/CTA only, never a text color on light.

## Typography
- Stack: UI `"GitLab Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`; code `"GitLab Mono", "JetBrains Mono", ui-monospace, monospace`. GitLab Sans is humanist with open apertures — friendly, not geometric.
- Display 48px/600/1.1/-0.5px · H1 32px/600/1.2 · H2 24px/600/1.25 · H3 20px/600/1.3 · Body 16px/400/1.5 · Body-sm 14px/400/1.5 (default UI size) · Label 12px/500/1.33/+0.2px
- Weights 400 body / 500 emphasis+labels / 600 headings. Bold (700) is for inline strong only — headings top out at 600.

## Spacing, radius, depth, motion
- Base 8px (Pajamas scale); scale 4 · 8 · 12 · 16 · 24 · 32 · 48. List/table rows on 8/12.
- Radius: 4px inputs · 6px buttons · 8px cards · 50% avatars · pill (9999px) for badges.
- Depth strategy = borders first, then soft shadows. Cards: `1px solid #dcdcde` + optional `rgba(0,0,0,0.1) 0 1px 4px`. Dropdowns: `rgba(0,0,0,0.16) 0 2px 8px`. Focus ring `0 0 0 1px #fff, 0 0 0 3px #1068bf`.
- Motion 100–200ms ease; hover on the primary lifts orange toward `#fc6d26`.

## Components (key)
- Primary CTA: bg `#e24329` / text `#ffffff` / padding 6px 16px / radius 6px / no border / hover bg `#c91c00` or gradient `linear-gradient(#fc6d26,#e24329)` / focus `3px #1068bf` ring.
- Secondary (confirm) button: bg `#ffffff` / text `#1068bf` / `1px solid #1068bf` / radius 6px — the blue-outlined workhorse.
- Brand gradient accent: `linear-gradient(135deg, #fc6d26 0%, #e24329 100%)` on hero rules, icon chips, and progress fills — one per section.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: treat the orange as a two-stop gradient (`#fc6d26` → `#e24329`) and ration it to one primary action / accent per view so it stays the loudest element.
- Don't: pair the orange with a warm or red secondary — the secondary action is cool blue (`#1068bf`); a second warm button muddies the brand burst.
- Don't: set body or large surfaces in orange — it is a CTA/accent only; an orange section reads as a warning, not the brand.
- Don't: use a geometric/grotesk display face — GitLab Sans is humanist and friendly; a stiff face contradicts the open, collaborative voice.

## Example component prompts
- "Hero on `#ffffff`: H1 48px GitLab Sans weight 600, line-height 1.1, letter-spacing -0.5px, `#1f1e24`; subhead 18px/400 in `#737278`. Primary CTA bg `#e24329` white text 6px radius, hover gradient `linear-gradient(#fc6d26,#e24329)`; secondary outlined button `1px solid #1068bf`, `#1068bf` text."
- "Feature card: white bg, `1px solid #dcdcde`, 8px radius, shadow `rgba(0,0,0,0.1) 0 1px 4px`. Icon chip with `linear-gradient(135deg,#fc6d26,#e24329)` background; title 20px/600 `#1f1e24`, body 14px/400 `#737278`, a 12px/500 pill badge in `#108548`."
