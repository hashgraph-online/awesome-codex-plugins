# Administering a running Gas City

> Day-2 operations: health cadence, the native surfaces to read (never wrap),
> lifecycle, backup, and binary discipline. Assumes `source <city>/env.sh`.

## Daily health cadence

```bash
gc status --json | jq '{controller: .controller, beads: .beads}'   # store MUST stay NativeDoltStore
gc doctor --json | jq '[.checks[] | select(.status != "pass")]'    # only exceptions
gc events --follow                                                  # live activity; Ctrl-C anytime
```

Doctor is the truth surface (73+ checks incl. the membrane's two). Memorize
the canonical green + benign warnings (standup.md §5) so a NEW warning stands
out. The dashboard SPA (supervisor port, e.g. `127.0.0.1:8373`) gives the same
picture visually; `gc events` carries `run_id`/`step_ref`/`seq` — filter by
`run_id` to trace one quest end-to-end.

## What gc already runs for you (don't rebuild)

~20 native housekeeping **orders** ride the controller: reaper, orphan-sweep,
gate-sweep, dolt/beads-health, prune-branches, spawn-storm-detect, … plus the
membrane pack's additions (`membrane-canary` — scheduled structural smoke;
optionally `membrane-lane-keepalive` — re-submits a no-op to reviewer lanes
idle past budget, using `gc session submit` ONLY). Inventory: `gc order list`.
Formulas: `gc formula list`. Sessions: `gc session list` / `gc session logs`.

Health patrol is an order; failures surface in `gc events` and the dashboard.
Do not build external stall-detection or notification infra.

## Session lifecycle facts that shape admin

- **Sessions are disposable; work survives them.** Beads are ground truth; if
  an agent dies its beads stay open and a fresh agent picks them up.
- **The orchestrator ADOPTS live sessions on restart** rather than respawning
  — so a supervisor restart is cheap and non-destructive.
- Pools scale by `scale_check` demand each tick, bounded by
  `min/max_active_sessions`; idle sessions retire on their own. Don't hand-kill
  pool members to "clean up".

## Store and backup

- Dolt is **gc-managed** — never attach your own `dolt sql-server` to
  `<city>/.beads/dolt`. Auto-GC on; stats workers off (managed defaults).
- **Cold backup:** `gc stop` (clean flush with 30 s grace) → copy
  `.beads/dolt` → `gc start`. Doctor's `jsonl-archive` keeps an on-host JSONL
  export as a versioned escape hatch (warns "local-only" — expected for an
  experiment city; a trunk city wants an off-box replica).
- The city's dolt is LOCAL-ONLY by design; don't wire it into any shared/
  cross-host dolt complex. Two-store rule: **bd/dolt is the city's substrate
  store; `br` remains the AgentOps repo tracker.** Never track agentops repo
  work in the city store or vice versa.

## Binary discipline (fork-built gc)

- Rebuild = `make build` in the fork checkout (CGO/icu4c), then `gc start` —
  `auto_restart_on_drift` (default true) restarts the supervisor when the
  on-disk binary drifts from the running one.
- **Verify the running binary carries local patches** after any rebuild.
  Today's checks are indirect: `git -C <fork> describe` (e.g. `edge-1-g<sha>`
  = 1 patch past the `edge` tag) tells you what the *tree* carries; `bin/gc`
  mtime newer than the patch commit tells you the *binary* was rebuilt after
  it; the behavioral probe (sling a trivial quest; builder spawns in
  ~10–15 s, no CPU peg) tells you the patch is *live*. A stale binary
  silently reintroduces the reconciler livelock — when in doubt, rebuild,
  restart, probe. (A doctor check that asserts patch-carry directly is the
  planned durable fix — bead age-gc-adoption-u0he.10.)
- Fork policy: read-only managed fork, **upstream-first** — local patches stay
  on one thin branch (`agentops-patches`-style: main + N patches), each also
  preserved as a `.patch` in the AgentOps repo
  (`docs/audits/gc-mvp-*/patches/`). Do not accumulate a private fork.

## Config knobs that matter (from gc's reference docs)

| Knob | Default | When to change |
|---|---|---|
| `nudge_dispatcher` | `legacy` (per-session 2 s `gc nudge poll` + bd shellout storm) | Set `"supervisor"` (in-runtime delivery, unix-socket wake) on any city with many sessions or session-server load symptoms |
| `auto_restart_on_drift` | `true` | Leave on; it's the rebuild-safety net |
| `start_ready_timeout` | `5m` | Raise for cities with many adopted sessions (wake budget: ~5 wakes/30 s tick) |
| `[mail] retention_ttl` | unset | Use Go durations (`"168h"`); `"7d"` is INVALID |

## Cost / analytics: honest state

`gc costs` and `gc analyze reliability` exist but are **empty by default**:
sub-backed providers emit no usage facts (`usage.jsonl` absent; unpriced
models drop from totals — it would fail-open) and production paths don't emit
`session.quarantined`. Treat both as decision-support-when-populated, never as
gates. `[usage] provider="local"` can populate costs where wired.

## Multi-city coexistence

Each city: own GC_HOME, own tmux socket, own supervisor port, own launchd
unit (GC_HOME-hashed label — read the plist's GC_HOME string to map unit →
city; the hash is not a plain sha256 of the path). Verify which supervisor
serves which city before restarting anything:
`ps aux | grep 'gc supervise'` + the plist contents.
