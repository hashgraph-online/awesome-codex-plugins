# Seed — detect

Flow reference for `/archcore:init`. `SKILL.md` loads this file when the run composes the code seed. The file covers Phase A: every signal the seed needs, computed in one pass with no writes. Phases B–E are in `lib/seed-compose.md`.

**Lazy reading (two sub-phases).** The detection/extraction catalogs at `_shared/grounding/*.md` and the composition files at `lib/*.md` are heavy (≥ 1000 lines combined) — read them in two ordered batches, never all at once. The **Detect** sub-phase (Phase A) loads the *detection* catalogs and, for each detector it runs, captures into working memory both the signals AND the small `## Output` create-fields + body template it will reuse later. The **Compose** sub-phase (Phase B) loads the *composition* contracts (`_shared/precision-rules.md`, `_shared/spec-contract.md`, `_shared/rule-contract.md`, `lib/compose-overview.md`) and **reuses the Output fields/templates already captured during Detect** — it does not re-read the bulky detection heuristics. "Release the detection catalogs" at the end of Phase A means dropping their heuristic prose from focus, not the captured Output specs.

## Phase A — DETECT (no writes; detection catalogs only)

Compute everything the seed needs in one detection pass. No documents are created here, and no composition contract is opened. For each detector, capture its signals AND its `## Output` create-fields for reuse in Phase B/E.

**Detect high-level, for ANY stack.** Each `detect-*` catalog leads with *what* it detects (the concept) and a universal, evidence-first method; its concrete lists of frameworks / ORMs / SDKs / extensions / conventional roots are **non-exhaustive examples**, not a checklist. When a project's language, framework, or layout is unfamiliar or highly specific, reason from first principles per the catalog — the entry file's imports, the dominant file types, the manifest / build system, and what the code actually does — and emit a fact only on **positive evidence** (prefer omission over a guess). Never return empty / `small` / "no entry points" merely because nothing matched a list.

### Step 0.5: Scale

Read `_shared/grounding/detect-scale.md`, `_shared/grounding/detect-domains.md`, `_shared/grounding/detect-modules.md`.

1. **Read the run inputs** — the `refresh` subject that `SKILL.md` step 3 resolved (a path scope, or a domain slug that forces a large-mode single-domain pass; see Step A.0), and the `coverage_set` from the assessment gate (`SKILL.md` step 5). Depth and scale are preview toggles, not arguments: detection runs the same at every depth — Phase A ranks hotspots up to the `deep`-depth ceiling (see Step A.3) and detects ALL facts regardless of the active depth; depth only governs how much is synthesized in Phase B.
2. **Compute signals:** `domain_count` (per `detect-domains.md`), `module_count` (source files > 100 LOC, excluding tests/generated), `entry_point_count` (per `detect-entry-points.md`, informational).
3. **Classify** per `detect-scale.md` — apply its evidence-based fallback when the language/layout is unlisted (recompute counts from the dominant code extension and tracked-file breadth; do not default to `small` just because the extension/root lists miss). A `scale:` toggle from the preview wins on the re-plan, but remember the auto-detected one; a `refresh <domain>` run forces large-mode behavior scoped to the named domain.

### Step A.0: Domain selection (large mode only)

Skip unless mode is `large`.

