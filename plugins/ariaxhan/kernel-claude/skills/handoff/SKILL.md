---
name: handoff
description: "Save provenance, decisions, phases, context policy, and next steps as kernel.handoff/v1. Triggers: handoff, save, pause, context, continue later."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob, Write
kernel:
  kind: state_transition
  version: 2
  side_effects: writes_meta
  confirmation: none
  produces:
    - kernel.handoff/v1
---

<skill id="handoff">

<purpose>
Compile the current task into an authoritative, resumable JSON manifest.
The JSON file is CANONICAL. A markdown rendering may be generated for humans but is
never a second source of truth.

Why manifest-first + bounded (EXP-L21): what a decision needs is flat (~50-70k tokens)
regardless of session length; the accumulating transcript is almost pure decoration by
late session. A handoff that says "read the conversation" recreates the waste. A handoff
that pins exact selectors + phases lets the next session reconstruct ONLY the load-bearing
state.

Reference: skills/context-mgmt/SKILL.md
</purpose>

<on_start>
```bash
agentdb read-start
```
</on_start>

<phase id="1_extract" name="EXTRACT STATE">
Capture (these become manifest sections, not prose):
- objective: goal, success_conditions (observable), non_goals
- contract: governing _meta/contracts/ file if one exists, invariants, assumptions,
  decisions_accepted (+rationale), alternatives_rejected (+reason) — rejected paths are
  as valuable as accepted ones; they stop re-exploration
- workflow.phases: name each phase of the work; status inherited (done, with evidence)
  | required (still to do). Add invalidation_rules: what live-state change would flip an
  inherited phase back to required. Rules use typed `when.event` plus optional
  `when.path_glob`; never prose trigger strings.
- open_threads, warnings (failed approaches — never re-explore silently)
- tier (1/2/3) in identity
</phase>

<phase id="2_gather" name="GATHER EVIDENCE">
```bash
git branch --show-current && git rev-parse HEAD && git status --short
git log --oneline -10
agentdb query "SELECT * FROM context WHERE type IN ('contract','checkpoint') ORDER BY ts DESC LIMIT 5"
```
Pin artifacts: for each file the next session must trust unchanged,
`shasum -a 256 <path>` → provenance.artifacts[{path, sha256, purpose}].
</phase>

<ask_user>
  Use AskUserQuestion when: state extraction complete, before writing the manifest
  Ask: "Anything to add to the handoff? Blockers, decisions, or context I might have missed?"
  Options: looks complete, add context, skip handoff
</ask_user>

<phase id="3_hygiene" name="GIT HYGIENE">
uncommitted: commit with "wip: checkpoint before handoff" or stash (document it)
push: push current branch to remote — a local-only handoff is stranded work
</phase>

<phase id="4_compile" name="COMPILE THE MANIFEST">
Write `_meta/handoffs/{name}-{date}.json` conforming to schemas/kernel.handoff.v1.schema.json.

Context section — the attention budget is the design center:
- policy.mode: advisory (default) | bounded (extra loads must be justified + ledgered)
  | sealed (forbidden globs hook-blocked; for controlled experiments)
- required: SELECTORS, not whole files, wherever a section suffices:
  `{path, heading: "## X"}` · `{path, lines: "A-B"}` · `{path, grep: "pat", context: N}`
  · `{git_diff: "revA..revB"}` — each with a reason
- forbidden: globs the resume must NOT touch (sealed mode enforces via guard-context hook)
- budget: target_tokens (aim: boot + manifest + 2-12k selected history, per EXP-L21),
  max_tokens (hard stop)

Execution section: entry_phase, entrypoint (the literal first operation), stop_conditions,
checkpoints (when to emit kernel.checkpoint/v1 during the resumed work).

Resume section: one-line continuation prompt:
  `/kernel:ingest resume from _meta/handoffs/{file}.json`

JSON strings are always quoted, so sha/commit fields cannot type-drift (the old YAML
fails validation).
</phase>

<phase id="5_validate" name="VALIDATE — MANDATORY">
```bash
"${CLAUDE_PLUGIN_ROOT:-.}/orchestration/manifest/kernel-manifest" validate _meta/handoffs/{file}.json
```
A handoff that does not validate DOES NOT EXIST. Fix and re-validate before reporting done.
Optional human rendering: a .md next to it, first line
`# RENDERED FROM {file}.json — NOT AUTHORITATIVE`.
</phase>

<delivery>
1. `kernel-manifest validate` passes (above)
2. Commit: "docs: handoff manifest for {name}"
3. Push to remote
</delivery>

<on_complete>
```bash
agentdb write-end '{"skill":"handoff","saved_to":"_meta/handoffs/{file}.json","branch":"X","tier":N}'
# If non-local profile: post handoff summary to GitHub Discussions (Agent Logs category)
# Suggest /kernel:retrospective if learnings accumulated across sessions
```
</on_complete>

</skill>
