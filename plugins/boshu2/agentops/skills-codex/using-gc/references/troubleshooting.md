# Gas City troubleshooting — the stall ladder

> Symptom-keyed. Every row was hit for real (fitness run age-gc-mvp-w2-nuiw.4,
> out-of-box exercise .9, factory-chain E1) — these are the proven moves, in
> the order that resolves fastest. General rule: **diagnose from gc's own
> surfaces** (`gc events`, `gc doctor --json`, `gc session list`, `gc status
> --json`) before touching anything; recovery verbs are narrow and specific.

## 1. Idle/draining interactive pane — round never advances

**Symptom:** a builder/verifier pane sits idle (often status `draining`);
the workflow round doesn't transition.

**The ONE verb that works:** `gc session submit <target> <text>` — gc's
semantic-delivery verb. `gc session kill`, `gc session reset`, and raw
`tmux send-keys` **all fail** against a draining pane (verified repeatedly).

```bash
gc session submit agentops-membrane.verifier 'membrane keepalive: reply READY if idle'
```

**Busy-pane variant:** if the pane is mid-self-exploration and queues the
submit without consuming it (seen with agy/gemini): **Esc-interrupt the pane,
then submit again.** (Fitness-run nudges 4–5: send-Enter failed;
esc-interrupt + submit worked.) Standing mitigation: the
`membrane-lane-keepalive` order re-submits on a cooldown — its recovery verb
must be `submit`, never kill/reset/send-keys.

## 2. codex/agy lane wedges at first startup — trust modal

**Symptom:** a fresh verifier session blocks at startup, produces no lane
JSON; the gate DEGRADES (transient — correct, no false REFUTE) every round.

**Fix (setup, one-time):** pre-trust the provider before it runs a lane —
codex: seed a city-scoped `CODEX_HOME` (`printf '{}\n' >
"$CODEX_HOME/hooks.json"` and wire `CODEX_HOME` into the provider env);
agy: run the provider once interactively and accept its `gc prime`/trust
prompt. Until cleared, the lane is dead to automation.

## 3. Every workflow quarantined at the check step

**Symptom:** `gc events` shows the control dispatcher quarantining/terminating
workflows the moment they hit `[steps.check]`.

**Cause:** the membrane gate scripts aren't materialized in the city —
`gc import` does NOT copy pack scripts, and `check.path =
"membrane/close-gate.sh"` resolves against the **city root** (gap A).

**Fix:** copy the pack's `membrane/` scripts into `<city>/membrane/` and
re-sling. There is **no re-fire-a-quarantined-step verb** — for an already-
quarantined quest, run `membrane/close-gate.sh` manually once to produce the
verdict, then let the normal loop resume.

## 4. Builders never spawn / reconciler pegs a CPU

**Symptom:** sling accepted, no session appears (healthy spawn is ~10–15 s);
a gc process burns 100% CPU.

**Cause:** the upstream `getAllDescendants` recursion livelock on PID-reuse
(no cycle guard) — fixed by the cycle-guard patch on the fork's patch branch.

**Fix:** verify the running binary carries the patch (rebuild from the patch
branch: `make build`, then `gc start` — auto-restart-on-drift picks it up).
Probe: sling a trivial quest; builder should spawn in seconds.

## 5. tmux session-server dies / whole city cold

**Symptom:** every session on the city socket is gone at once (the socket
died — e.g. the hosting terminal/mosh session ended, or tmux crashed).

**What saves you:** the launchd supervisor unit restarts the supervisor; the
orchestrator **adopts** what's live and respawns named sessions; **beads are
ground truth** so no work is lost — open beads get picked up fresh.
Keepalive hardening for the supervisor itself is the current frontier
(supervisor keepalive plist). After recovery: `gc status`, then `gc doctor`,
then check in-flight quests via `gc events` — expect them to resume or retry;
only intervene per rows 1–3.

## 6. `gc bd` errors / "no beads database found" / dead dispatcher + orders

**Symptom:** control lane dead, core orders failing with bd errors.

**Cause:** you're on the file backend (`GC_BEADS=file`) — the dispatcher and
core-pack orders shell out to `bd` and die without a real store. File backend
is a docs-troubleshooting escape hatch, NOT an operating mode.

**Fix:** move the city to the native store (standup.md §1–2). Do not build
pumps/workarounds — every file-backend brittleness measured to date was
bd-absence and vanished on native.

## 7. Everything is slow — per-op subprocess churn

**Symptom:** ops work but crawl.

**Cause:** `dolt_mode != "server"` — gc fell off the native in-process store
onto per-op `bd` subprocess calls (the documented perf cliff). Usual root:
bd version doesn't exactly match gc's linked beads library.

**Fix:** re-check the version contract, then confirm
`bd context --json | jq .dolt_mode` == `"server"` and `gc status --json`
shows `NativeDoltStore`.

## 8. Pack clone / `gc import install` hangs ~151 s

**Symptom:** network git spawned by gc hangs ~151 s to github.com (host
quirk: rtk/homebrew-git parent-process signature).

**Fix:** git shim — `$GC_HOME/bin/git -> /usr/bin/git`, first on PATH via
`env.sh`. For pack iteration, a local read-in-place path import avoids the
network entirely.

## 9. Reviewer keeps refuting on file placement — unwinnable redo loop

**Symptom:** a lane raises "file outside <quest-dir>/" (or similar
path-frame findings) on a file that is correctly placed; bounded redo would
burn all attempts without converging.

**Cause:** diff-frame mismatch — the review diff is quest-repo-relative while
the contract non-goal is written city-relative (or vice versa).

**Fix:** fix the CONTRACT's frame (one consistent frame), re-sling. Don't
spend redo attempts on it; it's a contract bug, not a build bug.

## 10. `gc costs` empty / `gc analyze reliability` shows 0 sessions

**Not a fault.** Sub-backed providers emit no usage facts (`usage.jsonl`
absent) and production paths don't emit `session.quarantined`. Known upstream
gaps — never gate on these surfaces.

## Escalation order when nothing above matches

1. `gc doctor --json` — a failing check usually names the subsystem.
2. `gc events` tail around the last state change (`run_id` correlation).
3. `gc session logs <session>` for the wedged lane.
4. Supervisor: `ps aux | grep 'gc supervise'`, the launchd unit's plist
   (match by its GC_HOME string), `gc service restart` as the deliberate move.
5. If it smells like an engine bug: minimal repro, then a `.patch` on the
   fork's thin patch branch + upstream issue — never a divergent private fork.
