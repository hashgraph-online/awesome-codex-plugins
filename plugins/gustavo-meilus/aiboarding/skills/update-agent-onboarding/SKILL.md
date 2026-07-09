---
name: update-agent-onboarding
description: Use when commits have landed since the onboarding files were last synced (the drift-check hook nudges for this), or the user asks to refresh AGENTS.md. Triages whether the change touches onboarding scope and patches only the affected sections; on no-op it advances the state pointer only.
---

# Updating agent onboarding files

Keep `AGENTS.md` current as the project evolves, without re-grilling the whole repo.

**Announce at start:** "Using update-agent-onboarding to triage onboarding drift."

## Runtime awareness
Works under Claude Code, Codex, Copilot CLI, or any SKILL.md-compatible agent - the
triage and patch logic below has no Claude Code dependency. Only the drift *nudge*
that usually leads here is a Claude Code hook; on other runtimes, run this skill
manually after meaningful commits.

## Triage
Read `last_synced_commit` from `.aiboarding/state.json` (NOT from any instruction
file - the pointer lives only in the sidecar).

**If `state.json` is missing or the pointer is missing/empty**, the repo was never
properly synced or the state was lost (fresh clone of a repo where state was
gitignored, hand-edited state, or the drift hook fired as a repair signal). Do NOT
take the No-op branch - go straight to the Targeted-delta patch for a full
re-validation of all nine sections, then reseed `state.json`.

**If the repo has `AIBOARDING.md` and no `AGENTS.md`**, it is on the legacy layout:
stop and run `migrate-aiboarding` instead.

1. **Gather the delta.** Run `git diff <last_synced_commit>..HEAD` and
   `git diff --name-only <last_synced_commit>..HEAD`. Drop paths matching
   `config.json:ignored_paths` plus the always-ignored set (`AGENTS.md`,
   `CLAUDE.md`, `.aiboarding/*`). Reflect on the current conversation - it is the
   "chat log" and is already in your context (after compaction, use the summary).
2. **Classify scope impact** against the `AGENTS.md` sections:
   - `Stack and Runtime` / `Build, Test, Run` - stack, tooling, or commands changed?
   - `Architecture Map` - boundaries, directories, data flow moved?
   - `Project Purpose` / `Domain Model` - new concepts or changed behavior?
   - `Agent Guardrails` / `Known Failure Modes` - new gotchas or constraints?
   - `Verification Before Completion` / `Escalation` - done-criteria or stop-and-ask
     cases changed?
3. **Branch:** no relevant change → No-op (below). Relevant change → Targeted-delta patch.

## No-op: nothing relevant changed
If triage finds no scope-relevant change:
- Set `last_synced_commit` in `.aiboarding/state.json` to the current
  `git rev-parse HEAD`.
- **Hard invariant: do not touch `AGENTS.md` or `CLAUDE.md`.** Not even whitespace.
  The pointer advance is a state-only write; this is what keeps the drift hook from
  ever re-nudging on its own bookkeeping.
- Do **not** ask the user - this advance is automatic.
- Briefly report: "No onboarding-relevant changes in <range>; advanced sync pointer."

## Targeted-delta patch: scope changed
Reuse create-agent-onboarding's Phases 1–3 (background crawl + grilling style,
architectural interrogation, reconciliation), scoped to the affected sections only.

1. **Scoped grill.** Ask focused, one-at-a-time questions about ONLY the changed
   scope, seeded by the diff. Skip sections the delta does not touch.
2. **Synthesize.** Re-draft only the affected sections, using the exact H2 heading
   text from the existing `AGENTS.md` to avoid duplicate headings. Leave untouched
   sections byte-for-byte intact. Keep commands/identifiers/paths backtick-quoted.
3. **Compress.** Follow the `compress-onboarding` skill on the re-drafted sections
   only (same level as the rest of the doc; Guardrails/Escalation capped at `lite`),
   verifying with `.aiboarding/tools/check-preservation`.
4. **Approval gate.** Show the user a diff of the patched sections against the prior
   `AGENTS.md`. Content changes ALWAYS require approval before writing. Only the
   no-op pointer advance is automatic.
5. **Advance state.** After the approved write, set `last_synced_commit` to the
   current `git rev-parse HEAD` in `state.json` and append the compression receipt.
6. **Validate.** Run create-agent-onboarding's Phase 7 gate (files, import line,
   size budget, command resolution, pointer == HEAD) before reporting done.
