# Kraken — Design Tokens (loopy-native)
> Category: fintech/crypto · Signature: commanding purple on white, 12px-capped buttons, whisper shadows

## Signature & atmosphere
Kraken puts a single commanding purple in charge of a clean white exchange — bold display type, professional and data-forward, with none of the playful crypto noise. The recognizable restraint is the button radius: a deliberate 12px, rounded but never a pill, signaling a serious trading tool rather than a consumer toy. Shadows exist but barely — whisper-level lifts at ~3% opacity keep cards grounded without drama.

## Color (hex · --var · role)
- `#ffffff` `--bg` — primary surface; `#101114` `--fg` — near-black text
- `#7132f5` `--primary` — Kraken Purple, CTA + links; `#5741d8` `--primary-dark` — outlined borders/variants; `#5b1ecf` deepest purple
- `rgba(133,91,251,0.16)` `--accent` — subtle purple button background
- `#686b82` neutral (borders at ~24%); `#9497a9` `--muted` — secondary text
- `#dedee5` `--border` — dividers; `--card` `#ffffff`
- `#149e61` success/positive (16% for badge bg); `#026b3f` badge text; `--destructive` use a conventional red
- Contrast note: white text on `#7132f5` clears AA; `#9497a9` on white is borderline for small text — bump to `#686b82` for fine print.

## Typography
- Stack: `"Kraken-Brand", "IBM Plex Sans", Helvetica, Arial, sans-serif` display; `"Kraken-Product", "Helvetica Neue", Helvetica, Arial, sans-serif` UI/body.
- Display-hero 48/700/1.17/-1px · H2 36/700/1.22/-0.5px · H3 28/700/1.29/-0.5px · Feature 22/600/1.20/normal · Body 16/400/1.38/normal · Body-medium 16/500/1.38 · Button 16/500-600/1.38 · Caption 14/400-700/1.43-1.71 · Small 12/400-500/1.33 · Micro 7/500/1.0/uppercase
- Display is bold (700) with negative tracking; body is Kraken-Product 400-500, neutral tracking.

## Spacing, radius, depth, motion
- Base 8px; scale 2 · 3 · 4 · 5 · 6 · 8 · 10 · 12 · 13 · 15 · 16 · 20 · 24 · 25.
- Radius: 3 · 6 · 8 (badge) · 10 (white button) · 12 (button cap — the workhorse) · 16 · 9999 (rare) · 50%.
- Depth strategy: subtle shadows — `rgba(0,0,0,0.03) 0 4px 24px` (cards), `rgba(16,24,40,0.04) 0 1px 4px` (micro). Whisper, never bold.
- Motion: short ease transitions ~150-200ms; gentle shadow/opacity shifts on hover, GPU only.

## Components (key)
- Primary CTA: bg `#7132f5` / text `#ffffff` / padding 13px 16px / radius 12px.
- Purple outlined: bg `#ffffff` / text `#5741d8` / `1px solid #5741d8` / radius 12px.
- Purple subtle: `rgba(133,91,251,0.16)` bg / `#7132f5` text / padding 8px / radius 12px.
- White button: `#ffffff`, `#101114` text, radius 10px, shadow `rgba(0,0,0,0.03) 0 4px 24px`.
- Success badge: `rgba(20,158,97,0.16)` bg, `#026b3f` text, radius 6px.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: cap button radius at 12px — rounded but deliberately not a pill, the trading-tool signal.
- Do: keep purple inside its defined scale (`#7132f5`/`#5741d8`/`#5b1ecf`); don't invent shades.
- Don't: pill the CTAs — the consumer-app pill instinct undermines Kraken's professional read; 12px is the cap.
- Don't: stack heavy/dramatic shadows — depth here is a whisper (~3%), not a lift.
- Don't: lighten display weight — headings are bold 700 with negative tracking, not airy.

## Example component prompts
- "Hero on `#ffffff`: headline 48px Kraken-Brand weight 700 letter-spacing -1px line-height 1.17 `#101114`; purple CTA bg `#7132f5` white text radius 12px padding 13px 16px; outlined secondary `#ffffff` `1px solid #5741d8` `#5741d8` text radius 12px."
- "Card: white, `1px solid #dedee5`, radius 12px, shadow `rgba(0,0,0,0.03) 0 4px 24px`; feature title 22px Kraken-Product weight 600; body 16px/400 `#9497a9`; success badge `rgba(20,158,97,0.16)` `#026b3f` radius 6px."
