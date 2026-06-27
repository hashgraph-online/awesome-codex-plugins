---
name: agentpack-review
description: Run the full AgentPack PR review flow for the current branch or PR with an optional reviewer lens.
---

# AgentPack Review

Use when the user invokes `@agentpack-review` or `@agentpack-review <reviewer context>`.

Do not claim correctness unless relevant checks actually ran.

## Steps

1. Refresh AgentPack context for this exact review task before reading PR diff or code. Prefer MCP:

```text
agentpack_pack_context(task="review current PR $ARGUMENTS")
```

If MCP is unavailable, run:

```bash
agentpack guard --agent auto --repair-stale --refresh-context
```

If you bypass this refresh, state the bypass reason before continuing.
2. Prepare the full review bundle:

```bash
agentpack review "$ARGUMENTS"
```

3. Read `.agentpack/review.prompt.md` and follow it end to end.
4. By default, `agentpack review` starts a fresh run under `.agentpack/reviews/<branch>/<run_id>/` and refreshes the stable alias files in `.agentpack/`.
5. Do not perform the review inline from this skill. If you cannot write the required files, stop and report blocked.
6. Stage 1 writes the run-scoped understanding TOON at the output path declared by `agentpack review`.
7. Stage 2 must read that understanding TOON from disk and then write the run-scoped findings TOON at the output path declared by `agentpack review`.
8. Do not produce a final review summary unless the findings TOON exists at the declared path and validates.
9. Resume an interrupted run only with `agentpack review --resume <run_id>`.
10. Use the latest PR head, `gh pr view`, `git diff`, and direct code reads as source of truth.
11. Treat `$ARGUMENTS` only as a prioritization lens. It must not replace code evidence.
12. Report findings first with file evidence, then state validation exactly: passed, failed, or not run.
