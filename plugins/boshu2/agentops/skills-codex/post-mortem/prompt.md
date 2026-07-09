# post-mortem

Close out completed work in a Codex-native way: validate outcomes, extract durable learnings, and harvest concrete follow-up work back into the queue.


<!-- BEGIN AGENTOPS OPERATOR CONTRACT -->
<!-- Generated from skills-codex-overrides/catalog.json for post-mortem. -->

## Codex Execution Profile

1. Treat `skills/post-mortem/SKILL.md` as the canonical close-out contract and `skills-codex/post-mortem/SKILL.md` as the Codex-facing artifact.
2. Keep the council/validation summary concise, then write learnings and harvested work to disk.
3. Prefer concrete follow-up items that can flow directly into `.agents/rpi/next-work.jsonl` for the next Codex loop.
4. Own Codex closeout during the post-mortem flywheel phase by running `ao session close --auto-extract` followed by `ao flywheel close-loop --quiet`; use `ao forge transcript <path-or-glob> --queue` first only when transcript discovery must be explicit.

## Guardrails

1. Keep harvested work machine-checkable: available on write, then claim/release/consume through the queue lifecycle.

<!-- END AGENTOPS OPERATOR CONTRACT -->
