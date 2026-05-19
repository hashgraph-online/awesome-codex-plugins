# quickstart

Guide new users through AgentOps in a Codex-first flow.

## Codex Execution Profile

1. Treat `skills/quickstart/SKILL.md` as canonical workflow.
2. Prefer Codex tooling and command examples first.
3. Treat `ao quick-start` as the canonical new-repo seed path and `ao quickstart` as its stable alias.
4. Keep optional cross-runtime references brief and non-blocking.

## Guardrails

1. Do not require Claude CLI checks to proceed.
2. Avoid instructions that assume `.claude/` directories.
3. Be explicit that current Codex installs are hookless by default; native hooks under `~/.codex/hooks.json` are an optional `install-codex.sh --with-hooks` profile. Legacy explicit fallback commands remain `ao codex ensure-start` once per thread and `ao codex ensure-stop` during closeout when needed.
4. Keep `ao codex status` as the manual lifecycle escape hatch, not the primary workflow.
5. Keep onboarding output action-oriented: next command, expected result, fallback.
6. Mention `$bootstrap` only as the product/operations expansion after the core seed, not as a competing initializer.
