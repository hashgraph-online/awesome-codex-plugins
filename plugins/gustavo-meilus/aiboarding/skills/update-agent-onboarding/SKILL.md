---
name: update-agent-onboarding
description: Use when commits have landed since the onboarding files were last synced (the drift-check hook nudges for this), or the user asks to refresh AGENTS.md. Triages whether the change touches onboarding scope and patches only the affected sections; on no-op it advances the state pointer only.
---

# Updating agent onboarding files

Keep `AGENTS.md` current as the project evolves, without re-grilling the whole repo.

**Announce at start:** "Using update-agent-onboarding to triage onboarding drift."

## Runtime awareness
Works under Claude Code, Codex, Copilot CLI, or any SKILL.md-compatible agent - the
triage and patch logic below has no runtime dependency. Claude repo hooks and optional
native Codex plugin hooks can nudge; when unavailable, disabled, untrusted, or using
copied standalone skills, run this skill manually after meaningful commits.

## Managed refresh
For an existing Claude installation, before classification compare the current
plugin's `templates/hooks/drift-check` and `templates/tools/classify-drift` with
their managed copies. If either is missing or differs, replace only those two
AIBoarding-owned files, then rerun classification. Do not rewrite config, state,
`AGENTS.md`, or `CLAUDE.md`. If current plugin assets cannot be located, route to
full revalidation. Repeating this refresh is byte-identical and rollback is safe:
older readers ignore the optional config and receipt fields.

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

1. **Classify before reading semantics.** Run the self-contained sibling
   `classify-drift --project <repo> --base <last_synced_commit> --head HEAD` (or
   `.aiboarding/tools/classify-drift` if installed). Missing tool, invalid pointer,
   malformed report, rebased pointer, or changed `HEAD` means full revalidation;
   never advance state from those outcomes. Its routes are unambiguous:
   `irrelevant` advances state only; `semantic-review` needs section evidence;
   `mandatory-revalidation` requires applicable section revalidation; and
   `invalid-pointer` requires all nine sections. High-risk evidence always wins over
   ignored paths and cannot be downgraded by a semantic no-op.
2. **Classify scope impact** for every potentially relevant path against the
   `AGENTS.md` sections:
   - `Stack and Runtime` / `Build, Test, Run` - stack, tooling, or commands changed?
   - `Architecture Map` - boundaries, directories, data flow moved?
   - `Project Purpose` / `Domain Model` - new concepts or changed behavior?
   - `Agent Guardrails` / `Known Failure Modes` - new gotchas or constraints?
   - `Verification Before Completion` / `Escalation` - done-criteria or stop-and-ask
     cases changed?
   Record each potential path's applicable sections and rationale. Only complete
   evidence covering every potential path can authorize `--semantic complete-no-op`.
   Semantic review may escalate scope, never hide deterministic high-risk evidence.
3. **Branch:** classifier `irrelevant`, or complete evidenced potential no-op → No-op.
   Mandatory route → Targeted-delta revalidation. Other routes → full revalidation.

## No-op: nothing relevant changed
If triage finds no scope-relevant change:
- Build a `drift-classification` evidence record from the classifier report: repository
  identity, exact base/head, final disposition, categorized path dispositions,
  reviewed sections, and outcome (`proven-irrelevant` or
  `revalidated-no-content-change`). Write it with `.aiboarding/tools/write-evidence`.
  Do not copy command output or prose into the record.
- Recheck `git rev-parse HEAD` equals the evidenced `head_commit`; only then set
  `last_synced_commit` and `last_drift_classification` together. An evidence write
  failure or changed `HEAD` leaves state unchanged. Preserve unknown top-level state
  fields.
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
   only (same level as the rest of the doc; it owns high-consequence preservation
   and any per-region opt-in), verifying with `.aiboarding/tools/check-preservation`.
4. **Approval gate.** Show the user a diff of the patched sections against the prior
   `AGENTS.md`. Content changes ALWAYS require approval before writing. Only the
   no-op pointer advance is automatic.
5. **Advance state.** After approved content work, persist the matching
   `drift-classification` and `onboarding-validation` evidence records first, with the
   exact base/head, affected sections, path dispositions, and validator identities.
   Recheck `HEAD` against the evidenced head immediately before writing the pointer
   and classification receipt together. Evidence failure or a changed head leaves
   state unchanged; preserve unknown fields, then append the legacy compression receipt.
6. **Validate.** Run create-agent-onboarding's Phase 7 gate (files, import line,
   local size sensor, Codex project-chain validation, command resolution, pointer ==
   HEAD) before reporting done.

When a state-owning create or update flow invokes `audit-onboarding-evidence`, import
only its machine-readable computed findings as validator provenance in the matching
record. The standalone `audit-agent-onboarding` workflow remains read-only and never
creates evidence history.
