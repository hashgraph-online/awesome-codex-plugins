# Evolve Autonomous Execution Rules

## Fully Autonomous

Evolve runs without human intervention from start to teardown. Every `/rpi` invocation uses `--auto`. Do NOT ask the user for confirmation, clarification, or approval at any point. Do NOT pause between cycles. Do NOT summarize and wait. The user's only touchpoint is the teardown report at the very end.

### Operator-shape carve-out

A single, bounded exception applies. a single operator question is permitted ONLY when the cycle has identified a **shape decision** that affects > 50 files OR touches a schema/contract surface, and where picking wrong costs > 10 minutes of rework. Examples that qualify: declaration carrier shape across a 533-file pool, frontmatter-key vs `$comment`-key vs sidecar-file choice, struct-field addition to a shared contract type. Anything that fits inside an established shape continues to be fully autonomous. The carve-out exists because a 30-second user pick can unblock 300+ file edits — but it is narrow: ask once per shape decision, then resume the autonomous loop.

## ScheduleWakeup self-perpetuation (Claude-Code harness)

Inside the Claude-Code harness, `/evolve` (the terminal-native loop) is not the only self-perpetuation surface. Each /evolve cycle can call `ScheduleWakeup` at end-of-turn to fire the next cycle:

- Productive cycle (commit landed): `delaySeconds=270` keeps the prompt cache warm.
- Scout cycle: `delaySeconds=600` — bigger gap, no cache reload cost since context isn't reused.
- Idle cycle: `delaySeconds=1800` — coarse poll for fresh signal.

Hard stops MUST NOT call `ScheduleWakeup`: KILL/STOP files, dormancy reached, or `--max-cycles` cap hit. `CONTEXT_BUDGET_EXHAUSTED` is NOT a hard stop — it is the one handoff that MUST re-arm: write the non-sticky `HANDOFF` marker and schedule the next fire so the loop survives compaction (soc-5qit session-handoff semantics, `references/context-budget.md`; ending the loop for context reasons is the category error that stranded a 10-bead-ready backlog on 2026-05-21). When dormancy fires (Step 3 hard-gate), `/evolve` writes `.agents/evolve/DORMANT` and Step 1 short-circuits on subsequent fires before any further tool calls — this is the operational enforcement of the "no ScheduleWakeup on dormancy" rule (see `references/cycle-history.md` for the marker semantics). The terminal-mode `/evolve` loop and the Claude-Code `ScheduleWakeup` loop are duals: both drive Step 1..Step 7 repeatedly, both honor the same kill switches and stop conditions, both persist resume state via `.agents/evolve/session-state.json`.

## Each Cycle = Complete /rpi Run

All 3 phases (discovery → implementation → validation). Never invoke a partial RPI. If a task is too large for one cycle, break it into smaller sub-tasks during discovery and let `/crank` handle the waves. Evolve's job is to keep the loop turning, not to micro-manage individual tasks.

## Break Large Work into Sub-RPI Cycles

When work selection identifies a massive task (7+ issues, multi-subsystem scope), decompose it during `/rpi`'s discovery phase into an epic with waves. One evolve cycle = one `/rpi` run = one complete lifecycle. If the epic is too large for a single session, `/rpi`'s built-in retry and `--from=` resume handle continuation.

## Respect Repo-Local Program Contracts

When `PROGRAM.md` or `AUTODEV.md` exists, treat it as a hard operational constraint for cycle selection and keep/revert decisions:
- prefer work that can plausibly land inside mutable scope
- do not intentionally select work that requires immutable-scope edits
- treat out-of-scope work as escalation or backlog material, not permission to widen scope in place
- let `/rpi` enforce the active program contract during execution, then use its validation and decision policy during the evolve regression gate

## Anti-Patterns (DO NOT)

| Anti-Pattern | Why It's Wrong | Correct Behavior |
|--------------|----------------|------------------|
| Ask the user anything during execution | Evolve is fully autonomous — questions break the loop | Make best judgment, report in teardown. Exception: shape decisions affecting > 50 files or schema/contract surfaces (see "Operator-shape carve-out" above) |
| Stop after one `/rpi` cycle and summarize | Evolve loops until kill switch, max-cycles, or dormancy | Increment cycle and re-enter Step 1 |
| Run `/rpi` without `--auto` | Non-auto `/rpi` has human gates that halt the loop | Always pass `--auto` to `/rpi` |
| Run partial `/rpi` (skip validation) | Each cycle must be a complete 3-phase lifecycle | Let `/rpi` run all 3 phases autonomously |
| Pause between cycles to explain progress | The user wants results, not narration | Log cycle results, immediately start next cycle |
| Treat "no queued work" as "stop" | Generator layers (testing, validation, drift, features) produce work | Run all generator layers before considering dormancy |
| Select work that obviously violates `PROGRAM.md` | Scope escape is a tracked outcome, not a license to widen the loop | Escalate or re-queue out-of-scope work and keep selection inside mutable scope |
