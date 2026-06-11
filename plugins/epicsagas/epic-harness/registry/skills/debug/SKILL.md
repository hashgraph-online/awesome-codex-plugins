---
name: debug
description: "Trigger: test failure, runtime error, or unexpected behavior. Systematic root-cause isolation."
---

# Debug — Systematic Debugging

## Iron Law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. Symptom fixes are whack-a-mole debugging.

## Process

### 0. Recall
- Query the knowledge graph: `epic mem search "ERROR_MESSAGE_OR_FILE"` for the error message or file name
- Check if a `resolution` or `pattern` node exists for this error category
- If a past resolution exists, apply it directly instead of re-debugging from scratch

**Why**: Past resolutions save 10-30 minutes of re-investigation. The knowledge graph exists so you don't repeat work.

### 1. Observe
- Read the full error message and stack trace
- Identify: What was expected? What actually happened?
- Note the exact file, line, and function

**Why**: Precise observation prevents misdiagnosis. Most debug loops start from skimming the error instead of reading it fully.

### 2. Hypothesize
Form 2-3 possible causes. Rank by likelihood.

**Why**: Ranked hypotheses prevent random code changes. Even a wrong hypothesis narrows the search space.

### 3. Isolate
- **Narrow the scope**: Binary search through recent changes
- **Reproduce minimally**: Smallest input that triggers the error
- **Check assumptions**: Print/log intermediate values
- **Bisect**: `git log --oneline -10` — when did it last work?

**Why**: Isolation proves the cause before you touch any code. Without it, you're guessing.

### 4. Fix
- Fix the root cause, not the symptom
- If the fix is a workaround, add a TODO with explanation

**Why**: Root cause fixes are permanent. Symptom patches rot and hide the real bug.

### 5. Verify
- Run the failing test — must pass now
- Run the full test suite — no regressions
- If this was a bug, the regression test stays

**Why**: A passing fix without verification is wishful thinking. The full suite catches side effects.

### 6. Record
- If the fix involved 3+ debug steps, record a `resolution` node via `epic mem add --title "..." --type resolution --body "..."`
- Include: error category, root cause, solution approach
- This enables future sessions to skip re-debugging the same class of issues

**Why**: Recording turns one-time debugging into institutional knowledge. Future sessions benefit from your effort.

## When to Trigger
- Any test failure during `/go` execution
- Runtime error in tool output
- "Unexpected" in any output

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "Let me just try again" | Retrying without changing anything is not debugging. | Form a new hypothesis before each attempt. |
| "It works on my machine" | Environment differences are bugs too. | Reproduce in the actual target environment first. |
| "I'll just catch the exception" | That hides the bug, doesn't fix it. | Fix the root cause. Only catch what you can handle meaningfully. |
| "It's probably a flaky test" | Flaky tests hide real bugs. Prove it's flaky before dismissing. | Run it 3x in isolation. If it fails consistently, it's real. |
| "I'll add more logging" | Logging without a hypothesis is fishing. | Hypothesize first, then add targeted logging to confirm/deny. |
| "It's probably just a typo" | Assumptions are the enemy of debugging. Reproduce first, then diagnose. | Read the full error, reproduce it, and verify before assuming simplicity. |
| "Let me just try changing this one thing" | Whack-a-mole debugging creates more bugs. Follow the hypothesis → isolate → fix cycle. | Form a hypothesis, isolate the cause, then fix with evidence. |
| "The error message tells me everything" | Error messages describe symptoms, not root causes. Investigate the chain. | Trace the error to its origin. The message is the starting point, not the answer. |

## Evidence Required

Before claiming the bug is fixed, show ALL of these:

- [ ] Root cause identified: one sentence explaining WHY it broke
- [ ] Fix applied: diff showing the change
- [ ] Previously failing test now passes (show output)
- [ ] Full test suite passes (no regressions)
- [ ] If bug came from a pattern, regression test added to prevent recurrence

**"It works now" without root cause = symptom patch, not a fix.**

## Red Flags
- Changing random things hoping something works
- More than 3 retry attempts without forming a new hypothesis
- Suppressing errors instead of fixing them
