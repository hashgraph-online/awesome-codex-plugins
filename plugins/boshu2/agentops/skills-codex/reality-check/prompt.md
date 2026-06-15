# Codex Execution Profile -- reality-check

Mid-epic strategic drift audit at a wave boundary: measure implemented reality
against the claimed vision, name every gap with file-level evidence, and route
the bridge into the planning stack.

## Steps

1. Read `../../skills/reality-check/SKILL.md` and identify the exact task path: which epic/wave boundary is being audited and which vision docs form the measuring stick.
2. Load only the source `references/*`, `fixtures/*`, or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps/ACFS binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, and validation output.
6. If the source skill is still being upgraded by the Claude lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Do not use Claude Code, `claude -p`, or Claude-only tools as the executor from Codex.
- Audit-only: never patch code, edit beads, or rewrite vision docs while auditing.
- Every gap row carries a file-level citation or a command output; uncited gaps are opinions.
- Tracker percentages are evidence about effort, never the verdict.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not broaden scope beyond the requested operator action.
- Keep backstage/operator terminology out of client-facing artifacts.
