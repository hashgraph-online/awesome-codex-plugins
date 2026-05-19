---
name: docs-orchestrator
user-invocable: false
tags: [docs, orchestration, audiences]
model: sonnet
model-preference: sonnet
description: >
  Use this skill when orchestrating documentation generation and updates within a
  session. Maps session scope to audience-specific docs tasks (User / Dev /
  Vault), dispatches the docs-writer agent with source-grounded prompts, and
  reports coverage gaps to session-end. Gated on
  `docs-orchestrator.enabled: true` in Session Config. Zero overhead when
  disabled.
---

# Docs Orchestrator Skill

> Project-instruction file resolution: CLAUDE.md and AGENTS.md (Codex CLI) are transparent aliases — see [skills/_shared/instruction-file-resolution.md](../_shared/instruction-file-resolution.md).

docs-orchestrator coordinates the full documentation lifecycle inside a session: it
detects which audiences (User, Dev, Vault) are touched by the agreed scope, generates
audience-specific task definitions, threads them into the session-plan pipeline, and
verifies that docs tasks produced diffs once waves complete. The skill is opt-in and
default-off — when `docs-orchestrator.enabled: false`, all three hook points
short-circuit with no output and no cost. docs-orchestrator fills the generative-content
gap that sibling skills leave open: `vault-sync` validates but does not write, `vault-mirror`
writes metrics-derived `_overview.md` entries but not narratives, `claude-md-drift-check`
diagnoses CLAUDE.md (or AGENTS.md on Codex CLI) drift but does not remediate it, and `daily` exclusively owns
`03-daily/*`. docs-orchestrator is the only skill that produces new prose grounded in
session output.

## Invocation

Not user-invocable. Triggered at three hook points within the session lifecycle:

1. **session-start Phase 2.5 "Docs Planning"** — after user alignment, before handing
   off to session-plan. Reads the agreed scope, runs audience detection (Phase 2 below),
   and threads the detected audience list into the plan context so session-plan can
   classify tasks correctly.
2. **session-plan Step 1.5 Agent Registry** — `docs-writer` is added to the agent
   registry when docs tasks are present; tasks carrying role `Docs` are assigned to it
   (see session-plan Step 1.8).
3. **session-end Phase 3.2 "Docs Verify"** — after waves complete, verifies that each
   `Docs`-classified task produced a diff in the expected file-pattern target and reports
   gaps per `docs-orchestrator.mode`.

All three hook points are gated on `docs-orchestrator.enabled: true`. When disabled,
every hook exits immediately after the config read.

---

## Phase 0: Input Validation

**When:** At the start of every docs-orchestrator execution (all three hook points).

**Action:** Confirm the invocation context is valid before doing any work.

1. **Caller check** — Verify that this skill was invoked from one of the three
   recognised hook points: `session-start Phase 2.5`, `session-plan Step 1.5`, or
   `session-end Phase 3.2`. If the call context is missing or unrecognised, abort
   with:
   ```
   [docs-orchestrator] ERROR: Unexpected invocation context '<context>'. Expected one of:
   session-start Phase 2.5 | session-plan Step 1.5 | session-end Phase 3.2. Aborting.
   ```

2. **Config gate** — Read `docs-orchestrator.enabled`. If `false`, exit immediately
   with no output, no logging, no side effects.

3. **Task spec validation (hook point 3 only — docs-writer dispatch tasks)** — When
   wave-executor dispatches a Docs task to docs-writer, the task spec MUST contain:
   - `audience` ∈ `{user, dev, vault}` — reject any other value.
   - `file-pattern` — a non-empty glob matching a pattern from `audience-mapping.md`.
   - `rationale` — a non-empty string describing why this audience was triggered.

   If any field is missing or `audience` is not one of the three valid values, abort
   the task dispatch with:
   ```
   [docs-orchestrator] ERROR: Malformed task spec — missing or invalid field '<field>'.
   Required: audience ∈ {user,dev,vault}, file-pattern (non-empty glob), rationale
   (non-empty string). Aborting task dispatch.
   ```
   Do not fall through to Phase 1 with a malformed spec.

4. **Mode validation** — Confirm `docs-orchestrator.mode` ∈ `{warn, strict, off}`.
   Any other value is a config error; abort with:
   ```
   [docs-orchestrator] ERROR: Invalid mode '<value>'. Expected: warn | strict | off.
   ```

---

## Phase 1: Read Session Config

Read Session Config per `skills/_shared/config-reading.md`. Extract:

- `docs-orchestrator.enabled` (boolean, default `false`)
- `docs-orchestrator.audiences` (list, default `[user, dev, vault]`)
- `docs-orchestrator.mode` (`warn` | `strict` | `off`, default `warn`)

If `enabled: false`, exit immediately with no output. Do not log, do not query scope.

Config is read once at invocation; subsequent phases use the cached values. If the
config block is absent entirely, all defaults apply and the skill proceeds as if
`enabled: false`.

---

## Phase 2: Audience Scope Detection

Given the agreed session scope (from the session-start Q&A), determine which audiences
are touched by the planned work:

- **User** — new CLI flags or commands, breaking API changes, install-flow changes,
  new user-facing features, changed examples.
