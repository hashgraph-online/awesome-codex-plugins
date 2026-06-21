---
name: agentpack-review
description: Review Codex edits with git diff and AgentPack benchmark capture guidance.
---

# AgentPack Review

Use when the user invokes `@agentpack-review` after edits.

Do not claim correctness unless relevant checks actually ran.

## Steps

1. Inspect current diff:

```bash
git diff --stat
git diff
```

2. Look for missed tests, config files, callers, broad unrelated diffs, or generated files.
3. Run or recommend the smallest relevant checks.
4. When the diff represents a completed task, suggest benchmark capture:

```bash
agentpack benchmark capture --since main --task "<task>"
agentpack benchmark --misses
```

5. Report validation exactly: passed, failed, or not run.

AgentPack benchmark capture records file-selection evidence. It does not prove the code is correct.
