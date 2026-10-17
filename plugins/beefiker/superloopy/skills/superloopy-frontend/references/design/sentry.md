# Sentry — Design Tokens (loopy-native)
> Category: dev-tools · Signature: warm purple-black IDE with tactile inset buttons and a lime pop

## Signature & atmosphere
Sentry feels like the late-night debugging session it was built for — a warm purple-black room, not the cold gray of most dev tools. Buttons read as physical objects pressed into the surface via inset shadow, and content seems to glow with its own purple-tinted light. A single irreverent display face and one acid lime-green carry the brand's "code breaks, fix it faster" attitude.

## Color (hex · --var · role)
- `#1f1633` `--bg` — primary purple-black (never `#000000`); `#ffffff` `--fg` — primary text
- `#150f23` `--card` — deeper sections/footer; `#362d59` `--border` — purple-tinted structural lines
- `#79628c` `--primary` — muted-purple button fill; `#6a5fc1` `--accent` — links/hover/focus; `#422082` — select/active high-emphasis
- `#c2ef4e` `--lime` — high-visibility pop (one per section max); `#ffb287` — coral focus bg; `#fa7faa` — pink focus outline
- `#e5e7eb` `--muted` — secondary text; light-context input border `#cfcfdb`
- Contrast: white on `#1f1633` is strong; lime `#c2ef4e` only on dark, never as text on light.

## Typography
- Stack: `Dammit Sans` (display/hero only — brand personality), `Rubik` (all functional UI), `Monaco` (code).
- Display 88px/700/1.2/0 (Dammit) · Display-2 60px/500/1.1/0 (Dammit) · Section 30px/400/1.2/0 (Rubik) · Card-title 24px/500/1.25/0
- Body 16px/400/1.5/0 · Nav 15px/500/1.4/0 · Button 14px/500–700/1.14/letter-spacing 0.2px UPPERCASE · Micro 10px/600/1.8/0.25px uppercase
- Rubik four-tier weights: 400 body · 500 nav/emphasis · 600 titles · 700 CTAs. Uppercase + 0.2px tracking is a system-wide label pattern.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 12 · 16 · 24 · 32 · 40 (plus organic 5/6/45/47 micro-values).
- Radius: 6px inputs · 8px buttons/cards · 12px glass panels · 13px primary muted button · 18px image containers.
- Depth = shadows + glow, purple-tinted. Inset `rgba(0,0,0,0.1) 0 1px 3px inset` on primary buttons (the tactile signature). Card `rgba(0,0,0,0.1) 0 10px 15px -3px`. Hover `rgba(0,0,0,0.18) 0 0.5rem 1.5rem`. Ambient hero glow `rgba(22,15,36,0.9) 0 4px 4px 9px`. Frosted glass `backdrop-filter: blur(18px) saturate(180%)`.
- Motion: 150–250ms ease; active states scale slightly.

## Components (key)
- Primary CTA (muted purple): bg `#79628c` / text `#ffffff` uppercase 14px/500–700 letter-spacing 0.2px / `1px solid #584674` / radius 13px / inset shadow `rgba(0,0,0,0.1) 0 1px 3px inset`. Hover → elevated shadow.
- White solid CTA: bg `#ffffff` / text `#1f1633` / 8px radius / 12px 16px. Hover bg→`#6a5fc1` text→white; focus bg `#ffb287` + `#6a5fc1` outline.
- Glass button: `rgba(255,255,255,0.18)` bg, `blur(18px) saturate(180%)`, 12px radius, white text.

## Do / Don't (anti-convention)
- Do: keep shadows purple-tinted and put an inset shadow on primary buttons so they feel pressed into the surface.
- Don't: use pure `#000000` or neutral gray borders — the blacks and borders are warm purple (`#1f1633`, `#362d59`); cold gray breaks the room.
- Don't: set body or UI text in Dammit Sans — it's hero-only; everything functional is Rubik.
- Don't: drop the uppercase + 0.2px tracking on buttons/labels, and never mix lime with coral/pink in one component.

## Example component prompts
- "Hero on `#1f1633`: headline 88px Dammit Sans weight 700, line-height 1.2, white. Sub-text 16px Rubik 400/1.5. White solid CTA 8px radius 12px 16px, hover bg `#6a5fc1`. Add an ambient glow `rgba(22,15,36,0.9) 0 4px 4px 9px` behind the hero."
- "Primary button: bg `#79628c`, `1px solid #584674`, inset shadow `rgba(0,0,0,0.1) 0 1px 3px`, white uppercase text 14px Rubik 700 letter-spacing 0.2px, radius 13px; hover shadow `rgba(0,0,0,0.18) 0 0.5rem 1.5rem`."
