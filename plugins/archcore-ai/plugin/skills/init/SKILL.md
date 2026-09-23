---
name: init
argument-hint: "[import|refresh] [path or domain]"
description: "First-time Archcore setup. Wires the host (MCP config, hooks, CLAUDE.md/AGENTS.md managed block), measures the authored context the repo already holds, then composes a first-day seed — stack rule, run guide, data-model, integrations, config, entry points, public surface, a linked architecture overview, and specs for the top hotspot modules — shown in ONE preview and created on a single confirm. Modes, named as the first word: init import converts the repo's authored context — CLAUDE.md, AGENTS.md, .cursor/rules and other agent instructions, ADR and RFC folders, contributor docs, internal pages of a published docs site, recoverable git history — into native typed documents with no import marks, staged by a plan when the volume is large; init refresh adds facts that appeared since, or drills into one domain with init refresh <domain>. Use on a fresh clone, empty `.archcore/`, 'set up archcore', 'migrate our CLAUDE.md to archcore', 'import our docs and ADRs', or to wire host configs. Not for individual docs or planning."
---

# /archcore:init

First-time onboarding. Wires the host, measures the authored context the repository already holds, and fills `.archcore/` from two sources — what people wrote and what the code shows — so the code-alignment hook and per-command grounding have substance from day one. Per `magic-first-day-init.adr` and `init-import-mode.adr`: extractive facts are composed in full; authored content wins over synthesized content on the same subject; the overview is an index, never a prose blob. **Nothing is written before `confirm`.**

Before planning or writing relations, load `skills/_shared/relation-authoring.md`.
Apply its claim check to seed and import wiring after reading the endpoint content.

## Arguments

The first word selects the run: `import` or `refresh`. These two words are the command's modes in the sense of `command-surface-v2.spec`. The rest of the arguments is the subject. No arguments, or any other first word, start a plain init.

- `import [path]` — convert the repository's authored context into native documents, at all five discovery levels of `lib/sources.md`; a path limits the run to that path. Resumes an open import plan when one exists.
- `refresh [path or domain]` — re-run on a seeded repo to add facts that appeared since (a new schema, config, or modules) and to retrofit host wiring. A subject scopes the top-up: an existing path wins; otherwise a detected domain slug runs the single-domain pass. Bypasses the "already seeded" early-exit.
- Depth and scale are not arguments. The preview offers the toggles `depth:light|standard|deep` (default `standard`) and `scale:small|medium|large`, where the user already sees each choice's cost (`lib/seed-compose.md`). Import has no depth.
- A retired form as the first word — `domain`, or a flag such as `--refresh`, `--depth=deep`, `--scale=large` — starts a plain init; name the current form once: *"`/archcore:init [import|refresh] [path or domain]`; depth and scale are toggles in the preview."*

## When to use

- Empty `.archcore/` — the SessionStart nudge points here.
- First session on a fresh clone / fresh install.
- User says: "initialize archcore", "set up archcore", "seed archcore", "first-time setup", "what should I do first".
- User says: "migrate our CLAUDE.md / AGENTS.md / cursor rules to archcore", "import our ADRs and docs", "move our docs into archcore" → `import`.

**Not init** (route elsewhere):

- Recording a specific decision → `/archcore:document`.
- Planning a feature → `/archcore:plan`.
- Documenting one module → `/archcore:document`.
- Codifying a team standard → `/archcore:document` (offers rule + guide continuation).
- Filing one external material or a finished report → `/archcore:document research`.
- Reading applicable context before coding → automatic; the code-alignment hook injects it on file edits.
- Docs health audit → `/archcore:review`.

## Routing table

**Mode routing** — evaluated top-to-bottom, first match wins.

| Signal | Route | Flow files |
|---|---|---|
| First word `import`, and the assessment gate (step 5) finds no authored source | → **no-source**: the no-source report; no gated operation, no confirm, no code seed | `lib/sources.md` "No authored source" |
| First word `import` | → **import**: the whole import track, levels L1–L5; no code seed | `skills/_shared/tracks/import.md`, `lib/sources.md` |
| First word `refresh` | → **refresh**: plain-init flow with the early-exit bypassed; existing artifacts are **skip (exists)** | as the plain rows below |
| Open import plan found (step 3) on a plain init | → report the plan, name `/archcore:init import`, then continue the plain init without new conversion targets | — |
| No manifest, no source, no authored source (step 4) | → **empty**: host wiring only, behind its own mini-confirm | `lib/host-wiring.md` "Empty route" |
| No manifest and no source, authored sources found | → **import-only**: host wiring + the import track in one preview; no code seed | `skills/_shared/tracks/import.md` |
| Anything else | → **plain init**: host wiring + facts + the fill the assessment gate divides | `lib/seed-detect.md`, `lib/seed-compose.md` |

