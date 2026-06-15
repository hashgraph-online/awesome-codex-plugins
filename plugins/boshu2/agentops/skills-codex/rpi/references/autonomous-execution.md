# Autonomous Execution Rules

## The Three-Phase Rule

RPI has THREE mandatory phases (unless complexity == `fast`). You MUST run all three — discovery, implementation, AND validation — in a single session. Do NOT stop after implementation. Do NOT ask the user if they want to commit after Phase 2. Phase 2 completing is NOT the end — it is the midpoint. Validation (Phase 3) is where learnings are captured and the knowledge flywheel turns. Skipping it breaks the flywheel.

## Fully Autonomous by Default

Unless `--interactive` is explicitly set, RPI runs hands-free from start to finish. Do NOT:
- Ask the user for confirmation between phases
- Ask "want me to commit?" or "should I continue?"
- Pause to summarize and wait for input
- Request clarification mid-execution
- Stop to ask about approach or strategy

The human's only touchpoint is AFTER Phase 3 completes. If something is genuinely blocked (3 retries exhausted), then and only then do you stop and report. Everything else runs autonomously. The user invoked `$rpi` because they want you to GO — not to narrate.

## Anti-Patterns (DO NOT)

| Anti-Pattern | Why It's Wrong | Correct Behavior |
|--------------|----------------|------------------|
| Stop after Phase 2 and ask to commit | Skips validation — no quality check, no learnings, flywheel doesn't turn | Proceed directly to Phase 3 |
| Call `$validate` directly instead of `$validate` | `$validate` is one sub-step; `$validate` wraps vibe + post-mortem + forge | Always call `$validate` from `$rpi` |
| Ask "want me to commit?" between phases | Interrupts autonomous flow — user invoked `$rpi` for hands-free execution | Commit only after ALL phases complete |
| Ask the user ANY question during execution | RPI is autonomous unless `--interactive` — questions break the flow | Make best judgment and proceed; report at end |
| Summarize findings and wait after Phase 1 | Discovery output is an input to Phase 2, not a deliverable | Proceed immediately to Phase 2 |
| Pause to explain what you're about to do | Narration wastes time — the user wants results, not commentary | Execute, then report at the end |

## Phase Completion Tracking

After each phase, log progress:
```text
PHASE 1 COMPLETE ✓ (discovery) — proceeding to Phase 2
PHASE 2 COMPLETE ✓ (implementation) — proceeding to Phase 3
PHASE 3 COMPLETE ✓ (validation) — RPI DONE
```
