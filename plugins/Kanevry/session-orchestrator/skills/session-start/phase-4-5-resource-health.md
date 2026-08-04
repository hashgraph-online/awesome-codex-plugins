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

The `evaluate()` result has three fields:
- `verdict`: `green` | `warn` | `critical`
- `reasons`: array of human-readable explanations
- `recommended_agents_per_wave_cap`: integer cap (0 = coordinator-direct) or null

The third `options` argument is optional (HR-003/HR-004, baseline #60) — when `config['heavy-repo']` is `true`, the cap is forced to at most `config['agents-per-wave']` regardless of the live verdict (static preflight ceiling; more-restrictive-wins against whatever the resource signals already computed). Omitting `options` entirely preserves pre-#60 behaviour.

## Adaptive Rules (default thresholds; configurable via `resource-thresholds`)

| Signal | Threshold | Action |
|--------|-----------|--------|
| RAM free below `ram-free-min-gb` (default 4) | warn | Cap `agents-per-wave` at 2 |
| RAM free below `ram-free-critical-gb` (default 2) | critical | Recommend coordinator-direct (0 agents) |
| CPU load above `cpu-load-max-pct` (default 80) sustained — judged on **min(1m, 5m)** load average (#943) | warn | Cap `agents-per-wave` at 2 |
| Claude processes ≥ `concurrent-sessions-warn` (default 5) | warn | Warn; suggest sequencing or waiting |
| SSH session detected AND `ssh-no-docker: true` | info | Append note: host is SSH-attached, Docker-dependent steps should run on a local dev host |

**CPU methodology (#943):** the gate/probe runs right after the coordinator's own CPU-saturating quality-gate run by construction, so the 1-minute load average systematically carries that decaying tail (observed: 96% → 75% within 36s). `probe()` therefore also emits `cpu_load_5m` / `cpu_load_5m_pct`, and `evaluate()` + `evaluateWaveResourceGate()` judge the CPU threshold on **min(1m, 5m)**: only-1m-high is reported as an informational "decaying transient" reason without capping; both-high (genuine sustained load) still caps. When `cpu_load_5m_pct` is `null` (Windows, zero-load), judging falls back to the 1m-derived `cpu_load_pct` alone.

## Presentation

Print a one-line Resource Health verdict immediately after Phase 4's output:

```
Resource Health: ⚠ warn — RAM free 3.1 GB below threshold 4 GB; capping agents-per-wave at 2.
```

When `config['heavy-repo']` is `true` and the HR-004 preflight ceiling actually reduces `recommended_agents_per_wave_cap` below what the live verdict alone would have produced, print an additional banner line right after the verdict line:

```
⚠ Heavy-repo mode active — agents-per-wave capped to 4 (Session Config heavy-repo: true)
```

When verdict is `warn` or `critical`, use the AskUserQuestion tool to present:
1. **Proceed as recommended** (apply the cap) — Recommended
2. **Proceed as originally planned** (user accepts the risk)
3. **Abort** (no wave planning runs; user closes or investigates)

When SSH is detected and the session type is `deep`, auto-append this note to the plan handoff to session-plan (no user prompt needed):
> Host is SSH-attached — Docker-dependent wave steps should run on a local dev host.

## Integration with session-plan

When Phase 4.5 recommends a cap, pass that cap into the session-plan handoff. session-plan honors the cap by reducing `agents-per-wave` for the upcoming plan, regardless of what the Session Config default says. This is an in-session override, not a config mutation.