**Fill routing** — what the assessment gate (step 5) decides on a plain init or a refresh. The extractive facts are composed in **every** row.

| Assessment result | Authored sources | Hotspot specs |
|---|---|---|
| no authored source — nothing found, or every source found is `skip` | none; the announce line names what was checked, and names `/archcore:init import` when deeper levels hold files | the depth's budget over the unchanged ranked pool |
| tier `S` (≤ 8 targets) | every target listed in the init preview; converted on the init confirm | budget over the pool **minus** the `coverage_set` |
| tier `M` (9–40) or `L` (> 40) | the init confirm creates the import plan and runs wave 1; the closing message names `/archcore:init import` | budget over the pool **minus** the `coverage_set` |

Scale routing (small / medium / large, and what each seeds) lives in `_shared/grounding/detect-scale.md` and `lib/seed-compose.md`. Tier-1 facts are seeded in any scale **when detected** — breadth scales with the repo, presence does not.

**Follow-up routing** — closing-message hand-offs. Init surfaces these as todos; MUST NOT auto-invoke.

| User wants to... | → Invoke |
|---|---|
| Continue an open import, or import beyond agent files and ADR folders | `/archcore:init import` |
| Import one folder only | `/archcore:init import <path>` |
| Add facts that appeared since first init | `/archcore:init refresh` |
| Drill into another domain (large) | `/archcore:init refresh <domain>` |
| Capture another module, record a decision, codify a convention | `/archcore:document` |
| Plan a feature | `/archcore:plan` |
| Scope queries to a domain (large) | `mcp__archcore__search_documents` with the domain tag |
| See what's loaded | `/archcore:review` |

## Execution

Content voice: default to architectural prose — decisions, rationale, intent. See `skills/_shared/precision-rules.md` Rule 6. Code blocks only where the document type requires it (`rule`, `guide`, `cpat`, and `spec` examples) or the user asks.

**Gating (write boundary).** `init_project()` and the read-only MCP calls (`list_documents`, `get_document`, `search_documents`) are infrastructure — they run **before** the preview. Three groups of operations are gated:

- document writes: `create_document`, `update_document`, `remove_document`, `add_relation`;
- host-wiring writes: `install_host_config` / `archcore init --agent` — they touch files outside `.archcore/`, like `.mcp.json` and `.claude/settings.json`;
- the source-file edits of the import track's retire gate.

**No gated operation fires before the user types `confirm`.** Absence of an answer is never `confirm`: IF this invocation cannot receive further user input in this turn (a print-mode run, a sub-agent call), THEN print the preview and stop. `cancel` therefore leaves `.archcore/` content-empty and the repo's files untouched (the directory and `settings.json` may exist from `init_project`, which is harmless and idempotent).

**Lazy reading.** Load a flow file only when its step starts: `lib/host-wiring.md` at step 1, `lib/sources.md` at step 5, `lib/seed-detect.md` then `lib/seed-compose.md` at step 6, `skills/_shared/tracks/import.md` when a route reaches it. Never load them all at once.

### 1. Pre-flight — CLI and host-wiring gate

Run the CLI availability check and the `cli-gte 0.7.0` host-wiring version gate per `lib/host-wiring.md` "Pre-flight". The canonical installer is documented at https://docs.archcore.ai/start/install/; never suggest another install channel. A missing CLI that the user declines to install stops the run. A CLI older than v0.7.0 continues with host wiring **disabled**.

### 2. Initialize and probe the host

Call `mcp__archcore__init_project()` exactly once (pre-gate infrastructure — idempotent, safe on an already-initialized project). It creates `.archcore/` and `settings.json` if missing. On `initialized: true` print *"Archcore initialized at `.archcore/`."*; on `already_initialized: true` print nothing.

