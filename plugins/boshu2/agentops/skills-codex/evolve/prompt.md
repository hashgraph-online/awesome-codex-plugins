# evolve

Run `$evolve` as the Codex-facing operator loop: post-mortem finished work, analyze repo state, select or create the next highest-value item, let `$rpi` plan/pre-mortem/implement/validate it, harvest follow-ups, and repeat until a real stop condition fires. Drive the lead cycle in-session through the skills; do not shell out to a CLI loop wrapper.

## Codex Execution Profile

1. Treat `skills/evolve/SKILL.md` as the canonical loop contract and `skills-codex/evolve/SKILL.md` as the Codex-facing artifact.
2. Use Codex commentary updates to show cycle boundaries, selection source, queue refreshes, and stop reasons.
3. Prefer Codex sub-agents for generator layers and sidecar audits when they can run in parallel without blocking the main loop.
4. Persist loop state under `.agents/evolve/` and recover from disk instead of relying on live context.
5. When `PROGRAM.md` or `AUTODEV.md` exists, treat it as the active execution layer: keep selection inside mutable scope, escalate immutable-scope work, and use its validation and decision policy in the cycle gate.
6. Do not invent a new loop skill name when the user asks what this should be called; the Codex-facing loop is `$evolve`, the in-session skill.
7. For Nightly/evolve maintenance cycles, start with the rolling Nightly evidence brief when present, or generate one with `scripts/nightly-rpi-brief.sh`, before selecting the next `$rpi` objective.
8. Prefer recurring code-driven failures over runtime-artifact-only or corpus-state-only fitness movement; treat those non-code signals as diagnostics unless the operator explicitly asks for corpus maintenance.

## Guardrails

1. Do not treat empty initial queues as success; run the full fallback ladder before dormancy.
2. Re-enter selection after every `$rpi` cycle and re-read harvested work immediately.
3. Keep kill-switch, regression gates, and stagnation protection active without short-circuiting useful work discovery.
4. Do not spend repeated cycles on `flywheel-compounding` unless corpus-active preconditions are true and the expected improvement can propagate beyond ignored runtime artifacts.
5. If a Codex-native override and the source skill diverge, keep behavior aligned with the source contract and then update the override.