- **Dev** — architecture decisions, major refactors, new modules or subsystems, test
  coverage changes, dependency upgrades, ADR-level choices.
- **Vault** — project status changes, ownership transitions, stack or infra decisions,
  cross-project dependencies, migrations, archival events.

See `audience-mapping.md` (in this directory) for the authoritative file-pattern table,
source rules per audience, and the non-overlap contracts with sibling skills.

Intersect the detected audiences with the `docs-orchestrator.audiences` config value.
Subset selection is supported — e.g., `audiences: [user, dev]` omits Vault writing even
when Vault signals are present in scope.

**When mode is `off`:** skip audience detection and return an empty list — no Docs tasks
are generated.

---

## Phase 3: Task Generation

For each selected audience, generate one or more docs tasks and thread them into the
wave plan.

Each task MUST specify:

| Field | Requirement |
|-------|-------------|
| `audience` | `user`, `dev`, or `vault` — exactly one value |
| `file-pattern` | Non-empty glob from `audience-mapping.md` Audiences & File Patterns table |
| `trigger` | Which scope element motivates this task (e.g., "new `--dry-run` flag added to CLI") |
| `allowed-sources` | Explicit list: `diff`, `git-log`, `session-memory`, `affected-files` |
| `rationale` | Why this audience was selected for this task |

Tasks flow through the standard session-plan pipeline. They are role-classified as
`Docs` and assigned to the `docs-writer` agent at Step 1.8. No custom dispatch path
is required.

**Audience routing — hard non-overlap rules:**

Before finalising a task's `file-pattern`, check it against the forbidden targets:

- `<vault>/01-projects/*/_overview.md` — owned by vault-mirror. If the requested
  target matches this pattern, abort the task with:
  ```
  [docs-orchestrator] ERROR: Target '<path>' matches vault-mirror's owned pattern
  (<vault>/01-projects/*/_overview.md). Docs-writer must not write here. Aborting task.
  ```
- `<vault>/03-daily/*` — owned by daily. Same abort with the relevant pattern
  message.

If no valid non-forbidden target exists for a triggered audience, log an advisory
(mode `warn`) or abort the session plan (mode `strict`):
```
[docs-orchestrator] WARN: Audience 'vault' triggered but all targets are forbidden.
No Docs task generated for this audience.
```

---

## Phase 4: Source Grounding (docs-writer execution protocol)

**This phase applies inside the docs-writer agent**, not in the coordinator. It
documents what the docs-writer MUST do when executing a dispatched Docs task.

Before writing any documentation, the docs-writer MUST read and ingest the actual
source material provided in the task prompt. The canonical four source types are:

1. **diff** — `git diff $SESSION_START_REF..HEAD` — the verbatim diff of all changes
   made during this session. This is the primary authoritative source for what changed.
2. **git-log** — `git log $SESSION_START_REF..HEAD --format="%H %s%n%b"` — commit
   messages and associated bodies. Secondary context for all audiences; use to
   reconstruct the "why" when diffs alone are ambiguous.
3. **session-memory** — Session transcript, wave outputs, and agent summaries stored
   at `~/.claude/projects/<project>/memory/session-*.md` and under `.orchestrator/`
   for the current session. Primary source for Vault narratives (status updates,
   decisions made in conversation).
