---
name: evolve
user-invocable: false
tags: [learning, intelligence, meta]
model: sonnet
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
args-schema:
  - flag: --apply
    description: "Apply dialectic-derived diff to USER.md + AGENT.md"
  - flag: --dry-run
    description: "Show diff without writing (default)"
  - flag: --model <name>
    description: "Override single-pass LLM (haiku|sonnet|opus)"
  - flag: --budget-tokens <N>
    description: "Token budget for derivation prompt (default 8000)"
description: >
  Use this skill when extracting session patterns into reusable learnings. Three modes: analyze (extract from session history),
  review (edit/manage existing learnings), list (display active learnings). Manages .orchestrator/metrics/learnings.jsonl.
---

> **Platform Note:** State files use the platform's native directory: `.claude/` (Claude Code), `.codex/` (Codex CLI), or `.cursor/` (Cursor IDE). Shared metrics live in `.orchestrator/metrics/` (v2) with fallback to `<state-dir>/metrics/` for pre-v2.0 legacy data. See `skills/_shared/platform-tools.md`.

# Evolve Skill

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## Phase 1: Config & Data Loading

### 1.1 Read Session Config

Read and parse Session Config per `skills/_shared/config-reading.md`. Store result as `$CONFIG`.

### 1.2 Check Persistence

Extract `persistence` from `$CONFIG`. If `persistence` is `false`, abort with message:

> "Learnings require persistence to be enabled in Session Config. Add `persistence: true` to your Session Config block (CLAUDE.md for Claude Code, AGENTS.md for Codex CLI)."

### 1.3 Determine Mode

Read mode from `$ARGUMENTS`:
- If empty or not provided, default to `analyze`
- Valid modes: `analyze`, `review`, `list`, `dialectic`
- If invalid mode provided, report error and list valid modes

### 1.4 Load Data

