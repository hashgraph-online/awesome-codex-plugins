# beads

Operate issue workflows with Codex-friendly execution and clear dependency control.

## Codex Execution Profile

1. Treat `skills/beads/SKILL.md` as canonical issue-tracking contract.
2. Treat live `br` reads (`br ready`, `br show`) as authoritative over JSONL exports.
3. Keep issue updates tightly coupled to implementation state changes.
4. After tracker mutations, run `br sync --flush-only`, inspect `git status`, commit tracker changes if pending, and push the tracker remote when configured.
5. Reconcile broad parents and stale parent notes after child closure instead of leaving umbrella beads stale.

## Guardrails

1. Avoid runtime-specific assistant assumptions in operator instructions.
2. Ensure dependency direction is explicit whenever adding `br dep` edges.
3. Require acceptance and validation details in issue descriptions for executable handoff.
4. Do not route execution from stale queue items without normalizing them to the actual remaining gap.
