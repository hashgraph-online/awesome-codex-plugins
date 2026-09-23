---
name: bug-investigator
description: Use when encountering any bug, test failure, or unexpected behavior during spec-superflow execution, before proposing fixes. Invoked automatically when build-executor hits a blockage.
---

# Bug Investigator

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

**Core principle:** Find root cause before attempting fixes. Symptom fixes are failure.

## New direct/planned changes

Investigate in executing without a phase transition or a separate debug ledger: reproduce, trace the root cause, make one focused repair and verify. Keep useful failure evidence in the existing progress entry. Three failures for the same unresolved issue warrant a decision; unrelated findings do not accumulate a shared budget. No task book or subagent is required. The detailed legacy protocol below is for an existing debugging state or an investigation that needs it.

## The Iron Law

No fixes without root cause investigation first. If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue: test failures, bugs, unexpected behavior, performance problems, build failures, integration issues. Especially when under time pressure, "one quick fix" seems obvious, you've already tried multiple fixes, or you don't fully understand the issue.

Don't skip because issue "seems simple" or you're "in a hurry" — systematic debugging is faster than thrashing.

## The Four Phases

Complete each phase before proceeding.

### Phase 1: Root Cause Investigation

1. **Read error messages carefully**: stack traces, line numbers, file paths, error codes — they often contain the exact solution
2. **Reproduce consistently**: exact steps, every time? If not reproducible → gather more data, don't guess
3. **Check recent changes**: git diff, recent commits, new dependencies, config changes, environment differences
4. **Multi-component systems**: add diagnostic instrumentation at each component boundary. Log what enters and exits each layer. Run once to gather evidence, then analyze which component fails
5. **Trace data flow**: backward tracing — where does the bad value originate? Keep tracing up until you find the source. Fix at source, not symptom

### Phase 2: Pattern Analysis

1. Find working examples of similar code in the same codebase
2. Compare against references — read reference implementation completely
3. Identify every difference between working and broken, however small
4. Understand dependencies: other components, settings, config, environment, assumptions

### Phase 3: Hypothesis and Testing

Scientific method: form a single hypothesis ("I think X is the root cause because Y"), test with the smallest possible change (one variable at a time), verify before continuing. If it didn't work, form a NEW hypothesis — don't add more fixes. When you don't know, say so and ask for help.

### Phase 4: Implementation

1. **Create failing test case** — simplest reproduction, automated if possible. Follow TDD rules from build-executor
2. **Implement single fix** — address root cause, one change at a time, no "while I'm here" improvements
3. **Verify fix** — test passes? no regressions? issue resolved?
4. **If fix doesn't work**: count attempts. < 3 → return to Phase 1. **≥ 3 → STOP and question architecture (DP-5)**

### DP-5: Debug Escalation (3+ Failures)

3+ failed fixes = architectural problem. Each fix revealing new problems elsewhere = wrong architecture.

After every failed fix, preserve its failure output in a physical file inside the change directory, then record the distinct attempt:

Full and legacy Hotfix require a current, valid execution plan before this command; establish one with `SSF execution recommend` and `SSF execution plan` if needed. Quick, Tweak, lightweight, and direct Hotfix keep their planless contract: their valid workflow receipt authorizes debugging, and the ledger binds attempts to that receipt plus the current workflow, artifact, and contract hashes. The debug command rejects a missing or replaced receipt or a stale required plan.

```bash
SSF debug attempt record <change-dir> \
  --id <unique-attempt-id> \
  --summary "<what was tried and why it failed>" \
  --evidence <change-local-failure-log>
```

Use `SSF debug attempt show <change-dir> --json` to present the complete attempt ledger. Wave Review repair failures are separate evidence and never count as debugging attempts.

After at least three distinct evidence-backed attempts, stop and discuss the architectural decision with the user. Only after the user explicitly chooses may DP-5 be recorded:

```bash
SSF debug escalate <change-dir> \
  --decision <continue|abandon> \
  --reason "<user-confirmed decision>" \
  --confirm
```

Never write `dp_5_*` through raw `SSF state set`; those fields are guarded by the debug ledger. If the user chooses `abandon`, transition to `abandoned` only after the guarded DP-5 receipt is recorded.

## Red Flags — Return to Phase 1

"Quick fix, investigate later" / "Just try changing X" / "Skip the test, I'll verify manually" / "It's probably X, let me fix that" / "I don't fully understand but this might work" / "One more fix attempt" (after 2+) / Proposing solutions before tracing data flow.

**All of these mean: STOP. Return to Phase 1.** If 3+ fixes failed, question the architecture.

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| 1. Root Cause | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| 2. Pattern | Find working examples, compare | Identify differences |
| 3. Hypothesis | Form theory, test minimally | Confirmed or new hypothesis |
| 4. Implementation | Create test, fix, verify | Bug resolved, tests pass |

## When No Root Cause Found

If truly environmental/timing-dependent/external: document what you investigated, implement appropriate handling (retry, timeout, error message), add monitoring. But 95% of "no root cause" cases are incomplete investigation.

## Exception Handling

- **Parse failures**: Report raw output, ask for clarification — don't guess
- **Missing files**: Escalate immediately — not a normal debugging scenario
- **User interruption**: Re-read investigation report on resume, continue from last completed phase
