# Mintlify — Design Tokens (loopy-native)
> Category: dev-tools · Signature: paper-white clarity with sparing mint-green and full-pill everything

## Signature & atmosphere
Mintlify is documentation-as-product: a luminous white surface that treats legibility as the highest aesthetic value, so the marketing page itself demonstrates the reading comfort it sells. The recognizable idea is calm restraint with one fresh signal — a bright mint green used only at the moments that matter (CTAs, hover, focus), riding over an otherwise disciplined black-on-white system. Depth comes from whisper-thin 5%-opacity borders and whitespace, never gray section bands; everything reads flat and paper-like, with the only flourish a soft cloud-like green gradient behind the hero.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page and card surfaces (no gray backgrounds anywhere); `#0d0d0d` `--fg` — text/headings (near-black for micro-softness, not pure `#000`)
- `#18E299` `--primary` / `--accent` — brand mint; CTAs, link-hover, focus rings, sparing accent touches only
- `#d4fae8` mint-tint surface for badges; `#0fa76e` deep mint for text on mint badges
- `#333333` `--muted` — body/secondary; `#666666` tertiary; `#888888` placeholder/disabled
- `rgba(0,0,0,0.05)` `--border` — the primary 5%-opacity separator; `rgba(0,0,0,0.08)` stronger border for interactive edges
- `#d45656` `--destructive`; `#c37d0d` warning; `#3772cf` info. Contrast: `#666666` on white ≈ 5.7:1 (body-ok); mint `#18E299` on white fails text contrast — use it as fill with `#0d0d0d` text, never as small text on white.

## Typography
- Stack: `Inter, "Inter Fallback", system-ui, sans-serif` (everything human-readable); `"Geist Mono", ui-monospace, monospace` (code + technical labels only). The boundary is strict — no mixing.
- Display 64px / 600 / 1.15 / -1.28px · Section 40px / 600 / 1.10 / -0.8px · Sub-head 24px / 500 / 1.30 / -0.24px · Card-title 20px / 600 / 1.30 / -0.2px
- Body-lg 18px / 400 / 1.50 · Body 16px / 400 / 1.50 · Button 15px / 500 · Link 14px / 500
- Mono label 12px / 500-600 / **+0.6px uppercase** (the terminal voice). Three weights only: 400 read, 500 interact, 600 announce — no 700.

## Spacing, radius, depth, motion
- Base 8px; scale 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px; section gaps 48–96px (documentation-grade breathing room, 1–2 messages per section).
- Radius: 4px inline code · 8px nav/transparent buttons · 16px cards/images · 24px featured cards · 9999px buttons, inputs, badges (the signature full-pill shape).
- Depth is border-driven, barely any shadow. Card border `1px solid rgba(0,0,0,0.05)` + ambient `rgba(0,0,0,0.03) 0 2px 4px`; button micro-shadow `rgba(0,0,0,0.06) 0 1px 2px`. Focus = `1px solid #18E299` outline.
- Motion 150ms; hover usually just `opacity: 0.9`.

## Components (key)
- Primary CTA (dark pill): bg `#0d0d0d` / text `#ffffff` / padding 8px 24px / radius 9999px / shadow `rgba(0,0,0,0.06) 0 1px 2px` / hover opacity 0.9.
- Ghost CTA (light pill): bg `#ffffff` / text `#0d0d0d` / radius 9999px / border `1px solid rgba(0,0,0,0.08)` / padding 4.5px 12px.
- Email input: pill (9999px) to match buttons, border `1px solid rgba(0,0,0,0.08)`, focus ring `#18E299`, placeholder `#888888`.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: use full-pill radius (9999px) on buttons AND inputs — the instinct toward 6–8px "modern" corners flattens the signature shape.
- Don't: pour mint `#18E299` into decorative fills or backgrounds — it's a sparing signal (CTA/hover/focus); over-using it cheapens the freshness.
- Don't: add gray section bands for "structure" — separation is 5%-opacity borders and whitespace on a single white field.
- Don't: cap headlines at 700 — the system tops out at 600; tight tracking (not weight) gives display its compressed-docs feel.
- Don't: let display tracking go loose — it scales negative with size (-1.28px@64 → -0.24px@24 → 0@body).

## Example component prompts
- "Hero on `#ffffff` with soft green-white cloud gradient wash. Headline 64px Inter weight 600, line-height 1.15, letter-spacing -1.28px, color `#0d0d0d`. Subtitle 18px Inter 400/1.50 in `#666666`. Dark pill CTA `#0d0d0d` 9999px 8px 24px + ghost pill `1px solid rgba(0,0,0,0.08)`."
- "Card: white bg, `1px solid rgba(0,0,0,0.05)` border, 16px radius, 24px padding, shadow `rgba(0,0,0,0.03) 0 2px 4px`. Title 20px Inter 600 / -0.2px; body 14px 400 in `#666666`."
- "Mint badge: bg `#d4fae8`, text `#0fa76e`, 9999px radius, 4px 12px, 13px Inter 500 uppercase."
