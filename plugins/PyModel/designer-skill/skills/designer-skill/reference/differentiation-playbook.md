# Differentiation Playbook

Positive creativity guide. Use **before** the ban-list in `avoid-ai-slop.md`. Slop rules say what to refuse; this file says how to be distinctive, intentional, and clean.

The bar: a viewer asks **"how was this made?"** — not **"which AI made this?"**

---

## The inverse test (run before any palette or layout)

Describe what you are about to build **the way a competitor would describe theirs**. If that sentence could appear on the category's modal landing page, restart.

| Category | Fails (category-modal) | Passes (specific) |
|---|---|---|
| Fintech | "Modern financial platform with secure payments and real-time insights" | "Ledger for freelancers who invoice from coffee shops — monospace amounts, receipt-paper texture, one brass accent" |
| AI tool | "AI-powered workflow that streamlines your creative process" | "Batch editor for podcast producers — waveform scrubber hero, dark booth lighting, lime peak meters only on active tracks" |
| Restaurant | "Farm-to-table dining experience in the heart of the city" | "Neapolitan counter service — hand-stretched dough photo, flour dust on charcoal, one red napkin stack" |
| Dev tool | "Developer platform built for modern teams" | "API debugger for solo backend devs — request timeline as the hero, terminal green on success states only" |
| Portfolio | "Creative professional showcasing bold work" | "Motion designer's reel-first site — full-bleed case studies, project titles at 8vw, no feature grid" |

**Second-order trap:** avoiding the obvious palette but landing on the obvious *alternative* (editorial serif + mono labels for a non-editorial AI tool). If category + anti-reference still predicts the look, rework.

---

## One weird thing (brand surfaces)

Every brand surface earns **exactly one** unexpected element that serves the brief — not random decoration:

- An asymmetric crop on the hero image
- One section that breaks the grid (full-bleed pull quote, horizontal scroll rail)
- A typographic move (oversized figure, mono telemetry band, single word at 12vw)
- One material texture (paper grain, scanlines, noise) scoped to one zone
- One color commitment (drenched section, accent-only nav)

If you cannot name the weird thing in one sentence, you do not have one yet.

---

## Layout innovation menu

Pick **≥2 different families** per page; never repeat the same family three times in a row.

| Family | When to use | Example |
|---|---|---|
| **Asymmetric bento** | Feature density without equal cards | Mixed cell sizes, hairline gutters |
| **Zig-zag narrative** | Story-led marketing | Image left / text right, then flip; max 2 consecutive |
| **Horizontal scroll rail** | Many peers of equal weight | Case studies, logos, product shots |
| **Single-purpose viewport** | One decisive message | Full-screen statement, one CTA |
| **Split asymmetric** | Hero with real visual weight | 60/40 or 70/30, not 50/50 |
| **Masonry / staggered** | Gallery, portfolio, mixed content | No identical row heights |
| **Scroll-pinned chapter** | Long-form brand story | One panel pins while copy advances |
| **Dense telemetry band** | Data, specs, proof | Monospace cluster + vast whitespace frame |

**Product register:** familiarity over surprise — use **one** layout family per view; innovate inside components, not page structure.

---

## Typographic surprise (without reflex faces)

1. **Scale jump:** 3×–5× between display and body, not 1.5×.
2. **Weight contrast:** 900 vs 400, or 200 vs 600 — not 600 vs 400.
3. **Mono as instrument:** telemetry, metadata, or one hero word — not lazy "technical" shorthand.
4. **Measure as layout:** narrow column (45ch) beside wide visual — not centered everything.
5. **Font procedure:** three physical-object words → reject reflex list → browse real catalogs → cross-check (see `aesthetic-systems.md` brand-identity).

---

## Named reference procedure

Before coding, name **2–3 real sites or products**. Extract **one move each** — not the layout wholesale:

- **Move types:** hierarchy trick, spacing rhythm, nav shape, color dosage, motion vocabulary, imagery crop, type pairing
- **Not moves:** "clean design", "nice typography", "good spacing"

Example: *"Stripe — restraint: accent ≤10% on white; Klim — one word at display scale carries the page; Linear — sidebar as second neutral layer, not a bordered box."*

Filter references through anti-slop: if the reference itself is category-modal, pick a deeper reference.

---

## Physical scene → forces decisions

One sentence: **who, where, light, mood.** It must force light vs dark and tone without you choosing by default.

- *"Solo founder reviewing metrics at 6am in a dim apartment"* → dark, quiet, mono accents
- *"Shop owner on a bright tablet at the counter"* → light, high contrast, large touch targets
- *"Guest booking a table on phone outside at dusk"* → warm dark hero, legible type, one warm accent

If the sentence does not change your palette or layout, rewrite it with more physical detail.

---

## Imagery as differentiation

When the brief implies visuals, **zero images is a bug**, not restraint.

1. Search for the **physical object**, not the category ("hand-cut pasta on scratched wood" not "Italian food").
2. **One decisive photo** beats five mediocre ones.
3. Alt text is voice ("Coastal fettuccine, hand-cut, terrace service" not "pasta dish").
4. Imagery includes screenshots, data-viz, SVG, canvas — not only photos.

---

## Product register: trust over distinctiveness

Inside apps, **earned familiarity** is the bar. Innovate in:

- State clarity (loading, error, empty — all designed)
- Semantic color (accent = action only)
- Second neutral layer (sidebar vs content without border soup)
- Motion that confirms action (150–200ms, reduced-motion alternative)

Do not import brand-register moves (full-bleed hero, editorial serif H1, scroll choreography) into dense product UI.

---

## Pre-code checklist (positive)

- [ ] Inverse test passed — competitor description is not category-modal
- [ ] Physical scene written — forces light/dark and tone
- [ ] One aesthetic system committed — whole surface, one language
- [ ] ≥2 layout families chosen (brand) or one clear product pattern
- [ ] 2–3 named references with one extracted move each
- [ ] One weird thing named in one sentence (brand only)
- [ ] Typography direction: pairing + scale ratio ≥1.25

Then load task-specific refs via `dispatch_intent`. Run `review_and_gate` before declaring done.
