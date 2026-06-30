---
name: designer-skill
description: Plug-and-play MCP for UI superpowers. Use when building, designing, redesigning, refactoring, polishing, auditing, or enhancing any web or app user interface — landing pages, marketing sites, dashboards, product UI, components, forms, or design systems. Use when an interface looks generic or "AI-made", or needs better typography, color, spacing, layout, hierarchy, motion, accessibility, or performance. For any coding agent doing frontend visual work. Not for backend logic, data pipelines, CLI tools, or non-UI code.
---

# designer-skill

A plug-and-play MCP that gives your agent UI superpowers: design, refactor, and ship interfaces that don't look AI-made.

**Foundation:** Brief by default → commit direction before code → deep refs on demand → deterministic gate before done.

This file is the router. Substance lives in fifteen reference files under `reference/`; load them on demand via MCP — do not work from memory.

## MCP workflow (every UI task)

When the **designer-skill** MCP server is connected:

1. **`get_preflight_brief`** — compact binding rules (~500 tokens). Call first.
2. **`commit_design_direction`** — declare register, aesthetic, physical scene, layouts, type direction, anti-slop risks, inverse test. Must **PASS** before code.
3. **`load_project_context`** — PRODUCT.md / DESIGN.md when present. If `NO_PRODUCT_MD` on greenfield, run `get_command({ verb: "setup" })`.
4. **`dispatch_intent`** — map the user's request to verb(s) + which references to load (2–4 files, not all fifteen).
5. **`get_reference`** — load only the files `dispatch_intent` recommends.
6. Implement. When writing or fixing CSS, pull `get_reference({ name: "css-techniques" })` for idiomatic patterns (centering, specificity, logical properties, container queries, `:has()`, `clamp()`).
7. **`review_and_gate`** — scan changed files; score ≥85, zero blocking slop. Do not claim done on **FAIL**.

Optional: `get_palette_seed` on greenfield (no committed brand colors); `detect_antipatterns` for ad-hoc scans; web-search MCP for contemporary UI references on visually-led net-new work (extract moves, don't copy layouts).

If MCP is unavailable, read local `reference/` files using the routing map below.

## Session preflight (after MCP bootstrap)

0. **Project context** — PRODUCT.md / DESIGN.md are authoritative when present. DESIGN.md wins visual decisions; PRODUCT.md wins strategic/voice; anti-references beat one-off prompts.
1. **Register** — **brand** (distinctiveness) vs **product** (earned familiarity). Write one physical-scene sentence.
2. **One aesthetic system** — from `reference/aesthetic-systems.md`. Never mix two signatures on one surface.
3. **Positive direction** — `reference/differentiation-playbook.md`: inverse test, layout families, named references, one weird thing (brand).
4. **Existing UI** — audit → diagnose → redesign in `reference/refactor-and-redesign.md`; preserve functionality.

## Project context files

- **PRODUCT.md** — register, users, purpose, 3-word personality, anti-references, strategic principles, a11y commitments.
- **DESIGN.md** — tokens + named visual rules. Recipe in `reference/refactor-and-redesign.md`.

## Reference routing map

| Open this | When the task is about |
|---|---|
| `reference/differentiation-playbook.md` | **How to be distinctive** — inverse test, layout menu, one weird thing, named references, physical scene |
| `reference/design-principles.md` | Visual fundamentals — typography, spacing, color, layout, hierarchy, depth (neutral baseline) |
| `reference/aesthetic-systems.md` | Five design languages + brand-identity font procedure |
| `reference/avoid-ai-slop.md` | **What to refuse** — ban-list, category-reflex, output-completeness, ship checklist |
| `reference/motion-and-interaction.md` | Animation timing, springs, scroll, reduced-motion |
| `reference/engineering-and-performance.md` | Tokens, a11y, responsive, CWV, framework-honest output |
| `reference/refactor-and-redesign.md` | Improve existing UI without breaking it |
| `reference/command-playbook.md` | Intent → verb dispatch |
| `reference/interaction-design.md` | Cognitive laws, forms, navigation, errors, loading |
| `reference/visual-critique.md` | Seven-dimension critique instrument |
| `reference/design-systems.md` | Token architecture, component specs, theming |
| `reference/project-init.md` | Discovery, PRODUCT.md, DESIGN.md setup |
| `reference/craft-flow.md` | Shape-then-build pipeline with user gates |
| `reference/live-mode.md` | Browser variant mode: HMR hot-swap |
| `reference/css-techniques.md` | **How to write the CSS** — resets, centering, selectors/specificity, logical properties, container queries, `:has()`, `clamp()`; the cookbook for applying CSS fixes |

## Precedence rule

`design-principles.md` is the neutral baseline. Committing to a system in `aesthetic-systems.md` **overrides baseline** for that surface. **Existing brand identity beats both** on edits; never second-guess committed fonts, lanes, or palettes.

## Cross-file ownership

- Contrast, type ramp, spacing, layout → `design-principles.md`
- Palettes, fonts, shadow tokens per system → `aesthetic-systems.md`
- Distinctive / creative direction → `differentiation-playbook.md`
- Bans + completeness contract → `avoid-ai-slop.md`
- Easing, durations → `motion-and-interaction.md`
- GPU, tokens, a11y engineering → `engineering-and-performance.md`
- Idiomatic CSS implementation, applying CSS fixes → `css-techniques.md`

## Ship gate

`review_and_gate` replaces manual checklist-only shipping. It runs the 44-rule detector, computes a slop score, and returns blocking fixes. Also verify: category-reflex pass, no truncated code output, text ≥4.5:1, focus-visible rings, reduced-motion alternative, touch targets ≥44×44px, tested at 375/768/1440px.
