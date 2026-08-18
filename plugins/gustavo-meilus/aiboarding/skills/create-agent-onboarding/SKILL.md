---
name: create-agent-onboarding
description: Use when a repo has no AGENTS.md and an AI coding agent needs onboarding context, or the user asks to generate onboarding files. Produces AGENTS.md (cross-agent), a CLAUDE.md wrapper, and the .aiboarding lifecycle (state, config, hooks). Fallback target when the session-start hook reports missing onboarding files.
---

# Creating agent onboarding files

Treat the AI as a fresh engineer. Generate a compressed, high-signal `AGENTS.md`
at the repo root - the canonical, tool-agnostic onboarding document read natively
by Codex, Copilot, Cursor and imported by Claude Code via a thin `CLAUDE.md`
wrapper - then bootstrap the lifecycle that keeps it current.

**Announce at start:** "Using create-agent-onboarding to generate this repo's onboarding files."

## Runtime awareness
The generation phases below are tool-agnostic and work when this skill runs under
Claude Code, Codex, Copilot CLI, or any SKILL.md-compatible agent. Only Phase 6's
hook/settings installation is Claude Code-specific: when there is no Claude Code
hook runtime (no `.claude/` conventions in play and you are not Claude Code), skip
the hook and settings steps, still install `AGENTS.md`, `CLAUDE.md`, `state.json`,
and `config.json`, and tell the user drift triage is manual (run
`update-agent-onboarding` after meaningful commits).

## Phase 0: Pre-flight routing
Inspect the repo root before generating anything:
- **`AIBOARDING.md` exists (legacy v1 layout):** stop and run `migrate-aiboarding`
  instead - never regenerate from scratch over an existing onboarding investment.
- **`AGENTS.md` already exists:** treat it as primary input. Skip greenfield
  grilling; interrogate only the gaps against the section schema below, then
  propose a restructure as an approval-gated diff. Never overwrite silently.
- **`CLAUDE.md` already exists:** preserve it. The only changes allowed are adding
  the `@AGENTS.md` import line and managing an aiboarding-owned block via
  `.aiboarding/tools/inject-fenced` (marker-fenced, idempotent, removable).

## Shared contracts
**`AGENTS.md` schema** - tool-agnostic, no frontmatter, no Claude-specific syntax.
H2 sections in this exact order:
1. `## Project Purpose`
2. `## Stack and Runtime`
3. `## Build, Test, Run` - exact commands; fast checks and full checks
4. `## Architecture Map` - directories, boundaries, data flow, dependency direction
5. `## Domain Model` - entities, workflows, invariants, vocabulary
6. `## Agent Guardrails` - what agents must NOT assume/refactor/delete/rename/"simplify"
7. `## Known Failure Modes` - mistakes previous agents made or will likely make
8. `## Verification Before Completion` - commands agents must run before claiming done
9. `## Escalation - Ask the User When` - stop-and-ask cases

Backtick-quote every command, identifier, file path, and error string - the
compression byte-preservation checker treats backtick spans as protected.

**`CLAUDE.md` wrapper** - first line `@AGENTS.md`, then an aiboarding-fenced block
of Claude-only workflow notes. Never duplicate `AGENTS.md` content: imports expand
into context at launch, so duplication doubles token cost for zero benefit.

**`.aiboarding/state.json`** - operational state, one top-level key per line
(hooks read it with a line scanner, not a JSON parser):
```json
{
  "aiboarding_version": 2,
  "canonical_file": "AGENTS.md",
  "claude_wrapper": "CLAUDE.md",
  "generated": "YYYY-MM-DD",
  "last_synced_commit": "<git rev-parse HEAD>",
  "receipts": [
  ]
}
```
State is committed. Advancing `last_synced_commit` must never modify `AGENTS.md`
or `CLAUDE.md` - that separation is what prevents self-referential drift loops.

## Phase 1: Background crawl + initial grilling
Run two tracks. A single agent cannot truly act in parallel: perform Track A's file
reads first and hold the findings, then immediately open Track B and keep grilling.

