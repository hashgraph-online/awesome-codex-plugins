# Codex Execution Profile -- continuity-loop

The unattended renewal spine: defines what a renewal tick is, how a stalled
lane is detected (two-tick rule), and when a stall escalates over Agent Mail.

## Steps

1. Read `../../skills/continuity-loop/SKILL.md` and identify the exact task path: wiring a continuity step into a loop skill, tuning tick cadence, diagnosing a stalled lane, or reading `.agents/continuity/state.json`.
2. Load only the source `references/*` or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps/ACFS binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, and validation output.
6. If the source skill is still being upgraded by the Claude lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Do not use Claude Code, `claude -p`, or Claude-only tools as the executor from Codex.
- This skill defines the tick contract; it never runs agents, schedules timers, or starts daemons itself.
- Render a verdict (suspect / stalled / converged) from recorded state, not from guesswork.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not broaden scope beyond the requested operator action.
- Keep backstage/operator terminology out of client-facing artifacts.
