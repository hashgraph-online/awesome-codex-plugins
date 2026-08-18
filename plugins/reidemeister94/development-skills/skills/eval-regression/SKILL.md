---
name: eval-regression
description: Use when the user asks to check a plugin or skill with behavioral evals, compare it with HEAD, or investigate a behavioral regression.
argument-hint: "--agent <claude|codex> --model <id> --effort <level> [--base <commit>]"
allowed-tools: Glob, Read, Bash, Grep, AskUserQuestion
---

# Eval regression

Use deterministic repository tests first. Stop when the target has no behavioral diff.

Resolve the plugin from the argument or cwd. Its catalog is `evals/evals.json`; the shared runner is `../ai-agent-bench/scripts/run_evals.py`. Require the user to choose agent, model, and effort. Never select a costly model or high effort silently.

## Normal check

1. Select cases by changed paths with `--changed-from <base>`, or name them with `--case`. Do not select the full catalog implicitly.
2. Run the command without `--run`. The runner prints the cases, modes, repeat count, session count, per-session timeout, and maximum duration without starting an agent.
3. Present that plan and stop for explicit cost approval.
4. After approval, repeat the same command with `--run`. The default is candidate-only, one run per case, 180 seconds per session, and at most four sessions.
5. Report every failed assertion, timeout, non-zero exit, duration, and token count. Missing evidence is inconclusive.

## Escalation

- Compare base and candidate only when the user asks, or when a failed candidate check needs to distinguish a regression from an existing failure. Extract the base with `git archive`; run the same selected cases, agent, model, effort, repeat, and timeout on both; compare reports with `--compare`.
- Repeat only a failed or observably unstable case. Three repeats are a stability benchmark, not a default.
- `--all`, `--repeat > 1`, a larger `--max-sessions`, or a longer timeout needs a new run plan and explicit approval.
- Routing cases stop at the first Skill selection. A tool assertion is appropriate there because routing is the contract; they must not execute the selected skill.

Remove temporary base copies after the comparison. Do not edit or commit the target.

Deterministic assertions are `tool`, `tool_not`, `clean_worktree`, `changed_files_exact`, `file_contains`, `file_not_contains`, `transcript_contains`, and `tool_sequence`. Use a semantic judge only when no filesystem, command, tool, ordering, or assistant-output observation can express the contract.