4. **affected-files** — Full content of the files listed in the wave-scope's
   `allowedPaths` (or the coordinator's `affected-files` context block). Primary for
   User and Dev content where understanding the updated interface, schema, or module
   structure is required.

**No other sources are permitted.** General knowledge about architectural patterns,
Node.js APIs, or project history that is not present in the four sources above must
not be used.

**Source grounding steps:**

1. Confirm all four source blocks are present in the task prompt. If a source block is
   empty or absent, note it before proceeding. **Hard guard:** if ALL four source blocks
   are empty or absent, ABORT this phase with error `docs-writer: no grounding sources
   available — refusing to produce source-less documentation`. Do not fall through to
   silent REVIEW-marker-only output — the coordinator must see the failure.
2. Read each source block in full before drafting any section.
3. For every paragraph drafted, identify which source (or sources) support it.
4. If a claim or narrative cannot be traced to at least one of the four sources, mark
   the paragraph with `<!-- REVIEW: source needed -->` inline — do NOT omit the marker
   to make output look cleaner.

**Write or Update semantics:**

- Prefer `Edit` on an existing file over `Write` (full replace).
- For multi-section updates, prefer surgical section-anchored Edits over full-file Writes.
- When the target file does not exist, use `Write` to create it.
- Respect existing document conventions: preserve heading levels, frontmatter
  structure, and table formats already present in the file.

---

## Phase 5: Source Citations

**This phase applies inside the docs-writer agent**, concurrent with writing.

Every substantive new paragraph MUST include a source attribution in one of two forms:

**Inline HTML comment** (preferred for single-source paragraphs):
```markdown
The coordinator now creates a git stash ref before dispatching each wave, enabling
crash recovery without data loss.
<!-- source: diff -->
```

**Multi-source inline comment:**
```markdown
The new `--dry-run` flag skips file writes and prints a diff to stdout instead.
<!-- source: diff, affected-file:src/cli/index.ts -->
```

**Collected `## Sources` section** (use when most paragraphs share the same sources):
```markdown
## Sources

- diff: `git diff abc123..HEAD`
- git-log: commits `abc123`–`def456`
- session-memory: wave-2 coordinator summary
- affected-files: `src/cli/index.ts`, `SKILL.md`
```

**Sourceless content:**

If a section cannot be sourced from diff, git-log, session-memory, or affected-files,
it MUST be marked:
```markdown
<!-- REVIEW: source needed -->
```

This marker signals to the human reviewer that the content requires verification before
the next release. The docs-writer MUST NOT remove this marker to make output appear
complete.

---

## Phase 6: Output Report

**When:** At the end of every docs-writer agent run, and aggregated by docs-orchestrator
at session-end Phase 3.2 "Docs Verify".

The docs-writer MUST emit a brief structured output summary:

```
[docs-orchestrator] Docs task complete.
  Files touched: <comma-separated list of relative paths>
  Audiences served: <comma-separated list: user | dev | vault>
  REVIEW markers: <count> (files: <comma-separated paths or "none">)
  Source coverage: diff=<used|not used>, git-log=<used|not used>,
    session-memory=<used|not used>, affected-files=<used|not used>
```

**Verification at session-end Phase 3.2:**

1. Collect every task classified as `Docs` in the plan.
2. For each task, resolve the expected `file-pattern` target and check for a diff:
   ```bash
   git diff --name-only $SESSION_START_REF..HEAD
   ```
   Match the output against the task's file-pattern using glob matching.
3. Classify gaps by severity:
   - **missing diff** — no matching file was changed; the task did not run or produced
     no output.
   - **partial** — a matching diff exists but one or more sections contain
     `<!-- REVIEW: source needed -->` markers; needs human review before next release.
4. Report per `docs-orchestrator.mode`:
   - `warn` — log all gaps as advisories in the session final report. Non-blocking;
     `/close` proceeds normally.
   - `strict` — block `/close` until every gap is either resolved (diff exists, no
     REVIEW markers) or explicitly overridden by the user via AskUserQuestion.
   - `off` — skip verification entirely; emit no output.

---

## Non-Overlap with Sibling Skills

- **vault-sync** — validates frontmatter schema; docs-orchestrator generates content.
  Complementary: vault-sync runs after docs-writer writes, catching any schema drift
  introduced by new docs.
- **vault-mirror** — writes `_overview.md` from JSONL metrics records; docs-orchestrator
  writes human-readable narratives in `context.md`, `decisions.md`, and `people.md`.
  Non-overlapping targets by design.
- **claude-md-drift-check** — detects drift in the project-instruction file (CLAUDE.md or AGENTS.md on Codex CLI; diagnostic only);
  docs-orchestrator remediates via the Dev audience path (generative). Complementary:
  drift-check can flag what docs-writer fixes. They must not run on the instruction file in parallel
  within the same session.
- **daily** — exclusively owns `<vault>/03-daily/YYYY-MM-DD.md`. This is a forbidden
  target for docs-orchestrator; the docs-writer prompt must carry this constraint
  explicitly (see Phase 3).

---

## Session Config Reference

The three fields below are parsed in `scripts/lib/config.mjs` (`_parseDocsOrchestrator`)
and validated in `scripts/lib/config-schema.mjs` (`validateDocsOrchestrator`). Defaults
apply when the block is absent.

```yaml
docs-orchestrator:
  enabled: false          # opt-in, default off
  audiences: [user, dev, vault]  # subset selection supported
  mode: warn              # warn | strict | off
```

- `enabled` — master switch. When `false`, all three hook points short-circuit.
- `audiences` — which audiences to generate tasks for. Any subset of
  `[user, dev, vault]` is valid.
- `mode` — verification strictness.
  - `warn` — surfaces gaps as advisories; `/close` is never blocked.
  - `strict` — blocks `/close` until all gaps are resolved or user-overridden.
  - `off` — disables audience detection, task generation, and verification entirely
    (lighter than `enabled: false`; config is still read but all execution paths
    exit early).

---

## Anti-Patterns

- **DO NOT write docs without a traceable source.** Every section must trace to diff,
  git-log, session-memory, or affected-files, or carry `<!-- REVIEW: source needed -->`.
- **DO NOT edit `_overview.md` or `03-daily/*`.** These are owned by vault-mirror and
  daily respectively. Attempting to write these targets aborts the task (Phase 3 hard
  non-overlap check).
- **DO NOT duplicate the audience-mapping table.** Always reference `audience-mapping.md`
  in this directory — never inline the table into a task prompt or another skill.
- **DO NOT dispatch docs-writer outside the wave-executor flow.** Docs tasks must go
  through the standard task → wave-executor → Agent() path so they appear in STATE.md,
  metrics, and the session final report.
- **DO NOT use `hard` as a mode value.** The canonical enum is `warn | strict | off`.
  Any other value fails config validation in Phase 0.
- **DO NOT generate Docs tasks when mode is `off`.** When mode is `off`, skip all
  execution after Phase 0 config read.
