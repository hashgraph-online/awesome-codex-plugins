---
name: agent-introspection
description: "Loop-breaking self-diagnosis. Use when 3+ consecutive failures occur, circular retries persist, or context overwhelms the session."
---

# Agent Introspection — Systematic Self-Diagnosis

## Iron Law
NO UNSUPPORTED SELF-HEALING CLAIMS. Only assert recovery actions you can actually perform with available tools.

## When to Trigger
- 3+ consecutive failures on the same task
- Repeating the same approach with different parameters (loop detection)
- Context window exceeds 70% without resolution
- Error messages repeat with no progress
- User explicitly says "you're stuck" or "try a different approach"

## Process

### 1. Failure Capture
Stop immediately and record:
- **Error type**: syntax_error / type_error / test_fail / lint_fail / build_fail / runtime_error / permission_denied / not_found
- **Last 3 tool calls**: what was attempted and what failed
- **Context pressure**: approximate context usage percentage
- **What changed**: what was the last successful state

### 2. Root Cause Diagnosis
Match against known patterns:

| Pattern | Symptoms | Root Cause |
|---------|----------|------------|
| **Loop trap** | Same error 3+ times | Wrong approach, not wrong parameters |
| **Context overflow** | Increasingly confused responses | Too much information, need compaction |
| **Environment drift** | "Works locally" failures | Missing env var, different tool version |
| **Cascade failure** | Fix A breaks B | Underlying assumption is wrong |
| **Tool mismatch** | Wrong tool for the job | Need a different approach entirely |

### 3. Controlled Recovery
Execute ONLY the smallest safe action:
- **Loop trap** → Abandon current approach entirely. Try a fundamentally different strategy.
- **Context overflow** → Run `/compact` or summarize current state, then continue.
- **Environment drift** → Verify environment with explicit checks (`which`, `--version`).
- **Cascade failure** → Revert to last known good state. Re-analyze assumptions.
- **Tool mismatch** → Switch tools. If `Edit` fails 3 times, try `Write`. If `Bash` fails, try `Read` first.

### 4. Introspection Report
Generate a structured report:
```markdown
## Introspection Report
- **Failure type**: [type]
- **Root cause**: [diagnosis]
- **Recovery action**: [what was done]
- **Confidence**: [high/medium/low]
- **Next step**: [what to do if this happens again]
```

Save to memory:
```bash
epic mem add \
  --title "Self-diagnosis: {error_type} in {file}" \
  --type error \
  --body "Pattern: ...\nRoot cause: ...\nRecovery: ...\n"
```

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "One more try might work" | 3 failures means the approach is wrong, not unlucky. | Stop and run the full 4-step introspection process. |
| "I just need to tweak the parameters" | Tweaking a failing approach is not debugging. Step back and reassess. | Abandon the current approach and try a fundamentally different strategy. |
| "I can fix this myself" | Asking for help is not weakness. Escalation saves everyone time. | Escalate to the user with a clear summary of what was tried and what failed. |
| "The error is clear, I know the fix" | You said that 3 times already. Prove it with a different approach. | Run the introspection report and verify the fix with a test before claiming success. |

## Evidence Required

- [ ] Failure type classified correctly
- [ ] Root cause matched to known pattern
- [ ] Recovery action is the smallest safe action
- [ ] Introspection report generated
- [ ] Failure pattern recorded in memory

## Red Flags
- Trying the same command more than 3 times with minor variations
- Claiming "fixed!" without running the actual test
- Not recording the failure pattern in memory
- Continuing after 70% context usage without compacting
