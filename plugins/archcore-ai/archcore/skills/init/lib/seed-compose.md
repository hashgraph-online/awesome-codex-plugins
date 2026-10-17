# Seed — compose, preview, confirm, create

Flow reference for `/archcore:init`. `SKILL.md` loads this file after `lib/seed-detect.md` released the detection catalogs. The file covers the depth axis and Phases B–E of the code seed.

## Depth axis (`depth:light|standard|deep`)

Orthogonal to scale (the `scale:` toggle, which measures repo *size*). Depth governs the code seed only — conversion of authored sources has no depth (`skills/_shared/tracks/import.md`). Depth sets the **synthesis budget**, not the artifact checklist. **Extraction is always on** in every depth — Tier-1 facts and the hotspot register are cheap and the highest-value / most-durable layer. Depth scales only the **expensive, staleness-prone synthesis**: spec bodies, cross-cutting rules, and enriched relations. Default: **`standard`** — a good first-day seed, not merely the cheapest one. Init is fully gated (nothing is written before `confirm`, and the preview shows all three depths' costs side by side before the user commits to any of them), so there is no reason to default to the thin tier just to be safe — `light` is the explicit **opt-down** for a cost-conscious user (still never empty — Universality invariant 3); `deep` is the explicit **opt-up** for a max plan.

| Depth | Hotspot specs (`rate` × pool, `floor`) | Cross-cutting synth (medium/large) | Relations |
|---|---|---|---|
| **light** (opt-down) | 10% of the ranked pool, floor 3 | every candidate clearing the recurrence threshold — MAY narrow scan toward guard + shared-indirection primitives for cost, but MUST still surface any high-confidence hit | basic |
| **standard** (default) | 25% of the ranked pool, floor 4 | every candidate clearing the recurrence threshold | basic |
| **deep** (opt-up) | 60% of the ranked pool, floor 6 | every candidate clearing the recurrence threshold | enriched (spec↔rule, spec↔spec) |

**The spec budget scales with the repo and carries no absolute maximum** — `budget = max(floor(depth), round(rate(depth) × pool_size))`, clipped to `pool_size`, where `pool_size` is the eligible ranked hotspot pool (`detect-hotspots.md` "Spec budget by coverage rate"). A 214-module pool budgets ~54 specs at `standard`; a 12-module pool budgets 4. Large mode adds a floor of ≥ 1 spec per domain selected in Step A.0, filling the rest by repo-wide rank; a later `refresh <domain>` re-run applies the same formula to that domain's narrowed pool. **Cross-cutting synthesis is on at every depth** — it is the highest value-per-token artifact init seeds; depth changes only its scan cost at `light`, never whether it runs and no longer how many candidates survive. A very large or hot hotspot (`LOC > 3000` OR top-quartile churn) may compose as a **flagship** at any depth, which makes it eligible for decomposition into ≤ 3 sub-specs by separable sub-surface instead of one spec (`detect-hotspots.md` "Flagship specs"). Every spec, flagship or not, is composed under the one ≤ 120-line cap in `_shared/spec-contract.md`.

Cost scales with depth AND with the repo — the preview shows the computed total per depth, never a constant. On a large repo `deep` can budget hundreds of specs; that is the intended behavior, and the preview's per-depth estimate is where the user sees the price before confirming. Treat any fixed multiplier as illustrative only.

### Universality invariants — hold in EVERY depth and for ANY codebase

1. **Ceiling, not quota.** A depth raises the budget; it NEVER fabricates to hit a number. If the ranked hotspot pool has 5 modules, `deep` produces at most those 5 specs, never a padded count; on a sparse repo `deep` ≈ `light`. Same for cross-cutting: if only 1 candidate clears the "surface nothing over a false rule" bar, that is the output at any depth. "Prefer omission over a guess" holds in every depth. The budget is a share of real evidence — an empty pool yields an empty seed, whatever the rate.
2. **"When detected", never "always."** No depth has a fixed artifact checklist. data-model / integrations / config / entry-points / cross-cutting appear only on positive evidence, identically across depths — a depth is defined by synthesis budget, not by mandatory docs.
3. **`light` is never empty.** Its floor rests on the universal spine — stack rule + run guide + public-surface (a library's exports, a CLI's commands, a plugin's skills, a SPA's routes) + register + the budgeted specs via the **test-independent fallback** ranking. At least one fires for any base (library, SPA, ML, CLI, embedded, data/IaC, agent-plugin/markdown, polyglot, monorepo); `light` never degrades to nothing for lack of schema/tests/authored files.
4. **Depth lives in Phase B (compose), not detection.** No depth branch adds a stack-specific detection heuristic; detection stays high-level, evidence-first, non-exhaustive (guarded by the detect-catalog universality test).
5. **`deep`'s extra budget flows to whatever the repo affords.** A module that authored sources cover has left the pool (`lib/seed-detect.md` Step A.4), so the budget goes to specs/relations that DO have evidence. `deep` is "more of what this repo actually has," not a fixed feature list assuming a stack shape.

Selection: the `depth:<tier>` toggle in the preview (Phase C), default `standard` — depth is not an argument; — the user can flip depth after seeing the plan and its per-depth cost, then still `edit` individual items.

## What each scale seeds

The scale mode comes from `_shared/grounding/detect-scale.md` (or the `scale:` toggle). Every artifact is composed **when detected** — a scale sets what is attempted, never a quota.

| Scale | Condition | Seeded |
|---|---|---|
| **small** | `domain_count ≤ 1` AND `module_count ≤ 15` | stack rule, run guide, data-model, integrations, config, entry points, public surface, overview + hotspot specs. No cross-cutting scan. ~6–10 docs at `standard` (4 specs — the sparse-repo floor) |
| **medium** | `domain_count ≤ 2` AND `module_count ≤ 40` | small set + cross-cutting rules. ~8–16 docs at `standard` (~5–8 specs) |
| **large** | `domain_count ≥ 3` OR `module_count > 40` | medium set + top-level map + domain dialog + a data-model doc per schema-bearing domain (all, not only selected) + a floor of ≥ 1 spec per selected domain. The seed scales with the pool: a 214-module pool yields ~54 specs at `standard` |

The counts are expectations, not targets: they tell you when a plan is far off (a `small` repo planning 40 specs, a `large` one planning 3), never how many documents to reach.

## Phase B — COMPOSE (in memory; composition contracts only)

Load the composition contracts and compose every planned artifact **without writing**. Honor each catalog's line cap. Mark any artifact whose `has_*` flag is already true as **skip (exists)**. Exception: in large mode or on a `refresh <domain>` run the per-domain data-model doc (`<domain-slug>-data-model`) dedupes by its own filename, not the repo-wide `has_data_model` tag — so a newly-selected domain's data-model is still composed when other domains' already exist.

**Apply the active depth** (`## Depth axis`, default `standard`) to this compose pass — it sets only these levers, and everything else is depth-independent:
- Hotspot spec count = the depth's computed budget (`detect-hotspots.md` "Spec budget by coverage rate"), large mode subject to the per-selected-domain floor; ranked hotspots beyond it go to the register regardless of depth. A flagship candidate (Change: size/churn-gated) composes as one spec or, only with genuine separable sub-contracts, decomposes into ≤ 3 sub-specs — at every depth, not gated by depth.
- Cross-cutting synthesis runs at **every** depth now (medium/large), and every candidate clearing the recurrence threshold becomes a stub — depth no longer trims the count. `light` MAY narrow the scan toward the guard + shared-indirection primitives for cost control but MUST still surface any high-confidence candidate it finds.
- Enriched relations: `deep` only.
Depth is a budget **ceiling, never a quota** — compose only what the repo affords on positive evidence (Universality invariant 1); a sparse repo at `deep` yields the same as `light`.

- **Tier-1 facts (full bodies, cheap/extractive):**
  - stack rule — `detect-stack.md` template (≤ 6 lines).
  - run guide — `extract-run-instructions.md` (single-app ≤ 15 lines; monorepo per-app ≤ 6).
  - data-model doc — `detect-data-model.md` Output (≤ 40 lines), when detected; large mode: one per domain, for every schema-bearing domain.
  - integrations doc — `detect-integrations.md` Output (≤ 15 lines), when detected.
  - config doc — `detect-config.md` Output (≤ 20 lines, **NAMES ONLY**), when detected.
  - entry-point inventory — `detect-entry-points.md` Output, when ≥ 1 entry point.
  - public-surface doc — `detect-surface.md` Output (≤ 25 lines, **NAMES + purpose only**), when a surface exists that entry points don't already cover.
  - top-level map — `detect-domains.md` Output (large mode).
- **Tier-2 stubs (NO source reads):**
  - hotspot specs — one stub each for the **active depth's budget** (`detect-hotspots.md`), large mode subject to the per-selected-domain floor: suggested spec title, the qualifying `LOC / test-ratio`, target filename + directory, a `flagship` marker when the size/churn gate is cleared, and an estimated synthesis cost ≈ `(source_LOC + test_LOC) × 6` tokens. The full body is composed only after confirm. Ranked hotspots **beyond** the budget are not stubbed — they go to the overview register (`compose-overview.md` Part 3) at ~0 cost.
  - cross-cutting rules (medium/large, **every depth**, no count cap) — one stub each: the pattern + the paths it would govern. Full body composed after confirm under `rule-contract.md`. **Drop a stub whose pattern an authored conversion target already covers** (dedup per `detect-cross-cutting.md`; the targets come from the assessment gate) and note the skip under that target — authored content wins over synthesized content.
- **Capstone:** plan the architecture-overview per `lib/compose-overview.md`. Its body indexes the *confirmed* seed, so it is composed in Phase E once the set is final. List it in the preview as "Architecture overview — index of the above".
- **Authored conversion targets (every tier):** when the assessment gate found one or more sources, run the `discover`, `triage`, and `plan` gates of `skills/_shared/tracks/import.md` in callable mode — callable mode means the gate computes its result and returns it to this flow; its preview becomes a block of this preview, and this flow's confirm is its confirm. Tier `S` lists each target document beside the seed. Tiers `M` and `L` list one summary line (target count, source count, wave-1 breakdown) followed by the plan gate's row list (see Phase C). No target carries an import mark; `_shared/grounding/convert-routing.md` owns the conversion.
- **Planned relations:** per the `compose-overview.md` "Relation wiring" table.

No `create_document` / `add_relation` has run yet.

## Phase C — PREVIEW (one manifest)

Present the entire plan as a single grouped manifest, then wait. Example:

```
Init plan — scale: medium · depth: standard (default).   confirm / edit / depth:light / depth:deep / scale:<mode> / cancel
Coverage: 4 specs / 11 load-bearing modules (36%) · 1 cross-cutting rule
Covered by authored sources (estimate): src/auth/session — CLAUDE.md · src/api/errors — .cursor/rules/error-handling.mdc

Facts (created in full):
  • Project stack — rule                                      [new]
  • Running the project — guide                               [new]
  • Data model — doc (6 entities)                             [new]
  • External integrations — doc (Stripe, AWS)                 [new]
  • Configuration — doc (12 vars)                             [new]
  • Entry points — doc (5)                                    [new]
  • Public surface — doc (8 routes)                           [new]
Synthesis (bodies composed only if kept):
  • spec: token-rotation   — 235 LOC src / 968 LOC tests   ~7k   [new]
  • spec: auth-client      — 52 LOC src / 0 tests          ~1k   [new]
  • rule: request-context  — cross-cutting; src/**/handlers ~1k  [new]
Capstone:
  • Architecture overview — doc (index of the above)          [new]
Authored sources (tier S — converted with this confirm):
  • rule: app-router-only     — .cursor/rules/app-router-only.mdc        ~1k   [new]
  • rule: error-handling      — .cursor/rules/error-handling.mdc, CLAUDE.md §Errors  ~2k   [new]
  • guide: local-dev-setup    — CLAUDE.md §Setup                         ~1k   [new]
  • skip: CLAUDE.md §Changelog — changelog class
Host wiring (as `archcore init`, host: claude-code) → /Users/x/myrepo
  • .mcp.json · .claude/settings.json (SessionStart hook) · CLAUDE.md + AGENTS.md (managed block)   (edit → hosts: all / skip)
Relations: ~14 edges.
Estimated: ~22k (standard, shown) · ~7k (light) · ~50k (deep).
Already present (skipped): <list, or "none">.
```

- The **Coverage line** always follows the header and surfaces sparseness explicitly:
  `Coverage: <N> specs / <M> load-bearing modules (<P>%) · <D>/<T> domains seeded · <C> cross-cutting rules`.
  `N` = kept hotspot specs at the active depth; `M` = the full ranked hotspot pool size (`detect-hotspots.md` primary + fallback, not just the budgeted slice); `P` = `N`/`M` as a percentage — the realized coverage rate, which lands on the depth's `rate` except where the sparse-repo `floor` or the per-domain floor raised it; `D`/`T` = domains with ≥ 1 seeded doc (data-model or spec) out of total detected domains — **large mode only**, omit the `· D/T domains seeded` clause in small/medium; `C` = kept cross-cutting rule stubs — omit that clause when `C` = 0 in small mode (cross-cutting never runs there). Every number is computed from the plan, never a constant.
- **Large mode**, any depth: append one recommendation line directly under Coverage showing the concrete jump to the adjacent tiers, computed from the plan's actual pool and per-depth rates — never constants:
  ```
  Init plan — scale: large · depth: standard (default).   confirm / edit / depth:light / depth:deep / cancel
  Coverage: 54 specs / 214 load-bearing modules (25%) · 18/24 domains seeded · 3 cross-cutting rules
  Large repo: standard covers 25% of load-bearing modules. depth:light → ~21 specs, cheaper; depth:deep → ~128 specs + enriched relations. Toggle depth: below before confirm.
  ```
  On a `light`-toggled re-plan the line instead points only upward (`depth:standard → …`, `depth:deep → …`); on `deep` it points only downward, since there is nowhere higher to go.
- **High-volume notice.** IF the budget exceeds **25** hotspot specs, THEN add one line under the recommendation line naming the spec count, the estimated token cost, and the cheaper depth — e.g. `54 spec bodies ≈ ~180k tokens in one run; depth:light → ~21 specs ≈ ~72k. edit drops individual specs.` The run stays a **single** confirm and a single pass (no second gate, no staging); this line is what keeps a large budget an informed choice rather than a surprise.
- For each **Tier-2 stub** show the qualifying `LOC / test-ratio` and the per-item synthesis cost, so `edit` is an informed budget lever. A flagship stub (`detect-hotspots.md` "Flagship specs") shows its treatment inline, e.g. `spec: order-service — 6400 LOC src / 1100 LOC tests ~24k [flagship: one spec]` or `[flagship: split → 2 sub-specs]`.
- **No authored source:** omit the Covered line and the Authored sources block; print no empty heading in their place (`lib/sources.md` "No authored source").
- The **Covered line** follows Coverage when the assessment gate returned a non-empty `coverage_set`: each removed module with the source that names it. Always carry the word `estimate` — the gate read path mentions, not file bodies.
- **Authored sources, tier `S`:** list each conversion target with its type, its source spans, and its cost, and each `skip` verdict with its reason (`lib/sources.md`). If a cross-cutting stub was dropped because a target covers it, show `↳ synthesis skipped` under that stub.
- **Authored sources, tier `M` or `L`:** show one block instead of the targets — `Authored sources (tier M — 23 targets from 9 sources): this confirm creates the import plan and runs wave 1 (7 rules, 4 decisions). Remaining waves: /archcore:init import.` Under that line, show the row list the `plan` gate returned — every source with its verdict, every target with its type and wave — so no document of wave 1 is created unseen.
- The **Host wiring line** follows `lib/host-wiring.md` "Preview line".

## Phase D — CONFIRM

Wait for the user. Only a literal `confirm` from the user licenses Phase E. IF this invocation cannot receive further user input in this turn (a print-mode run, a sub-agent call), THEN print the preview and stop — absence of an answer is never `confirm`.

- **`cancel`** → stop. Fire zero `create_document` / `add_relation` calls. No partial state.
- **`edit`** → accept deselections by name/number ("drop spec:auth-client", "drop rule:error-handling", "facts only"), a verdict change on an authored source ("skip CLAUDE.md §Setup"), and the host-wiring toggles from Phase C ("hosts: all" widens to every detected agent, "skip wiring" drops the line). Re-show the trimmed total, then proceed.
- **`depth:light|standard|deep`** → re-plan at that depth: recompute the spec count, the relation plan, and the per-depth cost, re-show the whole preview (Coverage line and, in large mode, the depth-nudge line included), then wait again (edits on top are still accepted).
- **`scale:small|medium|large`** → re-plan with that scale mode forced; report the auto-detected mode beside it.
- **`confirm`** → Phase E with the surviving set.

A deselected Tier-2 spec's source file is **never read** — the read happens in Phase E only for kept specs.

## Phase E — CREATE + WIRE (gated; runs only after confirm)

For the confirmed set only, in order:

0. **Host wiring** — when the line survived `edit`, run the Execution cascade of `lib/host-wiring.md` first.
1. **Tier-1 facts** — `create_document` per the fields in each catalog's `## Output` section (type / directory / filename / title / status / tags). Skip any marked exists.
2. **Hotspot specs** — for each kept stub: **now** read its source + companion tests, compose the full body under `_shared/spec-contract.md` (≤ 120-line cap, the same for every spec). If the stub is marked **flagship** (`detect-hotspots.md` "Flagship specs" — `LOC > 3000` OR top-quartile churn): compose one spec (default treatment), or — only when the module has ≥ 2 genuinely separable, independently-consumable sub-surfaces — decompose into ≤ 3 sub-specs (`filename=<module-slug>-<sub-surface-slug>` each), each under the same cap. Then `create_document(type='spec', filename=<module-slug>[-<sub-surface-slug>], directory=<domain-or 'architecture'>, status='draft', tags=['spec', <area>])` — `status='draft'` in every case: the spec is heuristic-derived from code, not authored/reviewed, so the user confirms it before it is canon (same rationale as the cross-cutting rules below). Skip if a doc with that filename already exists (dedupe). For decomposed sub-specs, evaluate relation candidates in Step 6 through `compose-overview.md`; splitting alone creates no edge.
3. **Cross-cutting rules** (medium/large, **every depth**, no count cap — per Phase B) — for each kept stub: compose under `_shared/rule-contract.md`, `create_document(type='rule', filename=<concern-slug>, directory='conventions', status='draft', tags=['conventions', <concern>])`. `status='draft'` because the rule is heuristic-derived and the user should confirm phrasing before it is canon. Skip if that filename already exists, or if the stub was deduplicated against an authored conversion target in Phase B.
4. **Authored sources** — hand over to `skills/_shared/tracks/import.md` at its `convert` gate: tier `S` converts every kept target now; tier `M` or `L` creates the import plan, then runs wave 1. Every target is composed under its type contract per `_shared/grounding/convert-routing.md`, with `status='draft'` and no import mark. The track's `verify` gate runs before step 5; its `retire` gate runs after the Report, behind its own confirm.
5. **Architecture overview** — skip if `has_overview`. Otherwise, now that the seed is final, compose its body per `compose-overview.md` (structural-facts line + type/topic index of the *created* docs) and `create_document`.
6. **Relations** — apply `skills/_shared/relation-authoring.md` to the planned wiring candidates using the composed bodies. Skip pairs whose endpoints were not both created. Add only supported claims; report unresolved candidates. At `deep` depth, evaluate applicable conventions and other specs by the same procedure. Roll forward on individual failure (surface the error, keep successful edges; do not delete prior creates).
7. **Report** one line per created document plus the total edge count.

### Closing message: outlook

Summarize what was created, then make the value-loop visible and list the over-time targets. When host wiring ran, lead with its outcome line per `lib/host-wiring.md` "Closing outcome lines". When authored sources were converted, add one line: the count of documents by type, the conflicts list if any, and — for tier `M` or `L` — the open waves with `/archcore:init import` as the continuation. When the assessment gate found **no authored source**, add one line instead: with a non-empty `deeper_present`, *"No agent instructions or decision records were found; contributor docs exist (`<paths>`) — `/archcore:init import` converts them."*; with nothing at any level, *"This repository holds no written conventions or decisions, so the seed covers only what the code shows. A choice the code does not explain — why a dependency, which convention reviewers enforce — enters through `/archcore:document`."* **Conditionalize the "Try it now" line:** if ≥ 1 hotspot spec was created, point at the top hotspot path; if none (empty pool or all deselected), point at a file in a seeded fact's area instead — the code-alignment hook injects that fact on edit. Per-mode template.

**Small:**

> Done. Seeded: stack rule, run guide[, data-model, integrations, config, entry points], architecture overview, and N hotspot specs.
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects via the code-alignment hook. (No hotspot specs? Edit a file in a seeded area — the hook injects what applies.) Over time: ADRs for non-trivial dependency choices (`/archcore:document`), more specs (`/archcore:document <path>`), a task-type for any repeating extension pattern (`/archcore:review`'s experience offer).

**Medium:**

> Done. Seeded: stack rule, run guide, data-model, integrations, config, entry points, architecture overview, N hotspot specs[, M cross-cutting rules].
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects. The hook injects what applies to any path you edit. Over time: ADRs for architectural decisions (persistence, auth, observability), more specs, rules per cross-cutting concern — via `/archcore:document`, `/archcore:plan`; task-types surface via `/archcore:review`'s experience offer when branch changes repeat a pattern.

**Large:**

> Done. Seeded: workspace stack rule, monorepo run guide, top-level map (T domains), entry points, data-model + integrations + config. Data-model seeded for D of T domains (every domain with a detectable schema, not only the ones you picked below). Architecture overview. Created M hotspot specs — a floor of ≥ 1 per domain you're working in now, the rest by repo-wide rank[, converted K documents from authored sources], and registered the remaining hotspots in the overview[ plus J cross-cutting rules].
>
> Try it now: edit a file under `<a selected-domain hotspot path>` — its spec auto-injects via the code-alignment hook. Other domains: <list>. Run `/archcore:init refresh <domain>` later to drill into any of them, and `mcp__archcore__search_documents` with the domain tag to scope queries. Over time each domain needs its own ADRs and specs via `/archcore:document`, and task-types via `/archcore:review`'s experience offer when branch changes repeat a pattern; repo-wide cross-cutting rules (logging, errors, auth, transactions, telemetry) accrue via `/archcore:document`.

Depth-nudge, keyed off whichever depth actually ran (never assume `standard` ran just because it is the default):

- Ran at **`light`** (opted down):

  > Ran at `light` depth (cheapest seed). `depth:standard` (the default) raises the spec budget; `depth:deep` additionally adds enriched relations and the widest spec coverage. Re-run `/archcore:init refresh` and toggle `depth:standard` or `depth:deep` in the preview — it shows each depth's cost before anything is created.

- Ran at **`standard`** (the default — most runs):

  > Ran at `standard` depth. `depth:deep` additionally enriches the relation graph (spec↔rule, spec↔spec) and raises the spec coverage to 60% of the ranked pool. Re-run `/archcore:init refresh` and toggle `depth:deep` in the preview for the max plan, or `depth:light` for a cheaper one.

- Ran at **`deep`**: no nudge — this is the max tier.

Always end with:

> Use `/archcore:review` for the dashboard, `/archcore:review deep` for a health audit.