1. **`refresh <domain>` run** — that domain is the sole selection; skip the dialog. (Tier-1 facts already present are skipped; the run tops up this domain's data-model + hotspot specs by applying the depth's `rate` / `floor` to the pool **narrowed to that domain's tree**, per `detect-hotspots.md`.)
2. **Otherwise** — present the top 5 ranked domains (per `detect-domains.md` ranking) and ask: *"Which domains are you working on now? (pick 1–3 by name or number, or `skip` to defer.)"* Accept a single name, a comma list, or `skip`.
3. **Allocate the hotspot budget.** Hotspots (A.3) are ranked **repo-wide** (candidate selection is never restricted to a domain's tree in the day-one dialog), and the budget itself comes from the repo-wide pool: `max(floor(depth), round(rate(depth) × pool_size))` per `detect-hotspots.md` "Spec budget by coverage rate". The selection changes **allocation, not size**: every selected domain is guaranteed a floor of ≥ 1 spec; remaining slots fill by repo-wide rank across all domains, selected or not. On `skip`, no domain gets a floor and the whole budget fills by repo-wide rank alone.
4. **Data-model breadth is decoupled from the dialog.** Seed a data-model doc for **every domain with a detectable schema** (`detect-data-model.md`, names-only — cheap regardless of repo size), not only the domains selected here. The dialog focuses hotspot-spec priority, not data-model breadth. A domain without a schema still appears as a row in the top-level map (`detect-domains.md`).

Remember the unselected domains for the closing message.

### Step A.1: Shape — single manifest batch

Read `_shared/grounding/detect-stack.md`, `_shared/grounding/detect-data-model.md`, `_shared/grounding/detect-integrations.md`, `_shared/grounding/detect-config.md`. **Read each manifest file once** (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `schema.prisma`, `.env.example`, …) and feed all four detectors from that shared parse — never re-read a manifest per detector. Collect:

- **Stack signals** (≤ 5) — per `detect-stack.md`.
- **Data model** — entities + key relations, NAMES ONLY, per `detect-data-model.md` (large mode: one doc per domain, seeded for EVERY domain with a detectable schema — not scoped to the Step A.0 selection; see Step A.0.4). Skip if no schema anywhere.
- **Integrations** — external services from allowlisted SDK deps, per `detect-integrations.md`. Skip if none.
- **Config surface** — env-var NAMES + purpose, **never values**, per `detect-config.md`. Skip if no env contract.

### Step A.2: Run commands, entry points & surface

- **Run commands** — per `_shared/grounding/extract-run-instructions.md` (README section → scripts → ask the user once if neither yields anything).
- **Entry points** — per `_shared/grounding/detect-entry-points.md`, bucketed HTTP / CLI / Worker / Cron / Other. Seed the entry-point `doc` in any mode when ≥ 1 entry point exists; in large mode group by domain.
- **Public surface** — per `_shared/grounding/detect-surface.md`. The role-based outward shape the entry-point inventory does NOT cover: web routes/pages, a library's exported API, a multi-command CLI's command catalog, an agent-plugin's skills/commands, mobile screens. Seed the public-surface `doc` when such a surface exists and is not already fully enumerated as entry points; in large mode group by domain. This is the fact that gives library / SPA / plugin / markdown-tooling repos a substantive seed.

### Step A.3: Hotspots & cross-cutting (candidates only — NO source reads)

- **Hotspot candidates** — rank per `_shared/grounding/detect-hotspots.md` and collect signal data (path + LOC + companion-test LOC + suggested type) for the **whole eligible ranked pool**, not a per-depth slice of it. The pool size is itself an input to every depth's budget, and signal collection reads **no source files**, so one Detect pass serves any depth, including a later `depth:` toggle in Phase D, with no re-read. Phase B then keeps the *active depth's* budget as spec stubs — `max(floor(depth), round(rate(depth) × pool_size))`, clipped to the pool (`detect-hotspots.md` "Spec budget by coverage rate") — subject to large mode's per-selected-domain floor of ≥ 1 spec; ranked candidates beyond the budget go to the overview register (`compose-overview.md` Part 3) as `→ /archcore:document` rows. The catalog ranks in two tiers: a tests-aware **primary** tier, and — when it fills fewer slots than the budget — a **test-independent fallback** (fan-in / public surface / size / churn) so repos with no tests (scripts, SPAs, ML, CLIs, agent-plugin/markdown tooling) still surface real specs instead of an empty pool. Mark fallback-tier stubs with their qualifying signal. A candidate clearing the **flagship** gate (`LOC > 3000` OR top-quartile churn) is flagged as such in the stub, for Phase E's one-spec/decomposition choice (`detect-hotspots.md` "Flagship specs"). **Tier-2 artifacts are always composed as `spec`** — use the `adr`/`task-type` hints in `detect-hotspots.md` only to *filter out* ineligible candidates (e.g. a `utils`/`helpers` module, or one failing `spec-contract.md`'s "when NOT to write a spec"), never to switch the document type. **Do not read source files yet** — that read is deferred to Phase E for kept specs only.
- **Cross-cutting candidates** (medium and large, whole-repo, **every depth**) — per `_shared/grounding/detect-cross-cutting.md`, every candidate that clears the recurrence threshold, with no per-depth count cap (Change: the `light` ≤2 / `standard` ≤3 / `deep` ≤4 caps are removed — the conservative "surface nothing over a false rule" bar is the only gate). init uses that catalog for **detection only** and overrides its standalone y/n "Output" flow: each candidate becomes a Tier-2 `rule` stub here and is created in Phase E, not handed to `/archcore:document`.

### Step A.4: Authored coverage

Authored sources are not detected here — the assessment gate (`SKILL.md` step 5) already listed them per `lib/sources.md`. Apply its `coverage_set` to the hotspot pool:

1. Remove every module the `coverage_set` names from the **eligible** ranked pool before any budget is computed. Authored content wins over synthesized content on the same module, so such a module gets no spec stub.
2. Keep the removed modules in a `covered` list with the source path that names each one; Phase C shows the list under the Coverage line, labeled as an **estimate** (the gate read path mentions, not file bodies).
3. Leave the budget formula unchanged — `max(floor(depth), round(rate(depth) × pool_size))` now runs over the narrowed pool. An empty `coverage_set` leaves the pool as ranked.

A `covered` module that the import later leaves without a document returns to the pool on the next `/archcore:init refresh`.

### Step A.5: Announce

Print one detection line, e.g.:

> Mode: medium (28 modules, 1 domain). Detected: Prisma (6 entities), Stripe + AWS, 12 env vars, 5 entry points, 5 hotspot candidates, 1 cross-cutting pattern, 2 modules covered by authored sources. Composing the plan…

In large mode, report the figures for the **selected** domains (selection already happened in Step A.0). Detection done — release the detection catalogs (heuristic prose), keeping the captured Output specs.
