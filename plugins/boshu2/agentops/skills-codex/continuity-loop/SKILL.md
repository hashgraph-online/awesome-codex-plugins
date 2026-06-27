---
name: continuity-loop
description: 'Own the unattended renewal spine: renewal'
---
# $continuity-loop — The Unattended Renewal Spine

This skill owns the renewal contract behind the live multi-agent substrate the
repo CLAUDE.md declares: **NTM panes + MCP Agent Mail + renewal ticks**. It does
not run agents and it does not schedule anything — it defines what a tick is,
what every supervised lane must do per tick, how a stall is detected, and when a
stall becomes an escalation. Loop skills compose it; they do not reimplement it.

**Use when:** a loop skill needs a continuity step, a lane looks dead and you
need a verdict (suspect / stalled / converged), or you are deciding whether to
nudge, relaunch, or escalate.

## ⚠️ Critical Constraints

- **This skill is a contract, not a scheduler** — because AgentOps 3.0 ships no
  daemon. Tick firing is owned by host timing (cron, systemd user timer, or
  the operator tending loop); a substrate that owns its own clock drifts from
  the hookless doctrine.
- **`.agents/continuity/state.json` is the only continuity state surface,** because
  two state surfaces guarantee a split-brain stall verdict; every consumer
  reads and renews the same file.
- **Two ticks before any stall verdict** — because a single tick cannot
  distinguish a slow tool call from a wedge. One missed renewal marks a lane
  SUSPECT, never STALLED; acting on one tick produces nudge-storms that kill
  healthy lanes.
- **Escalation is a message, never a silent kill,** because the tender and the
  operator must see the same evidence trail; a killed pane with no Agent Mail
  record is indistinguishable from a crash.
