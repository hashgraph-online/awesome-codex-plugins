---
name: migrate-aiboarding
description: Use when a repo has a legacy AIBOARDING.md (v1 layout) and should move to the standard AGENTS.md + CLAUDE.md layout with the .aiboarding/state.json sidecar. One-shot, preview-first migration that preserves the existing onboarding content and rewires the hooks.
---

# Migrating AIBOARDING.md → AGENTS.md + CLAUDE.md

One-shot migration from the v1 custom-injection layout to the standard-files
layout. The onboarding knowledge in `AIBOARDING.md` is an investment - carry it
over; never regenerate from scratch and never delete anything without approval.

**Announce at start:** "Using migrate-aiboarding to move this repo to the AGENTS.md layout."

**Precondition:** `AIBOARDING.md` exists at the repo root. If it does not, stop and
suggest `create-agent-onboarding`. If `AGENTS.md` *also* already exists, stop and ask
the user which file is authoritative before writing anything.

## Step 1: Carry over state
Read the `AIBOARDING.md` frontmatter (`aiboarding_version`, `generated`,
`last_synced_commit`). These seed `.aiboarding/state.json`:
- `aiboarding_version: 2`
- `generated`: today's date
- `last_synced_commit`: carried over verbatim (empty stays empty - the repair
  semantics of an empty pointer are preserved).

## Step 2: Map the body
Map the three v1 H1 sections onto the v2 schema (see create-agent-onboarding's
Shared contracts for the exact section list and order):

| v1 source | v2 target sections |
| :--- | :--- |
| `# 1. Engineering Basics` | `Stack and Runtime`, `Build, Test, Run`, `Architecture Map` |
| `# 2. Domain & Business Logic` | `Project Purpose`, `Domain Model` |
| `# 3. AI-Specific Context` | `Agent Guardrails`, `Known Failure Modes` |

Preserve the compressed density of the source text; split it, don't rewrite it.
Backtick-quote any command, identifier, path, or error string that isn't already.

Two v2 sections have no v1 source: `Verification Before Completion` and
`Escalation - Ask the User When`. Run a short, scoped grilling pass (the
one-question-at-a-time style from create-agent-onboarding) ONLY for these gaps.

## Step 3: Generate the wrapper and lifecycle files
Follow create-agent-onboarding Phase 6: `CLAUDE.md` (`@AGENTS.md` + fenced
Claude-notes block), `state.json`, `config.json`, `.aiboarding/.gitignore`, the six
hook files, and the three tools. Runtime awareness applies (hook/settings steps are
Claude Code-only).

## Step 4: Rewire hooks and settings (Claude Code runtimes)
In `<repo>/.claude/settings.json`:
- Replace the `SessionStart` full-injection entry with the current template's entry
  (the modern `session-start` is a fallback warner, not an injector).
- **Delete** the `PreToolUse[Task]` entry (`pre-task` is retired - `SubagentStart`
  is native now).
- Replace the `PostToolUse` entry so it dispatches `drift-check` (not `post-commit`).
- Add the `SubagentStart` and `InstructionsLoaded` entries from the template.
Delete `<repo>/.aiboarding/hooks/pre-task` and `<repo>/.aiboarding/hooks/post-commit`.
All edits idempotent: match aiboarding entries by `command` containing
`.aiboarding/hooks/run-hook.cmd`; never duplicate; leave non-aiboarding hooks alone.

## Step 5: Retire the legacy document
Ask the user to choose (default: archive):
- **Archive (default):** move `AIBOARDING.md` to `docs/archive/AIBOARDING.md`
  unchanged. Git history preserves it either way; nothing at the root keeps stale
  onboarding discoverable by tools.
- **Keep as legacy:** leave `AIBOARDING.md` in place and prepend a deprecation
  banner via `inject-fenced AIBOARDING.md deprecation <banner-file>` pointing to
  `AGENTS.md`. The drift hook keeps honoring the legacy layout only when
  `state.json` is absent, so with both present the sidecar wins.
Never delete `AIBOARDING.md` outright unless the user explicitly asks.

## Step 6: Single approval gate, then write
Before writing ANYTHING, present the full migration plan in one preview: every file
to be created, modified (with the settings diff), moved, or deleted. One approval
covers the whole batch; a rejection means nothing was touched.

## Step 7: Exit check
Run create-agent-onboarding's Phase 7 validation gate, then `audit-agent-onboarding`
if available. Report the file-by-file outcome, and remind the user to commit the new
layout (the drift hook stays silent for onboarding-only commit ranges).
