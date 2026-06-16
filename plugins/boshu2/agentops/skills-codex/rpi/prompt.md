# rpi

Run the full RPI lifecycle in a Codex-native way: direct in-session orchestration, concise progress updates, and file-backed handoff between phases.


<!-- BEGIN AGENTOPS OPERATOR CONTRACT -->
<!-- Generated from skills-codex-overrides/catalog.json for rpi. -->

## Codex Execution Profile

1. In Codex hookless mode, run `ao codex ensure-start` before phase orchestration; the CLI records startup once per thread and skips duplicates automatically.
2. When beads are present, resolve bead IDs before routing; when beads are absent, preserve the current goal or execution-packet objective across phases.
3. Keep a single lifecycle objective spine across discovery, crank, and validation. Never replace it with a child issue ID or one ready slice from `br ready`, `br show`, or `.agents/rpi/next-work.jsonl`.
4. If discovery does not yield an epic id, invoke `$crank .agents/rpi/execution-packet.json` and standalone `$validate` instead of inventing one.
5. If `$crank` returns `<promise>PARTIAL</promise>`, rerun `$crank` on the same lifecycle objective until the work is done, blocked, or the retry budget is exhausted.
6. Orchestrate phases directly in the current session; do not hand RPI orchestration to wrapper commands.
7. For Nightly, evolve, or auto-prompt goals, inspect the last 14 days of Nightly PRs and scheduled Nightly runs before choosing the implementation slice.
8. Classify recurring evidence as code-driven, runtime-artifact-only, or corpus-state-bound; prefer a code-driven fix unless the user explicitly asked for corpus maintenance.
9. Route `br` unavailability, tag push failures, worktree-disposition friction, and security/eval advisory recurrence as prompt/runtime debt rather than treating them as background noise.
10. claim, release, and consume semantics exactly
11. claim before work, consume on success, release on failure or interruption

## Guardrails

1. Do not stop after a partial phase result; only stop on `<promise>BLOCKED</promise>`, retry-budget exhaustion, or final completion. Do not count runtime-only artifact flips or corpus-state flywheel movement as successful code improvement without a tracked source change or explicit operator request. Do not invoke Dream/overnight from RPI; use Dream evidence only as input, and keep code-mutating work in the RPI lifecycle.

<!-- END AGENTOPS OPERATOR CONTRACT -->
