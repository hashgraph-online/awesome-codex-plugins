# Continuation engine

Load this reference when `SUPERLOOPY_STOP_HOOK=on`, when a loop is `blocked` or `paused`, or when scheduling a resume after a quota reset.

## Continuation Engine

The optional `Stop` hook is a bounded, progress-gated engine, not a one-shot nudge. With `SUPERLOOPY_STOP_HOOK=on`, while work remains it keeps driving you toward evidence-backed completion, counting iterations in `.superloopy/loop-control.json`.

- Progress is measured by recorded proof (passed criteria and completed goals) against a high-water mark; only new proof resets the no-progress counter.
- It never completes anything. Completion stays the plan's authority via `superloopy loop check` + `superloopy loop finish` with real artifacts.
- A cap or no-progress stall marks the loop `blocked` (visible in `superloopy loop status`) and asks for a human — it never fabricates a done.
- Quota/usage limits are distinct from `blocked`: when the host transcript shows a usage/rate/quota-limit marker, the loop is marked `paused` (reason `quota`) in `.superloopy/loop-control.json` — a *resumable* state. It does **not** burn the no-progress counter and is never mistaken for completion; a `loop_paused`/`loop_resumed` pair is written to the ledger. Superloopy is hook-driven and cannot self-wake, so it only pauses cleanly and stays resumable — see "Auto-resume after a quota reset" below.
- Knobs: `SUPERLOOPY_MAX_ITERATIONS` (default 50, `0` = unlimited; the no-progress guard stays active), `SUPERLOOPY_MAX_STALLED` (default 3), `SUPERLOOPY_CONTINUATION=off` (legacy single continuation), `SUPERLOOPY_QUOTA_MARKERS` (comma/newline list of extra host-specific limit phrases — the built-in set is conservative, so set this to your host's exact banner text).

### Auto-resume after a quota reset

Superloopy detects the limit and pauses; *waking* when quota resets is an external job (Superloopy has no daemon). Run an idempotent scheduler that resumes the loop and stops once it is done:

- Read `superloopy loop status --json`: if `summary.aggregateComplete` is false, resume by re-running the loop (`loopy <continue>`, or `superloopy loop guide --json` then the next command); if complete, no-op.
- Schedule it on a cadence that outlasts the limit window — a host cron / cloud routine every 20–30 min, or aligned to a known weekly reset. The first run after the reset succeeds; earlier runs simply no-op while still limited.
- Keep it idempotent and self-terminating, exactly like Superloopy's own gates. Superloopy supplies the resumable state; the scheduler supplies the wake.
