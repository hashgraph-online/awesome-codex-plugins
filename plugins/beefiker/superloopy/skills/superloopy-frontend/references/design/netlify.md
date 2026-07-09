# Netlify — Design Tokens (loopy-native)
> Category: dev-tools · Signature: teal-to-cyan gradient on a clean canvas, with a glowing dark deploy console

## Signature & atmosphere
Netlify feels like the satisfying moment a deploy goes green — bright, fast, and friendly. The recognizable idea is the teal-cyan brand gradient (`#00ad9f` → `#00c7b7`/`#2ec4b6`) that arcs across logos, hero accents, and primary actions, set against an airy near-white canvas. Where the product gets serious — the deploy logs and console — it flips to a dark teal-tinted surface where that same cyan glows like a live build. Approachable jamstack optimism, not enterprise austerity.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page; `#f7f8f8` `--bg-subtle` — alternating section tint; `#13262f` `--bg-dark` — deep teal-slate console/dark mode
- `#14323b` `--fg` — primary text (dark teal-slate, not `#000`); `#9fb3bf` text on dark
- `#00ad9f` `--primary` — Netlify teal; CTA fill + brand signal; hover `#00897f`
- `#00c7b7` `--accent` — bright cyan; gradient end-stop, glow, link emphasis on dark
- `#2a47d6` `--link` — action blue/indigo for inline links on light (cool counterpoint)
- `#5c7480` `--muted` — secondary text; `#7e96a1` tertiary/placeholder
- `#cbd6db` `--border` — hairline on light; `#2a4a57` border on dark
- `#e60042` `--destructive` — alert pink-red; `#ffce00` warn; the teal itself signals success/deployed
- Contrast: muted `#5c7480` on white ≈ 4.8:1 (AA body). The teal gradient is decoration/CTA only — never run it under body text.

## Typography
- Stack: UI `"Pacaembu", "Mulish", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` (rounded, warm geometric for the friendly voice); code `"Roboto Mono", "JetBrains Mono", ui-monospace, monospace` for deploy logs.
- Display 64px/800/1.05/-1.5px · H1 40px/700/1.15 · H2 28px/700/1.25 · H3 20px/600/1.3 · Body 17px/400/1.6 · Body-sm 14px/400/1.5 · Label 12px/600/1.3/+0.3px UPPERCASE
- Display goes heavy (700–800) and friendly — the rounded face plus weight is the optimistic voice. Body sits roomy at 17px/1.6. Deploy-log text is monospace at 13–14px.

## Spacing, radius, depth, motion
- Base 8px; scale 4 · 8 · 16 · 24 · 32 · 48 · 64 (generous, marketing-paced). Section gaps 64–96px.
- Radius: 4px inputs · 8px buttons · 12px cards · 16px featured/media cards · pill for status badges.
- Depth strategy = soft shadows + the gradient glow. Cards lift with `rgba(20,50,59,0.08) 0 2px 8px, ... 0 8px 24px`. Hero/featured CTAs get a teal glow `0 0 32px rgba(0,199,183,0.35)` on dark. Focus ring `0 0 0 3px rgba(0,173,159,0.4)`.
- Motion 150–250ms ease-out; "deploying" states pulse the cyan; transform/opacity only.

## Components (key)
- Primary CTA: bg `#00ad9f` / text `#ffffff` / padding 10px 20px / radius 8px / no border / hover bg `#00897f` / focus `3px rgba(0,173,159,0.4)` ring. On dark, add teal glow.
- Secondary (teal-outline) button: bg `#ffffff` / text `#14323b` / `1px solid #cbd6db` / radius 8px / hover border `#00ad9f`, text `#00ad9f`.
- Deploy-status pill: pill radius, 12px/600 uppercase — teal `#00ad9f` "Published" / `#ffce00` "Building" / `#e60042` "Failed", with a leading dot.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: build the brand around the teal→cyan gradient (`#00ad9f`→`#00c7b7`) and let the same cyan glow on the dark console — one continuous color story across light marketing and dark product.
- Don't: substitute a flat single teal everywhere — the directional gradient (and its glow on dark) is the signature; a flat fill reads generic.
- Don't: go cold-gray or pure-black on the dark surface — it's a teal-tinted slate (`#13262f`); neutral black kills the brand warmth in the console.
- Don't: set the display in a stiff grotesque at weight 400–500 — Netlify's voice is the rounded face at 700–800; thin weights make it forgettable.

## Example component prompts
- "Hero on `#ffffff`: H1 64px Pacaembu weight 800, line-height 1.05, letter-spacing -1.5px, `#14323b`; subhead 20px/400 `#5c7480`. Primary CTA bg `#00ad9f` white text, 8px radius, 10px 20px, hover `#00897f`; secondary `1px solid #cbd6db`. A teal→cyan gradient `linear-gradient(135deg,#00ad9f,#00c7b7)` accent rule under the headline."
- "Deploy console on `#13262f`: log text 14px Roboto Mono `#9fb3bf`; a status pill `#00ad9f` 'Published' with leading dot and teal glow `0 0 32px rgba(0,199,183,0.35)`; section title 12px/600 uppercase `#7e96a1` +0.3px tracking."
