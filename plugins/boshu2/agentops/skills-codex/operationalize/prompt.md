# Codex Execution Profile -- operationalize

Distill a finished research artifact or hard-won learning into a handful of
evidence-anchored rules, then route each rule to the automation shape that
will actually fire next time (skill, workflow, hook, gate, bead, playbook).

## Steps

1. Read `../../skills/operationalize/SKILL.md` and identify the exact task path: which source artifact is being operationalized and what the expected rule-packet output is.
2. Load only the source `references/*`, `fixtures/*`, or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps/ACFS binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, and validation output.
6. If the source skill is still being upgraded by the Claude lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Do not use Claude Code, `claude -p`, or Claude-only tools as the executor from Codex.
- Anchor every distilled rule to evidence in the source artifact; uncited rules do not ship.
- Emit rule packets and routed handoff stubs only; do not build the routed automation inline.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not broaden scope beyond the requested operator action.
- Keep backstage/operator terminology out of client-facing artifacts.