Then run the host and project-root probe per `lib/host-wiring.md` "Host and project root probe" — always, even when host wiring is disabled. It prints one token: `claude-code` | `cursor` | `codex-cli` | `__UNKNOWN__`. On `__UNKNOWN__`, or anything else than the three host tokens, ask one `AskUserQuestion` — "Which AI host is this session running in?" with options Claude Code / Cursor / Codex (CLI or desktop app) / GitHub Copilot CLI — and map the answer to the agent id (`claude-code` / `cursor` / `codex-cli` / `copilot`); there is no `codex-desktop` id. A GitHub Copilot CLI session always lands on `__UNKNOWN__`. Do not run `archcore init` yourself at this step; if the archcore MCP tools are unavailable in this session, the terminal command `archcore init --agent <host> --project "<root>"` is the user's recovery path.

Host wiring is planned **first** in every preview: when the probe finds the host configs absent, the Host wiring line leads the preview, and its writes lead the create phase.

### 3. Check state

Call `mcp__archcore__list_documents()` once. **Derive every flag below from local documents only** — skip any result carrying `global: true` / `read_only: true` / `source_kind: "global"`. A mounted global source must not satisfy the already-seeded early-exit: init seeds THIS repo's documents. If any global results appear, load `skills/_shared/globals.md`; never modify a global document and never target one with `add_relation`. Derive:

- `has_stack_rule` — a `rule` whose title contains "stack" in `conventions/`; `has_run_guide` — a `guide` whose title contains "run"/"running" in `onboarding/`.
- `has_data_model`, `has_integrations`, `has_config`, `has_entry_points`, `has_surface`, `has_top_level_map`, `has_overview` — any `doc` tagged `data-model`, `integrations`, `config`, `entry-points`, `surface`, `top-level-map`, `architecture-overview`.
- `open_import_plan` — a local `plan` tagged `import-plan`.

**Open import plan.** On `import`, resume it (`skills/_shared/tracks/import.md`, "Track state and the import plan") and skip steps 4–5. On a plain init or a refresh, report it — rows done, rows open — and name `/archcore:init import`; plan no new conversion targets in this run.

**Already-seeded early-exit.** If `has_stack_rule` AND `has_run_guide` AND `has_overview` are all true AND the first word is neither `refresh` nor `import`, reply:

> Init already seeded this repo. Applicable context auto-injects on file edits via the code-alignment hook; use `/archcore:review` for the dashboard. To add facts that appeared since (a new schema, config, or modules), re-run `/archcore:init refresh`; to drill into one domain, `/archcore:init refresh <domain>`; to convert the repo's authored docs and agent instructions, `/archcore:init import`. (Seeded before host wiring existed, or missing the host configs? `refresh` also adds host wiring — MCP config, SessionStart hook, usage hint.)

Then stop. On a `refresh` run, skip this early-exit — every already-present artifact is marked **skip (exists)** in the preview and only missing ones are composed. Resolve a `refresh` subject here: an existing path → path scope; else a detected domain slug → single-domain pass; else ask one question that lists the detected domains.

### 4. Source-signal gate

Single filesystem probe — one shell call, no catalog reads:

