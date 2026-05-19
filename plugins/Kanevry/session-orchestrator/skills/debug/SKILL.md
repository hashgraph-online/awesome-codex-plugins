---
name: debug
description: Use when encountering any bug, test failure, build break, or unexpected behavior — runs a 4-phase systematic debugging process before proposing any fix. Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. Produces a `.orchestrator/debug/` artifact the fixer agent must reference.
model: inherit
color: red
tools: Read, Grep, Glob, Bash, Write
---

# Debug Skill

> 4-phase root-cause investigation. Iron Law: no fix without root cause.

## When to use

- Any test failure (unit, integration, E2E)
- Build break or compile error
- Runtime exception in production code
- Performance regression
- Integration issue between modules
- "It worked yesterday" bugs

## When NOT to use

- Feature implementation (use `/plan` or wave-executor)
- Pure refactoring with no broken behavior
- Style/lint fixes with no behavioral impact

## Phase 0: Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. If the gate is CLOSED, invoke `skills/bootstrap/SKILL.md` and wait for completion before proceeding. If the gate is OPEN, continue to Phase 1.

<HARD-GATE>
Do NOT proceed past Phase 0 if GATE_CLOSED. There is no bypass. Refer to `skills/_shared/bootstrap-gate.md` for the full HARD-GATE constraints.
</HARD-GATE>

## The Iron Law

> **NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

No matter how obvious the fix looks, complete Phase 1 (Root Cause Investigation) and produce the artifact BEFORE writing any fix code. This is non-negotiable.

The "2-hour obviously a typo" case has been the root cause of every multi-day debugging session in every project's history. Treat the obvious fix as a hypothesis to verify, not a conclusion to act on.

## Phase 1: Root Cause Investigation

### 1.1 Read the error carefully

Quote the exact error message, full stack trace, and exit code in the artifact. Do not paraphrase. Paraphrasing introduces your assumptions before investigation begins.

### 1.2 Reproduce reliably

Document the exact command and environment that triggers it. If reproduction is flaky, that itself is a data point — write down the failure rate.

```bash
# minimum reproduction attempt
<exact command>
# env: Node version, OS, env vars relevant to the failure
```

### 1.3 Check recent changes

```bash
git log --oneline -20
git diff HEAD~5..HEAD -- <affected paths>
```

Identify the smallest set of commits that could have introduced this. Do not assume the most recent commit is the culprit without checking.

### 1.4 Instrument every component boundary

Add temporary logging at each input/output point along the failing path's modules. Capture actual values, not assumptions about what they should be. Run with instrumentation in place and record results.

### 1.5 Trace data flow backward

Start from the failure point and walk upstream. At each step, verify what you think is true with an actual Read or Bash call. "I assume X is Y" is not data.

### Phase 1 artifact

Write to `.orchestrator/debug/<session-id>-<sequence>.md` (sequence = 1, 2, 3 within session).

**Artifact MUST be written before proceeding to Phase 2.** See "Artifact contract" section below.

## Phase 2: Pattern Identification

After the Phase 1 artifact is written:

- Is this a recurrence of a previously fixed bug? Search `git log --all --grep="<symptom keyword>"`.
- Is there a class of bug this exemplifies (race condition, off-by-one, null check, encoding, async ordering)?
- Is there a missing test that would have caught this? Identify what the test would look like.
- Search the codebase for similar patterns:
  ```bash
  grep -rn "<suspect pattern>" --include="*.ts" --include="*.mjs"
  git grep "<symbol>"
  ```

Record findings in the artifact's Phase 2 section.

## Phase 3: Impact Analysis

- What else does the root-caused code touch?
  ```bash
  grep -rn "<function or symbol name>"
  ```
- What other code paths could share the same root cause?
- Will the fix break anything else? Identify callers, dependents, transitive effects.
- List the affected files explicitly in the artifact.

## Phase 4: Solution

Only after Phases 1-3 are complete and the artifact is written:

1. Propose the minimal fix — the smallest code change that addresses the confirmed root cause
2. Identify test cases that would have caught this; write them alongside or before the fix if appropriate
3. Document the fix decision in the artifact under a "Resolution" section
4. Verify the fix: run the test command from Session Config (`test-command`) and confirm the failure no longer reproduces

Do not gold-plate the fix. Scope creep during a bugfix introduces new bugs.

## Artifact contract

`.orchestrator/debug/<session-id>-<sequence>.md`:

```markdown
# Debug session: <topic>
Created: <ISO timestamp>
Session: <session-id>

## Phase 1 — Root Cause

### Error
[exact error message + stack trace + exit code — verbatim]

### Reproduction
[exact command]
[environment: Node version, platform, relevant env vars]
[frequency: always | intermittent (~N/10)]

### Suspect commits
- <sha> <subject> — reason

### Instrumentation data
[per-boundary observations with actual values]

### Hypothesized root cause
[ONE sentence] · Confidence: [low|medium|high]

## Phase 2 — Pattern

[recurrence? class? missing test? similar code paths?]

## Phase 3 — Impact

[affected files, callers, dependents]

## Phase 4 — Solution

[proposed fix + test cases identified]

## Resolution

[commit SHA, files changed, tests added — filled in after fix lands]
```

**Rules for the artifact:**
- "Hypothesized root cause" is always ONE sentence. Multiple hypotheses signal you have none — pick the most evidence-backed one and lower confidence if uncertain.
- Do not write fix code in Phase 1-3 sections. Those sections are investigation only.
- The artifact is the deliverable — not an optional note.

## Integration with wave-executor

When `wave-executor` classifies a task as `bugfix`, it routes through this skill. `code-implementer` agents handling bugfix-classified tasks must reference an existing Phase-1 artifact path in their task description before editing any production code. Wire-up happens in wave-executor's routing layer (Wave 3 P1 cross-reference).

## Anti-Patterns

- **Skipping Phase 1 because "it's obviously a typo"** — see Iron Law. The obvious hypothesis goes in Phase 1 as a hypothesis to verify, not a fix to apply.
- **Multiple hypotheses in "Hypothesized root cause"** — pick ONE. Lower confidence rating if uncertain. "Either X or Y" means you don't know yet.
- **Writing fix code in Phase 1** — fixes belong in Phase 4. Investigation and implementation are separate acts.
- **Skipping the artifact write** — the artifact IS the work product. No artifact = no investigation.
- **Fixing the symptom** — the error location is the symptom; the root cause may be several frames upstream. Trace backward.
- **Assuming the most recent commit is the cause** — check `git log -20` and the diff before assuming recency.

## See Also

- `skills/discovery/SKILL.md` — discovery surfaces problems; debug investigates them
- `.claude/rules/verification-before-completion.md` — once fixed, verify fresh (issue #38)
- `agents/code-implementer.md` — references this skill for bugfix-classified tasks
