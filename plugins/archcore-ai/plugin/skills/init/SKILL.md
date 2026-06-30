---
name: init
argument-hint: "[--mode=small|medium|large] [--domain=<slug>] [--refresh]"
description: "First-time Archcore setup. Detects repo scale and shape, then composes a full first-day seed — stack rule, run guide, data-model, integrations, config, entry points, public surface, a linked architecture overview, and specs for the top hotspot modules — shown in ONE preview and created on a single confirm. Imports CLAUDE.md/AGENTS.md/.cursorrules. Use on a fresh clone, empty `.archcore/`, or 'set up archcore'. Not for individual docs or planning."
---

# /archcore:init

First-time onboarding. Detects repo scale (small / medium / large) and shape, composes a scale-appropriate seed of `.archcore/` documents, shows them in **one preview**, and creates them on a **single `confirm`** — so push-mode (`check-code-alignment`) and pull-mode (`/archcore:context`) have substance and the relation graph is live from day one. Per `magic-first-day-init.adr`: extractive facts are composed in full; the top hotspot modules get real `spec`s (synthesized only after confirm); the overview is an index, never a prose blob. **Nothing is written before `confirm`.** Exact per-mode output is in the Routing Table below.

## Arguments

- `--mode=small|medium|large` — force a mode, overriding auto-detection.
- `--domain=<slug>` — re-run focused on one domain (large repos): scopes data-model + hotspot specs to that domain's tree, tops up only its docs. Bypasses the "already seeded" early-exit.
- `--refresh` — re-run on an already-seeded repo to add facts that appeared since the first init (a new schema, config, or modules). Bypasses the early-exit; existing docs are skipped, missing ones composed.

## When to use

- Empty `.archcore/` — the SessionStart nudge points here.
- First session on a fresh clone / fresh install.
- User says: "initialize archcore", "set up archcore", "seed archcore", "first-time setup", "what should I do first".

**Not init** (route elsewhere):

- Recording a specific decision → `/archcore:decide`.
- Planning a feature → `/archcore:plan`.
- Documenting one module → `/archcore:capture`.
- Codifying a team standard → `/archcore:decide` (offers rule + guide continuation).
- Reading applicable context before coding → `/archcore:context`.
- Docs health audit → `/archcore:audit`.

## Routing table

**Mode routing** — Step 0.5 classifier, evaluated top-to-bottom, first match wins. The **empty** route is decided earlier in Step 0(b). Precise conditions in `lib/detect-scale.md`.

| Signal | Route | Seeded (composed when detected) |
|---|---|---|
| No manifest AND no top-level source (Step 0b) | → **empty** | none — acknowledge-only, no placeholder docs |
| `--mode=X` flag | → forced `X` (detected mode still reported) | per row below |
| `domain_count ≤ 1` AND `module_count ≤ 15` | → **small** | stack rule, run guide, data-model, integrations, config, entry points, public surface, overview + **3** hotspot specs |
| `domain_count ≤ 2` AND `module_count ≤ 40` | → **medium** | small set + **0–2** cross-cutting rules + **5** hotspot specs |
| `domain_count ≥ 3` OR `module_count > 40` | → **large** | medium set + top-level map + domain dialog + **3** hotspot specs per selected domain |

Every non-empty mode also composes the architecture-overview capstone, plans relation wiring, and offers agent-file import (CLAUDE.md / AGENTS.md / .cursorrules) inside the preview. Tier-1 facts (data-model, integrations, config, entry points, public surface) are seeded in any mode **when detected** — breadth scales with the repo, presence does not. The public-surface fact is what carries the seed for library / SPA / multi-command-CLI / agent-plugin repos, where there is no server to enumerate as entry points. The empty route exits after Step 0.

**Follow-up routing** — closing-message hand-offs. Init surfaces these as todos; MUST NOT auto-invoke.

| User wants to... | → Invoke |
|---|---|
| Capture another module | `/archcore:capture <path>` |
| Record a decision | `/archcore:decide` |
| Codify a convention as a rule | `/archcore:decide` |
| Plan a feature | `/archcore:plan` |
| Drill into another domain (large) | `/archcore:init --domain=<slug>` |
| Add facts that appeared since first init | `/archcore:init --refresh` |
| Scope queries to a domain (large) | `/archcore:context domain:<slug>` |
| See what's loaded | `/archcore:audit` |

## Execution

Content voice: default to architectural prose — decisions, rationale, intent. See `skills/_shared/precision-rules.md` Rule 6. Code blocks only where the document type requires it (`rule`, `guide`, `cpat`, and `spec` examples) or the user asks.

