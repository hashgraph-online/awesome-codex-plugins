---
name: agentpack-review
description: Run the full AgentPack PR review flow for the current branch or PR with an optional reviewer lens.
---

# AgentPack Review

Use when the user invokes `$agentpack-review` or `$agentpack-review <reviewer context>`.

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
6. The Anchor role starts from `.agentpack/review-understanding.template.toon` and writes the compatible run-scoped understanding TOON at the output path declared by `agentpack review`.
7. Run `agentpack review --check`; do not start Judge unless Anchor validates.
8. Judge must read that understanding TOON from disk, start from `.agentpack/review-findings.template.toon`, and write the candidate findings TOON at the declared run-scoped path.
9. Run `agentpack review --check`; Critic must read the canonical Anchor and Judge handoffs, start from `.agentpack/review-critique.template.toon`, and write exactly one accept, reject, or downgrade decision for every Judge finding at the declared path.
10. Run `agentpack review --check` to validate Critic and generate `approved-findings.toon`. `--dry-run-post` and `--post-inline-comments` consume only that approved artifact. Actor is publish-only: it never edits or pushes a PR branch. Do not produce a final review summary unless Critic validates and any intended PR-bound inline post succeeds.
11. If an older model emits valid JSON or fenced output instead of TOON, rerun `agentpack review --check`; AgentPack canonicalizes schema-valid output to TOON and writes a repair guide for invalid output.
12. Resume an interrupted run only with `agentpack review --resume <run_id>`.
13. Use the latest PR head, `gh pr view`, `git diff`, and direct code reads as source of truth.
14. Treat any non-PR portion of `$ARGUMENTS` only as a prioritization lens. It must not replace code evidence.
15. Report approved findings first with file evidence, then state inline-post status and validation exactly: dry-run passed, posted, failed, or not run.
