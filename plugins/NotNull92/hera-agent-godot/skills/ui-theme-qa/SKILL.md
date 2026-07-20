---
name: ui-theme-qa
description: "Use this skill to find and fix undisciplined Control-node UI in a Godot project — spacing that follows no ladder, font sizes with no modular scale, near-duplicate colours, and text that fails WCAG contrast — by measuring the live editor with the `hera` CLI and snapping theme tokens to a reference corpus. It also reports (without changing) inert container wrappers and decorative nodes. Triggers: \"clean up the UI spacing/type/contrast\", \"the UI values look arbitrary\", \"tidy the Godot UI\", \"check UI contrast\", or any request to mechanically remove statistical UI-design defects without a redesign. Reductive only; edits per-node theme overrides (undoable), never copy or layout content."
---

# UI Theme QA (Godot, reductive)

Mechanically remove statistical design defects from a live Godot editor, over
`Control` nodes. It does not redesign: it snaps theme tokens to a reference
corpus and never touches copy, information order, or layout structure.

Six areas, split by what they may do:

| | areas | effect |
|---|---|---|
| **enforcing** | `spacing` · `type-scale` · `color` · `contrast` | set `theme_override_*` (undoable) |
| **report-only** | `containers` · `decoration` | proposals in the report; **no mutation** |

The report-only pair would have to delete or re-parent nodes, which cannot be
decided mechanically — a node that looks decorative may be a divider, and
flattening a wrapper breaks the `$Path/To/Node` references scripts rely on. They
measure and surface; a human decides.

**Why a pipeline, not one pass:** one context holding every rule while fixing a
large UI lets loud items crowd out quiet rules, which get silently dropped. So
inspection and enforcement are split per area, and findings live in files. The
orchestrator (this context) stays thin — it holds routing only; the detailed
rules and findings live in the reference doc and the findings files.

Rules SSOT: [references/ui-theme-areas.md](references/ui-theme-areas.md).
Values: [references/reference-corpus.md](references/reference-corpus.md).
Read only the area section you are working; do not load all rules into one
context.

## 0. Prep

1. `hera status` — confirm one live editor (the `live-editor` skill covers
   setup). If multiple, pass `hera --instance <pid>` to every mutation.
2. `hera guidance ui` — respect the returned UI mode.
3. Ensure git is clean or on a branch; each area fix is one commit.
4. Enumerate the target Controls: `hera --ids scene tree` (edited scene) — this
   is the static surface the checks read.

## 1. Inspect (parallel, static, read-only)

Dispatch one inspector per area (`spacing`, `type-scale`, `color`, `contrast`,
`containers`, `decoration`). Each:
- reads **only its area section** of `references/ui-theme-areas.md`,
- measures the live editor with the read commands listed there
  (`node get --props`, `eval get_theme_color`, `game ui tree` rects),
- writes `findings-<area>.md` using the schema (each item a **`check`
  predicate**, never a status word).

No mutation here. Inspectors snap replacement values to the corpus so the fix is
carried in the finding, not invented later.

## 2. Report

Merge the `findings-*.md` into one local HTML report and serve it:
`python3 -m http.server <port>` from the run folder, then hand the user
`http://localhost:<port>/`. Show measured values verbatim (distinct spacing
values, font-size ratios, contrast ratios). No artifact, no browser auto-open —
link only.

## 3. Enforce (sequential: spacing → type-scale → color → contrast)

One area enforcer at a time, in order. `containers` and `decoration` are skipped
here — they enforce nothing. Each enforcing area:
- loads `findings-<area>.md` + its area section,
- **re-measures each `check` from the live editor**; applies the fix only where
  the predicate is currently false (never trust the finding text),
- enforces with `hera node set <path> --prop "<theme_override…>" --value <v>`
  (undoable), snapping to the corpus rung/hex,
- commits that area before the next runs.

Order = dependency order: `spacing` commits before `type-scale`, `color`
converges before `contrast`, and `contrast` runs last because it depends on the
final colours.

## 4. Re-inspect (fresh, parallel)

Dispatch fresh inspectors (not the enforcers) to recompute each **enforcing**
area's `check` predicates from source and write `verify-<area>.md` (true =
applied, false = missed). Any false re-enters step 3 for that area only. The
report-only areas have no `check` — they changed nothing, so there is nothing to
re-verify, and inventing a predicate that always passes would be a lie.

## 5. Render QA (confirmation only)

`hera run --current --wait`, then `hera screenshot --runtime --analyze` for a
before/after and a clipping/blank sanity gate (`possible_clipping`, `nonblank`).
`hera stop --wait`. Render is confirmation, not measurement — the design facts
came from steps 1/3. Update the report in place.

## Contract (why this skill exists)

- **Thin orchestrator.** This context holds routing only. Rules and findings
  live in files. Holding all areas here reintroduces the capacity drop.
- **A check is a predicate, not a status.** A finding is a `check` recomputed
  from the live editor every time — never a stored "done". Enforcers fix only
  false predicates; fresh re-inspectors recompute them.
- **Snap, don't invent.** Replacement values come from the corpus, which is
  rooted in Godot's own default theme plus WCAG. A project's own theme/tokens
  win over the corpus if present.
- **Undoable + reductive.** Only per-node theme overrides change, via
  `node set` (Ctrl+Z survives). Copy, order, and layout are inviolable — which
  is precisely why `containers` and `decoration` report instead of enforce.
  Widening that would need an explicit opt-in flag, never a quiet default.
- **Static inspect, render once.** Measurement is `node get` / `eval` /
  `game ui tree`; the screenshot analyzer is the confirmation gate, not a
  measurement tool.

## Non-interactive

Fast, mechanical, non-interactive. Ambiguous items are proposed in the report,
not asked. Redesign-scale decisions (which accent, is this density right) are
out of scope — surface them, do not silently pick.

## Out of scope

Project-wide `Theme` resource construction (needs a `hera theme set` primitive),
before/after pixel diffing, and any wholesale restyle. See the repo's
`docs/UI_THEME_QA_DESIGN.md` (§6 gaps, §11 phasing).
