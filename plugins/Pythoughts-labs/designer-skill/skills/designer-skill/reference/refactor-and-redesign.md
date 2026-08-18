# Refactor & Redesign

Improve EXISTING UI without breaking it. Presentation changes only; behavior stays identical unless the user asked otherwise. Work with the current stack — never migrate frameworks or styling libraries.

## 1. Audit the current state

Inspect before you touch. Capture:

- **Screenshots** at 375 / 768 / 1440px (the breakpoints you'll re-verify against).
- **Existing design tokens / CSS / components** — find the token source (CSS vars, theme file, Tailwind config), the class system, shared component imports.
- **Framework & build pipeline** — read `package.json`; note styling method (Tailwind v3 vs v4, vanilla CSS, CSS-in-JS); never assume.

Score each dimension **0–4** (0 = absent/broken, 2 = partial, 4 = excellent). Criteria for visual/type/color/spacing/hierarchy come from `design-principles.md`; AI-slop tells from `avoid-ai-slop.md`; motion from `motion-and-interaction.md`; a11y/responsive from `engineering-and-performance.md`.

| # | Dimension | What to check |
|---|-----------|---------------|
| 1 | Visual hierarchy | One clear focal point per view; primary > secondary > muted. See `design-principles.md`. |
| 2 | Typography | Font has character (not Inter-by-reflex); body ~65ch; weights beyond 400/700; tracking on display. `design-principles.md` |
| 3 | Color / contrast | One accent, saturation <80%, off-black not `#000`; text ≥4.5:1 (AA), 7:1 (AAA). `design-principles.md`, `engineering-and-performance.md` |
| 4 | Spacing rhythm | Consistent scale, no random 13px gaps; generous whitespace. `design-principles.md` |
| 5 | Motion | Interactive elements transition 200–300ms; no layout-property animation. `motion-and-interaction.md` |
| 6 | A11y | Focus rings, keyboard path, alt text, semantic HTML, labels. `engineering-and-performance.md` |
| 7 | Responsiveness | 375/768/1440 hold; touch targets 44×44px; no horizontal scroll. `engineering-and-performance.md` |
| 8 | AI-slop tells | Count distinct tells (see §2). `avoid-ai-slop.md` |
| 9 | IA / flow-shape drift | Progressive-disclosure parity with neighboring features; multi-step flows match the shape of comparable flows (modal vs page, inline vs route); same conceptual weight = same visual weight; consistent naming (a "Workspace" here isn't a "Project" elsewhere). `engineering-and-performance.md` |

Total /36. Below ~22 = significant work; below ~14 = major overhaul. Record findings before editing — the audit is the work plan.

This table scores the visual/technical layer. The UX-heuristics layer — Nielsen rubric, persona walk-throughs, cognitive load — lives in `command-playbook.md`'s scored review protocol; run it alongside this audit, don't duplicate it here.

## 2. Diagnose generic patterns

Run the full ban-list in `avoid-ai-slop.md` against the live UI. Highest-frequency offenders to find first:

- **Purple/blue "AI gradient"** — the single most common fingerprint.
- **Three identical card columns** as the feature row.
- **Eyebrow label on every section** ("OUR FEATURES", small-caps over each block).
- **Cream/sand background** as the default safe canvas.
- **Inter (or browser default) everywhere** — chosen by reflex, not intent.
- **Fake content** — "John Doe", "Acme Corp", round numbers (`99.99%`, `$100.00`, `50%`), Lorem Ipsum, same avatar repeated, identical dates.
- **Copy clichés** — Elevate, Seamless, Unleash, Next-Gen, Game-changer, Delve, Tapestry, "In the world of…".

Replace fakes with organic data (`47.2%`, `$99.00`, real-sounding names, varied dates). The complete cross-register tell list and the output-completeness contract live in `avoid-ai-slop.md` — use it as the authority.

## 3. The redesign loop (don't break functionality)

Change presentation surgically, one concern at a time, re-verifying after each change.

**Preserve these contracts — do not alter:**
- Markup/DOM structure that JS or tests query (tag names, IDs, hook classes).
- `data-*` attributes, `aria-*` attributes, roles.
- Event handlers, `onClick`/listeners, form `name`/`action`.
- Route definitions, state shape, store keys.

**Migrate toward a target aesthetic incrementally** — pick one system from `aesthetic-systems.md` (Minimalist / Brutalist / Soft / High-end-Stitch / Brand-identity) and move toward it; never rewrite wholesale. Apply changes in this priority order (highest visual gain, lowest risk first):

1. **Font swap** — biggest instant lift, lowest risk.
2. **Color cleanup** — collapse to one accent, desaturate (<80%), off-black (`#0a0a0a`/`#121212`) not `#000`.
3. **Hover / active states** — makes it feel alive (see `motion-and-interaction.md`).
4. **Layout & spacing** — grid, max-width container (~1200–1440px), consistent padding.
5. **Replace generic components** — swap the three-card row, the 3-tower pricing table, the sun/moon toggle for less default patterns.
6. **Loading / empty / error states** — in scope. Empty states come in five types, each needing different treatment: **first-use** (sell the value, give a starting CTA), **user-cleared** (acknowledge the win, suggest what's next), **no-results** (help refine the query), **no-permission** (explain who to ask), **error** (what happened + how to recover). Anatomy and copy live in `command-playbook.md`'s onboard kit; engineering coverage in `engineering-and-performance.md`.
7. **Type scale & spacing polish** — the premium final touch.

Match existing conventions: reuse the project's token names, class system, and framework idioms. Centralize new values as tokens rather than scattering literals (`engineering-and-performance.md`). Before importing any library, check `package.json`; before editing Tailwind config, confirm v3 vs v4. Keep each diff small and reviewable.

## 4. Surgical-change discipline

| Do | Don't |
|----|-------|
| Touch only what the redesign requires | Refactor adjacent code that isn't broken |
| Match existing style even if you'd do it differently | Rename, reformat, or restructure unrelated code |
| Remove imports/vars/CSS *your* change orphaned | Delete pre-existing dead code (mention it instead) |
| Prefer additive changes (new class, new variant) | Destructive rewrites of working markup |
| Feature-flag risky visual changes for easy rollback | Ship a big-bang restyle with no off-switch |
| Verify before/after behavior is identical where the change is cosmetic | Assume a CSS-only change can't break JS that reads layout |

Every changed line should trace to a specific audit finding. If you can't explain why a line changed, revert it.

## 5. Image / reference-to-code workflow

When given a screenshot or design reference, analyze deeply **before** writing code — treat the image as a spec, not a vibe.

1. **Extract the design system** — layout structure, spacing rhythm, type scale & weights, palette (background/panel/accent/text), button shapes & hierarchy, radius logic, motion cues. Pull readable text verbatim (headline, subhead, CTA labels).
2. **Reproduce section-by-section**, preserving the source's layout logic, spacing, and ordering. Don't drift into a generic coded layout — the result must look like the same design, not "inspired by" it.
3. **Generate or verify real assets** — never invent image IDs or paths that resolve to broken placeholders. Use a reliable source when real assets are absent: `https://picsum.photos/seed/{name}/1920/1080`. Every meaningful image needs real `alt` text.
4. **Compare built result against the reference at each breakpoint** (375/768/1440). Where the source is ambiguous, preserve its language/spacing/component family before falling back to defaults.

**Self-generate a target when none is provided, if useful:** for a visually-led task with no reference, produce clean design images first, analyze them, then build to match. Run the probes in this order:

1. **Palette artifact first** — one small image: the type pairing on the chosen background, primary + accent swatches, one signature motif. Confirm direction before generating anything bigger.
2. **1–3 mocks that differ in STRUCTURE** — hierarchy, topology, density, composition — never in color or motif (those were locked by the palette artifact). One readable image per section — don't crop sections out of one compressed board. Keep heroes calm: short headline (1–3 lines), one focal point, no nested boxes, no filler pills/fake system labels.
3. **Mock-fidelity inventory before building** — list the approved mock's major visible ingredients (hero silhouette, signature motifs, nav/CTA treatment, second-fold section sequence, image-native content) and assign each an implementation route: semantic HTML/CSS/SVG, generated raster, sourced raster, icon library, canvas/WebGL, or accepted omission. The mock is a north star, not a screenshot to trace — but if the live result is missing the mock's major ingredients, the implementation is wrong.

**Asset rule:** if CSS will own the radius, clipping, shadow, borders, or captions, don't bake them into the bitmap — and strip baked UI text out of rasters. When image generation is unavailable, announce the skip in one line and treat the brief as the only visual reference. Probes test direction — they are never the final UX, copy, or a11y specification. Image direction details: `aesthetic-systems.md`.

## 6. Generating variants of existing UI

When asked for design alternatives on an existing surface ("show me 3 options for this hero"), the wrong frame is "three different design directions" — the brand is already chosen. The job is variation **within identity**.

### Phase A — lock the identity (non-skippable)

Read DESIGN.md if present; else the CSS custom properties; else computed styles; else sibling components. Write **one sentence** recording:

- Dominant surface + accent color — actual values or token names, never adjectives like "warm".
- The actual loaded font names.
- Layout topology (stacked / side-by-side / grid / asymmetric / overlay).
- Surface treatment (corners, borders, shadows, decoration density).
- Copy voice.

No aesthetic-family adjectives ("editorial-leaning", "brutalist") — those are conclusions, not data, and they collapse the lock into self-fulfilling prophecy. Can't extract a real value for an axis? Skip the axis rather than fabricate. This sentence is the **identity lock**: every variant must read as the same brand side by side.

### Phase B — pick the mode

- **Default mode** (~90% of cases) preserves the identity.
- **Departure mode** only when the project's anti-references call out *this specific surface* as the failure, or the user explicitly asks ("rebuild from scratch", "something completely different").

The cost is asymmetric: a wrong default is recoverable (the user picks none and you retry); a wrong departure is unrecoverable (off-brand work, trust burned). Unsure = default mode.

### Phase C — three variants on three DIFFERENT primary axes

**Default mode** — pick three distinct axes from: hierarchy / layout topology / typographic system *within the available faces* / color dosage *with existing palette tokens* / density / structural decomposition (merge, split, progressive disclosure).

**Departure mode** — derive directions from the brand-personality words via physical/material referents, never from a fixed lane catalog: reaching for Swiss-grid / Terminal / Industrial-signage every time is itself the training-data reflex. Each direction must be expressible as one sentence naming a real-world referent — "a museum exhibition label system", not "clean and minimal" (adjectives-only means not concrete).

Per-verb axes, so three variants never collapse into one idea:

| Verb | The three variants differ by |
|------|------------------------------|
| bolder | scale / saturation / structure — never three "slightly bigger" |
| typeset | a different pairing AND a different scale ratio each |
| colorize | a different hue family each |
| layout | a different structural arrangement — not spacing tweaks |
| adapt | a different target context each |
| animate | a different motion vocabulary (cascade stagger / clip wipe / scale-and-focus / morph / parallax) |
| delight | a different flavor (micro-interaction / typographic surprise / illustrated accent / sonic moment / easter egg) |
| overdrive | a different convention broken |

### Phase D — squint tests before presenting

**Default mode:** any variant that drifted the palette, type voice, or rhetoric crossed into departure by accident — rework it. Three "tighter density" variants = failure.

**Departure mode:** run the **family pass** — label each variant with one concrete noun of your own (exhibition, storefront, cockpit, playbill); two sharing a label = rework. Then the **sentence pass** — write the three one-liners side by side; if two rhyme, rework the offender. When the axis is color/theme, the trio must not share theme + dominant hue — two-dark-plus-one-dark is not three color worlds.

**A freeform prompt is a ceiling, not a script.** The user's words bound the direction but still earn three meaningfully different *interpretations*: "more confident" → v1 amplifies hierarchy, v2 commits the existing accent harder, v3 tightens density — three axes, same brand. On conflict, the project's anti-references beat the prompt.

## 7. Documenting the design system (DESIGN.md)

Capture an existing project's visual system in a root `DESIGN.md` so later work — yours or another agent's — stays on-brand.

**Scan order:** CSS custom properties (`--color-`, `--font-`, `--spacing-`, `--radius-`, `--shadow-`, `--ease-`, `--duration-`) → Tailwind `theme.extend` → CSS-in-JS theme files → token JSON → the main button/card/input/nav/dialog components (variant APIs + defaults) → the global stylesheet → live computed styles from rendered output.

**Structure:** machine-readable token frontmatter, then six prose sections — Overview, Colors, Typography, Elevation, Components, Do's and Don'ts.

**Named Rules.** Each section carries 1–3 rules in the shape "**The [Name] Rule.** [short, forceful doctrine]" — e.g. "The One Voice Rule. The primary accent appears on ≤10% of any screen. Its rarity is the point." Named rules are memorable and citable, and stick far better with AI consumers than bullet lists.

**One-sentence audit tests.** "If it looks like a 2014 app, the shadow is too dark and the blur is too small." A sentence-length test beats a paragraph of principle.

**Style:** descriptive over technical — "gently curved edges (8px)", not "rounded-lg" — with exact values in parentheses; functional over decorative (where and why per token, not just what); forceful design-director voice ("prohibited", "never", "always" — not "consider" or "might"). Carry every PRODUCT.md anti-reference into the Don'ts **verbatim**, so the visual spec enforces the strategic line.

**Pitfalls:**

- Don't extract every token — stop at what's actually reused; one-offs pollute the spec.
- Don't invent components that don't exist in the codebase.
- Don't overwrite an existing DESIGN.md without asking.
- Don't duplicate a value in two places — the token layer is normative.

**Seed mode** (pre-code projects with nothing to scan): ask five questions — color strategy plus one hue/anchor, typography direction (serif+sans / single sans with a feel / display+mono / mono-forward / script+sans), motion energy (restrained / responsive / choreographed), three named references, one named anti-reference — then write a clearly-marked seed scaffold with honest placeholders. Never fabricate tokens.

## 8. Redesign checklist

Run before declaring done:

- [ ] **Functionality intact** — handlers fire, routes work, forms submit, state persists; behavior identical where the change was cosmetic.
- [ ] **DOM/ARIA/`data-*` contracts unchanged** (or changed deliberately and verified).
- [ ] **No new slop tells** — re-scan against `avoid-ai-slop.md`; no AI gradient, three-card reflex, fake content, banned copy.
- [ ] **Contrast verified** — text ≥4.5:1 (AA); no gray text on colored backgrounds (`design-principles.md`).
- [ ] **Responsive at 375 / 768 / 1440** — no overflow; touch targets ≥44×44px.
- [ ] **Motion respects reduced-motion** — transitions 200–300ms, ease-out (quart/quint/expo), never bounce/elastic; animate `transform`/`opacity` only (`motion-and-interaction.md`).
- [ ] **Tokens centralized** — new values are tokens, not scattered literals; no hard-coded colors (`engineering-and-performance.md`).
- [ ] **Orphans removed** — only those *your* change created; pre-existing dead code left alone (flagged, not deleted).

```css
/* Reduced-motion: always include */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

```css
/* Full-screen sections: dvh, not vh (avoids iOS Safari jump) */
.section { min-height: 100dvh; }      /* not height: 100vh */
/* Press feedback */
.btn:active { transform: scale(0.98); }   /* or translateY(1px) */
/* Flex/grid children that hold long text must allow shrink */
.flex-item, .grid-item { min-width: 0; }
/* Long text */
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.balance  { text-wrap: balance; }     /* headings */ /* body: text-wrap: pretty */
```

For the intent→verb dispatch (which redesign operation to run for a given request), see `command-playbook.md`.
