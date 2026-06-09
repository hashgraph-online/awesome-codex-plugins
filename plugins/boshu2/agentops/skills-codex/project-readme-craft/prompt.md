# Codex Execution Profile -- project-readme-craft

Codex runtime wrapper for `project-readme-craft`.

## Steps

1. Read `../../skills/project-readme-craft/SKILL.md` and identify the exact task path, trigger, or command family that applies.
2. Load only the source `references/*` or `scripts/*` files needed for that path.
3. Confirm live command syntax with local `--help`, repo docs, or the source skill's evidence before running state-changing commands.
4. Execute with Codex-native tools: local shell, `rg`, `apply_patch`, repo scripts, and AgentOps binaries as directed by the source skill.
5. Capture machine-checkable evidence: command, exit code, affected paths, and validation output.
6. If the source skill is still being upgraded by another lane, do not rewrite it. Report the missing source-side contract and keep this Codex wrapper intact.

## Guardrails

- Use Codex-native tools for execution; do not shell out to another agent runtime.
- Do not invent command flags. Verify with `--help` or checked-in references.
- Do not broaden scope beyond the requested operator action.
- Keep backstage/operator terminology out of client-facing artifacts.
