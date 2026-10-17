---
name: checkpoint
description: "Save bounded progress as kernel.checkpoint/v1 for exact resume after reset. Triggers: checkpoint, save progress, context reset, compact soon, long task."
user-invocable: true
allowed-tools: Read, Bash, Grep, Glob, Write
kernel:
  kind: state_transition
  version: 1
  side_effects: writes_meta
  confirmation: none
  produces:
    - kernel.checkpoint/v1
---

<skill id="checkpoint">

<purpose>
The small resumable manifest. A handoff transfers a whole session; a checkpoint records
bounded progress INSIDE a long-running task so work can continue after a context reset
with a fresh, minimal context instead of an inherited transcript.

When to fire (EXP-L21: attention efficiency decays to ~11% late-session; a reset from a
checkpoint restores the flat ~50-70k load-bearing line):
- a long task crosses a natural boundary (a commit lands, a phase completes)
- context is about to compact, or the session is degrading (anchor-drift, I0.13)
- the manifest's execution.checkpoints list says so

Checkpoint vs handoff: same task + same session continuation → checkpoint.
Ending the session / transferring to a future session with decisions and policy → handoff.
</purpose>

<flow>
1. Gather provenance:
   ```bash
   git branch --show-current && git rev-parse HEAD && git status --short
   ```

2. Write `_meta/checkpoints/{task}-{timestamp}.json` per
   schemas/kernel.checkpoint.v1.schema.json:
   - task: goal + handoff_ref/contract_ref if they exist
   - steps_completed: each with EVIDENCE (commit sha, test output, command result),
     never intent. Receipts describe intent; files describe reality.
   - current_outputs: files produced so far
   - provenance.dirty_tree_sha256: when dirty, sha256 of `git diff --binary HEAD`
   - pending_steps: what remains, in order
   - resume: position (exact place in the work), entrypoint (skill to re-enter),
     next_operation (the LITERAL first action — "retarget tests/run-tests.sh lines
     ~1250 registration tests", not "continue the migration")
   - context (optional): required selectors + budget if the resume should be bounded

   Quote every sha/commit string (all-digit shas parse as integers and fail validation).

3. Validate — MANDATORY:
   ```bash
   "${CLAUDE_PLUGIN_ROOT:-.}/orchestration/manifest/kernel-manifest" validate _meta/checkpoints/{file}.json
   ```

4. Record:
   ```bash
   agentdb write-end '{"skill":"checkpoint","saved_to":"_meta/checkpoints/{file}.json","position":"..."}'
   ```

Resume path: `/kernel:ingest` discovers the newest manifest automatically
(`kernel-manifest latest` — checkpoints and handoffs share discovery), or accepts an
explicit path.
</flow>

<hard_stops>
- steps_completed without evidence → not a checkpoint, a hope. Add evidence or move the
  step to pending_steps.
- unvalidated json → does not exist. Validate before reporting done.
</hard_stops>

</skill>
