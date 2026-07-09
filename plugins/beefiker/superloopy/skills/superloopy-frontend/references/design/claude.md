# Claude — Design Tokens (loopy-native)
> Category: ai-labs · Signature: warm parchment + single-weight serif headlines

## Signature & atmosphere
Claude feels like a well-made book left open on a wooden desk: the surface reads as paper, not glass. Every neutral leans yellow-brown, so the screen never goes clinical or cold. The one idea to get right is warmth-as-trust — a literary, unhurried calm that says "thoughtful" before it says "AI."

## Color (hex · --var · role)
- `#f5f4ed` `--bg` — page background (warm parchment, never pure white); `#141413` `--fg` — text (warm near-black, slight olive, not `#000`)
- `#faf9f5` `--card` — ivory card surface, one step up from bg
- `#c96442` `--primary` — terracotta; CTA fills and top brand signal only
- `#d97757` `--accent` — coral; links/emphasis on dark surfaces
- `#5e5d59` `--muted` — secondary text (warm olive-gray); `#87867f` tertiary
- `#f0eee6` `--border` — barely-there cream hairline; `#e8e6dc` emphasized divider
- `#b53333` `--destructive` — warm crimson; `#3898ec` focus ring (the only cool color, accessibility only)
- `#30302e` `--card-dark` / `#141413` dark bg for alternating chapter sections. Contrast: muted `#5e5d59` on `#f5f4ed` ≈ 5.4:1 — fine for body, not for 12px labels.

## Typography
- Stack: serif display `"Anthropic Serif", Georgia, serif`; UI `"Anthropic Sans", system-ui, sans-serif`; code `"Anthropic Mono", ui-monospace, monospace`. Serif = authority, sans = utility.
- Display 64px / 500 / 1.10 / 0 · H2 52px / 500 / 1.20 / 0 · Card title 32px / 500 / 1.10 · Body-serif 17px / 400 / 1.60 (editorial passages) · Body 16px / 400 / 1.60 · Label 12px / 500 / 1.25 / +0.12px
- All serif headings sit at weight 500 — one voice, no bold, no light.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/20/24/32/48/80px; section gaps 80–120px (magazine pacing).
- Radius scale 6 / 8 / 12 / 16 / 32px (hero media + embeds go to 32).
- Depth strategy: ring shadows, not drops — `0 0 0 1px` in warm gray (`#d1cfc5`) reads like a soft border. Elevated cards: `rgba(0,0,0,0.05) 0 4px 24px`. Bigger contrast comes from light/dark section alternation, not elevation.
- Motion 150–240ms, ease-out; transform/opacity only.

## Components (key)
- Primary CTA: bg `#c96442` / text `#faf9f5` / padding 10px 16px / radius 12px / no border / hover lifts ring `0 0 0 1px #c96442` + darken 4%, active inset ring, focus `#3898ec` 2px ring.
- Secondary (workhorse) button: bg `#e8e6dc` / text `#4d4c48` / radius 8px / ring `0 0 0 1px #d1cfc5`.
- Chapter section: full-bleed band flips between `#f5f4ed` and `#141413`; headline `#faf9f5`, body `#b0aea5` on dark.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep every gray warm (yellow-brown undertone); set serif headlines at weight 500 only; use ring shadows for interactive states; pace sections like book chapters.
- Don't: reach for weight 600–700 on display — 500 is the whole voice. Don't use `#000`/`#fff` or any cool blue-gray. Don't drop heavy box-shadows. Don't render headings in the sans — the serif/sans split IS the identity.

## Example component prompts
- "Hero on `#f5f4ed`: H1 in Anthropic Serif 64px / weight 500 / line-height 1.10 in `#141413`; subhead Anthropic Sans 20px / 400 / 1.60 in `#5e5d59`; terracotta `#c96442` CTA, white text, 12px radius."
- "Feature card on `#faf9f5` with 1px `#f0eee6` border, 8px radius, whisper shadow `rgba(0,0,0,0.05) 0 4px 24px`; title serif 32px/500, body 16px/1.60 in `#5e5d59`."
- "Dark chapter band on `#141413`: serif H2 52px/500 in `#faf9f5`, body in `#b0aea5`, dividers `#30302e`."
