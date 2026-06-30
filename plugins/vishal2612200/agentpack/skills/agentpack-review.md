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
2. Prepare the full review bundle. If `$ARGUMENTS` names a PR number or PR URL, `agentpack review` must bind metadata, diff, and context to that PR. If the user did not name a PR, `agentpack review` must identify the current PR through `gh`; do not accept silent `HEAD~1` fallback.

```bash
agentpack review "$ARGUMENTS"
```

Use this explicit form when the PR target is known:

```bash
agentpack review --pr <number-or-url> "$ARGUMENTS"
```

3. Read `.agentpack/review.prompt.md` and follow it end to end.
4. By default, `agentpack review` starts a fresh run under `.agentpack/reviews/<branch-or-pr>/<run_id>/` and refreshes the stable alias files in `.agentpack/`.
5. Do not perform the review inline from this skill. If you cannot write the required files, stop and report blocked.
6. Stage 1 writes the run-scoped understanding TOON at the output path declared by `agentpack review`.
7. Run `agentpack review --check`; do not start Stage 2 unless Stage 1 validates.
8. Stage 2 must read that understanding TOON from disk and then write the run-scoped findings TOON at the output path declared by `agentpack review`.
9. Run `agentpack review --check`; do not produce a final review summary unless the findings TOON exists and validates.
10. Resume an interrupted run only with `agentpack review --resume <run_id>`.
11. Use the latest PR head, `gh pr view`, `git diff`, and direct code reads as source of truth.
12. Treat any non-PR portion of `$ARGUMENTS` only as a prioritization lens. It must not replace code evidence.
13. Report findings first with file evidence, then state validation exactly: passed, failed, or not run.
