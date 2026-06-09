# operating-loop-workflow

Run the operating-loop seven-move loop (shape → plan → pre-flight → implement → capture) in Codex.

## Codex Execution Profile

1. In Codex, the operating-loop seven moves ARE the `$rpi` chain (`$discovery` → `$crank` → `$validate`); there is no separate engine to install.
2. Run `$rpi --auto "<intent>"` for the full loop, or `$discovery "<intent>"` stopping after `$pre-mortem` for the plan-only half.
3. Keep cross-runtime references brief and non-blocking.

## Guardrails

1. Treat `$rpi` as the canonical seven-move loop in Codex.
2. Preserve each move's evidence (plan, pre-mortem verdict, validation result) before advancing.