**Track A - automated discovery (no user input):** read dependency manifests
(`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.), the directory
structure, CI configs, and any README/docs. Extract tech stack, build/test/run
commands, and standard engineering basics. Hold these findings for Phase 3.

**Track B - grilling interrogation:** open with:
> "I'm scanning your codebase structure in the background for the tech stack. While I
> do that: what is the core business problem this project solves?"
Then walk the conceptual tree **one question at a time**, challenging vague answers and
incentivizing a targeted brain-dump per micro-topic. Do not batch questions.

## Phase 2: Architectural & AI context
Steer the grilling toward architecture and AI-specific guardrails. Extract constraints
and known AI failure modes, e.g.:
> "You mentioned a custom Auth provider. What are the architectural gotchas or AI
> failure modes around it that a future sub-agent must not trip over?"
Also cover the two sections agents skip most: what must be verified before claiming
work done (`Verification Before Completion`) and which situations demand stopping to
ask the user (`Escalation`). Continue until you have at least one architectural
constraint, one AI-specific failure mode or guardrail, one verification command, and
one escalation case.

## Phase 3: Reconciliation & gap analysis
**HARD GATE - do not start until BOTH Track A (crawl) and Track B (grilling) are
complete.** Cross-examine Track A findings against Track B answers. Run a short, final
grilling pass focused only on discrepancies, e.g.:
> "The crawl found a Postgres connection string, but you didn't mention a database. How
> does Postgres fit the core domain, and are there AI constraints here?"

## Phase 4: Synthesis & generation
When the reconciliation pass is complete and no open discrepancies remain, combine
verified Track A findings with reconciled Track B domain knowledge. Draft `AGENTS.md`
against the schema above. Nothing Claude-specific goes in it; Claude-only workflow
notes belong in the `CLAUDE.md` wrapper block.

## Phase 5: Token compression
Compress the draft by following the `compress-onboarding` skill: level from
`config.json` (`compression_level`, default `full`), Agent Guardrails and Escalation
capped at `lite`, byte-preservation verified with
`.aiboarding/tools/check-preservation`, receipt appended to `state.json`. Present the
compressed document to the user for approval before writing it to the repo root.

## Phase 6: Install & bootstrap
After the document is approved and written, install the lifecycle with your own file
tools (no shell installer), for cross-platform safety. Every step is idempotent  - 
running create twice must not duplicate hooks, settings entries, or fenced blocks.

1. **Locate the templates** at `<plugin-root>/templates/`, where `<plugin-root>` is
   two levels up from this skill. Use `${CLAUDE_PLUGIN_ROOT}/templates` if set;
   otherwise resolve relative to this skill's own directory.
2. **Write `CLAUDE.md`**: line one `@AGENTS.md`, then the Claude-notes block via
   `inject-fenced <repo>/CLAUDE.md claude-notes <notes-file>`. If `CLAUDE.md` exists,
   only add the import line (if absent) and the fenced block.
3. **Write state and config**: `<repo>/.aiboarding/state.json` per the contract above
   with `last_synced_commit` = current `git rev-parse HEAD`; copy
   `templates/state/config.json` to `<repo>/.aiboarding/config.json` (keep an existing
   config); copy `templates/state/dot-gitignore` to `<repo>/.aiboarding/.gitignore`.
4. **Copy hook scripts** *(Claude Code runtimes only)*: create
   `<repo>/.aiboarding/hooks/` and copy these six files from
   `<plugin-root>/templates/hooks/` verbatim: `run-hook.cmd`, `_lib`, `session-start`,
   `subagent-start`, `drift-check`, `instructions-loaded`.
5. **Copy tools**: create `<repo>/.aiboarding/tools/` and copy `inject-fenced`,
   `check-size-budget`, `check-preservation` from `<plugin-root>/templates/tools/`.
6. **Merge settings** *(Claude Code runtimes only)*: merge the `hooks` block of
   `<plugin-root>/templates/settings/hooks.json` into `<repo>/.claude/settings.json`,
   per top-level event. Before adding an entry, check for an existing aiboarding entry
   for that event (a `command` containing `.aiboarding/hooks/run-hook.cmd`) and replace
   it in place. **Remove** stale entries pointing at the retired `pre-task` and
   `post-commit` hooks, and delete those files from `<repo>/.aiboarding/hooks/` if
   present.

## Phase 7: Validation gate (blocking)
Do not report success until every check passes; fix and re-check instead of skipping:
1. `AGENTS.md` and `CLAUDE.md` exist; `CLAUDE.md` contains a line `@AGENTS.md`.
2. No content duplication: the Claude-notes block must not restate `AGENTS.md` sections.
3. `.aiboarding/tools/check-size-budget AGENTS.md` passes (no FAIL; resolve WARNs or
   get the user's explicit OK).
4. Every command quoted in `Build, Test, Run` and `Verification Before Completion`
   resolves against the repo (package scripts, Makefile targets, CI workflows, or a
   binary on PATH).
5. `state.json:last_synced_commit` equals `git rev-parse HEAD`.
6. On Claude Code: the settings merge contains exactly one aiboarding entry per event
   and no `pre-task`/`post-commit` references.

Then report which files were created or updated and which hook entries were installed.
On Windows without Git Bash, tell the user once: hooks will not fire (`run-hook.cmd`
degrades silently), but native `CLAUDE.md`/`AGENTS.md` loading still works.