- **`has_manifest`** — at least one project-defining manifest or build file at the project root (depth ≤ 2 for monorepo workspaces): `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`, `*.csproj`, `pom.xml`, `build.gradle*`, `mix.exs`, `Package.swift`. **Seed examples, not exhaustive** — also `CMakeLists.txt`, `Makefile`, `deps.edn`, `pubspec.yaml`, `build.sbt`, `*.cabal`, `*.tf`, `Chart.yaml`, `*.sln`, and agent/LLM-plugin manifests such as `marketplace.json` / `plugin.json` / `.claude-plugin/*`.
- **`has_top_level_source`** — at least one file with a recognizable source extension under the project root, capped at depth 3, excluding `.archcore/`, `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `coverage/`, `.venv/`, `__pycache__/`, `.next/`, `.turbo/`. The extension list is **not exhaustive** — count any file whose contents are plainly source (a shebang, or import/include/package/module/def/func/class constructs).

If BOTH are false, do not decide yet — step 5 tells whether authored sources exist. Both false and no authored source → the **empty** route of `lib/host-wiring.md` (no placeholder documents, ever). Both false with authored sources → the **import-only** route.

### 5. Assessment gate

Skip on the `import` mode when step 3 resumed a plan. Otherwise read `lib/sources.md` and run the assess gate of `skills/_shared/tracks/import.md` in callable mode: list authored sources from paths, byte sizes, heading counts, and path mentions — never a full file body — with sizes computed only **after stripping any archcore managed block** (a file whose only content is the managed block is not a source). A plain init and a refresh assess levels L1–L2 — agent instructions (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, `.github/instructions/*.md`, and the other L1 paths) and decision records; `import` assesses L1–L5. A plain init and a refresh also record `deeper_present` — a presence-only path listing of L3–L4 that feeds no measure.

The gate returns `targets_est`, `tier`, `coverage_set`, and `levels_found`. Announce them in one line, e.g.:

> Authored context: 9 sources at L1–L2 (CLAUDE.md 6 KB, 6 .cursor/rules files, docs/adr × 2) → ~14 target documents, tier M. 2 hotspot modules look covered (estimate).

Print the line in every run, including the run that finds nothing. WHEN the gate returns no authored source (`levels_found` is empty), follow `lib/sources.md` "No authored source": a plain init or a refresh prints the "none" announce line and goes on to step 6 with the pool unchanged; the `import` mode prints the no-source report and stops — it MUST NOT fall back to the code seed, because the user asked for a conversion and the seed is a separate, costlier run.

### 6. Run the route

- **Plain init / refresh** — run `lib/seed-detect.md` (Phase A — DETECT), then `lib/seed-compose.md` (Phase B compose → Phase C preview → Phase D confirm → Phase E — CREATE + WIRE). The `coverage_set` narrows the hotspot pool in Phase A; the authored block of the preview follows the Fill routing table. One preview, one confirm.
- **Import / import-only** — run `skills/_shared/tracks/import.md` from its discover gate (or from the resumed row). Its plan preview carries the Host wiring line when wiring is absent. One confirm per wave when the plan grew; a separate confirm before any source file is edited.

### 7. Close

Seed runs close per `lib/seed-compose.md` "Closing message"; host-wiring outcome lines per `lib/host-wiring.md`. Import runs close with: documents created by type, the conflicts list, fidelity departures, rows still open with `/archcore:init import` as the continuation, and — after the last row — the retire offer and the removal of the import plan. Always end with:

> Use `/archcore:review` for the dashboard, `/archcore:review deep` for a health audit.

## Result

A `.archcore/` filled from two sources, created only on `confirm`; existing artifacts skipped.

- **Empty**: 0 content docs — `.archcore/` and `settings.json`, plus host wiring behind its own mini-confirm. No catalog files read.
- **Plain init**: host wiring, the detected Tier-1 facts, the architecture overview, hotspot specs for the depth's budget over the pool that authored sources do not cover (the spec budget has no absolute maximum — `standard` 25% of the ranked pool, `light` 10%, `deep` 60%; `lib/seed-compose.md`), cross-cutting rules (medium/large), and — tier `S` — the converted authored documents, or — tier `M`/`L` — the import plan with wave 1 done. Every synthesized or converted document is `status='draft'`.
- **No-source** (`import` found nothing to convert): 0 documents, 0 file writes — a per-level report of what was checked, each `skip` with its class, and the next command.
- **Import**: native typed documents (`rule`, `adr`, `rfc`, `guide`, `spec`, `doc`, `idea`) clustered by topic across sources, linked to each other and to the seed facts where their claims support a relation; a conflicts list instead of silent choices; no `imported` tag, no `source:` tag, no pointer line, no `imported-` prefix. After the last wave: the retire offer for agent-instruction files, then the import plan is removed, so the corpus holds no record of the import.

Idempotency: the flagged Tier-1 facts and the overview are skip-on-exists; Tier-2 specs and rules dedupe by filename before create; conversion targets dedupe by a topic search before create and, for tiers `M`/`L`, by the import plan's row states. Host wiring is idempotent end-to-end. A second `/archcore:init` on a fully-seeded repo early-exits (step 3) unless `refresh` or `import` is the first word. The empty route never creates placeholder documents, so the SessionStart nudge keeps pointing here.