### Pre-flight: CLI availability check

Before any init step, verify that the Archcore CLI is available on PATH. The canonical installer is documented at https://docs.archcore.ai/cli/install/ — use it as the single source of truth; do **not** suggest other channels (`brew`, `go install`, etc.) even if the user mentions them.

1. Run: `archcore --version` (via Bash tool)
2. If it **succeeds** → proceed immediately to Step -1.
3. If it **fails** (command not found):
   - Detect the platform via `uname -s` (Bash). `Darwin`/`Linux` → POSIX path. Anything else (Windows native) → instruct-only path.
   - **POSIX path** — ask the user once:
     > Archcore CLI not found. The official installer runs:
     >
     > ```
     > curl -fsSL https://archcore.ai/install.sh | bash
     > ```
     >
     > Run it now? (y/N)
   - On `y` → execute the command exactly as shown (Bash tool). After it returns, re-run `archcore --version`.
     - Success → print: *"Archcore CLI installed (`<version>`). Proceeding with init."* → go to Step -1.
     - Still failing → print the install message below and **stop**.
   - On `N` / silence / **instruct-only path** → print and stop:
     > Archcore CLI required. Install it, then re-run `/archcore:init`:
     >
     > - macOS / Linux / WSL: `curl -fsSL https://archcore.ai/install.sh | bash`
     > - Windows (PowerShell 5.1+): `irm https://archcore.ai/install.ps1 | iex`
     > - Verify: `archcore --version`
     > - Full docs: https://docs.archcore.ai/cli/install/

Do **not** attempt `brew install`, `go install`, package-manager wrappers, or any other install command — they are not the supported path and will produce a CLI that is not version-compatible with the plugin.

### Pre-flight: gating and lazy reading

Two disciplines bind the whole run:

- **Gating (write boundary).** `init_project()` and the read-only MCP calls (`list_documents`, `get_document`) are infrastructure — they run **before** the preview. `create_document` and `add_relation` are the **only** gated operations: none fire before the user types `confirm`. `cancel` therefore leaves `.archcore/` content-empty (the directory and `settings.json` may exist from `init_project`, which is harmless and idempotent).
- **Lazy reading (two sub-phases).** The `lib/*.md` catalogs are heavy (≥ 1000 lines combined) — read them in two ordered batches, never all at once. The **Detect** sub-phase (Phase A) loads the *detection* catalogs and, for each detector it runs, captures into working memory both the signals AND the small `## Output` create-fields + body template it will reuse later. The **Compose** sub-phase (Phase B) loads the *composition* contracts (`_shared/precision-rules.md`, `_shared/spec-contract.md`, `_shared/rule-contract.md`, `lib/compose-overview.md`, `lib/extract-routing.md`) and **reuses the Output fields/templates already captured during Detect** — it does not re-read the bulky detection heuristics. "Release the detection catalogs" at the end of Phase A means dropping their heuristic prose from focus, not the captured Output specs.

### Step -1: Initialize and acknowledge (fast)

Call `mcp__archcore__init_project()` exactly once (pre-gate infrastructure — idempotent, safe on an already-initialized project). It creates `.archcore/` and `settings.json` if missing.

Immediately after, give the user a one-line confirmation:

- Response includes `initialized: true` (created now) — print: *"Archcore initialized at `.archcore/`."*
- `already_initialized: true` — print nothing here; the existing knowledge base speaks for itself in Step 0(a).

Do NOT ask the user to run `archcore init` in the terminal — `init_project` is the correct path in a plugin session.

### Step 0: Check state and source signal

Two cheap probes, in order. Each can short-circuit the whole skill. Neither reads anything under `lib/`.

#### Step 0(a) — Existing documents

Call `mcp__archcore__list_documents()` once. Derive:

- `has_stack_rule` — a `rule` whose title contains "stack" in `conventions/`.
- `has_run_guide` — a `guide` whose title contains "run"/"running" in `onboarding/`.
- `has_data_model` — any `doc` tagged `data-model`.
- `has_integrations` — any `doc` tagged `integrations`.
- `has_config` — any `doc` tagged `config`.
- `has_entry_points` — any `doc` tagged `entry-points`.
- `has_surface` — any `doc` tagged `surface`.
- `has_top_level_map` — any `doc` tagged `top-level-map`.
- `has_overview` — any `doc` tagged `architecture-overview`.
- `has_imports` — any document tagged `imported`.

