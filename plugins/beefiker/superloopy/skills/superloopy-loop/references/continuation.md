# Continuation engine

Load this reference when the Stop hook re-prompts you, when a loop is `blocked` or `paused`, or when scheduling a resume after a quota reset.

## Continuation Engine

The packaged `Stop` hook is a bounded, progress-gated engine, not a one-shot nudge. While work remains it keeps driving you toward evidence-backed completion, counting iterations in `.superloopy/loop-control.json`.

- Who it drives: by default only a host session whose user started or resumed a loop with a full-loop trigger (`loopy …`, `loopycrew`, `ultrawork`), until that user sends a plain prompt; a guidance-only trigger (`loopywork`, `lpy`, `$lpy`), a `SUPERLOOPY_STEER` prompt, or an output-style toggle leaves that as it is. `SUPERLOOPY_STOP_HOOK=on` drives every session with unresolved work; any other non-empty value turns it off. A user interrupt never becomes a continuation.
- If only the user can unblock a criterion (a decision, credentials, access), write the question to an artifact and record that criterion `--status blocked`; it is not re-driven, and the guide moves on to the goal's other open criteria. If nothing else in the goal can proceed, checkpoint the goal `--status blocked` and move to the next goal. When only blocked goals remain, the guide's state is `blocked_on_user`: report the question and stop. Once the user answers, record each blocked criterion with `loop evidence` and finish as usual.
- A worker that used up its receipt attempts was allowed to stop without proof. The next continuation lists it once under "Workers that stopped without proof"; treat its reply as unproven and re-dispatch a narrower card or do the work and prove it yourself.
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
