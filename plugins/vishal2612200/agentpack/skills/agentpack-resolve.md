---
name: agentpack-resolve
description: Resolve all actionable PR review comments with cited fixes, validation, and replies.
---

Use when the user invokes `$agentpack-resolve`.

Examples: `$agentpack-resolve pr 123` or `$agentpack-resolve PR #123 focus on backward compatibility`.

The skill invocation owns the full loop; the internal `--check` and `--reply` commands are agent steps, not extra user commands.

1. Run `agentpack resolve "$ARGUMENTS"`; use `--pr <number>` when the PR is explicit.
2. Read `.agentpack/resolve.prompt.md` and `.agentpack/resolve-comments.json` completely.
3. Write every comment disposition to the declared plan TOON with exact source evidence citations.
4. Run `agentpack resolve --check`; do not edit code until the plan passes.
5. Apply all validated fixes in one pass, run targeted and relevant project checks, and write one cited reply record per comment.
6. Run `agentpack resolve --reply`; it refuses missing citations, invalid replies, and a changed PR head.
7. Start a fresh resolve pass after posting and repeat until no actionable unresolved comment remains or the iteration limit is reached.
8. Use concise inline replies: a short bold outcome, one explanation, exact `path:line` citations, `Suggested fix:` when relevant, and validation status. Do not mark a thread resolved merely because a reply was posted.

If a comment cannot be verified or fixed, record `blocked` with evidence and explain the blocker. Do not silently defer actionable comments.
