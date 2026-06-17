# Codex Execution Profile -- toil-mining

Mine the operator's usage history for repeated toil, cluster it, score each
cluster by frequency x pain, and emit a ranked automation-candidate list for
automation-shape-routing.

## Steps

1. Read `../../skills/toil-mining/SKILL.md` and identify the exact task path: which evidence sources are in scope and what the candidate-list output contract is.
2. Load only the source `references/*`, `fixtures/*`, or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps/ACFS binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, and validation output.
6. If the source skill is still being upgraded by the Claude lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Do not use Claude Code, `claude -p`, or Claude-only tools as the executor from Codex; scheduled sweeps dispatch via `codex exec`.
- Measure before believing: candidates come from counted history, never intuition.
- Filter machine echoes (tool results, confirmations, error strings) before clustering.
- Emit candidates only; never build the automation or pick its shape from this skill.
- Read sources read-only; never rewrite or prune the historical record.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not broaden scope beyond the requested operator action.
- Keep backstage/operator terminology out of client-facing artifacts.
