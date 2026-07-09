# Anti-Slop Rules

Generic AI UI is recognizable because models converge on the same defaults and ship them unseen. This file converts "taste" into rules a model can self-audit against: each rule **names the default, bans it, and gives a concrete replacement plus an override path**. Phrase every limit as binary (`zero`), never graduated (`sparingly`) — models honor a hard zero and quietly defeat "use sparingly".

## Named-default bans

Each ban: the signature → why it's a tell → what to do instead. Override only when the brand genuinely demands it (state the reason).

- **AI-purple / glow (the LILA tell)**: purple→blue gradients, glowing mesh backgrounds. The #1 visual tell. → Pick a committed accent from the DESIGN.md palette (emerald, electric blue, deep rose, amber) and use it once, consistently. Override: brand color is genuinely violet.
- **Inter/Roboto by default**: the most-tested typographic tell. → Choose a deliberate stack per the Design Read (e.g. Geist, Satoshi, Cabinet Grotesk, a real serif with intent). Override: existing brand ships Inter.
- **Premium beige + brass palette**: `#f5f1ea`/`#f7f5f1` backgrounds with `#b08947`/`#b6553a` accents and espresso text — the "premium consumer" cliché that makes every such site look identical. → Use a distinct committed palette (cold luxury, forest, cobalt+cream, terracotta+slate). Don't reuse the same family twice in a row.
- **True black + one generic shadow**: `#000000` text and a single flat `box-shadow` everywhere. → Use the DESIGN.md foreground token (near-black, not pure) and a multi-level, optionally tinted elevation ladder.
- **Glassmorphism on everything / three equal feature cards / centered hero on dark mesh**: the default landing composition. → Vary composition; above `DESIGN_VARIANCE` 4, avoid the symmetric three-card row and the centered hero.

## Countable rules (verify by counting, no judgment needed)

- **Em-dash: zero.** No `—` or separator `–` anywhere visible (headlines, body, captions, buttons, alt text). A single one = fail. Rewrite with commas, periods, or parentheses.
- **Eyebrow restraint**: count uppercase tracked labels across sections; if `count > ceil(sectionCount / 3)`, fail.
- **Zigzag cap**: the 3rd consecutive image+text split row = fail. Break the pattern.
- **Bento integrity**: N items → exactly N cells, no empty filler cell.
- **Layout-family variety**: 8 sections must use ≥4 distinct layout families; reject if one composition anchor repeats 3+ rows.

## Consistency locks (one decision holds page-wide)

- **Color lock**: one accent everywhere — a warm-grey site does not get a blue CTA in section 7.
- **Shape lock**: one corner-radius scale across all components.
- **Theme lock**: no section inverts light/dark mid-page (a lone dark section reads as a copy-paste accident).
- **One system lock**: one palette, one icon family, one type system, one component library per project.

## Real-asset mandate

- **No div-based fake screenshots** — the strongest "AI-made wireframe" tell. Use a real image, a real source, or a clearly-labeled placeholder slot.
- **Real SVG logos** for logo walls (not styled text wordmarks); **icon libraries** (Phosphor, Radix, Tabler, Lucide), never hand-rolled decorative SVG paths.
- Even minimalist pages need real imagery — a pure-text page is incomplete work, not minimalism.

## Copy self-audit (slop prose is as strong a tell as slop visuals)

Re-read every visible string before shipping. Ban:

- AI clichés: *Elevate, Seamless, Unleash, Delve, Empower, Supercharge*.
- "Quietly trusted by…" / performative-craftsman labels (*Field notes, From the field*).
- Generic names (*John Doe*), placeholder brands (*Acme*).
- Fake-perfect stats (`99.99%`) — prefer organic figures (`47.2%`) or omit. No fake-precise spec numbers unless real or labeled mock.

## Micro-tell catalogue (small details that collectively scream "AI")

Banned by default (narrow override only): version labels in the hero (`v0.6`, `BETA`), section-number eyebrows (`00 / INDEX`, `001 Capabilities`), middle-dot overuse, decorative status dots, br-broken italicized headlines, vertical rotated text, fake version footers (`v1.4.2 · last sync 4s ago`), weather/locale strips (`LIS 14:23 18°C`), pills overlaid on images, fake photo-credit captions, generic step labels (`Stage 1/2/3`).

## Pre-Flight checklist (run before declaring done; any unticked box = not done)

- [ ] Zero em-dashes anywhere visible.
- [ ] Eyebrow count ≤ `ceil(sectionCount / 3)`.
- [ ] No AI-purple/glow default (or brand-justified).
- [ ] Non-default, deliberate font stack.
- [ ] No banned premium beige+brass palette as default.
- [ ] Color / shape / theme consistency locks hold across all sections.
- [ ] ≥4 layout families across the page; no anchor repeats 3+ rows.
- [ ] No div-based fake screenshots; real or generated imagery; real SVG logos.
- [ ] Copy passed the self-audit (no clichés, no fake-perfect numbers, no placeholder names).
- [ ] No micro-tells from the catalogue.
- [ ] Motion claimed = motion implemented (transform/opacity/filter only); reduced-motion respected.
- [ ] Every color/size/spacing/radius/shadow traces to a DESIGN.md token; no orphan hex, no magic spacing.
- [ ] All interactive states (hover/active/focus/disabled) and empty/loading/error states handled.
- [ ] No horizontal scroll at 390 / 768 / 1280 px.
