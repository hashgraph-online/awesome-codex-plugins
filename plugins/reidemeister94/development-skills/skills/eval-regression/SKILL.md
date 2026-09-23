---
name: eval-regression
description: "Check skill routing or behavior, investigate a regression, or compare plugin changes with a base commit."
argument-hint: "--agent <claude|codex> --model <id> --effort <level> [--base <commit>]"
allowed-tools: Glob, Read, Bash, Grep, AskUserQuestion
---

# Eval regression

Use deterministic repository tests first. Stop when the target has no behavioral diff.

Resolve the plugin from the argument or cwd. Its catalog is `evals/evals.json`; the runner is `scripts/run_evals.py` in this skill.
Require the user to choose agent, model, and effort. Never select a costly model or high effort silently.

## Normal check

1. Select cases by changed paths with `--changed-from <base>`, or name them with `--case`. Do not select the full catalog implicitly.
2. Run the command without `--run`. The runner prints cases, modes, repeats, sessions, timeout, and maximum duration without starting an agent.
3. An approved plan that names this exact run already authorizes it. For a standalone eval, present the run plan and stop once.
4. After approval, repeat the same command with `--run`. Default to candidate-only, one run per case, 180 seconds, and four sessions maximum.
5. Report every failed assertion, timeout, non-zero exit, duration, and token count. Missing evidence is inconclusive.

## Escalation

- Compare base and candidate only when the user asks, or when a failed candidate check needs a baseline.
- Extract the base with `git archive`. Use the same cases, agent, model, effort, repeats, and timeout on both versions.
- Repeat only a failed or observably unstable case. Three repeats are a stability benchmark, not a default.
- `--all`, `--repeat > 1`, more sessions, or a longer timeout is new scope. Update the run plan and get authority first.
- Routing cases stop at the first Skill selection. Tool assertions are appropriate because routing is the contract.

Remove temporary base copies after the comparison. Do not edit or commit the target.

Deterministic assertions are `tool`, `tool_not`, `clean_worktree`, `changed_files_exact`, `file_contains`, `file_not_contains`, `transcript_contains`, and `tool_sequence`.
Use a semantic judge only when no filesystem, command, tool, ordering, or assistant-output observation can express the contract.
