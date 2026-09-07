# Phase 4.5: Resource Health (v3.1.0)

> Skip this phase if `resource-awareness: false` in Session Config.

Read `.orchestrator/host.json` (written by `hooks/on-session-start.mjs`) and run a live resource snapshot. Compare against `resource-thresholds` from Session Config to derive an adaptive wave-sizing recommendation before session-plan runs.

## Probe + Evaluate

```js
// Conceptual — the wave-executor and session-plan skills call these directly.
import { probe, evaluate } from '$PLUGIN_ROOT/scripts/lib/resource-probe.mjs';
const snapshot = await probe();
const verdict = evaluate(snapshot, config['resource-thresholds'], {
  heavyRepo: config['heavy-repo'],
  agentsPerWave: config['agents-per-wave'],
});
```

The `evaluate()` result has four fields:
- `verdict`: `green` | `warn` | `critical` (the `degraded` tier is no longer produced)
- `reasons`: array of human-readable explanations, including `info:`-prefixed
  lines for signals that were seen but deliberately not acted on
- `recommended_agents_per_wave_cap`: integer cap (0 = coordinator-direct) or null
- `signals`: `{ hard: string[], soft: string[] }` — which axes fired (#1089)

The third `options` argument is optional (HR-003/HR-004, baseline #60) — when `config['heavy-repo']` is `true`, the cap is forced to at most `config['agents-per-wave']` regardless of the live verdict (static preflight ceiling; more-restrictive-wins against whatever the resource signals already computed). Omitting `options` entirely preserves pre-#60 behaviour.

## Adaptive Rules (rebuilt in #1089 — see `.claude/rules/host-resources.md`)

The rule set is **signal precedence + the two-signal rule**, not a list of
independent thresholds ORed together. Measured 2026-08-21 over 1477
`orchestrator.session.started` events across 18 repos, the previous OR-of-three
produced warn-or-worse on **99.0%** of session starts — a warning that fires
almost always changes no decision except how fast it gets ignored.

**Memory — judge on the best signal present, never on a worse one:**

| Precedence | Signal | Hard (→ critical) | Soft |
|---|---|---|---|
| 1 | `memory_pressure_pct_free` (macOS) | `< 15%` | `< 30%` |
| 2 | `ram_available_gb` (macOS, vm_stat) | `< ram-free-critical-gb` | `< ram-free-min-gb` |
| 3 | `ram_free_gb` (`os.freemem`) | same | same |

Level 3 is reached only when neither better signal exists — i.e. on
Linux/Windows, where `os.freemem()` is accurate. On Darwin it reports `Pages
free` only (median **0.4 GB** across the corpus, on 24-128 GB hosts), so gating
on it there fired the *critical* threshold on 84.0% of starts.

**Other axes:**

| Signal | Threshold | Class |
|---|---|---|
| CPU, judged on **min(1m, 5m)** (#943) | above `cpu-load-max-pct` (default 90) | soft |
| Live peer **sessions** from the registry | ≥ `concurrent-sessions-warn` (default 5) | soft |
| Claude **processes** (fallback only, registry unreadable) | ≥ threshold × 6 | soft |
| Swap, **only while memory is unhealthy** | `> 3072 MB` hard / `> 1024 MB` soft | both |
| Zombie processes with a live peer/process context | ≥ 1 | **info** (reported, never counted — see HR-104) |
| SSH detected AND `ssh-no-docker: true` | — | info note |

**Verdict composition:**

- any **hard** signal → `critical`, recommend coordinator-direct (0 agents)
- **two or more independent soft** signals → `warn`, cap agents-per-wave at 2
- exactly **one soft** signal → `green`, reported in `reasons`, **no cap**
- none → `green`

`evaluate()` additionally returns `signals: { hard: [...], soft: [...] }` so a
caller can log which axes fired rather than re-deriving them from prose.

**Unit note (#1089):** `concurrent-sessions-warn` is denominated in SESSIONS. It
was compared against `claude_processes_count` until this rebuild — a measured 6x
unit error (median processes:sessions = 6.0 over 1461 paired samples) that made
the threshold fire on 93.6% of starts instead of 4.2%. `probe()` now supplies
`peer_sessions_count` from the session registry (`detectPeers()`, self excluded,
heartbeat-fresh); the rescaled process count is a fallback for hosts where the
registry is unreadable.

**CPU methodology (#943):** the gate/probe runs right after the coordinator's own
CPU-saturating quality-gate run by construction, so the 1-minute load average
systematically carries that decaying tail (observed: 96% → 75% within 36s).
`probe()` therefore also emits `cpu_load_5m` / `cpu_load_5m_pct`, and both
`evaluate()` and `evaluateWaveResourceGate()` judge CPU on **min(1m, 5m)**:
only-1m-high is reported as an informational "decaying transient" and is NOT
counted as a signal at all — so it cannot become the second signal that triggers
a cap. When `cpu_load_5m_pct` is `null` (Windows, zero-load), judging falls back
to `cpu_load_pct` alone.

## Presentation

Print a one-line Resource Health verdict immediately after Phase 4's output:

```
Resource Health: ⚠ warn — two signals agree (cpu + concurrency); capping agents-per-wave at 2.
```

On `green` with a reported signal, print the line but say plainly that nothing
was capped — a bare signal with no consequence reads as a suppressed warning:

```
Resource Health: ✓ green — 6884 MB swap present but memory_pressure healthy (53% free); no cap.
```

When `config['heavy-repo']` is `true` and the HR-004 preflight ceiling actually reduces `recommended_agents_per_wave_cap` below what the live verdict alone would have produced, print an additional banner line right after the verdict line:

```
⚠ Heavy-repo mode active — agents-per-wave capped to 4 (Session Config heavy-repo: true)
```

**AUQ only on `critical`** (#1089). A `warn` applies its cap and reports it in
one line — it does not interrupt. Under the previous rule set warn-or-worse was
the verdict on 99.0% of session starts, so an AUQ here was an operator interrupt
on essentially every session, which `.claude/rules/ask-via-tool.md` AUQ-005
names outright ("an AUQ that blocks nothing"). `critical` means coordinator-direct
— zero agents — which genuinely changes the plan, so it earns the prompt:

1. **Proceed coordinator-direct** (0 agents) — Recommended
2. **Proceed as originally planned** (operator accepts the risk)
3. **Abort** (no wave planning runs; operator closes or investigates)

When SSH is detected and the session type is `deep`, auto-append this note to the plan handoff to session-plan (no user prompt needed):
> Host is SSH-attached — Docker-dependent wave steps should run on a local dev host.

## Integration with session-plan

When Phase 4.5 recommends a cap, pass that cap into the session-plan handoff. session-plan honors the cap by reducing `agents-per-wave` for the upcoming plan, regardless of what the Session Config default says. This is an in-session override, not a config mutation.
