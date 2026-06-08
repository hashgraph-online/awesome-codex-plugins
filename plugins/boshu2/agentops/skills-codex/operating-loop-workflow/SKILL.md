---
name: operating-loop-workflow
description: "Run operating loop workflow."
---
# $operating-loop-workflow

> **One job:** Run the operating-loop seven-move loop (shape → plan → pre-flight → implement → capture) in Codex.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

In the Codex runtime the operating-loop seven moves ARE the `$rpi` skill chain — there is no
separate engine to install. `$rpi` composes the loop end to end.

## Execution

1. Run `$rpi --auto "<the capability/intent to drive through the loop>"`.
   - `$rpi` chains `$discovery` (shape → plan → pre-mortem) → `$crank` (TDD per slice across
     conflict-free waves) → `$validate` (acceptance roll-up + capture).
   - For the plan-only half (shape → plan → pre-flight, no implementation), run
     `$discovery "<intent>"` and stop after `$pre-mortem`.
2. Report the resulting plan, the `$pre-mortem` verdict, and the `$validate` outcome.

## Guardrails

1. Treat `$rpi` as the canonical seven-move loop in Codex.
2. Preserve each move's evidence (plan, pre-mortem verdict, validation result) before advancing.
