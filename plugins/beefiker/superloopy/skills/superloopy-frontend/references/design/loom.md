# Loom — Design Tokens (loopy-native)
> Category: productivity/saas · Signature: warm coral-to-purple gradient, recording-bubble friendliness

## Signature & atmosphere
Loom feels like a quick, warm hello recorded just for you — async video made casual and human. The recognizable idea is its sunset-leaning gradient (coral/orange into purple) paired with the circular camera-bubble motif, so the brand reads personable rather than corporate. Surfaces are clean and white to let video thumbnails carry the color, while the chrome stays soft, rounded, and a touch playful.

## Color (hex · --var · role)
- `#ffffff` `--bg` — page background; `#1a1a2e` `--fg` — foreground (deep blue-charcoal, not pure black)
- `#625df5` `--primary` — Loom indigo/violet; primary buttons, links, brand chrome
- `#4f4ad6` `--primary-active` — pressed violet
- `#fa5d5d` `--accent-coral` — record-dot / warm accent; the camera-bubble energy
- gradient `--brand-gradient` — `linear-gradient(120deg, #fa5d5d 0%, #625df5 100%)` (coral → violet); hero washes + the recording bubble ring
- `#6f6f8d` `--muted` — secondary text (~5.3:1 on white, AA)
- `#9a9ab0` `--placeholder` — placeholder/timestamps
- `#e6e6ef` `--border` — light hairline divider
- `#f5f5fa` `--muted-surface` — alternating band / panel fill
- `#1a8245` `--success` · `#d93030` `--destructive` — status hues

## Typography
- Stack: `"Inter", "GT Walsheim", -apple-system, system-ui, sans-serif` — clean geometric-humanist; intent is approachable and modern, never stiff.
- Display 60/700/1.08/-1.5px · H1 44/700/1.12/-0.75px · H2 32/600/1.20 · CardTitle 20/600/1.25 · Body 18/400/1.55 · BodySm 16/400/1.50 · Nav 15/600/1.30 · Label 12/600/1.33/+0.3px (uppercase eyebrows)
- Display is bold (700) and tightly tracked; the warmth comes from gradient + rounded geometry, not from the type weight.

## Spacing, radius, depth, motion
- Base 8px (4px micro); scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 80px; section gaps 64–96px.
- Radius: 8px inputs · 10px buttons · 16px cards · 20px feature media · 9999px pills + the camera bubble (always a perfect circle).
- Depth strategy: **soft single shadows + light borders**. Card `0 2px 12px rgba(26,26,46,0.08)`; hover `0 8px 28px rgba(26,26,46,0.12)`; the recording bubble gets a gradient ring + soft glow. No harsh elevation.
- Motion 150–250ms ease-out; play-button + bubble pulse/scale on hover; transform/opacity only.

## Components (key)
- Primary CTA: bg `#625df5` / text `#ffffff` / padding 12px 20px / radius 10px / no border / weight 600. Hover → `#4f4ad6`; active → darken + `scale(0.98)`; focus → 3px `rgba(98,93,245,0.3)` ring.
- Recording bubble: perfect circle (9999px), gradient ring `linear-gradient(120deg,#fa5d5d,#625df5)`, coral record-dot `#fa5d5d`, soft glow shadow — the brand's hero motif.
- Video card: white bg, 16px radius, soft shadow, 16:9 thumbnail, play overlay, title 20px/600, hover lifts.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: lead with the coral→violet gradient (`#fa5d5d → #625df5`) and the circular camera-bubble motif; keep the recording bubble a true circle with a gradient ring.
- Don't: render Loom as a flat single-violet enterprise tool — the warm coral and the gradient are what make it feel human and async-casual; dropping the coral kills the personality.
- Don't: square off the camera bubble or use hard drop shadows — the perfect circle + soft glow is the signature. Avoid pure `#000`/`#fff` ink; the deep blue-charcoal `#1a1a2e` keeps it warm.

## Example component prompts
- "Hero on `#ffffff` with faint coral→violet wash: H1 Inter 44px / weight 700 / 1.12 / -0.75px in `#1a1a2e`; subhead 18px/400/1.55 in `#6f6f8d`; violet CTA `#625df5`, white text 600, 10px radius, 12px 20px padding, hover `#4f4ad6`."
- "Recording bubble: 96px perfect circle, gradient ring `linear-gradient(120deg,#fa5d5d,#625df5)`, coral record-dot `#fa5d5d`, soft glow `0 8px 28px rgba(98,93,245,0.25)`."
- "Video card: white bg, 16px radius, shadow `0 2px 12px rgba(26,26,46,0.08)`, 16:9 thumbnail with play overlay, title 20px/600 in `#1a1a2e`, hover `0 8px 28px rgba(26,26,46,0.12)`."
