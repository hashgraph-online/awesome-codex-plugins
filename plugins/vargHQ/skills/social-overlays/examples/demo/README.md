# social-overlays demo

The preview video for the `social-overlays` card on varg.ai/how-to: four overlays from this skill, each over a calm
generated "footage" plate inside a 9:16 phone panel, with the universal 9:16 safe box drawn once at the start.

| Time | Template · preset | What it shows |
|---|---|---|
| 0.0–3.4 s | `cta-pill-pop · floating-pill` | Safe box draws on (x 120–888, y 288–1248, x ≤ 780 below y 840), then the pill pops in at centre (450, 1120): 0.35 s `back.out(1.7)`, scale 0.6 → 1, label rises 12 px at +0.08 s, arrow nudges +8 px at +1.2 s, exit 0.25 s Material accelerate. An "AD" disclosure chip sits next to the pill |
| 3.4–7.2 s | `follow-tap-prompt · tiktok-style` | Dark card (#000 @70%, 720×176, radius 32), finger dot taps Follow (#FE2C55, 200×72, radius 36): press 1 → 0.94 in 3 f, release 4 f `back.out(1.7)`, ripple 0 → 2.2× in 0.4 s, flip to "Following" with a 0.2 s cross-fade and 8 px label slide, finger parks 40 px below the button |
| 7.2–11.5 s | `review-proof-card · app-store-style` | White card, radius 36, padding 44; stars sweep over 0.6 s `power2.out` to a fractional 4.6 (house gold #FFB400 over #D1D1D6) while the score counts in sync; quote 40 px/500, ≤ 34 characters a line |
| 11.5–15.0 s | `live-badge · instagram-style` | Gradient pill (#DD2A7B → #F58529) at (120, 312), 56 px tall, label 30 px/800 +4% tracking, 14 px dot pulsing on a 1.0 s period; viewer chip (#000 @45%) ticks on a seeded schedule (mulberry32(42), every 0.9–1.4 s, +0.3–2%), shown as 3 significant figures: 1.18K → 1.19K → 1.21K, digits rolling 8 px in 0.2 s |

1920×1080, 30 fps, 15 s, silent. Every value comes from `assets/presets/*.json` and the "Timing and numbers" of each
reference; motion uses the shared tokens in `references/platform-safe-zones.md` (enter `cubic-bezier(0.05,0.7,0.1,1)`,
exit `cubic-bezier(0.3,0,0.8,0.15)`, implemented as a small bezier ease in each scene).

## Render

```bash
cd social-overlays/examples/demo
PATH=$HOME/.nvm/versions/node/v22.19.0/bin:$PATH npx --yes hyperframes@0.8.206 check
PATH=$HOME/.nvm/versions/node/v22.19.0/bin:$PATH npx --yes hyperframes@0.8.206 render -o social-overlays.mp4 --fps 30 --crf 20
```

`npx hyperframes preview` opens it in the Studio for editing. Copy (CTA label, name, handle, quote) is exposed as
composition variables.

## Content and credits

- The review, reviewer ("Jo Rivera"), date, rating and viewer count are **invented for this demo** and labelled on
  screen ("SAMPLE", "invented sample", "illustrative count"). A real ad must use real, permissioned reviews and real
  counts (FTC 2024 rule, see the skill's Gates).
- "Northwind" is an invented brand. No platform logos; the "-style" presets are generic look-alikes by colour and shape.
- Backgrounds are hand-drawn SVG gradients (no footage).
- Fonts: Inter and JetBrains Mono (OFL, bundled with HyperFrames); TikTok Sans 400/700 Latin subset (OFL, Google
  Fonts) in `assets/fonts/`.

## Deviations

- The 9:16 overlays are shown inside a 16:9 frame as a centred 540×960 phone panel: each scene lays out on a
  1080×1920 canvas at the presets' pixel values and is scaled 0.5, so on-screen text is half the preset size.
- Holds are shorter than the 4–6 s template lengths so four presets fit in 15 s: each keeps its enter/exit timings
  and the minimum readable hold (CTA 1.85 s settled ≥ 1.5 s; review card 3.3 s ≥ 3.0 s; follow 1.8 s after the flip,
  under the 2.5 s the reference asks for).
- `follow-tap-prompt`: the card sits at x 144–864, centre y 740, not the default centre y 1080 (see preset problems
  below). The "Following" fill (white @16%) is a house value; the preset does not give one.
- `review-proof-card`: the card is 768 px wide (the full safe box), not 840 px, and sits at y 300 so it stays above
  y 840.
- `live-badge`: the badge leaves at 3.25 s of its 3.5 s slot (the preset's 0.2 s exit) instead of at 5.7 s.

## Preset problems found

- `follow-tap-prompt`: card 720 px wide at default centre y = 1080 (56%) breaks the skill's own safe-box rule: below
  y 840 content must stay at x ≤ 780, which leaves 660 px (x 120–780). Fix: default centre y ≤ 752 (card above
  y 840, x 144–864) or card width ≤ 660 px when it sits below y 840.
- `review-proof-card`: card width 840 px is wider than the 768 px universal safe box (x 120–888). Fix: 768 px max
  (and ≤ 660 px if any of the card falls below y 840).
