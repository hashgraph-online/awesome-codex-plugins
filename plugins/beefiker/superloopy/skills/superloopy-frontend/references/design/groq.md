# Groq — Design Tokens (loopy-native)
> Category: ai-labs · Signature: single hot-coral on near-black, engineered for speed

## Signature & atmosphere
Groq looks like inference hardware feels: fast, hot, and stripped to essentials. The surface is near-black, the type is a tight technical grotesque, and one furnace-coral red does all the signaling — it's the color of velocity. The recognizable idea is monochrome + one hot accent, deployed with engineering restraint: no gradients, no glass, no decoration, just sharp geometry and the sense that something is happening at the speed of light. Coral on black reads "low latency" before a word is read.

## Color (hex · --var · role)
- `#0b0b0d` `--bg` — near-black canvas (cool-neutral, faintly blue-black); `#ffffff` for the inverted light marketing sections
- `#fafafa` `--fg` — primary text on dark (soft white); `#0b0b0d` text on light
- `#161618` `--card` — raised surface on dark; `#1f1f23` panel
- `#f55036` `--primary` — Groq coral-red; the singular accent — CTAs, active states, the wordmark, data highlights
- `#ff6b4a` `--accent` — lighter coral for hover/glow on the primary
- `#8b8b92` `--muted` — secondary text (cool gray); `#5c5c63` tertiary
- `rgba(255,255,255,0.1)` `--border` — hairline on dark; `#e4e4e7` border on light
- `rgba(245,80,54,0.12)` `--surface-accent` — faint coral wash behind highlighted metrics
- `#f55036` `--destructive` — shares the coral (or `#dc2626` if separation needed). Contrast: `#f55036` on `#0b0b0d` ≈ 5.1:1 — passes for large/bold text and borders; keep coral off small body copy, use `#fafafa`.

## Typography
- Stack: UI/display `"Söhne", "Inter", system-ui, sans-serif` (tight technical grotesque); code/metrics `"Söhne Mono", "JetBrains Mono", ui-monospace, monospace`. Mono is load-bearing — tokens/sec, latency numbers, model names live in mono.
- Display 64px / 600 / 1.05 / -1.5px · H1 44px / 600 / 1.10 / -1px · H2 30px / 600 / 1.15 · Body 16px / 400 / 1.55 · Mono-metric 14px / 500 / 1.40 (throughput figures) · Label 12px / 600 / 1.30 / +0.6px UPPERCASE
- Display goes weight 600 with aggressive negative tracking — the tightness reads as precision/speed. Uppercase tracked labels mark technical sections.

## Spacing, radius, depth, motion
- Base 8px; scale 4/8/12/16/24/32/48/64px; tight, grid-locked layouts.
- Radius scale 2 / 4 / 8px — sharp, near-square geometry; almost no pills. Hard corners signal hardware.
- Depth strategy: flat with hairline borders, no soft drop shadows; the only "glow" is a coral focus/active ring `0 0 0 1px #f55036` or a faint coral box-glow `0 0 24px rgba(245,80,54,0.25)` on the hero CTA. Depth = light/dark zone flip.
- Motion 100–160ms ease-out — deliberately fast (the brand is speed); counters/throughput numbers animate-up on view; no slow eases.

## Components (key)
- Primary CTA: bg `#f55036` / text `#0b0b0d` (black on coral for max punch) / padding 10px 20px / radius 4px / no border / hover lighten to `#ff6b4a` + glow `0 0 24px rgba(245,80,54,0.25)` / active inset / focus 2px coral ring. Secondary: transparent, 1px `rgba(255,255,255,0.1)`, `#fafafa` text.
- Throughput stat (signature): a huge mono number (e.g. `500` tokens/s) at 48–64px Söhne Mono weight 500 in `#fafafa`, the unit suffix in coral `#f55036`, sitting on `#0b0b0d` with a faint `rgba(245,80,54,0.12)` wash — the recurring proof-of-speed block.

## Do / Don't (anti-convention — name the wrong instinct)
- Do: keep it monochrome + one coral; render every metric/model name in mono; use sharp 2–4px radius and fast (≤160ms) motion; let coral mark only what's active or fast.
- Don't: add a second accent or a gradient — the wrong instinct is "AI brand = blue/purple gradient"; Groq is single-coral, no gradient. Don't soften corners to pills or add glass/blur — hardware reads as hard edges. Don't use slow, bouncy easing; the motion language must feel instant. Don't put coral on small body text (fails contrast); it's fills, borders, and large numerals only.

## Example component prompts
- "Hero on `#0b0b0d`: H1 Söhne 64px / weight 600 / -1.5px in `#fafafa`; one word or the unit in coral `#f55036`; coral CTA with black `#0b0b0d` text, 4px radius, glow `0 0 24px rgba(245,80,54,0.25)` on hover."
- "Throughput stat block: Söhne Mono 56px / 500 number in `#fafafa`, 'tokens/s' suffix in `#f55036`, faint `rgba(245,80,54,0.12)` wash, 4px radius, count-up animation on view (140ms)."
- "Section label: Söhne 12px / 600 / +0.6px uppercase in `#8b8b92`; hairline divider `rgba(255,255,255,0.1)`."
- "Secondary button on dark: transparent, 1px `rgba(255,255,255,0.1)`, `#fafafa` text, 4px radius, fast 120ms hover to coral border."