- **Never route continuity through `rpi` or `bd` — retired legacy** — to prevent
  reviving a SPOF the substrate already paid to remove: the in-session ao-rpi
  loop is retired as the live workflow and bd/Dolt was retired 2026-06-11 (see
  [Retired legacy](#retired-legacy-explicitly-not-live)).
- **Healthy lanes are left alone,** because interruptions reset agent context —
  a lane renewing on cadence gets no nudge, no message, no restart; the
  intervention IS the failure mode when the lane was fine.

## What a renewal tick is

A **renewal tick** is one bounded observation pass over the supervised lanes:
read each lane's pane activity (NTM robot state) and Agent Mail traffic, decide
per lane whether forward progress happened since the last tick, and renew that
lane's entry in the state surface. A tick observes and records; intervention is
a separate decision the tick's output feeds.

Forward progress evidence (any one suffices):

| Signal | Source |
|---|---|
| New pane output delta since last tick | NTM pane/robot state |
| New Agent Mail message or reservation activity | `am` inbox / reservations |
| Lane self-renewed its `state.json` entry | the state surface |
| Work-product delta (commit, closed item, new artifact) | git / tracker / `.agents/` |

## Tick cadence and the renewal contract

- **Default cadence: one tick per 10 minutes** of unattended operation; tighten
  for short-lived swarms, loosen for overnight runs. Cadence lives in the host
  timer, and is recorded in `state.json` so consumers can compute staleness.
- **Renewal contract:** every supervised lane gets its `last_renewal` and
  `tick_seq` advanced each tick — either self-renewed by the lane or renewed by
  the tender on observed evidence. An entry whose `tick_seq` is behind the
  global tick counter by one is SUSPECT; behind by two or more is STALLED.
- A lane that finishes cleanly is marked `converged` and leaves supervision; it
  is never reported as stalled.

## Stall detection — the two-tick rule

1. **Tick N:** no forward-progress evidence → mark lane `suspect`. No action.
2. **Tick N+1:** still no evidence → mark lane `stalled`. Now intervene, in
   order: one nudge → if the next tick shows no recovery, relaunch the lane and
   route it through [recover](../recover/SKILL.md) → if the relaunched lane
   stalls again on the same work item, escalate.
3. Any forward-progress evidence at any point resets the lane to `active`.

## State surface

**Path:** `.agents/continuity/state.json` — single file, renewed in place per
tick (write temp + rename).

```json
{
  "schema": "continuity-state.v1",
  "tick_seq": 42,
  "cadence_minutes": 10,
  "last_tick": "2026-06-12T14:30:00Z",
  "lanes": [
    {
      "lane": "ntm:agentops:pane-3",
      "agent": "claude-worker-3",
      "work_item": "ag-xxxx",
      "status": "active",
      "tick_seq": 42,
      "last_renewal": "2026-06-12T14:30:00Z",
      "evidence": "am message 2026-06-12T14:28Z; pane delta +214 lines"
    }
  ]
}
```

`status` ∈ `active | suspect | stalled | converged | escalated`. Every status
change cites its evidence string — a bare status flip is invalid.

## How loop skills route their continuity step here

- **[evolve](../evolve/SKILL.md)** — its halt/handoff machinery (non-sticky
  HANDOFF, context exhaustion is not a stop) maps onto the tick contract: a
  handoff written this tick is forward-progress evidence, and the next tick
  expects the resumed lane to renew. Evolve consults `state.json` instead of
  inventing its own liveness probe.
- **[using-atm](../using-atm/SKILL.md)** — the ATM tending loop is the
  reference **tick executor**: each tending pass over the panes is one renewal
  tick, and its nudge/relaunch/re-dispatch triggers are the intervention ladder
  this skill sequences. Pane-truth beats roster state when they disagree.
- **[recover](../recover/SKILL.md)** — the re-entry adapter. A relaunched lane
  runs recover to rebuild context, then renews its `state.json` entry; that
  renewal closes the stall.

## Escalation criteria

Escalate (Agent Mail message to the operator/tender lane + lane status
`escalated`) when any of these hold:

- Two-tick stall that survived one nudge **and** one relaunch.
- The same work item stalls two different lanes (the work is poisoned, not the lane).
- Auth or rate-limit failure that account rotation did not clear.
- A file-reservation conflict on the lane's write surface (route to agent-mail
  coordination, not to a retry).
- A lane is re-doing work its own `evidence` trail shows complete (loop without
  progress — context saturation).

## Retired legacy (explicitly NOT live)

- **The in-session ao-rpi loop** — retired as the live workflow. Its run
  directories are not a continuity surface; do not write renewal state there.
- **bd/Dolt tracker liveness** — retired 2026-06-11. Tracker reachability is
  not a lane-liveness signal and `state.json` never syncs into it.

Both are listed here only so nobody routes a continuity step back into them.

## Output Specification

**Format:** JSON file (`continuity-state.v1`, shown above) renewed atomically
each tick, plus an Agent Mail escalation message when a lane reaches `escalated`.
**Path:** `.agents/continuity/state.json`, written to in place (temp + rename);
escalations go to the operator/tender lane via `am`.
**Exit signal:** a tick reports `lanes: N active / N suspect / N stalled /
N converged` to the tender.

## Quality Rubric

- [ ] No stall verdict was issued on a single missed tick (two-tick rule held)
- [ ] Every status change in `state.json` carries an evidence string
- [ ] Escalations exist as Agent Mail messages, not just status flips
- [ ] No continuity state was written outside `.agents/continuity/state.json`
- [ ] No live-path reference to rpi or bd anywhere in the continuity step

## See Also

- [using-atm](../using-atm/SKILL.md) — the reference tick executor (ATM tending loop)
- [vibing-with-ntm](../vibing-with-ntm/SKILL.md) — pane-level liveness truth and unsticking
- [agent-mail](../agent-mail/SKILL.md) — the message + reservation leg escalations ride on
- [evolve](../evolve/SKILL.md), [recover](../recover/SKILL.md) — loop consumers of this contract
- [handoff](../handoff/SKILL.md) — what a context-saturated lane writes before relaunch
