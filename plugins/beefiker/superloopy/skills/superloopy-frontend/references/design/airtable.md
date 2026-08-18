# Airtable — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: Swiss-clean enterprise, blue-tinted depth

## Signature & atmosphere
Airtable reads as "sophisticated simplicity" — a white canvas, deep blue-navy ink, and one decisive Airtable Blue carrying every interactive moment. Where most SaaS sites tighten type, Airtable does the opposite: positive letter-spacing across body text gives it a precise, almost engineered Swiss-grid calm. Even the shadows lean blue rather than neutral gray, so cards feel lit by the same brand light rather than dropped on a dim surface.

## Color (hex · --var · role)
- `#ffffff` `--bg` — primary surface
- `#181d26` `--fg` — deep navy foreground (not pure black; cooler and more structured than warm-neutral brands)
- `#1b61c9` `--primary` — Airtable Blue; CTA buttons + links (~5:1 on white, AA)
- `#254fad` `--accent` — darker blue for accents/secondary links
- `rgba(4,14,32,0.69)` `--muted` — weak/secondary text
- `#333333` `--muted-2` — neutral secondary text
- `#e0e2e6` `--border` — card + container border
- `#f8fafc` `--surface-2` — subtle alternate surface
- `#006400` `--success` — success text
- Shadow note: depth is blue-tinted — `rgba(45,127,249,0.28) 0 1px 3px` sits inside the stack, not a neutral gray drop.

## Typography
- Stack: `Haas, -apple-system, system-ui, "Segoe UI", Roboto` (text); `"Haas Groot Disp", Haas` (display). Substitute Inter / Helvetica Neue if Haas is unavailable.
- Display 48/400/1.15/normal · DisplayBold 48/900/1.50 (Haas Groot Disp) · H2 40/400/1.25 · Sub 32/400–500/1.20
- CardTitle 24/400/1.25/+0.12px · Feature 20/400/1.35/+0.1px · Body 18/400/1.35/+0.18px
- BodyMed 16/500/1.30/+0.08–0.16px · Button 16/500/1.28/+0.08px · Caption 14/400–500/1.30/+0.07–0.28px
- Signature: positive tracking everywhere (+0.08px to +0.28px) — never tighten body type.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 48.
- Radius: 2px tiny/sharp consent buttons · 12px standard buttons · 16px cards · 24px sections · 32px large · 50% circles.
- Depth strategy: **blue-tinted multi-layer shadows**. Card stack `rgba(0,0,0,.32) 0 0 1px, rgba(0,0,0,.08) 0 0 2px, rgba(45,127,249,.28) 0 1px 3px, rgba(0,0,0,.06) 0 0 0 .5px inset`; soft ambient `rgba(15,48,106,.05) 0 0 20px`.
- Motion: brief ease on hover; restrained — this is an enterprise tone.

## Components (key)
- Primary CTA: bg `#1b61c9` / text `#ffffff` / padding 16px 24px / radius 12px / no border. Generous 12px radius reads friendly-enterprise, not playful pill.
- White button: bg `#ffffff` / text `#181d26` / radius 12px / `1px solid #e0e2e6`.
- Card: bg `#ffffff`, `1px solid #e0e2e6`, 16px radius, blue-tinted shadow stack above.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: apply positive letter-spacing (+0.08–0.28px) to body and labels — it is the Swiss-precision voice.
- Don't: tighten type with negative tracking — that is the opposite of Airtable's register and makes it read like a generic startup.
- Don't: drop neutral gray shadows — depth must carry the blue tint (`rgba(45,127,249,0.28)`), otherwise cards look unlit and off-brand.

## Example component prompts
- "Hero on `#ffffff`: headline 48px Haas weight 400, line-height 1.15, color `#181d26`. Body 18px/400/1.35, letter-spacing +0.18px, `#333333`. Blue CTA `#1b61c9`, 12px radius, 16px 24px padding, white text."
- "Card: `#ffffff`, `1px solid #e0e2e6`, 16px radius, shadow `rgba(0,0,0,.32) 0 0 1px, rgba(0,0,0,.08) 0 0 2px, rgba(45,127,249,.28) 0 1px 3px`. Title 24px Haas/400/+0.12px."
- "Button label 16px Haas weight 500, letter-spacing +0.08px, `#ffffff` on `#1b61c9`."
