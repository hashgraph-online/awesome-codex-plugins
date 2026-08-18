---
name: init
argument-hint: "[--depth=light|standard|deep] [--mode=small|medium|large] [--domain=<slug>] [--refresh]"
description: "First-time Archcore setup. Detects repo scale and shape, then composes a full first-day seed — stack rule, run guide, data-model, integrations, config, entry points, public surface, a linked architecture overview, and specs for the top hotspot modules — shown in ONE preview and created on a single confirm, plus host wiring (MCP config, hooks, CLAUDE.md/AGENTS.md managed block). Imports agent-instruction files — aggregate files (CLAUDE.md/AGENTS.md/.cursorrules) as link stubs, modular rule files (.cursor/rules/*.mdc and equivalents) as rule docs by default. Use on a fresh clone, empty `.archcore/`, 'set up archcore', or to wire host configs (MCP/hooks/CLAUDE.md+AGENTS.md). Not for individual docs or planning."
---

# /archcore:init

First-time onboarding. Detects repo scale (small / medium / large) and shape, composes a scale-appropriate seed of `.archcore/` documents, shows them in **one preview**, and creates them on a **single `confirm`** — so the code-alignment hook injection and per-command grounding have substance and the relation graph is live from day one. The same confirm also installs **host wiring** (project MCP config, SessionStart hook, usage hint — the same files `archcore init` writes), so the repo works for CLI-only teammates. Per `magic-first-day-init.adr`: extractive facts are composed in full; the top hotspot modules get real `spec`s (synthesized only after confirm); the overview is an index, never a prose blob. **Nothing is written before `confirm`.** Exact per-mode output is in the Routing Table below.

## Arguments

- `--depth=light|standard|deep` — synthesis budget (default `standard`), orthogonal to `--mode`. See the Depth axis section below. Also settable via the `depth:<tier>` toggle in the preview.
- `--mode=small|medium|large` — force a mode, overriding auto-detection.
- `--domain=<slug>` — re-run focused on one domain (large repos): scopes data-model + hotspot specs to that domain's tree, tops up only its docs. Bypasses the "already seeded" early-exit.
- `--refresh` — re-run on an already-seeded repo to add facts that appeared since the first init (a new schema, config, or modules) — and to retrofit host wiring on repos seeded before wiring existed. Bypasses the early-exit; existing docs are skipped, missing ones composed.

## When to use

- Empty `.archcore/` — the SessionStart nudge points here.
- First session on a fresh clone / fresh install.
- User says: "initialize archcore", "set up archcore", "seed archcore", "first-time setup", "what should I do first".

**Not init** (route elsewhere):

- Recording a specific decision → `/archcore:document`.
- Planning a feature → `/archcore:plan`.
- Documenting one module → `/archcore:document`.
- Codifying a team standard → `/archcore:document` (offers rule + guide continuation).
- Reading applicable context before coding → automatic; the code-alignment hook injects it on file edits.
- Docs health audit → `/archcore:review`.

## Routing table

**Mode routing** — Step 0.5 classifier, evaluated top-to-bottom, first match wins. The **empty** route is decided earlier in Step 0(b). Precise conditions in `_shared/grounding/detect-scale.md`.

| Signal | Route | Seeded (composed when detected) |
|---|---|---|
| No manifest AND no top-level source (Step 0b) | → **empty** | no content docs — host wiring only, behind its own mini-confirm |
| `--mode=X` flag | → forced `X` (detected mode still reported) | per row below |
| `domain_count ≤ 1` AND `module_count ≤ 15` | → **small** | stack rule, run guide, data-model, integrations, config, entry points, public surface, overview + hotspot specs (`light` 3 / `standard` 4 / `deep` 6 — see Depth axis) |
| `domain_count ≤ 2` AND `module_count ≤ 40` | → **medium** | small set + cross-cutting rules (every depth — `light` ≤2 / `standard` ≤3 / `deep` ≤4) + hotspot specs (`light` 4 / `standard` 6 / `deep` 10 — see Depth axis) |
| `domain_count ≥ 3` OR `module_count > 40` | → **large** | medium set + top-level map + domain dialog + data-model per schema-bearing domain (all, not only selected) + hotspot specs (per-domain floor + repo-wide rank — `light` 2/domain min6 cap12 / `standard` 3/domain min10 cap24 / `deep` 4/domain min14 cap40 — see Depth axis) |

Every non-empty mode also composes the architecture-overview capstone, plans relation wiring, and offers agent-file import — aggregate files (CLAUDE.md / AGENTS.md / .cursorrules) as link stubs and modular rule files (`.cursor/rules/*.mdc`, `.github/instructions/*.md`, `.windsurf/rules/*.md`) as rule docs by default, per `lib/agent-files.md` — inside the preview. Tier-1 facts (data-model, integrations, config, entry points, public surface) are seeded in any mode **when detected** — breadth scales with the repo, presence does not. The public-surface fact is what carries the seed for library / SPA / multi-command-CLI / agent-plugin repos, where there is no server to enumerate as entry points. The empty route exits after Step 0.

**Follow-up routing** — closing-message hand-offs. Init surfaces these as todos; MUST NOT auto-invoke.

| User wants to... | → Invoke |
|---|---|
| Capture another module | `/archcore:document <path>` |
| Record a decision | `/archcore:document` |
| Codify a convention as a rule | `/archcore:document` |
| Plan a feature | `/archcore:plan` |
| Drill into another domain (large) | `/archcore:init --domain=<slug>` |
| Add facts that appeared since first init | `/archcore:init --refresh` |
| Scope queries to a domain (large) | `mcp__archcore__search_documents` with the domain tag |
| See what's loaded | `/archcore:review` |

## Depth axis (`--depth=light|standard|deep`)

