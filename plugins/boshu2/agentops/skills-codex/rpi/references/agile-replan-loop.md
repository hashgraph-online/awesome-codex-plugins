# Agile Re-Plan Loop (the anti-waterfall rule)

The initial plan/wave-sequence is a **hypothesis**. Each wave is an experiment
that produces evidence; that evidence re-plans the remaining waves. This is what
makes `--auto` *autonomous* rather than *blind*.

## At every wave boundary (and after the validation phase)

1. **Reflect** — run a bounded post-mortem$discovery delta over the wave just
   completed (delegate to `$post-mortem` then `$discovery`'s re-plan, isolated;
   do not inline). Input = what shipped, what the gate/refuters said, what broke,
   what the wave *taught* that the plan didn't know.
2. **Re-plan the REMAINING waves** — the delta may, autonomously:
   - **refactor** a downstream wave's scope (split, merge, narrow, widen),
   - **insert** a new wave the evidence revealed is needed,
   - **drop** a wave the evidence made unnecessary,
   - **reorder** waves as the critical path shifts,
   - **re-scope / re-prioritize / re-sequence** beads,
   - **escalate** (circuit-breaker) when the evidence invalidates the objective itself.
   Persist the mutated plan (the execution packet / plan doc is rewritten, not
   appended-to-blindly) so the next wave reads the *current* plan, not the stale one.
3. **Proceed** to the next (possibly new/changed) wave.

## Bounds (so agility ≠ thrash)

Re-planning shares the run's circuit breakers — token/time budget, the attempt
cap, and **oscillation detection** (if the plan flips the same decision back and
forth across waves, stop and surface it). Honor the autonomous-session scope
(CLAUDE.md): at ≥5 ships in one session, the post-mortem checkpoint is mandatory
and may itself end the session. The operator is touched only at the terminal
objective or a breaker trip — never just to approve a pivot.

## Anti-patterns this rule kills

- **Waterfall**: executing the initial wave list to the letter because "that was the plan."
- **Retry-not-replan**: re-cranking a failed wave on the same objective forever instead of asking whether the *remaining plan* should change.
- **Permission-seeking**: pausing to ask the operator to approve a pivot that `--auto` already authorizes.

## How the phase skills feed this loop

`$crank` (implementation) and `$validate` **surface their findings up to the
orchestrator** for re-planning — they do not swallow a finding into a silent
local retry. `$discovery` is the re-plan engine; `$post-mortem` is the reflect step.