**Lazy-create defensive (#185):** If `.orchestrator/metrics/learnings.jsonl` does not exist (pre-#185 repo or bootstrap skipped), create an empty file and emit an info log — do NOT hard-fail:

```bash
LEARNINGS_FILE=".orchestrator/metrics/learnings.jsonl"
if [[ ! -f "$LEARNINGS_FILE" ]]; then
  mkdir -p "$(dirname "$LEARNINGS_FILE")"
  : > "$LEARNINGS_FILE"
  echo "info(#185): auto-created $LEARNINGS_FILE (was missing)" >&2
fi
```

This defensive step is idempotent and cheap — it ensures `/evolve analyze|review|list` never fails because of a missing artifact file.

1. Read `.orchestrator/metrics/sessions.jsonl` (session history). If it does not exist, check `<state-dir>/metrics/sessions.jsonl` as a legacy fallback (where `<state-dir>` is `.claude/`, `.codex/`, or `.cursor/` per platform). If neither exists, warn: "No session history found. Run at least one session first."
2. Read `.orchestrator/metrics/learnings.jsonl` if it exists. If not found, check `<state-dir>/metrics/learnings.jsonl` as a legacy fallback.
3. Count existing learnings, note any where `expires_at` < current date (expired)

## Phase 2: Mode Dispatch

Route based on mode:
- `analyze` → Phase 3
- `review` → Phase 4
- `list` → Phase 5
- `dialectic` → Phase 6

---

## Phase 3: Analyze Mode (default)

Extract learnings from session history.

> **Vault Integration:** If `vault-integration.enabled` is `true` in Session Config, confirmed learnings are mirrored to the configured Obsidian vault after the atomic write (Step 3.5, step 9). See `docs/session-config-reference.md` for the `vault-integration` config block.

### Step 3.1: Read Session Data

- Read all entries from `.orchestrator/metrics/sessions.jsonl` (or `<state-dir>/metrics/sessions.jsonl` if the v2 path does not exist — see Phase 1.4 fallback)
- Parse each JSONL line as JSON
- Sort by `completed_at` descending (most recent first)
- If no sessions found, abort: "No session data available. Complete at least one session before running evolve."

### Step 3.1b: Read Extra Sources (#638)

When `evolve.extra-sources` is configured in Session Config (default `[]` ⇒ this step is a no-op), `/evolve` consumes OUT-OF-BAND domain measurement sidecars to surface `domain-regression` learnings.

**READ-ONLY contract:** `/evolve` NEVER runs the domain measurement. The measurement (e.g. an eval-learn regression harness) runs elsewhere and writes a sidecar JSON; this step only READS that sidecar's output. Never shell out to produce the sidecar from here.

For each configured `extra-sources` entry `{path, kind, learning-type}`:

1. **Read the sidecar** at `path` (parser-validated as repo-relative, with absolute paths and `..` escape segments dropped before this step, then resolved against the repo root). If the file is missing or unreadable, **skip with a WARN** (`evolve: extra-source not found: <path>`) — do not abort the whole run.
2. **Schema-gate** the sidecar against the `kind`'s expected shape. For `kind: regression-flags` the schema is `{ flags: [ { metric, baseline, recent, delta } ] }`. If the parsed JSON does not match (missing `flags` array, or a flag missing a required field), **skip with a WARN** (`evolve: extra-source <path> failed regression-flags schema gate`) — never guess at a different shape.
3. **Emit one `domain-regression` learning candidate per flag that is PERSISTENT** — i.e. the same `metric` regressed across ≥2 consecutive sessions (cross-reference prior sessions' sidecar reads or the existing learnings store for the same `subject`). A one-off flag is noise; only a persistent regression earns a candidate.
   - `type`: `learning-type` from the entry (registered enum value `domain-regression`)
   - `subject`: the flag's `metric`
   - `insight`: a human-readable regression statement (e.g. "metric `<metric>` regressed: baseline <baseline> → recent <recent> (delta <delta>) persisting across ≥2 sessions")
   - `evidence`: `baseline → recent` (the concrete data points from the sidecar)
   - `confidence` / `expires_at`: derived via the existing confidence + decay infrastructure (Step 3.5), exactly as for the built-in learning types. `domain-regression` carries a 60-day TTL (`LEARNING_TTL_DAYS`).
4. Candidates flow into the SAME Step 3.4 AskUserQuestion confirmation + Step 3.5 write path as the built-in learning types — there is no separate write path.

### Step 3.2: Pattern Extraction

For each of the 9 built-in analyzer learning types, apply these heuristics:

#### 1. fragile-file (type: `fragile-file`)

- Look at wave data: if the same file appears in 3+ waves' `files_changed` within a session, it is fragile
- Cross-session: if a file appears in 3+ different sessions' `files_changed`, flag it
- Subject = file path (relative to project root)

#### 2. effective-sizing (type: `effective-sizing`)

- Compare `total_agents` and `total_waves` across session types
- Calculate average agents per wave for each session type
- Subject = canonical identifier like `deep-session-sizing` or `feature-session-sizing`
- Insight = "Deep sessions average X agents across Y waves" or "Feature sessions work well with X agents/wave"
- **Over-delivery ratio aggregation (#730/H4, #794.7):** compute the MEDIAN of `waves[].over_delivery_ratio` across the last ~5 `sessions.jsonl` records of the same `session_type`, filtered to waves whose `role` is not `Discovery`/`Finalization` and which carry the field (skip records lacking the field — pre-#730; also skip Discovery/Finalization waves, whose planned set is empty by design). This exclusion clause is intentionally identical to `skills/session-plan/SKILL.md` Step 0.5 "Over-delivery sizing" — keep the two wordings in sync on edit. Fold the median into this candidate's `insight`/`evidence` fields — e.g. `evidence`: `"median_over_delivery_ratio: 1.4 (n=12 waves, session_type=deep)"` — so `session-plan` Step 0.5 can read the ratio from the `effective-sizing` learning first, falling back to its own direct `sessions.jsonl` scan only when no such learning exists.

#### 3. recurring-issue (type: `recurring-issue`)

- Look at `agent_summary` — if `failed` or `partial` > 0 across multiple sessions, flag
- Check wave `quality` fields — repeated failures indicate recurring issues
- Subject = issue pattern identifier (e.g., "test-failures-in-wave-execution", "lint-regressions")

#### 4. scope-guidance (type: `scope-guidance`)

- Cross-reference `effectiveness.planned_issues` vs `effectiveness.completion_rate`
- **Skip sessions that lack the `effectiveness` field** (early sessions may not have it)
- If completion_rate is consistently 1.0 with N issues, note "N issues per session works well"
- If completion_rate < 0.7, note "scope was too large"
- Subject = `optimal-scope-per-session-type`

#### 5. deviation-pattern (type: `deviation-pattern`)

> **Ownership Reference:** See `skills/_shared/state-ownership.md`. evolve has read-only access to STATE.md.

- Read `<state-dir>/STATE.md` if it exists and check `## Deviations` section
- Cross-reference with session duration vs planned waves
- Subject = pattern name (e.g., "scope-creep-in-feature-sessions", "underestimated-complexity")

#### 6. stagnation-class-frequency (type: `stagnation-class-frequency`)

- Read `stagnation_events` from the most recent 5 sessions in `sessions.jsonl` (skip sessions lacking the field — they predate #84).
- For each `(file, error_class)` pair appearing in ≥2 sessions, extract a candidate:
  - Subject = `<file>:<error_class>` (e.g., `skills/wave-executor/wave-loop.md:edit-format-friction`)
  - Insight = "File <X> has <error_class> stagnation in <N> recent sessions — candidate for pre-edit grounding (#85)."
  - Evidence = "<N> sessions with stagnation_events for this file/class"
- These learnings feed #85 (pre-edit grounding injection) when it ships — high-frequency pairs trigger grounding.

#### 7. hardware-pattern (type: `hardware-pattern`)

> **v3.1.0 / Sub-Epic #160 (C2, issue #171).** Keyed on `host_class` rather than project — surfaces hardware-bound problems that affect the user across every repo on the same machine. Complements the project-keyed types above.

- Read `.orchestrator/metrics/events.jsonl` (session + wave events) and the registry `sweep.log` at `~/.config/session-orchestrator/sessions/sweep.log`. Both are optional — missing files produce no candidates.
- Invoke `scripts/lib/hardware-pattern-detector.mjs` → `detectHardwarePatterns({events, sweepLogEntries, thresholds})`. Thresholds come from Session Config `resource-thresholds` when present, falling back to `DEFAULT_THRESHOLDS`.
- Five detection signals (aggregated per `(signal, host_class)` pair, ≥2 occurrences required):
  - **oom-kill** — `orchestrator.session.stopped` with `exit_code: 137` or OOM-marker in `error`
  - **heartbeat-gap** — registry sweep-log entries with `gap_minutes` above `resource-thresholds.zombie-threshold-min`
  - **concurrent-session-pressure** — session-start events with `peer_count ≥ concurrent-sessions-warn`
  - **disk-full** — events whose `error` matches `ENOSPC` / "no space left"
  - **thermal-throttle** — events whose `resource_snapshot.cpu_load_pct` crosses `cpu-load-max-pct`
- Each candidate is piped through `candidateToLearning()` → `validateLearning()`. Default `scope` is `private` (in-repo only). To promote to `public`, the user runs `npm run share:hw-learnings -- --promote` (C3 export). This anonymizes each `private` hardware-pattern entry, validates via the privacy contract, and appends a `public` twin to `learnings.jsonl` (original preserved). Use `--dry-run` to preview without writing.
- Subject convention: `<signal>::<host_class>` (e.g., `oom-kill::macos-arm64-m3pro`). The `::` separator avoids colliding with project-keyed subjects.
- Confidence starts at 0.5 like other learning types, but decay is slower in practice: hardware stays the same longer than code. This is an emergent property of the existing expire-after-N-days policy applied to a mostly-stable `host_class` — no special-casing needed.
- **Presentation in step 3.5** (see below): render hardware-patterns in a dedicated section titled `## Hardware Patterns (keyed on host_class)` after the project-keyed patterns. This makes the source of the learning obvious to the user at confirmation time.

#### 8. autopilot-effectiveness (type: `autopilot-effectiveness`)

> **v3.2 Autopilot / Sub-Epic #271 (issue #298).** Compares manual vs. autopilot session outcomes per mode (housekeeping, feature, deep) so the loop can learn whether walk-away runs preserve quality. Complements the project-keyed and hardware-keyed types above.

- Read `.orchestrator/metrics/autopilot.jsonl` (one record per autopilot loop run) **and** `.orchestrator/metrics/sessions.jsonl` (manual + autopilot session outcomes). Both are optional — missing files produce no candidates.
- Invoke `scripts/lib/evolve/autopilot-effectiveness.mjs` → `analyze(autopilotRuns, sessions)`. The module pairs records by `mode` and compares completion-rate, carryover-rate, kill-switch frequency, and quality-gate pass-rate between the two populations.
- **Data-gating contract:** the analyzer requires **≥20 paired manual+autopilot runs per mode** before emitting any candidates. Below that threshold the function returns `[]` (empty input contract) — evolve simply skips this type for that mode and reports nothing. This prevents premature conclusions from small samples (#297 calibration depends on the same threshold).
- Subject convention: `<mode>-manual-vs-autopilot` (e.g., `housekeeping-manual-vs-autopilot`, `feature-manual-vs-autopilot`, `deep-manual-vs-autopilot`). One subject per mode that crosses threshold.
- Insight = "Autopilot <mode> sessions complete at <X>% vs. manual <Y>% (Δ <Z>pp across N pairs)" or analogous carryover/kill-switch framing when those signals dominate.
- Confidence starts at 0.5 like other learning types; lifecycle ±0.15 / -0.20 via the existing dedupe-and-update infrastructure in Step 3.3 — no special-casing.
- Each candidate is piped through `candidateToLearning()` → `validateLearning()` exactly like the other types. Default `scope` is `private` (autopilot RUN data is per-host until the user opts in to share). (refs #298)

#### 9. autonomy-verdict (type: `autonomy-verdict`)

> **Dispatcher Autonomy / P3.5 (issue #683).** Synthesizes per-repo or per-scope autonomy readiness from autopilot run outcomes plus advisory skill-judge signals. Complements `autopilot-effectiveness`: type 8 asks whether autopilot preserves quality by mode; this type asks whether a repo/scope is ready for more dispatcher autonomy.

- Read `.orchestrator/metrics/autopilot.jsonl`, `.orchestrator/metrics/sessions.jsonl`, and `.orchestrator/metrics/skill-judgments.jsonl`. All are optional — missing files produce no candidates.
- Invoke `scripts/lib/evolve/autonomy-verdict.mjs` → `analyze(autopilotRuns, sessions, skillJudgments, { repo | scope })`. The analyzer reuses the type-8 mode rollups and combines them with counted skill-judge `applied`/`completed` signals.
- **Data-gating contract:** the analyzer requires **≥1 autopilot run and ≥1 canonical advisory skill-judge judgment** (`schema_version: 1`, `event: "judged"`, `advisory: true`) before emitting a candidate. Below that threshold it returns `[]` so `/evolve analyze` stays quiet during cold-start.
- Subject convention: `<repo-or-scope>-autonomy-readiness` (e.g., `session-orchestrator-autonomy-readiness`).
- Insight frames the readiness verdict (`ready`, `watch`, or `not-ready`), the combined score, and the signal counts. Evidence includes the normalized scope, verdict, autopilot summary, and skill-judge summary.
- Confidence is derived in the analyzer from signal volume, judge confidence, and score separation, then flows through the existing dedupe-and-update infrastructure in Step 3.3. Default `scope` is `private` because autopilot and skill-judge data are host/session-local. (refs #683)

### Step 3.2b: Zero Patterns Check

If no patterns were extracted across all built-in analyzers and configured extra sources, report: "No patterns found in session history. This can happen with very few sessions or sessions that lack detailed wave/agent data." and skip to end (do not proceed to AskUserQuestion).

### Step 3.3: Deduplicate Against Existing Learnings

For each extracted pattern, check if a learning with same `type` + `subject` already exists in `learnings.jsonl`:

- **If exists:** propose confidence update (+0.15 if confirmed by new evidence, -0.2 if contradicted)
- **If new:** propose as new learning with confidence 0.5

This match is **exact string equality on `type` + `subject`** — it is blind to two records that say the same thing in different words, and it cannot detect a contradiction at all. The `-0.2 if contradicted` branch above has therefore had no producer since it was written. Step 3.3b is that producer.

### Step 3.3b: Relation Judgment (#1016)

> **Cadence: once per candidate.** Step 3.2b's zero-patterns check and Step 3.4's single AUQ are once-per-run; Step 3.5's write is once-per-run. This step is the only per-candidate one in Phase 3 — the pool build happens once, the judgment runs for each pattern that seeds a pool.

> **Runs in `/evolve`, never in a wave.** The pool build is O(N²) over the candidate + corpus union (~13 ms at N=100 records; the viability boundary is ~N=2000). `/evolve` is operator-invoked and off the dispatch hot path — that is the whole reason this lives here and not in `skills/wave-executor/`. Do not invoke it from a wave prompt, an inter-wave checkpoint, or a hook.

Skip this step entirely when `.orchestrator/metrics/learnings.jsonl` is absent or holds fewer than 2 entries — with no corpus there is no relation to judge.

1. **Pool.** Call `buildCandidatePools(records, { now })` from `scripts/lib/learnings/candidates.mjs`, passing the union of this run's extracted candidates and the on-disk corpus. It returns `{pools, duplicates, stats}`: `duplicates` are the exact-`learning_key` groups (already certain — no judgment needed), and each `pools[]` entry is `{seed, candidates}` where `candidates[].record` is a bounded, per-seed, non-transitive neighbour set. No clustering, no transitive closure: a neighbour of a neighbour is not a neighbour.

2. **Judge, per candidate that seeds a pool.** `buildJudgmentInput({candidate, neighbours})` then `judgeCandidate(input, { judge })`, both from `scripts/lib/learnings/judgment.mjs`. `buildJudgmentInput` returns `null` for a candidate with no usable `id` — skip that candidate, do not judge it. `judge` is the injected verdict provider: on Claude Code the coordinator reads the `input` envelope and returns the JSON object its `output_contract` field describes. There is no subagent type for this — do not dispatch one (#614: a read-only agent that must write its own sidecar never fires).

3. **Apply, through the one choke point.** `applyVerdict(verdict, effects)` is the only place a judgment may become an effect. In `/evolve` every effect handler is a *proposal recorder*, never a writer: `refine` / `supersede` / `merge` record a proposed change, and `proposeContradiction` records a contradiction pair. `applyVerdict` resolves all four handlers before invoking any of them, so an unwired handler refuses the whole batch rather than applying the decisions that happened to come first.

4. **Fail closed.** `verdict.ok === false` (any of the eight failure modes — unparseable, partial, phantom_id, self_reference, empty, timeout, enum_violation, duplicate_target) means **no relation was read**, not "no relation exists". The candidate keeps its Step 3.3 exact-match verdict and nothing about it is surfaced as a relation. Never fall back to a default decision, never repair-retry a malformed verdict, and never render an unreadable judgment to the operator — surfacing a relation IS the claim, so a voided judgment must not reach the AUQ at all.

5. **Route into the existing gate.** Every surviving decision becomes an OPTION in Step 3.4's AskUserQuestion, never an action:
   - `contradict` → a contradiction pair, presented as its own category beside "duplicate". If the operator selects it, it feeds the `-0.2 if contradicted` branch in Step 3.3 above, applied by Step 3.5(3) — which deliberately does NOT reset `expires_at`.
   - `supersede` / `merge` → an omit-the-loser (or replace-both-with-one) proposal. If selected, the operator's next generation simply omits those ids and Step 3.5(5) archives them — never a hand-delete. The merged record must carry both sources' provenance in its own `evidence`.
   - `refine` → an edit proposal against the existing record's `insight` / `evidence`.
   - `skip` / `abstain` → nothing is surfaced.

**The brandmauer holds here, unchanged (#693 FA2/FA3).** The judgment computes; it never writes. Every `.claude/rules/` write and every `learnings.jsonl` write stays behind the operator's Step 3.4 selection and Step 3.5's `--prune` invocation.

**Named ceiling (revisit trigger).** A `supersede` or `merge` executed through Step 3.5(5) is tagged `_archive_reason: "superseded"` with a `_superseded_by` tombstone **only when the two records share `type` + non-empty `subject`** — that is `pruneLearnings()`'s own consolidation pass. A cross-wording pair (the exact case this step exists to find) does not share a subject, so its loser is archived `pruned` instead: still in the corpus, still resolvable by id, but the archive record does not name its replacement. Revisit when the CLI grows per-record drop routing, or when an archive audit needs to answer "what replaced this?" for cross-wording merges.

### Step 3.4: Present Findings via AskUserQuestion

Present extracted patterns to the user for confirmation. Use AskUserQuestion with `multiSelect: true`:

> On Codex CLI where AskUserQuestion is unavailable, present as a numbered Markdown list.

```
AskUserQuestion({
  questions: [{
    question: "Which learnings should be saved?\n\nExtracted patterns from session history:",
    header: "Evolve — Confirm Learnings",
    options: [
      {
        label: "[type] subject",
        description: "insight | evidence: ... | confidence: 0.5 (new) or +0.15 (update)"
      },
      ...
      {
        label: "Skip all",
        description: "Do not save any learnings this time"
      }
    ],
    multiSelect: true
  }]
})
```

If user selects "Skip all" or selects nothing, abort gracefully: "No learnings saved."

### Step 3.5: Write Confirmed Learnings

For confirmed learnings, use atomic rewrite strategy:

1. Read ALL existing lines from `.orchestrator/metrics/learnings.jsonl` (if exists) into memory. If not found, check `<state-dir>/metrics/learnings.jsonl` as a legacy fallback. If legacy data is found, it will be migrated to the v2 path on write (step 5).
2. Apply confidence updates for confirmed existing learnings:
   - Increment confidence by +0.15
   - Cap at 1.0
   - Reset `expires_at` using `deriveExpiresAt(now, type)` unless the candidate supplies a more specific expiry
3. Apply confidence decrements for contradicted learnings (-0.2) — do NOT reset `expires_at` for contradicted learnings (let them decay naturally)
4. Append new learnings with the **canonical schema_version:1 shape** — every field is required (#303):
   - `schema_version`: **1** (integer, ALWAYS — never omit)
   - `id`: UUID v4 string generated via `node -e "const {randomUUID}=require('crypto');process.stdout.write(randomUUID())"` or `uuidgen | tr '[:upper:]' '[:lower:]'`. MUST be a non-empty UUID string. **Never omit** — missing `id` causes 100% mirror-skip (#303).
   - `type`: one of `fragile-file`, `effective-sizing`, `recurring-issue`, `scope-guidance`, `deviation-pattern`, `stagnation-class-frequency`, `hardware-pattern`, `autopilot-effectiveness`, `autonomy-verdict`, `domain-regression` (#638 — only when sourced from `evolve.extra-sources`, see Step 3.1b)
   - `subject`: the pattern subject
   - `insight`: human-readable description of the pattern. **MUST be `insight`** — do NOT use `description` or `recommendation` (legacy alias keys that vault-mirror cannot read; see #303).
   - `evidence`: specific data points that support the pattern
   - `confidence`: use the candidate's derived confidence when supplied (e.g., `autonomy-verdict`); otherwise 0.5 for new learnings
   - `source_session`: **non-empty kebab-slug string** identifying the session from which the pattern was extracted (e.g. `main-2026-04-27-1942`). MUST be a string — never an object, array, number, or null. If multiple sessions contributed, use the earliest. If unknown, use `"unknown"` (the string). **Never** pass `String(<object>)` — that yields `"[object Object]"` and breaks the YAML mirror downstream (#307). Optional pre-write validation: `jq -e 'select(.source_session | type == "string" and length > 2)'`.
   - `created_at`: current ISO 8601 date
   - `expires_at`: preserve the candidate's derived expiry when supplied; otherwise derive from `LEARNING_TTL_DAYS[type]` via `deriveExpiresAt()` (falling back to the schema default) rather than hard-coding a 30-day horizon
   - `file_paths` (optional): repo-relative path(s) scoping the learning to specific files/directories. Required for a learning to ever become `/reconcile`-eligible (issue #900; see `docs/rule-authoring.md` § "Learning Type-Taxonomy, TTL & Provenance Standard"). For a `fragile-file` candidate, `file_paths: [subject]` is mechanically derivable — `subject` already IS the file path.
5. **Write the next generation through the archive-safe pipeline — NEVER a `>` redirect (#1017).**

   Steps 6–8 (prune, consolidate, rewrite) are **not prose you execute by hand**. They are
   `pruneLearnings()` in `scripts/lib/learnings/expiry-sweep.mjs`, the same module (and the same
   crash-safe ordering, KEEP-batch probe, and `.bak-<ISO>` snapshot) the expiry sweep uses. Until
   #1017, this step said "write entire result back with `>`" — with no archive append at all, which
   deleted 11 of 13 `learning-id` provenance targets referenced by rendered `.claude/rules/*.md`.
   Do not hand-roll a `jq | ... > learnings.jsonl` pass; it bypasses every #721 safety net.

   Write the full next-generation entry set (existing entries **with** the step-2/3 confidence
   updates, **plus** the step-4 new learnings) as JSONL to a temp sidecar **via the Write tool**
   (not a shell `>` redirect — the destructive-command guard blocks it), then invoke the
   `--prune` subcommand of the sweep CLI:

   ```bash
   NEXT=".orchestrator/metrics/.learnings-next.jsonl"   # written by the step above
   node scripts/sweep-expired-learnings.mjs --prune --apply --json --entries "$NEXT" && rm -f "$NEXT"
   ```

   `--file` / `--archive` default to the canonical store + archive paths — pass them only when
   operating on a non-default pair. The command prints ONE JSON line; capture it as `$PRUNE` and
   report its `{scanned, kept, archived, byReason}` in the final summary. Preview first with
   `--prune --dry-run --json` (same counts, zero writes) whenever the next generation was
   hand-assembled.

   > **This step is `/evolve`'s only store-write path.** Until #1017 the invocation lived here as
   > an inline `node --input-type=module -e` block, which is a mechanism hiding inside prose: no
   > `--help`, no exit-code contract, no test. Do not re-inline it, and do not hand-roll a
   > `jq | ... > learnings.jsonl` pass — that bypasses every #721 safety net.

   **Exit codes are the no-op rule.** `0` = applied (or a clean no-op). `1` = input error: the
   sidecar is absent, carries a malformed line, or holds no records — the store and the archive
   were **not touched**;
   re-write the sidecar and re-run. `2` = the prune itself failed inside the lib. On any non-zero
   exit, surface the error and stop — never retry with a shell rewrite, and never delete `$NEXT`
   (the `&&` above already withholds the `rm`, so the assembled generation survives for a retry).

   `pruneLearnings()` — the function the subcommand calls — performs steps 6 + 7 + 8 mechanically
   and archives **every** record that
   leaves the store, tagged with `_archived_at` + an `_archive_reason` from the closed enum
   `expired | pruned | superseded | merged`:

   - **6. Prune** — `expires_at` < now → `expired`; `confidence <= 0.0` → `pruned`.
   - **7. Consolidate duplicates (NULL-SUBJECT SAFE)** — same `type` + non-empty `subject`: the
     highest-confidence entry wins; each loser is archived `superseded` with a
     `_superseded_by: <winning id>` tombstone. Entries with null/empty/missing `subject` are NEVER
     collapsed — each is keyed by its unique `id` and always preserved (issue #284).
   - **8. Rewrite** — via `rewriteLearnings()`: full schema validation, a `.bak-<ISO>` snapshot
     (keep-3 rotation), then an atomic tmp+rename. Any id you drop from the temp sidecar without
     an explicit reason is archived `pruned` automatically — the store can no longer lose a record
     silently, whatever the next generation omits.

   No `graceDays` here, deliberately: `/evolve` re-stamps `expires_at` on every reinforced learning
   in steps 2–3 of THIS run, strictly before the prune, so an entry still expired at prune time is
   one the analyzer just declined to reinforce. (The sweep's 14-day grace exists to protect entries
   from being archived *before* that reinforcement pass runs — a hazard that cannot occur here.)

   Report the returned `{scanned, kept, archived, byReason}` alongside the counts in the final
   summary line. On a non-zero exit, do NOT retry with a shell rewrite — surface the error. The
   old "read back the first line to confirm valid JSON" check is redundant here: `rewriteLearnings()`
   round-trip-validates EVERY line before any byte reaches disk (#662), and the `malformed` guard
   above rejects an unparseable sidecar before the store is touched at all.
6. **Vault mirror (conditional):** Check `$CONFIG."vault-integration".enabled` via jq. If the field is missing or `false`, skip this step entirely — skill behavior is unchanged.

   If `enabled` is `true`:

   a. Check `$CONFIG."vault-integration".mode`. If `mode` is `off`, skip the mirror invocation (treat as disabled). If `mode` is absent, default to `warn`.

   b. Resolve the vault directory: use `$CONFIG."vault-integration"."vault-dir"` if non-null, otherwise fall back to the `$VAULT_DIR` environment variable. If neither is set, emit a warning and skip.

   c. Invoke the mirror script. Derive a synthetic `EVOLVE_SESSION_ID` so the vault-mirror auto-commit phase (#31) produces a traceable commit subject (`chore(vault): mirror evolve-<date> — N learnings + 0 sessions`). Pass `--vault-name` when `vault-integration.vault-name` is set in Session Config:
      ```bash
      EVOLVE_SESSION_ID="evolve-$(date -u +%Y-%m-%d-%H%M)"
      EVOLVE_VAULT_NAME=$(echo "$CONFIG" | jq -r '."vault-integration"."vault-name" // empty')
      node "$PLUGIN_ROOT/scripts/vault-mirror.mjs" \
        --vault-dir "<vault-dir>" \
        --source .orchestrator/metrics/learnings.jsonl \
        --kind learning \
        --session-id "$EVOLVE_SESSION_ID" \
        ${EVOLVE_VAULT_NAME:+--vault-name "$EVOLVE_VAULT_NAME"}
      ```

   d. Handle the exit code according to `mode`:
      - `warn` (default): on non-zero exit, surface a warning in evolve output (e.g. "Warning: vault mirror failed — learnings saved locally but not mirrored.") but do NOT fail the skill.
      - `strict`: on non-zero exit, fail the skill immediately and report the error to the user.

   e. On success (exit 0), report: "Mirrored N learnings to `<vault-dir>/40-learnings/`."

Report: "Saved N new learnings, updated M existing. Total active: K."

### Step 3.6: C2 Auto-Repair Feeder (opt-in — #647)

> **Default OFF (advisory-only).** With no `skill-evolution:` block in Session Config, this step surfaces repair candidates as ADVICE only — it applies nothing and opens no MR. This mirrors the opt-in precedent of `slopcheck` (#520) and `verification-auto-fix` (#521): the engine is dark unless explicitly enabled.

After confirmed learnings are written (Step 3.5), the actionable subset can feed the C2 tiered auto-repair engine (Epic #643 / issue #647). This is a pointer section — the modules own the logic; do not duplicate it here.

**`skill-evolution:` is a DISTINCT sibling of the pre-existing `evolve:` block.** `evolve:` (`extra-sources`) tunes learning EXTRACTION (Step 3.1b); `skill-evolution:` tunes repair AUTONOMY. They are parsed by different modules and never share keys — do not conflate them. The `skill-evolution:` block is parsed by `scripts/lib/config/skill-evolution.mjs` (`_parseSkillEvolution`) and surfaced at `$CONFIG['skill-evolution']` (wired in `scripts/lib/config.mjs`). Shape: `{ autonomy: 'off'|'advisory'|'autonomous-gated', 'evidence-floor': number, judge: boolean }`, default `autonomy: 'off'`. Do NOT add `skill-evolution:` as a column-0 key to any consolidated Session Config parity block — it is a standalone top-level block (claude-md-drift-check Check-6 enforces parity only on the `## Session Config` keys).

**Candidate intake.** Pass the post-Step-3.5 learnings (and, when available, the `claude-md-drift-check` result) to `extractCandidates({ learnings, driftResult, evidenceFloor: $CONFIG['skill-evolution']['evidence-floor'], now })` from `scripts/lib/skill-evolution/candidate-intake.mjs`. It is a pure transform — only actionable, non-expired learnings whose `confidence ≥ evidence-floor` AND whose insight is prescriptive AND resolves to a repo-relative path become `RepairCandidate`s.

**Gate per artifact type.** Each candidate's `target_path` is classified by `classifyTarget(target_path, { repoRoot })` from `scripts/lib/skill-evolution/blast-radius-classifier.mjs` (the heart of the design; path-traversal-safe, fail-closed):

| Target type | Gate | Posture |
|---|---|---|
| plugin-skill (`skills/…`) | none | **always-mr** — never autonomous |
| local-skill (`.claude/skills/…`) | none | **always-mr** — never autonomous |
| local-config (ROOT `CLAUDE.md` / `AGENTS.md` Session Config) | config-validation | **autonomous-gated** |
| anything else | none | always-mr (fail-closed) |

Only ROOT-instruction Session Config edits are eligible for autonomous apply, and only when ALL of: `runConfigValidationGate({ repoRoot })` (`scripts/lib/skill-evolution/config-validation-gate.mjs`) is GREEN (parse-config + config-schema + claude-md-drift-check) **AND** `evidence ≥ evidence-floor` **AND** `autonomy: autonomous-gated`. Skill repairs are MR-only by construction.

**Invocation contract (this foundation slice = ADVISORY surfacing).** The single orchestrator that ties intake → classify → gate → route → stamp together is `runRepairEngine({ repoRoot, config, learnings, driftResult, dryRun })` from `scripts/lib/skill-evolution/engine.mjs` — it returns `{ outcomes, summary }` and applies the full gate-per-artifact-type decision matrix internally (`autonomy: off` ⇒ every outcome is advisory-only). In the default/advisory posture, `/evolve` SURFACES candidates and their classification only — it does not apply or open MRs. Apply is gated on the config-validation gate above; MR-opening (`openRepairMr({ candidate, diff, repoRoot, dryRun })` from `scripts/lib/skill-evolution/mr-opener.mjs`) is gated on `autonomy != off`. Candidate de-dup / `processed_at` lifecycle is owned by `scripts/lib/skill-evolution/idempotency.mjs`. When `autonomy: off` (default), report the surfaced candidates as advice and stop.

---

## Phase 4: Review Mode

Interactive management of existing learnings.

### Step 4.1: Load Learnings

- Read `.orchestrator/metrics/learnings.jsonl`. If not found, check `<state-dir>/metrics/learnings.jsonl` as a legacy fallback.
- If neither exists or both are empty: "No learnings found. Run `/evolve analyze` first."
- Parse each line as JSON

### Step 4.2: Display Learnings

Present a formatted table grouped by type. Include the **Effective** column — the
recency-decayed surfacing score (#670) — so stale high-confidence entries are visible
as decay candidates next to their static confidence:

```
## Active Learnings

| # | Type | Subject | Confidence | Effective | Expires | Insight |
|---|------|---------|------------|-----------|---------|---------|
| 1 | fragile-file | src/lib/auth.ts | 0.80 | 0.78 | 2026-07-05 | Changed in 4 of last 5 sessions |
| 2 | effective-sizing | feature-session-sizing | 0.65 | 0.61 | 2026-06-20 | Feature sessions work well with 3 agents/wave |
| ... | ... | ... | ... | ... | ... | ... |

Summary: N active learnings (M high confidence, K expiring soon)
```

> **Effective (decayed) score — #670.** Retrieval/surfacing ranks by an
> `effectiveScore = max(confidence × 0.5^(ageDays / halfLifeDays), confidence × floorFactor)`
> blend, NOT raw confidence. `ageDays` derives from `last_reinforced` / `last_accessed` /
> `updated_at` when present, else `created_at`. So a stale high-confidence learning ranks
> below a fresh mid-confidence one, while the `floorFactor` (default 0.1) guarantees a
> durable learning never collapses to ~0. Tuned under the existing `evolve:` Session Config
> block (`decay-enabled: true`, `decay-half-life-days: 90`, `decay-floor-factor: 0.1` — all
> conservative defaults; set `decay-enabled: false` to restore pure-confidence ordering).
> Implemented in `scripts/lib/learnings/surface.mjs` (`effectiveScore` + `surfaceTopN`).
> The confidence FILTER (`> 0.3`) is unchanged — decay re-ranks survivors, it does not
> change eligibility.

### Step 4.3: Interactive Management

Use AskUserQuestion with options:

> On Codex CLI where AskUserQuestion is unavailable, present as a numbered Markdown list.

```
AskUserQuestion({
  questions: [{
    question: "What would you like to do with your learnings?",
    header: "Evolve — Review",
    options: [
      { label: "Boost confidence", description: "Select learnings to boost (+0.15)" },
      { label: "Reduce confidence", description: "Select learnings to reduce (-0.2)" },
      { label: "Delete specific learnings", description: "Select learnings to remove" },
      { label: "Extend expiry", description: "Reset expires_at by learning-expiry-days from now" },
      { label: "Done — no changes", description: "Exit without changes" }
    ]
  }]
})
```

If user selects "Boost confidence", "Reduce confidence", "Delete specific learnings", or "Extend expiry", present a follow-up AskUserQuestion with `multiSelect: true` listing all learnings by `# | type | subject` so the user can select which ones to modify.

> On Codex CLI where AskUserQuestion is unavailable, present as a numbered Markdown list.

### Step 4.4: Apply Changes

Use the same archive-safe pipeline as Phase 3, Step 3.5 — **never** a hand-rolled `>` rewrite (#1017):

1. Read all lines from `learnings.jsonl`
2. Apply the selected operation to selected learnings:
   - **Boost:** +0.15 confidence (cap 1.0), reset expires_at to +`learning-expiry-days`
   - **Reduce:** -0.2 confidence
   - **Delete:** omit the selected entries from the next generation — do NOT delete them by hand.
     `pruneLearnings()` detects every **record** that left the store — reconciled by `id`, or by a
     content fingerprint when a record carries no usable `id` — and archives it with
     `_archive_reason: "pruned"`, so a `learning-id` referenced by a rendered rule stays resolvable.
   - **Extend:** reset expires_at to current date + `learning-expiry-days`
3. Steps 3–5 of the old prose (prune / consolidate / rewrite) are `pruneLearnings()` — run the
   **exact** Step 3.5(5) invocation, writing the post-operation entry set to the `--entries`
   sidecar. It prunes
   (`expires_at` < now → `expired`; `confidence <= 0.0` → `pruned`), consolidates duplicates
   (same `type` + non-empty `subject`, highest confidence wins, loser archived `superseded` with
   `_superseded_by`; null-subject entries preserved individually per #284), and rewrites through
   `rewriteLearnings()` with its `.bak-<ISO>` snapshot.

Report: "Updated N learnings. Total active: K. Archived: A (<byReason>)."

---

## Phase 5: List Mode

Simple read-only display.

### Step 5.1: Load and Display

- Read `.orchestrator/metrics/learnings.jsonl`. If not found, check `<state-dir>/metrics/learnings.jsonl` as a legacy fallback.
- If neither exists: "No learnings yet. Run `/evolve analyze` to extract patterns from session history."
- Parse each line as JSON

### Step 5.2: Formatted Output

Display a formatted table grouped by type:

```
## Active Learnings

### fragile-file
| Subject | Confidence | Expires | Insight |
|---------|------------|---------|---------|
| ... | ... | ... | ... |

### effective-sizing
| Subject | Confidence | Expires | Insight |
|---------|------------|---------|---------|
| ... | ... | ... | ... |

(repeat for each type that has entries)
```

### Step 5.3: Summary

Display summary line:

```
N active learnings (M high confidence, K expiring soon)
```

- **High confidence** = confidence > 0.7
- **Expiring soon** = expires_at within 14 days of current date

---

## Phase 6: Dialectic Mode

Single-pass LLM derivation of USER.md + AGENT.md (peer cards from #503) updates from current learnings + sessions + steering files. Dry-run-default per #506 EARS contract.

### Step 6.0: Argument Parsing

Parse `$ARGUMENTS` for trailing flags after the `dialectic` keyword:

| Flag | Default | Behavior |
|---|---|---|
| `--apply` | `false` | Write diff to USER.md/AGENT.md via merger.mjs; without it = dry-run |
| `--dry-run` | `true` | Explicit dry-run (default); mutually exclusive with --apply |
| `--model <name>` | from Session Config `dialectic.model` (default `haiku`) | Override LLM |
| `--budget-tokens <N>` | from Session Config `dialectic.budget-tokens` (default 8000) | Token budget |

Mutex check: `--apply` + `--dry-run` together = error "flags mutually exclusive".

### Step 6.1: Pre-checks
- Bootstrap gate (Phase 0) — already executed
- Persistence check (Phase 1.2) — already executed
- Cadence check: if invoked via session-end Phase 3.6.7 auto-trigger, the trigger has already pre-checked cadence. For manual invocation, skip cadence — manual always runs.

### Step 6.2: Data Load
Read all 4 input sources via `runDialecticDeriver()` from `scripts/dialectic-deriver.mjs` (see W2 I1):
1. Top-N learnings from `.orchestrator/metrics/learnings.jsonl` (default 50, sorted by confidence DESC)
2. Last-K sessions from `.orchestrator/metrics/sessions.jsonl` (default 10, sorted by completed_at DESC)
3. Peer cards via `readPeerCards(repoRoot)` from `scripts/lib/peer-cards/reader.mjs` — returns `{user, agent}` or null
4. Project steering files (CLAUDE.md / AGENTS.md Session Config block + narratives)

Graceful degradation: any null/empty source is acceptable. If ALL inputs empty → return `{status: 'empty-input'}`.

### Step 6.3: Dispatch the Deriver Agent

Construct a `dispatchAgent` function that uses the harness Agent tool to invoke the `dialectic-deriver` agent (see `agents/dialectic-deriver.md`):

```javascript
const dispatchAgent = async ({ model, prompt, maxTokens }) => {
  // Coordinator uses Agent tool with subagent_type: "session-orchestrator:dialectic-deriver"
  // and the model parameter to invoke the right tier
  const result = await Agent({
    description: "Dialectic-deriver LLM pass",
    subagent_type: "session-orchestrator:dialectic-deriver",
    model,
    prompt,
  });
  return { text: result.text, usage: result.usage ?? { input_tokens: 0, output_tokens: 0 } };
};

> **Why `maxTokens` is not passed to Agent():** the Claude Code harness `Agent()` tool does not currently accept a `max_tokens` parameter. Output-token budget is therefore enforced via prompt text (see line 414 in `skills/session-end/SKILL.md`: "with budget ${budget-tokens} input + 4000 output tokens"). The dispatchAgent contract declares `maxTokens` as the canonical interface; the evolve skill destructures it for forward-compat but routes enforcement through the prompt body. When the harness adds a max_tokens hint, this dispatchAgent becomes the single update point.

const result = await runDialecticDeriver({
  dispatchAgent,
  repoRoot: process.cwd(),
  model: argv.model ?? config.dialectic?.model ?? 'haiku',
  budget: { input: argv['budget-tokens'] ?? config.dialectic?.['budget-tokens'] ?? 8000, output: 4000 },
  dryRun: !argv.apply,
  allowEmptying: argv['allow-emptying'] ?? false,
});
```

### Step 6.4: Diff Output & Apply Gate
- If dry-run (default): present diff inline; write to `.orchestrator/dialectic-pending.md` (atomic tmp+rename); EXIT. Suggestion: "Re-run with `/evolve --dialectic --apply` to apply."
- If `--apply`: call `mergePeerCard(existingBody, managedUpdates)` from `scripts/lib/peer-cards/merger.mjs` for each card target, then `writePeerCard(repoRoot, 'user', mergedUserCard)` and `writePeerCard(repoRoot, 'agent', mergedAgentCard)` from `scripts/lib/peer-cards/writer.mjs`. Update the `updated:` frontmatter.
- Report: `Dialectic-derived: M deltas to USER.md, N deltas to AGENT.md. Dry-run | Applied. Tokens: in=<X> out=<Y>.`

### Step 6.5: Error Handling
- `status: 'unknown-model'` → fail with clear error (already thrown by validateModel)
- `status: 'budget-exceeded'` → emit `{status:'budget-exceeded', used:N, budget:M}`, do NOT truncate
- `status: 'would-empty-card'` → warn + require `--allow-emptying` flag
- `status: 'empty-input'` → exit clean with message "dialectic: skipped (no input)"
- subagent crash → log ⚠, exit cleanly (do NOT write to `.orchestrator/dialectic-pending.md`)

Cross-reference: PRD #506 AC1-AC4 + EARS gates. Vault Integration: dialectic does NOT mirror to vault (#506 scope — peer cards are repo-local by design; vault mirror is for cross-repo sessions/learnings).

---

## Critical Rules

- **NEVER** modify `learnings.jsonl` without reading it first — race condition prevention
- **NEVER** skip the deduplication check — duplicates degrade the intelligence system
- **NEVER** write learnings without user confirmation — always present via AskUserQuestion first (on Codex CLI where AskUserQuestion is unavailable, present as a numbered Markdown list)
- **ALWAYS** use uuid-v4 for new learning IDs (generate via `uuidgen` or equivalent bash command)
- **ALWAYS** preserve a candidate-supplied `expires_at`; otherwise derive it from `LEARNING_TTL_DAYS[type]` via `deriveExpiresAt()` rather than hard-coding `learning-expiry-days`
- **ALWAYS** present findings to user before writing — no silent writes
- **ALWAYS** route store writes through `pruneLearnings()` / `rewriteLearnings()` — never a shell
  `>` rewrite and never an append `>>`. Those helpers own the schema validation, the `.bak-<ISO>`
  snapshot, and the atomic tmp+rename; a hand-rolled redirect owns none of them (#721, #1017)
- **ALWAYS** let a removed entry land in `learnings-archive.jsonl` — a record may leave the STORE,
  but it may never leave the CORPUS. Rendered `.claude/rules/*.md` cite `learning-id` as provenance;
  a hard delete turns that citation into a dangling pointer (#1017 measured 11 of 13 dead)
- **ALWAYS** cap confidence at 1.0 — never exceed

## Anti-Patterns

- **DO NOT** write learnings without user confirmation — always present via AskUserQuestion first (on Codex CLI where AskUserQuestion is unavailable, present as a numbered Markdown list)
- **DO NOT** append to `learnings.jsonl` with `>>`, and **DO NOT** rewrite it with `>` — call
  `pruneLearnings()` (Step 3.5(5)); a shell redirect bypasses validation, backup, and the archive
- **DO NOT** hard-delete a learning. Every record that leaves the store is archived with an
  `_archive_reason` (`expired` | `pruned` | `superseded` | `merged`) and, for the last two, a
  `_superseded_by` / `_merged_into` tombstone naming its replacement
- **DO NOT** create duplicate learnings — always check type + subject match first
- **DO NOT** set confidence above 1.0 or forget to cap it
- **DO NOT** fabricate patterns — only extract from actual session data with verifiable evidence
- **DO NOT** skip the pruning step — expired and zero-confidence entries must be removed on every write