Orthogonal to scale (`--mode`, which measures repo *size*). Depth sets the **synthesis budget**, not the artifact checklist. **Extraction is always on** in every depth — Tier-1 facts, imported authored rules, and the hotspot register are cheap and the highest-value / most-durable layer. Depth scales only the **expensive, staleness-prone synthesis**: spec bodies, cross-cutting rules, and big-file / aggregate extraction. Default: **`standard`** — a good first-day seed, not merely the cheapest one. Init is fully gated (nothing is written before `confirm`, and the preview shows all three depths' costs side by side before the user commits to any of them), so there is no reason to default to the thin tier just to be safe — `light` is the explicit **opt-down** for a cost-conscious user (still never empty — Universality invariant 3); `deep` is the explicit **opt-up** for a max plan.

| Depth | Hotspot specs | Cross-cutting synth (medium/large) | Big authored (>200) & CLAUDE.md/AGENTS.md | Authored decisions → ADR | Relations |
|---|---|---|---|---|---|
| **light** (opt-down) | small 3 / medium 4 / large 2-per-domain (min 6, cap 12) | ≤ 2 candidates — MAY narrow scan toward guard + shared-indirection primitives for cost, but MUST still surface any high-confidence hit | link | — | basic |
| **standard** (default) | small 4 / medium 6 / large 3-per-domain (min 10, cap 24) | ≤ 3 candidates | link | — | basic |
| **deep** (opt-up) | small 6 / medium 10 / large 4-per-domain (min 14, cap 40) | ≤ 4 candidates | **extract + split** | **extract from files** (Route 2), never invent from code | enriched (spec↔rule, spec↔spec) |

Large's per-domain numbers apply to the day-one dialog (Step A.0); a later `--domain=<slug>` re-run uses its own flat row (`light` 3 / `standard` 5 / `deep` 8 — `detect-hotspots.md` "Top-N by mode"). **Cross-cutting synthesis is on at every depth** — it is the highest value-per-token artifact init seeds; only its cap and (at `light`) its scan-cost priority change with depth, never whether it runs. A very large or hot hotspot (`LOC > 3000` OR top-quartile churn) may compose as a **flagship** at any depth — raised body cap (≤ 120 vs. the default ≤ 80 lines) or decomposition into ≤ 3 sub-specs by separable sub-surface, never both (`detect-hotspots.md` "Flagship specs").

Cost scales with depth AND with the repo — the preview shows the computed total per depth, never a constant; on large mode it also scales with how many domains are selected in Step A.0. Treat any fixed multiplier as illustrative only.

### Universality invariants — hold in EVERY depth and for ANY codebase

1. **Ceiling, not quota.** A depth raises the budget cap; it NEVER fabricates to hit a number. If the ranked hotspot pool has 5 modules, `deep` produces 5 specs, not its 6/10/40 ceiling; on a sparse repo `deep` ≈ `light`. Same for cross-cutting: if only 1 candidate clears the "surface nothing over a false rule" bar, that is the output at any depth, not the depth's cap. "Prefer omission over a guess" holds in every depth.
2. **"When detected", never "always."** No depth has a fixed artifact checklist. data-model / integrations / config / entry-points / imports / cross-cutting appear only on positive evidence, identically across depths — a depth is defined by synthesis budget, not by mandatory docs.
3. **`light` is never empty.** Its floor rests on the universal spine — stack rule + run guide + public-surface (a library's exports, a CLI's commands, a plugin's skills, a SPA's routes) + register + top-N specs via the **test-independent fallback** ranking. At least one fires for any base (library, SPA, ML, CLI, embedded, data/IaC, agent-plugin/markdown, polyglot, monorepo); `light` never degrades to nothing for lack of schema/tests/authored files.
4. **Depth lives in Phase B (compose), not detection.** No depth branch adds a stack-specific detection heuristic; detection stays high-level, evidence-first, non-exhaustive (guarded by the detect-catalog universality test).
5. **`deep`'s extra budget flows to whatever the repo affords.** No authored files → nothing to extract, so the budget goes to specs/relations that DO have evidence. `deep` is "more of what this repo actually has," not a fixed feature list assuming a stack shape.

Selection: the `--depth` flag, or the `depth:<tier>` toggle in the preview (Phase C) — the user can flip depth after seeing the plan and its per-depth cost, then still `edit` individual items.

## Execution

Content voice: default to architectural prose — decisions, rationale, intent. See `skills/_shared/precision-rules.md` Rule 6. Code blocks only where the document type requires it (`rule`, `guide`, `cpat`, and `spec` examples) or the user asks.

### Pre-flight: CLI availability check

Before any init step, verify that the Archcore CLI is available on PATH. The canonical installer is documented at https://docs.archcore.ai/cli/install/ — use it as the single source of truth; do **not** suggest other channels (`brew`, `go install`, etc.) even if the user mentions them.

1. Run: `archcore --version` (via Bash tool)
2. If it **succeeds** → check the host-wiring version gate with the deterministic helper (never compare versions yourself — lexical comparison breaks on double-digit fields). Resolve `$d` **in this same Bash call** (each Bash invocation is a fresh shell — nothing persists from a later step), exactly as the Step -1 probe below does: run `d="${CLAUDE_SKILL_DIR:-<absolute dir of this SKILL.md>}"; "$d/../../bin/cli-gte" 0.7.0`. It prints exactly one token:
   - `yes` → proceed immediately to Step -1 (host wiring enabled).
   - `__NO_CLI__` (unexpected here — `--version` just succeeded) → treat as `no`.
   - `no` → the seed still works, but the host-wiring step (see "Host wiring" below) needs a newer CLI. Ask the user once:
     > Archcore CLI `<version>` is older than v0.7.0 — host wiring (project MCP config, SessionStart hook, usage hint) will be skipped. Update now via `archcore update`? (y/N)
     - On `y` → run `archcore update` (Bash), re-run the `cli-gte 0.7.0` check, and proceed to Step -1 (host wiring enabled on `yes`, disabled otherwise).
     - On `N` / silence → proceed to Step -1 with host wiring **disabled**: omit the Host wiring line from the preview, skip Phase E step 0 entirely (the cascade never runs — its manual-fallback leg is NOT a substitute for this note), and in the closing message note: *"Host wiring skipped (CLI < v0.7.0) — update with `archcore update`, then run `archcore init --agent <host> --project "<root>"` in a terminal to make this repo self-contained for CLI-only teammates."* (`<host>`/`<root>` come from the Step -1 probe, which runs regardless of the gate.)
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
     - Success → print: *"Archcore CLI installed (`<version>`). Proceeding with init."* → apply the same v0.7.0 comparison from item 2 (a fresh install is normally current, so host wiring is enabled) → go to Step -1.
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

- **Gating (write boundary).** `init_project()` and the read-only MCP calls (`list_documents`, `get_document`) are infrastructure — they run **before** the preview. The gated operations are `create_document`, `add_relation`, and the **host-wiring writes** (`install_host_config` / `archcore init --agent` — they touch files outside `.archcore/`, like `.mcp.json` and `.claude/settings.json`): none fire before the user types `confirm`. `cancel` therefore leaves `.archcore/` content-empty and the repo's host configs untouched (the directory and `settings.json` may exist from `init_project`, which is harmless and idempotent).
- **Lazy reading (two sub-phases).** The detection/extraction catalogs at `_shared/grounding/*.md` and the composition files at `lib/*.md` are heavy (≥ 1000 lines combined) — read them in two ordered batches, never all at once. The **Detect** sub-phase (Phase A) loads the *detection* catalogs and, for each detector it runs, captures into working memory both the signals AND the small `## Output` create-fields + body template it will reuse later. The **Compose** sub-phase (Phase B) loads the *composition* contracts (`_shared/precision-rules.md`, `_shared/spec-contract.md`, `_shared/rule-contract.md`, `lib/compose-overview.md`, `_shared/grounding/extract-routing.md`) and **reuses the Output fields/templates already captured during Detect** — it does not re-read the bulky detection heuristics. "Release the detection catalogs" at the end of Phase A means dropping their heuristic prose from focus, not the captured Output specs.

### Step -1: Initialize, detect host, and acknowledge (fast)

Call `mcp__archcore__init_project()` exactly once (pre-gate infrastructure — idempotent, safe on an already-initialized project). It creates `.archcore/` and `settings.json` if missing.

Immediately after, give the user a one-line confirmation:

- Response includes `initialized: true` (created now) — print: *"Archcore initialized at `.archcore/`."*
- `already_initialized: true` — print nothing here; the existing knowledge base speaks for itself in Step 0(a).

**Host + project root for wiring** — always run this probe, even when host wiring is disabled by the pre-flight version gate (it is one cheap Bash call, and the disabled-path closing message still needs `<host>`/`<root>`). One Bash call:

```sh
d="${CLAUDE_SKILL_DIR:-<absolute dir of this SKILL.md>}"; host=$("$d/../../bin/detect-host"); root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); printf '%s\n%s\n' "$host" "$root"
```

`${CLAUDE_SKILL_DIR}` is set by Claude Code only. On other hosts (Cursor, Codex, GitHub Copilot CLI) substitute the absolute directory of this skill file — you know it from having read this file; `bin/detect-host` is two directories up from it (`<plugin-root>/bin/detect-host`).

`bin/detect-host` resolves the current host from environment only (never cwd or stdin — Cursor guarantees neither) and prints exactly one token: `claude-code` | `cursor` | `codex-cli` | `__UNKNOWN__`. **A GitHub Copilot CLI session always lands on `__UNKNOWN__`** — Copilot sets no environment marker in the shell commands it runs, so it is resolved by the question below rather than by the probe (rationale in `bin/detect-host`). If the probe returns `__UNKNOWN__` **or anything else than the three host tokens** (empty output, a path error — treat all the same), ask one `AskUserQuestion` — "Which AI host is this session running in?" with options Claude Code / Cursor / Codex (CLI or desktop app) / GitHub Copilot CLI — and map the answer to the agent id (`claude-code` / `cursor` / `codex-cli` / `copilot`). The Codex option names both surfaces on purpose: they share one binary, one `~/.codex/config.toml` and one plugin install, so `codex-cli` is the agent id for the desktop app too and there is no `codex-desktop` (`codex-adapter.spec`). Remember `host` and `root` for the Host wiring preview line and Phase E; do not re-run the probe.

`init_project` initializes only `.archcore/` — host wiring (MCP config, hook, usage hint) is planned in the preview and executed in Phase E, never here. Do not run `archcore init` yourself at this step; the terminal path is the Phase E fallback for the user, not a pre-flight action.

### Step 0: Check state and source signal

Two cheap probes, in order. Each can short-circuit the whole skill. Neither reads anything under `_shared/grounding/` or `lib/`.

#### Step 0(a) — Existing documents

Call `mcp__archcore__list_documents()` once. **Derive every flag below from local documents only** — skip any result carrying `global: true` / `read_only: true` / `source_kind: "global"`. A mounted global source may already provide a stack rule or an overview, but it must not satisfy the already-seeded early-exit: init seeds THIS repo's documents, and a repo with globals mounted but no local seed is still unseeded. If any global results appear, load `skills/_shared/globals.md`; never modify a global document and never target one with `add_relation`. Derive:

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

> Init already seeded this repo. Applicable context auto-injects on file edits via the code-alignment hook; use `/archcore:review` for the dashboard. To add facts that appeared since (a new schema, config, or modules), re-run `/archcore:init --refresh`; to drill into another domain, `/archcore:init --domain=<slug>`. (Seeded before host wiring existed, or missing the host configs? `--refresh` also adds host wiring — MCP config, SessionStart hook, usage hint.)

Then stop. **With `--refresh` or `--domain`, skip this early-exit and proceed** — every already-present artifact is marked **skip (exists)** in the preview and only missing ones are composed; the Host wiring line appears as usual (its writes are idempotent — already-wired hosts show as skip/converge). (`--domain` additionally scopes the run to one domain; see Step A.0.)

#### Step 0(b) — Source-signal gate (empty-repo early exit)

Single filesystem probe — one shell call, no catalog reads. Detect whether the repository has any executable shape yet:

- **`has_manifest`** — at least one of these exists at the project root (depth ≤ 2 for monorepo workspaces): `package.json`, `pyproject.toml`, `Pipfile`, `requirements.txt`, `Cargo.toml`, `go.mod`, `Gemfile`, `composer.json`, `*.csproj`, `*.fsproj`, `*.vbproj`, `pom.xml`, `build.gradle`, `build.gradle.kts`, `mix.exs`, `Package.swift`. **This list is seed examples, not exhaustive** — also treat ANY project-defining manifest or build file as a manifest (e.g. `CMakeLists.txt`, `Makefile`, `dune-project`/`*.opam`, `deps.edn`/`project.clj`, `pubspec.yaml`, `build.sbt`, `stack.yaml`/`*.cabal`, `*.tf`/`*.tfvars`, `Chart.yaml`, `project.godot`, `*.sln`, `Project.toml`, and agent/LLM-plugin manifests such as `marketplace.json` / `plugin.json` / `.claude-plugin/*`).
- **`has_top_level_source`** — at least one file with a recognizable source extension exists anywhere under the project root, capped at depth 3, excluding `.archcore/`, `.git/`, `node_modules/`, `vendor/`, `dist/`, `build/`, `out/`, `target/`, `coverage/`, `.venv/`, `__pycache__/`, `.next/`, `.turbo/`. Extensions: `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.py`, `.rs`, `.go`, `.rb`, `.php`, `.java`, `.kt`, `.kts`, `.swift`, `.cs`, `.fs`, `.ex`, `.exs`, `.scala`, `.clj`, `.cljs`. **The extension list is seed examples, not exhaustive** — also count any file whose contents are plainly source (a shebang, or import/include/package/module/def/func/class/use constructs), and recognize other common code extensions (e.g. `.vue`, `.svelte`, `.astro`, `.dart`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, `.m`, `.mm`, `.ipynb`, `.hs`, `.ml`, `.mli`, `.tf`, `.sol`, `.lua`, `.jl`, `.r`, `.zig`, `.nim`, `.gd`).

If BOTH are false, take the **empty** route. No content seed — but host wiring still applies (an empty repo is exactly where a teammate going CLI-only needs the configs).

When host wiring is **disabled** by the pre-flight version gate, reply with exactly this and stop (no writes):

> Archcore is ready at `.archcore/`. No source code detected yet — no content to seed. Host wiring skipped (CLI < v0.7.0) — update with `archcore update`, then re-run `/archcore:init`. The SessionStart empty-state nudge will keep pointing here until then.


Otherwise show a mini-preview:

> Archcore is ready at `.archcore/`. No source code detected yet — no content to seed.
>
> One thing worth doing now — host wiring, same files `archcore init` writes (makes the repo work for teammates using the CLI without this plugin):
>
> ```
> Host wiring (<host>) → <root>
>   • <per-host file list — e.g. for claude-code: .mcp.json · .claude/settings.json (SessionStart hook) · CLAUDE.md + AGENTS.md (managed block)>
> ```
>
> `confirm` to write these, `cancel` to leave the repo untouched. Re-run `/archcore:init` after the first manifest or source file lands — the SessionStart empty-state nudge will keep pointing here until then.

On `confirm` → execute the Host wiring cascade (Phase E step 0) and stop. On `cancel` → stop with no writes. Either way, **do NOT** create placeholder documents — they have no practical value, cost roundtrips and tokens, and suppress the SessionStart empty-state nudge that is the user's breadcrumb back here.

Otherwise (`has_manifest` OR `has_top_level_source`), proceed to Phase A.

---

## Phase A — DETECT (no writes; detection catalogs only)

Compute everything the seed needs in one detection pass. No documents are created here, and no composition contract is opened. For each detector, capture its signals AND its `## Output` create-fields for reuse in Phase B/E.

**Detect high-level, for ANY stack.** Each `detect-*` catalog leads with *what* it detects (the concept) and a universal, evidence-first method; its concrete lists of frameworks / ORMs / SDKs / extensions / conventional roots are **non-exhaustive examples**, not a checklist. When a project's language, framework, or layout is unfamiliar or highly specific, reason from first principles per the catalog — the entry file's imports, the dominant file types, the manifest / build system, and what the code actually does — and emit a fact only on **positive evidence** (prefer omission over a guess). Never return empty / `small` / "no entry points" merely because nothing matched a list.

### Step 0.5: Scale

Read `_shared/grounding/detect-scale.md`, `_shared/grounding/detect-domains.md`, `_shared/grounding/detect-modules.md`.

1. **Parse arguments** — `--depth=light|standard|deep` (synthesis budget, default `standard`; see the Depth axis section), `--mode=X` (force the mode), `--domain=<slug>` (force a large-mode single-domain pass; see Step A.0), `--refresh` (already consumed in Step 0a). Depth does NOT affect detection — Phase A ranks hotspots up to the `deep`-depth ceiling (see Step A.3) and detects ALL facts/imports regardless of the active depth; depth only governs how much is synthesized in Phase B.
2. **Compute signals:** `domain_count` (per `detect-domains.md`), `module_count` (source files > 100 LOC, excluding tests/generated), `entry_point_count` (per `detect-entry-points.md`, informational).
3. **Classify** per `detect-scale.md` — apply its evidence-based fallback when the language/layout is unlisted (recompute counts from the dominant code extension and tracked-file breadth; do not default to `small` just because the extension/root lists miss). A forced `--mode` wins but remember the auto-detected one; `--domain` forces large-mode behavior scoped to the named domain.

### Step A.0: Domain selection (large mode only)

Skip unless mode is `large`.

1. **`--domain=<slug>` given** — that domain is the sole selection; skip the dialog. (Tier-1 facts already present are skipped; the run tops up this domain's data-model + hotspot specs using the flat `--domain=<slug>` re-run cap — `light` 3 / `standard` 5 / `deep` 8, per `detect-hotspots.md`.)
2. **Otherwise** — present the top 5 ranked domains (per `detect-domains.md` ranking) and ask: *"Which domains are you working on now? (pick 1–3 by name or number, or `skip` to defer.)"* Accept a single name, a comma list, or `skip`.
3. **Scope the hotspot budget.** Hotspots (A.3) are ranked **repo-wide** (candidate selection is never restricted to a domain's tree in the day-one dialog), but the *budget* now depends on the selection: the active depth's per-domain formula (`detect-hotspots.md` "Top-N by mode" — `light` 2 / `standard` 3 / `deep` 4 per selected domain, clamped to that depth's min/max) guarantees **every selected domain a floor of ≥ 1 spec**; remaining slots up to the computed cap fill by repo-wide rank across all domains, selected or not. On `skip`, no domain gets a floor and the whole budget fills by repo-wide rank alone (the formula collapses to its flat `min` — 6 / 10 / 14).
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

- **Hotspot candidates** — rank per `_shared/grounding/detect-hotspots.md` and collect signal data (path + LOC + companion-test LOC + suggested type) for the full ranked pool **up to each scale's `deep`-depth ceiling** — small 6, medium 10, large `clamp(4 × selected_domain_count, 14, 40)` (0 if the domain dialog was `skip`ped, so the ceiling collapses to 14) — NOT just the `standard` baseline, so this one Detect pass serves any `--depth`, including a later `depth:` toggle in Phase D, with no re-read of source. Phase B then keeps only the *active depth's* top-N as spec stubs — small 3/4/6, medium 4/6/10, large per-domain-scaled (`light`/`standard`/`deep`; see `detect-hotspots.md` "Top-N by mode") — subject to large mode's per-selected-domain floor of ≥ 1 spec; ranked candidates beyond that go to the overview register (`compose-overview.md` Part 3) as `→ /archcore:document` rows. The catalog ranks in two tiers: a tests-aware **primary** tier, and — when it yields fewer than N — a **test-independent fallback** (fan-in / public surface / size / churn) so repos with no tests (scripts, SPAs, ML, CLIs, agent-plugin/markdown tooling) still surface real specs instead of an empty pool. Mark fallback-tier stubs with their qualifying signal. A candidate clearing the **flagship** gate (`LOC > 3000` OR top-quartile churn) is flagged as such in the stub, for Phase E's raised-cap/decomposition choice (`detect-hotspots.md` "Flagship specs"). **Tier-2 artifacts are always composed as `spec`** — use the `adr`/`task-type` hints in `detect-hotspots.md` only to *filter out* ineligible candidates (e.g. a `utils`/`helpers` module, or one failing `spec-contract.md`'s "when NOT to write a spec"), never to switch the document type. **Do not read source files yet** — that read is deferred to Phase E for kept specs only.
- **Cross-cutting candidates** (medium and large, whole-repo, **every depth**) — per `_shared/grounding/detect-cross-cutting.md`, at most the active depth's cap (`light` ≤2 / `standard` ≤3 / `deep` ≤4). init uses that catalog for **detection only** and overrides its standalone y/n "Output" flow: each candidate becomes a Tier-2 `rule` stub here and is created in Phase E, not handed to `/archcore:document`.

### Step A.4: Agent files

Detect **all** agent-instruction candidates per `lib/agent-files.md` (paths + byte sizes + **class**) — do not stop at CLAUDE.md/AGENTS.md; enumerate the modular directories (`.cursor/rules/*.mdc`, `.github/instructions/*.md`, `.windsurf/rules/*.md`) too. **Sizing exception for CLAUDE.md / AGENTS.md**: compute their size and non-emptiness only **after stripping any archcore managed block** (`<!-- archcore:start -->` … `<!-- archcore:end -->`) — never from a raw file-size probe; a file whose only content is the managed block is not a candidate at all and must not appear in the preview (`lib/agent-files.md` → Probe paths). `lib/agent-files.md` assigns each file a class that sets its default import mode:

- **`aggregate`** (CLAUDE.md, AGENTS.md, .cursorrules, …) — default **link** (one pointer `doc`). Extract is opt-in.
- **`modular-rule`** (`.cursor/rules/*.mdc` and equivalents) — default **extract**: one `rule`/`doc` per file, classified by content (genuine conventions → `conventions/`), reproduced verbatim. A file > 200 lines degrades to `link`.

Estimate extract **yield** without loading `extract-routing.md`: aggregate → count H1/H2/H3 headings, capped at 10; modular-rule → 1 per file (they are one rule each). Compute the cost tier **per class**: **aggregate HIGH** if combined aggregate size > 50 KB OR estimated aggregate yield > 8 docs; **modular-rule HIGH** if combined modular-rule size > 50 KB (**file count is NOT a signal** — many small rule files are cheap). HIGH gates only whether extract needs an explicit opt-in.

### Step A.5: Announce

Print one detection line, e.g.:

> Mode: medium (28 modules, 1 domain). Detected: Prisma (6 entities), Stripe + AWS, 12 env vars, 5 entry points, 5 hotspot candidates, 1 cross-cutting pattern, CLAUDE.md (4 KB) + 6 .cursor/rules files (18 KB, modular). Composing the plan…

In large mode, report the figures for the **selected** domains (selection already happened in Step A.0). Detection done — release the detection catalogs (heuristic prose), keeping the captured Output specs.

---

## Phase B — COMPOSE (in memory; composition contracts only)

Load the composition contracts and compose every planned artifact **without writing**. Honor each catalog's line cap. Mark any artifact whose `has_*` flag is already true as **skip (exists)**. Exception: in large / `--domain` mode the per-domain data-model doc (`<domain-slug>-data-model`) dedupes by its own filename, not the repo-wide `has_data_model` tag — so a newly-selected domain's data-model is still composed when other domains' already exist.

**Apply the active depth** (`## Depth axis`, default `standard`) to this compose pass — it sets only these levers, and everything else is depth-independent:
- Hotspot spec count = the depth's top-N (`detect-hotspots.md`), large mode subject to the per-selected-domain floor; ranked hotspots beyond it go to the register regardless of depth. A flagship candidate (Change: size/churn-gated) composes at the raised body cap or, only with genuine separable sub-contracts, decomposes into ≤ 3 sub-specs — at every depth, not gated by depth.
- Cross-cutting synthesis runs at **every** depth now (medium/large); only its cap changes — `light` ≤2, `standard` ≤3, `deep` ≤4. `light` MAY narrow the scan toward the guard + shared-indirection primitives for cost control but MUST still surface any high-confidence candidate it finds.
- Import mode: `light`/`standard` → aggregate link, big (>200) modular link; `deep` → aggregate extract, big modular extract + split.
- ADR-from-authored-decisions and enriched relations: `deep` only.
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
  - hotspot specs — one stub each for the top-N **of the active depth** (`detect-hotspots.md`), large mode subject to the per-selected-domain floor: suggested spec title, the qualifying `LOC / test-ratio`, target filename + directory, a `flagship` marker when the size/churn gate is cleared, and an estimated synthesis cost ≈ `(source_LOC + test_LOC) × 6` tokens. The full body is composed only after confirm. Ranked hotspots **beyond** the top-N are not stubbed — they go to the overview register (`compose-overview.md` Part 3) at ~0 cost.
  - cross-cutting rules (medium/large, **every depth** — cap `light` ≤2 / `standard` ≤3 / `deep` ≤4) — one stub each: the pattern + the paths it would govern. Full body composed after confirm under `rule-contract.md`. **Drop a stub whose pattern is already covered by an imported authored rule** (dedup per `detect-cross-cutting.md`) and note the skip under that import.
- **Capstone:** plan the architecture-overview per `lib/compose-overview.md`. Its body indexes the *confirmed* seed, so it is composed in Phase E once the set is final. List it in the preview as "Architecture overview — index of the above".
- **Agent-file import:** behavior is set by file class from `lib/agent-files.md` (captured in Detect):
  - **Aggregate** (CLAUDE.md, AGENTS.md, .cursorrules, …): default **link** (one pointer `doc`, ~0 cost). Extract is opt-in via `edit`; the aggregate-HIGH flag gates that opt-in.
  - **Modular-rule** (`.cursor/rules/*.mdc` and equivalents): default **extract** per `_shared/grounding/extract-routing.md` — one document per file (they are one rule each), classified by content: a genuine convention → `rule` in `conventions/`; a reference/role/meta file → `doc` in `imported/`. Title from the frontmatter `description:`, body verbatim, `status: draft`. A file > 200 lines degrades to **link** (opt-in extract to split). No synthesis.
  - **Dedup:** after both sets are assembled, drop any cross-cutting stub whose constraint is already covered by a modular-rule file imported as a `rule` (same symbol/module) — prefer the authored rule; never create both.
  Reuse the `agent-files.md` encoding (`imported` + `source:<slug>` tags, pointer first line) for all modes.
- **Planned relations:** per the `compose-overview.md` "Relation wiring" table.

No `create_document` / `add_relation` has run yet.

---

## Phase C — PREVIEW (one manifest)

Present the entire plan as a single grouped manifest, then wait. Example:

```
Init plan — scale: medium · depth: standard (default).   confirm / edit / depth:light / depth:deep / cancel
Coverage: 5 specs / 11 load-bearing modules · 1 cross-cutting rule

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
Imports (aggregate — link by default):
  • CLAUDE.md (4 KB) — link, 1 doc                         ~0   (edit → extract)
Imports (modular rules — extract → rule by default):
  • .cursor/rules/app-router-only.mdc — rule, 1 doc        ~0   (edit → link)
  • .cursor/rules/error-handling.mdc (240 ln) — link       ~0   (large; edit → extract)
Host wiring (as `archcore init`, host: claude-code) → /Users/x/myrepo
  • .mcp.json · .claude/settings.json (SessionStart hook) · CLAUDE.md + AGENTS.md (managed block)   (edit → hosts: all / skip)
Relations: ~14 edges.
Estimated: ~22k (standard, shown) · ~7k (light) · ~50k (deep).
Already present (skipped): <list, or "none">.
```

- The **Coverage line** always follows the header and surfaces sparseness explicitly:
  `Coverage: <N> specs / <M> load-bearing modules · <D>/<T> domains seeded · <C> cross-cutting rules`.
  `N` = kept hotspot specs at the active depth; `M` = the full ranked hotspot pool size (`detect-hotspots.md` primary + fallback, not just the top-N); `D`/`T` = domains with ≥ 1 seeded doc (data-model or spec) out of total detected domains — **large mode only**, omit the `· D/T domains seeded` clause in small/medium; `C` = kept cross-cutting rule stubs — omit that clause when `C` = 0 in small mode (cross-cutting never runs there). All four numbers are computed from the plan, never a constant.
- **Large mode**, any depth: append one recommendation line directly under Coverage showing the concrete jump to the adjacent tiers, computed from the plan's actual pool and per-depth caps — never constants:
  ```
  Init plan — scale: large · depth: standard (default).   confirm / edit / depth:light / depth:deep / cancel
  Coverage: 24 specs / 214 load-bearing modules · 6/24 domains seeded · 3 cross-cutting rules
  Large repo: standard covers ~11% of load-bearing modules. depth:light → ~9 specs, cheaper; depth:deep → ~40 specs + big-file extraction + enriched relations. Toggle depth: below before confirm.
  ```
  On a `light`-toggled re-plan the line instead points only upward (`depth:standard → …`, `depth:deep → …`); on `deep` it points only downward, since there is nowhere higher to go.
- For each **Tier-2 stub** show the qualifying `LOC / test-ratio` and the per-item synthesis cost, so `edit` is an informed budget lever. A flagship stub (`detect-hotspots.md` "Flagship specs") shows its raised-cap or decomposition treatment inline, e.g. `spec: order-service — 6400 LOC src / 1100 LOC tests ~24k [flagship: raised cap]` or `[flagship: split → 2 sub-specs]`.
- For **aggregate imports**, show as **link** by default with `(edit → extract)`; if a file's cost tier is **HIGH**, prefix `⚠️ HIGH COST` on the extract option — extract is only entered when the user explicitly opts in.
- For **modular-rule imports**, show as **extract → rule** by default with `(edit → link)`; a file > 200 lines shows as **link** with `(large; edit → extract)`. If a cross-cutting stub was dropped because an imported rule covers it, show `↳ synthesis skipped` under that stub.
- The **Host wiring line** (omit when disabled by the pre-flight version gate) names the detected host, the resolved project root **explicitly** (the user must see WHERE files will land — Cursor can misroute cwd, and this line is the check against it), and the per-host file list: claude-code → `.mcp.json` + `.claude/settings.json` (SessionStart hook) + `CLAUDE.md` + `AGENTS.md` managed blocks (CLAUDE.md is what Claude Code actually reads; AGENTS.md is the shared standard block — one write, both files; the CLI also deletes the legacy nudge file under `.claude/rules/` left by pre-v0.6.1 CLIs); cursor → `.cursor/mcp.json` + `.cursor/hooks.json` + `AGENTS.md` managed block; codex-cli → `.codex/config.toml` + `AGENTS.md` managed block; copilot → `.mcp.json` + `.github/hooks/archcore.json` (sessionStart) + `AGENTS.md` managed block. **On copilot the Host wiring line is never optional** — the plugin ships no MCP server for that host (Copilot launches a plugin's MCP in the plugin's own directory, github/copilot-cli#4234), so without wiring the session has skills and hooks but no document tools at all. If the version gate disabled wiring, say so plainly in the closing message rather than seeding silently. `edit → hosts: all` widens the install to every agent auto-detected in the repo; `edit → skip wiring` drops the line. These files live **outside** `.archcore/` — they are written only after `confirm`, like everything else.

## Phase D — CONFIRM

Wait for the user.

- **`cancel`** → stop. Fire zero `create_document` / `add_relation` calls. No partial state.
- **`edit`** → accept deselections by name/number ("drop spec:auth-client", "skip import", "rules only"), opt-ins ("extract CLAUDE.md"), batch answers ("link all"), and the host-wiring toggles from Phase C ("hosts: all" widens to every detected agent, "skip wiring" drops the line). Re-show the trimmed total, then proceed.
- **`depth:light|standard|deep`** → re-plan at that depth: recompute the spec count, the cross-cutting cap, import modes, and per-depth cost, re-show the whole preview (Coverage line and, in large mode, the depth-nudge line included), then wait again (edits on top are still accepted).
- **`confirm`** → Phase E with the surviving set.

A deselected Tier-2 spec's source file is **never read** — the read happens in Phase E only for kept specs.

## Phase E — CREATE + WIRE (gated; runs only after confirm)

For the confirmed set only, in order:

0. **Host wiring** (when the preview carried the line and it survived `edit`) — deterministic cascade, first available path wins:
   1. **MCP tool** — if `install_host_config` is among the available archcore MCP tools, call `install_host_config(host=<host>)` (add `all_detected=true` on `hosts: all`). The server's project root is correct by construction; relay the returned report (files ensured / errors) in the closing message.
   2. **CLI fallback** — tool absent (older server still running, or a Cursor day-one session where no archcore MCP is connected yet): run via Bash `archcore init --agent <host> --project "<root>"` (repeat `--agent` per host on `hosts: all`), with `<root>` exactly the path shown in the preview. Non-interactive by contract: no prompts, artifacts land under `--project` regardless of cwd.
   3. **Manual fallback** — the CLI turns out too old for `--agent` at execution time (reachable only when the version check passed at pre-flight but the CLI is stale/broken by Phase E — e.g. a concurrent downgrade; a user who declined the update never reaches this cascade, their channel is the closing-message note from the pre-flight gate): print the ready-to-run command *`archcore update && archcore init --agent <host> --project "<root>"`* for the user's terminal and continue with the content seed — wiring failure never aborts the seed.
   On partial failure inside a path (e.g. one host errored), report per-artifact results and continue; do not retry a different path for artifacts that succeeded.

   **On `copilot`, verify the result instead of assuming it.** Everywhere else a failed wiring costs convenience — the plugin's own MCP server still answers. On this host it costs the entire document surface (`copilot-mcp-architecture.adr`), and the user discovers that a session later, as "the plugin is broken". So after the cascade, check the artifact that carries the tools, in one Bash call: `grep -q '"archcore"' "<root>/.mcp.json"`. On a match, report wiring as done. On no match — including a zero-exit CLI that wrote nothing — report it as **failed**, name `<root>/.mcp.json` as the missing file, and give the user the ready-to-run `archcore init --agent copilot --project "<root>"`. Either way continue with the content seed: wiring failure never aborts it.

1. **Tier-1 facts** — `create_document` per the fields in each catalog's `## Output` section (type / directory / filename / title / status / tags). Skip any marked exists.
2. **Hotspot specs** — for each kept stub: **now** read its source + companion tests, compose the full body under `_shared/spec-contract.md` (default ≤ 80-line cap). If the stub is marked **flagship** (`detect-hotspots.md` "Flagship specs" — `LOC > 3000` OR top-quartile churn): either raise the cap to ≤ 120 lines (default treatment), or — only when the module has ≥ 2 genuinely separable, independently-consumable sub-surfaces — decompose into ≤ 3 sub-specs at the default ≤ 80-line cap (`filename=<module-slug>-<sub-surface-slug>` each), never both. Then `create_document(type='spec', filename=<module-slug>[-<sub-surface-slug>], directory=<domain-or 'architecture'>, status='draft', tags=['spec', <area>])` — `status='draft'` in every case: the spec is heuristic-derived from code, not authored/reviewed, so the user confirms it before it is canon (same rationale as the cross-cutting rules below). Skip if a doc with that filename already exists (dedupe). For a decomposed flagship, also `add_relation('related')` between its sub-specs (Step 6 wiring, `compose-overview.md`).
3. **Cross-cutting rules** (medium/large, **every depth** — cap `light` ≤2 / `standard` ≤3 / `deep` ≤4, per Phase B) — for each kept stub: compose under `_shared/rule-contract.md`, `create_document(type='rule', filename=<concern-slug>, directory='conventions', status='draft', tags=['conventions', <concern>])`. `status='draft'` because the rule is heuristic-derived and the user should confirm phrasing before it is canon. Skip if that filename already exists, or if the stub was deduplicated against an imported authored rule in Phase B.
4. **Agent-file import** — execute kept items per class (`lib/agent-files.md`) at the modes Phase B set for the active depth: aggregate → link (`light`/`standard`) or extract (`deep`/opt-in); modular-rule → extract one `rule`/`doc` per file, classified by content (genuine conventions to `conventions/`), with big (>200) files linked at `light`/`standard` and extract+split at `deep`. At `deep`, authored decision blocks become `adr` docs via `_shared/grounding/extract-routing.md` Route 2 (extracted from the file, never invented from code). Route content via `_shared/grounding/extract-routing.md`; dedupe against existing `source:<slug>` tags first.
5. **Architecture overview** — skip if `has_overview`. Otherwise, now that the seed is final, compose its body per `compose-overview.md` (structural-facts line + type/topic index of the *created* docs) and `create_document`.
6. **Relations** — `add_relation` per the planned wiring table; skip any edge whose endpoints were not both created. Roll forward on individual failure (surface the error, keep successful edges; do not delete prior creates). At `deep` depth also add the enriched edges (each hotspot spec → the convention rule(s) it must honor, and → sibling specs in the same tree) from the relation-wiring plan.
7. **Report** one line per created document plus the total edge count.

### Closing message: outlook

Summarize what was created, then make the value-loop visible and list the over-time targets. When host wiring ran, lead with its one-line outcome — e.g. *"Host wiring (claude-code): .mcp.json, SessionStart hook, CLAUDE.md + AGENTS.md managed block — repo now works for CLI-only teammates."* — or the per-artifact errors if any failed. Per-mode template.

**On `copilot` the outcome line MUST end with the restart requirement**, e.g. *"Host wiring (copilot): .mcp.json, .github/hooks/archcore.json, AGENTS.md — now restart the Copilot session to connect the Archcore MCP document tools. This host reads .mcp.json at session start, so they are not available in this one."* Copilot is the only host where wiring is the sole route to those tools, and they do not appear in the session that wrote the file. A user who is not told this sees a green report followed by an agent that cannot read or create a single document — which reads as a broken plugin, not as a pending restart. `bin/session-start` gives the same instruction in its own Copilot messages; keep the two in step.

**On `codex-cli` the outcome line MUST name the two consents the wiring waits on.** Codex loads a project `.codex/` layer — `.codex/config.toml` and `.codex/hooks.json` alike — only for a project marked `trust_level = "trusted"`, and runs a non-managed command hook only after the user reviews and trusts it under `/hooks`. Neither is granted by writing the files. So the line reads e.g. *"Host wiring (codex-cli): .codex/config.toml, .codex/hooks.json, AGENTS.md — Codex applies them once you trust this project and approve the hooks in `/hooks`; both surfaces (CLI and desktop app) read the same files."* Without that sentence a teammate sees green wiring and a session with no Archcore MCP and no hooks, and `codex exec` skips untrusted hooks without printing why. **Conditionalize the "Try it now" line:** if ≥ 1 hotspot spec was created, point at the top hotspot path; if none (empty pool or all deselected), point at a file in a seeded fact's area instead — the code-alignment hook injects that fact on edit.

**Small:**

> Done. Seeded: stack rule, run guide[, data-model, integrations, config, entry points], architecture overview, and N hotspot specs.
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects via the code-alignment hook. (No hotspot specs? Edit a file in a seeded area — the hook injects what applies.) Over time: ADRs for non-trivial dependency choices (`/archcore:document`), more specs (`/archcore:document <path>`), a task-type for any repeating extension pattern (`/archcore:review`'s experience offer).

**Medium:**

> Done. Seeded: stack rule, run guide, data-model, integrations, config, entry points, architecture overview, N hotspot specs[, M cross-cutting rules].
>
> Try it now: edit a file under `<top hotspot path>` — its spec auto-injects. The hook injects what applies to any path you edit. Over time: ADRs for architectural decisions (persistence, auth, observability), more specs, rules per cross-cutting concern — via `/archcore:document`, `/archcore:plan`; task-types surface via `/archcore:review`'s experience offer when branch changes repeat a pattern.

**Large:**

> Done. Seeded: workspace stack rule, monorepo run guide, top-level map (T domains), entry points, data-model + integrations + config. Data-model seeded for D of T domains (every domain with a detectable schema, not only the ones you picked below). Architecture overview. Created M hotspot specs — a floor of ≥ 1 per domain you're working in now, the rest by repo-wide rank[, imported K authored rules from the repo's modular rule files], and registered the remaining hotspots in the overview[ plus J cross-cutting rules].
>
> Try it now: edit a file under `<a selected-domain hotspot path>` — its spec auto-injects via the code-alignment hook. Other domains: <list>. Run `/archcore:init --domain=<slug>` later to drill into any of them, and `mcp__archcore__search_documents` with the domain tag to scope queries. Over time each domain needs its own ADRs and specs via `/archcore:document`, and task-types via `/archcore:review`'s experience offer when branch changes repeat a pattern; repo-wide cross-cutting rules (logging, errors, auth, transactions, telemetry) accrue via `/archcore:document`.

Depth-nudge, keyed off whichever depth actually ran (never assume `standard` ran just because it is the default):

- Ran at **`light`** (opted down):

  > Ran at `light` depth (cheapest seed). `depth:standard` (the default) raises the spec and cross-cutting budget; `depth:deep` additionally adds big-file/CLAUDE.md extraction, extracted ADRs, enriched relations, and flagship-spec decomposition for the largest hotspots. Re-run with `--depth=standard` or `--depth=deep` — the preview shows each depth's cost before anything is created.

- Ran at **`standard`** (the default — most runs):

  > Ran at `standard` depth. `depth:deep` additionally extracts big authored files (CLAUDE.md/AGENTS.md, oversized rule files) into typed docs, extracts ADRs from authored decisions, enriches the relation graph (spec↔rule, spec↔spec), and raises the spec/cross-cutting caps. Re-run with `--depth=deep` for the max plan, or `--depth=light` for a cheaper one.

- Ran at **`deep`**: no nudge — this is the max tier.

Always end with:

> Use `/archcore:review` for the dashboard, `/archcore:review --deep` for a health audit.

## Result

Mode-appropriate, single-confirm `.archcore/` seed (created only on `confirm`; existing artifacts skipped). The doc counts below anchor on **`standard` (the default)** — a good first-day seed with hotspot specs AND cross-cutting rules; **`light`** (opt-down) is a cheaper floor with a smaller spec cap and a tighter (≤ 2) cross-cutting cap, never zero; **`deep`** (opt-up) adds big-file/CLAUDE.md extraction, extracted ADRs, enriched relations, flagship-spec decomposition, and the highest spec/cross-cutting caps:

- **Empty**: 0 content docs — `.archcore/` and `settings.json`, plus host wiring behind its own mini-confirm. No catalog files read.
- **Small**: ~6–10 docs at `standard` (stack rule, run guide, detected Tier-1 facts, overview + 4 specs; the fallback tier keeps specs non-zero even in test-less repos); ~5–9 at `light` (3 specs); `deep` ≈ +2 specs over standard and big-file extraction.
- **Medium**: ~8–14 docs at `standard` (small set + 6 specs + 0–3 cross-cutting rules + imported authored rules); ~6–10 at `light` (4 specs + 0–2 cross-cutting rules); ~10–18+ at `deep` (10 specs + up to 4 cross-cutting rules + extraction).
- **Large**: ~15–25+ docs at `standard` (medium set + top-level map + domain dialog + data-model for every schema-bearing domain + a per-domain-floored, repo-wide-ranked spec set — 3/domain, min 10, cap 24 — + up to 3 cross-cutting rules + imported authored rules); ~10–16 at `light` (2/domain, min 6, cap 12; ≤ 2 cross-cutting rules); up to 40 specs + up to 4 cross-cutting rules + big-file extraction + ADRs + flagship decomposition at `deep`.

Idempotency: the flagged Tier-1 facts, the overview, and imports are skip-on-exists; Tier-2 specs/rules dedupe by filename before create. Host wiring is idempotent end-to-end (existing archcore entries are kept, or updated in place when written by an older CLI; foreign config content is never touched), so re-running init never duplicates hooks or MCP entries. A second `/archcore:init` on a fully-seeded repo early-exits (Step 0a) unless `--refresh` (top up newly-detectable facts) or `--domain` (scoped domain pass) is passed. Tier-2 spec bodies and the overview are composed only after `confirm`, so a `cancel` or deselect spends no source-read cost. The empty route never creates placeholder documents, keeping `.archcore/` functionally empty so the SessionStart nudge keeps pointing here.