**Already-seeded early-exit.** If `has_stack_rule` AND `has_run_guide` AND `has_overview` are all true AND **neither `--refresh` nor `--domain` was passed**, reply:

> Init already seeded this repo. Use `/archcore:context` to see what applies to a code area, or `/archcore:audit` for the dashboard. To add facts that appeared since (a new schema, config, or modules), re-run `/archcore:init --refresh`; to drill into another domain, `/archcore:init --domain=<slug>`.

Then stop. **With `--refresh` or `--domain`, skip this early-exit and proceed** — every already-present artifact is marked **skip (exists)** in the preview and only missing ones are composed. (`--domain` additionally scopes the run to one domain; see Step A.0.)

#### Step 0(b) — Source-signal gate (empty-repo early exit)

Single filesystem probe — one shell call, no catalog reads. Detect whether the repository has any executable shape yet:

- **`has_manifest`** — at least one of these exists at the project root (depth ≤ 2 for monorepo workspaces): `package.json`, `pyproject.toml`, `Pipfile`, `requirements.txt`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`, `*.csproj`, `*.fsproj`, `*.vbproj`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `mix.exs`, `Package.swift`. **This list is seed examples, not exhaustive** — also treat ANY project-defining manifest or build file as a manifest (e.g. `CMakeLists.txt`, `Makefile`, `dune-project`/`*.opam`, `deps.edn`/`project.clj`, `pubspec.yaml`, `build.sbt`, `stack.yaml`/`*.cabal`, `*.tf`/`*.tfvars`, `Chart.yaml`, `project.godot`, `*.sln`, `Project.toml`, and agent/LLM-plugin manifests such as `marketplace.json` / `plugin.json` / `.claude-plugin/*`).
- **`has_top_level_source`** — at least one file with a recognizable source extension exists anywhere under the project root, capped at depth 3, excluding `.archcore/`, `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `coverage/`, `.venv/`, `__pycache__/`, `.next/`, `.turbo/`. Extensions: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.py`, `.rs`, `.go`, `.rb`, `.php`, `.java`, `.kt`, `.kts`, `.swift`, `.cs`, `.fs`, `.ex`, `.exs`, `.scala`, `.clj`, `.cljs`. **The extension list is seed examples, not exhaustive** — also count any file whose contents are plainly source (a shebang, or import/include/package/module/def/func/class/use constructs), and recognize other common code extensions (e.g. `.vue`, `.svelte`, `.astro`, `.dart`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, `.m`, `.mm`, `.ipynb`, `.hs`, `.ml`, `.mli`, `.tf`, `.sol`, `.lua`, `.jl`, `.r`, `.zig`, `.nim`, `.gd`).

If BOTH are false, take the **empty** route. Reply with exactly:

> Archcore is ready at `.archcore/`. No source code detected yet — nothing to set up.
>
> Re-run `/archcore:init` after the first manifest or source file lands. The SessionStart empty-state nudge will keep pointing here until then.

Then stop. **Do NOT** create placeholder documents — they have no practical value, cost roundtrips and tokens, and suppress the SessionStart empty-state nudge that is the user's breadcrumb back here.

Otherwise (`has_manifest` OR `has_top_level_source`), proceed to Phase A.

---

## Phase A — DETECT (no writes; detection catalogs only)

Compute everything the seed needs in one detection pass. No documents are created here, and no composition contract is opened. For each detector, capture its signals AND its `## Output` create-fields for reuse in Phase B/E.

**Detect high-level, for ANY stack.** Each `detect-*` catalog leads with *what* it detects (the concept) and a universal, evidence-first method; its concrete lists of frameworks / ORMs / SDKs / extensions / conventional roots are **non-exhaustive examples**, not a checklist. When a project's language, framework, or layout is unfamiliar or highly specific, reason from first principles per the catalog — the entry file's imports, the dominant file types, the manifest / build system, and what the code actually does — and emit a fact only on **positive evidence** (prefer omission over a guess). Never return empty / `small` / "no entry points" merely because nothing matched a list.

### Step 0.5: Scale

Read `lib/detect-scale.md`, `lib/detect-domains.md`, `lib/detect-modules.md`.

1. **Parse arguments** — `--mode=X` (force the mode), `--domain=<slug>` (force a large-mode single-domain pass; see Step A.0), `--refresh` (already consumed in Step 0a).
2. **Compute signals:** `domain_count` (per `detect-domains.md`), `module_count` (source files > 100 LOC, excluding tests/generated), `entry_point_count` (per `detect-entry-points.md`, informational).
3. **Classify** per `detect-scale.md` — apply its evidence-based fallback when the language/layout is unlisted (recompute counts from the dominant code extension and tracked-file breadth; do not default to `small` just because the extension/root lists miss). A forced `--mode` wins but remember the auto-detected one; `--domain` forces large-mode behavior scoped to the named domain.

### Step A.0: Domain selection (large mode only)

Skip unless mode is `large`.

1. **`--domain=<slug>` given** — that domain is the sole selection; skip the dialog. (Tier-1 facts already present are skipped; the run tops up this domain's data-model + hotspot specs.)
2. **Otherwise** — present the top 5 ranked domains (per `detect-domains.md` ranking) and ask: *"Which domains are you working on now? (pick 1–3 by name or number, or `skip` to defer.)"* Accept a single name, a comma list, or `skip`.
3. **Scope** the subsequent steps (A.1 data-model, A.3 hotspots) to the selected domains' trees. On `skip`, seed whole-repo Tier-1 facts and **no** hotspot specs. Remember the unselected domains for the closing message.

### Step A.1: Shape — single manifest batch

Read `lib/detect-stack.md`, `lib/detect-data-model.md`, `lib/detect-integrations.md`, `lib/detect-config.md`. **Read each manifest file once** (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `schema.prisma`, `.env.example`, …) and feed all four detectors from that shared parse — never re-read a manifest per detector. Collect:

- **Stack signals** (≤ 5) — per `detect-stack.md`.
- **Data model** — entities + key relations, NAMES ONLY, per `detect-data-model.md` (scoped to selected domains in large mode). Skip if no schema.
- **Integrations** — external services from allowlisted SDK deps, per `detect-integrations.md`. Skip if none.
- **Config surface** — env-var NAMES + purpose, **never values**, per `detect-config.md`. Skip if no env contract.

### Step A.2: Run commands, entry points & surface

- **Run commands** — per `lib/extract-run-instructions.md` (README section → scripts → ask the user once if neither yields anything).
- **Entry points** — per `lib/detect-entry-points.md`, bucketed HTTP / CLI / Worker / Cron / Other. Seed the entry-point `doc` in any mode when ≥ 1 entry point exists; in large mode group by domain.
- **Public surface** — per `lib/detect-surface.md`. The role-based outward shape the entry-point inventory does NOT cover: web routes/pages, a library's exported API, a multi-command CLI's command catalog, an agent-plugin's skills/commands, mobile screens. Seed the public-surface `doc` when such a surface exists and is not already fully enumerated as entry points; in large mode group by domain. This is the fact that gives library / SPA / plugin / markdown-tooling repos a substantive seed.

### Step A.3: Hotspots & cross-cutting (candidates only — NO source reads)

- **Hotspot candidates** — rank per `lib/detect-hotspots.md`; take the top-N for the mode (small 3 / medium 5 / large 3 per selected domain). Collect path + LOC + companion-test LOC + suggested type. The catalog ranks in two tiers: a tests-aware **primary** tier, and — when it yields fewer than N — a **test-independent fallback** (fan-in / public surface / size / churn) so repos with no tests (scripts, SPAs, ML, CLIs, agent-plugin/markdown tooling) still surface real specs instead of an empty pool. Mark fallback-tier stubs with their qualifying signal. **Tier-2 artifacts are always composed as `spec`** — use the `adr`/`task-type` hints in `detect-hotspots.md` only to *filter out* ineligible candidates (e.g. a `utils`/`helpers` module, or one failing `spec-contract.md`'s "when NOT to write a spec"), never to switch the document type. **Do not read source files yet** — that read is deferred to Phase E for kept specs only.
- **Cross-cutting candidates** (medium and large, whole-repo) — per `lib/detect-cross-cutting.md`, at most 2. init uses that catalog for **detection only** and overrides its standalone y/n "Output" flow: each candidate becomes a Tier-2 `rule` stub here and is created in Phase E, not handed to `/archcore:decide`.

### Step A.4: Agent files

Detect `CLAUDE.md` / `AGENTS.md` / `.cursorrules` candidates per `lib/agent-files.md` (paths + byte sizes). Estimate the extract **yield** cheaply without loading `extract-routing.md`: count H1/H2/H3 headings per file, capped at 10 (an upper bound). Compute the cost tier: **HIGH** if combined size > 50 KB OR file count > 5 OR estimated yield > 8 documents. Note: yield matters only for the *extract* path; a *link* import (the default) yields exactly 1 doc.

### Step A.5: Announce

Print one detection line, e.g.:

> Mode: medium (28 modules, 1 domain). Detected: Prisma (6 entities), Stripe + AWS, 12 env vars, 5 entry points, 5 hotspot candidates, 1 cross-cutting pattern, CLAUDE.md (4 KB). Composing the plan…

In large mode, report the figures for the **selected** domains (selection already happened in Step A.0). Detection done — release the detection catalogs (heuristic prose), keeping the captured Output specs.

---

## Phase B — COMPOSE (in memory; composition contracts only)

Load the composition contracts and compose every planned artifact **without writing**. Honor each catalog's line cap. Mark any artifact whose `has_*` flag is already true as **skip (exists)**. Exception: in large / `--domain` mode the per-domain data-model doc (`<domain-slug>-data-model`) dedupes by its own filename, not the repo-wide `has_data_model` tag — so a newly-selected domain's data-model is still composed when other domains' already exist.

- **Tier-1 facts (full bodies, cheap/extractive):**
  - stack rule — `detect-stack.md` template (≤ 6 lines).
  - run guide — `extract-run-instructions.md` (single-app ≤ 15 lines; monorepo per-app ≤ 6).
  - data-model doc — `detect-data-model.md` Output (≤ 40 lines), when detected.
  - integrations doc — `detect-integrations.md` Output (≤ 15 lines), when detected.
  - config doc — `detect-config.md` Output (≤ 20 lines, **NAMES ONLY**), when detected.
  - entry-point inventory — `detect-entry-points.md` Output, when ≥ 1 entry point.
  - public-surface doc — `detect-surface.md` Output (≤ 25 lines, **NAMES + purpose only**), when a surface exists that entry points don't already cover.
  - top-level map — `detect-domains.md` Output (large mode).
- **Tier-2 stubs (NO source reads):**
  - hotspot specs — one stub each: suggested spec title, the qualifying `LOC / test-ratio`, target filename + directory, and an estimated synthesis cost ≈ `(source_LOC + test_LOC) × 6` tokens. The full body is composed only after confirm.
  - cross-cutting rules (medium/large) — one stub each: the pattern + the paths it would govern. Full body composed after confirm under `rule-contract.md`.
- **Capstone:** plan the architecture-overview per `lib/compose-overview.md`. Its body indexes the *confirmed* seed, so it is composed in Phase E once the set is final. List it in the preview as "Architecture overview — index of the above".
- **Agent-file import:** default to **link** (a one-line pointer `doc` per file, ~0 synthesis cost) per `lib/agent-files.md`. *Extract* (split into typed docs per `lib/extract-routing.md`) is offered only on explicit user opt-in via `edit`. Reuse the `agent-files.md` encoding (`imported` + `source:<slug>` tags, pointer first line) captured in Detect. Carry the HIGH-cost flag from Step A.4 (it gates the extract opt-in).
- **Planned relations:** per the `compose-overview.md` "Relation wiring" table.

No `create_document` / `add_relation` has run yet.

---

## Phase C — PREVIEW (one manifest)

Present the entire plan as a single grouped manifest, then wait. Example:

```
Init plan — mode: medium.   confirm / edit / cancel

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
Imports:
  • CLAUDE.md (4 KB) — link, 1 doc                         ~0   (edit → extract)
Relations: ~14 edges.
Estimated total: ~18k tokens.
Already present (skipped): <list, or "none">.
```

- For each **Tier-2 stub** show the qualifying `LOC / test-ratio` and the per-item synthesis cost, so `edit` is an informed budget lever.
- For the **agent-file import**, show it as **link** by default with `(edit → extract)`; if a file's cost tier is **HIGH**, prefix `⚠️ HIGH COST` on the extract option — extract is only entered when the user explicitly opts in.

## Phase D — CONFIRM

Wait for the user.

- **`cancel`** → stop. Fire zero `create_document` / `add_relation` calls. No partial state.
- **`edit`** → accept deselections by name/number ("drop spec:auth-client", "skip import", "rules only"), opt-ins ("extract CLAUDE.md"), and batch answers ("link all"). Re-show the trimmed total, then proceed.
- **`confirm`** → Phase E with the surviving set.

A deselected Tier-2 spec's source file is **never read** — the read happens in Phase E only for kept specs.

## Phase E — CREATE + WIRE (gated; runs only after confirm)

For the confirmed set only, in order:

1. **Tier-1 facts** — `create_document` per the fields in each catalog's `## Output` section (type / directory / filename / title / status / tags). Skip any marked exists.
2. **Hotspot specs** — for each kept stub: **now** read its source + companion tests, compose the full body under `_shared/spec-contract.md`, then `create_document(type='spec', filename=<module-slug>, directory=<domain-or 'architecture'>, tags=['spec', <area>])`. Skip if a doc with that filename already exists (dedupe).
3. **Cross-cutting rules** — for each kept stub: compose under `_shared/rule-contract.md`, `create_document(type='rule', filename=<concern-slug>, directory='conventions', status='draft', tags=['conventions', <concern>])`. `status='draft'` because the rule is heuristic-derived and the user should confirm phrasing before it is canon. Skip if that filename already exists.
4. **Agent-file import** — execute kept items: link (default) or extract (opt-in) per `lib/extract-routing.md`; dedupe against existing `source:<slug>` tags first.
5. **Architecture overview** — skip if `has_overview`. Otherwise, now that the seed is final, compose its body per `compose-overview.md` (structural-facts line + type/topic index of the *created* docs) and `create_document`.
6. **Relations** — `add_relation` per the planned wiring table; skip any edge whose endpoints were not both created. Roll forward on individual failure (surface the error, keep successful edges; do not delete prior creates).
7. **Report** one line per created document plus the total edge count.

### Closing message: outlook

Summarize what was created, then make the value-loop visible and list the over-time targets. Per-mode template. **Conditionalize the "Try it now" line:** if ≥ 1 hotspot spec was created, point at the top hotspot path; if none (empty pool or all deselected), point at a seeded fact via `/archcore:context` instead.

**Small:**

> Done. Seeded: stack rule, run guide[, data-model, integrations, config, entry points], architecture overview, and N hotspot specs.
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects via `check-code-alignment`. (No hotspot specs? Run `/archcore:context <a seeded area>` to see what applies.) Over time: ADRs for non-trivial dependency choices (`/archcore:decide`), more specs (`/archcore:capture <path>`), a task-type for any repeating extension pattern.

**Medium:**

> Done. Seeded: stack rule, run guide, data-model, integrations, config, entry points, architecture overview, N hotspot specs[, M cross-cutting rules].
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects. `/archcore:context <path>` shows what applies. Over time: ADRs for architectural decisions (persistence, auth, observability), more specs, rules per cross-cutting concern, task-types for common change patterns — via `/archcore:decide`, `/archcore:capture`, `/archcore:plan`.

**Large:**

> Done. Seeded: workspace stack rule, monorepo run guide, top-level map (N domains), entry points, data-model + integrations + config, architecture overview. Focused on: <selected-domains>. Created M hotspot specs in the selected domains[ and K repo-wide cross-cutting rules].
>
> Try it now: edit a file under `<a selected-domain hotspot path>` — its spec auto-injects via `check-code-alignment`. Other domains: <list>. Run `/archcore:init --domain=<slug>` later to drill into any of them, and `/archcore:context domain:<slug>` to scope queries. Over time each domain needs its own ADRs, specs, and task-types; repo-wide cross-cutting rules (logging, errors, auth, transactions, telemetry) accrue via `/archcore:decide`.

Always end with:

> Use `/archcore:audit` for the dashboard, `/archcore:audit --deep` for a health audit.

## Result

Mode-appropriate, single-confirm `.archcore/` seed (created only on `confirm`; existing artifacts skipped):

- **Empty**: 0 seeded — `.archcore/` and `settings.json` only. Fast acknowledge + early exit. No catalog files read.
- **Small**: ~5–9 docs — stack rule, run guide, the Tier-1 facts that were detected (data-model / integrations / config / entry points / public surface), architecture overview + 3 hotspot specs (the hotspot fallback tier keeps this non-zero even in test-less repos).
- **Medium**: ~8–12 docs — small set + 0–2 cross-cutting rules + 5 hotspot specs.
- **Large**: ~12–20+ docs — medium set + top-level map + domain selection + 3 hotspot specs per selected domain.

Idempotency: the flagged Tier-1 facts, the overview, and imports are skip-on-exists; Tier-2 specs/rules dedupe by filename before create. A second `/archcore:init` on a fully-seeded repo early-exits (Step 0a) unless `--refresh` (top up newly-detectable facts) or `--domain` (scoped domain pass) is passed. Tier-2 spec bodies and the overview are composed only after `confirm`, so a `cancel` or deselect spends no source-read cost. The empty route never creates placeholder documents, keeping `.archcore/` functionally empty so the SessionStart nudge keeps pointing here.
