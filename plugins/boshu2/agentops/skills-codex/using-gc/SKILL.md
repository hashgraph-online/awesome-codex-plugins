---
name: using-gc
description: Drive a Gas City (gc) factory day-to-day —
---
# Using Gas City — the operator loop

Gas City (`gc`, the gastownhall/gascity engine) is a **blessed, coexisting
orchestration substrate** for city-shaped work: durable agents in their own tmux
sessions, work as beads in a gc-managed bd/dolt store, an orchestrator that
spawns/retries/drives formula graphs *outside your session* and survives your
session dying. AgentOps composes its **verification membrane** on top as the
`agentops-membrane` pack — the fail-closed, cross-family, verdict-bound close
door stock gc lacks (see [`gc-membrane`](../gc-membrane/SKILL.md)).

**Settled doctrine:** *stock gc is the substrate; AgentOps is the membrane.*
Use gc's orchestration wholesale (store, DAG, worktrees, pools, orders,
dashboard, doctor). Never rebuild it. The membrane is the one add-on.

**Boundaries (hard constraints):**
- gc coexists BESIDE NTM/`ao` — it is NOT a swap for NTM and there is no
  `runtime=gc` in AgentOps (severed, soc-2rtm0). No gc subcommand lives under
  the `ao` CLI, ever. This skill routes to **gc's own native surface**
  (`gc status --json`, `gc events`, `gc doctor --json`, `gc session …`) and
  never wraps it.
- **LAW 0 applies inside a city**: gc's builtin claude provider defaults to
  `print_args = ["-p"]` (headless title-gen + `gc prompt` sinks). Every city
  MUST set `[providers.claude] print_args = []` (and the same on
  `antigravity`), guarded by the `law0-print-args` doctor check.
- **The membrane never merges.** CONFIRMED closes the quest bead; a human
  merges the branch. No convenience crosses that line.

## When to use / when to skip

**Use:** standing up a city; slinging and tending quests; a lane is stalled,
wedged, or draining; reading verdicts; city admin (doctor, orders, backup,
binary rebuild); deciding whether a city is healthy.

**Skip:** in-session parallel fan-out (→ `swarm`); unattended bead-queue work
on our own swarm substrate (→ `using-atm`); choosing an automation shape at
all (→ `automation-shape-routing`). City-shaped multi-quest work is an
**operator choice**, not an auto-route.

## The four jobs (JIT references)

| Job | Read | You're done when |
|---|---|---|
| **Stand up** a correct city | **`scripts/install-gc-city.sh <city-dir>`** (one command; automates + enforces the whole contract — fail-hard version pins, native store, LAW-0, gap-A materialization, sessions verified, doctor gate). Manual fallback: [`references/standup.md`](references/standup.md) | `gc doctor` green incl. `law0-print-args` + `membrane-health`; `gc status --json` shows `NativeDoltStore` |
| **Run** the quest loop | this file, below | quest bead closed on CONFIRMED; human merged |
| **Admin** a running city | [`references/admin.md`](references/admin.md) | doctor green cadence; backups; binary current |
| **Troubleshoot** a stall | [`references/troubleshooting.md`](references/troubleshooting.md) | the symptom row's move resolved it |

## The day-to-day loop

All commands assume the city env: `source <city>/env.sh` (sets `GC_HOME`, PATH
shim, `gc` wrapper). Never operate a city with a bare `gc` against the wrong
`GC_HOME` — check `gc status` header names YOUR city.

**1. Shape the quest (move 1 — intake).** A quest = a slug dir with a
default-FAIL acceptance contract. Scaffold deterministically:

```bash
membrane/scaffold-quest.sh <slug> --ask "<one-line build ask>"   # CONTRACT.md (default-FAIL), test.sh (red), impl.sh placeholder
```

The builder never reads `CONTRACT.md` (the gate reads it from `main` only);
the builder reads `test.sh`. Write the contract in city-relative *or*
quest-relative frame consistently — frame mismatch produces unsatisfiable
review findings (see troubleshooting §9).

**2. Sling it.** One motion creates the work and routes it:

```bash
gc sling agentops-membrane.builder "<quest title>" --on membrane-quest \
  --var quest=<slug> --var task="<build task text>"
```

(Text-sling creates the quest bead from the title and attaches the workflow —
no separate `bd create` needed.)

The reconciler spawns the builder session on its own tick (healthy: ~10–15 s).
Nothing to babysit — the control dispatcher advances the workflow.

**3. Watch through gc's native surface (never poll panes):**

```bash
gc events --follow            # live stream; run_id/step_ref correlate a quest
gc status --json | jq .beads  # store health: NativeDoltStore + eligible
gc doctor --json              # full health; membrane checks included
tmux -L <socket> ls           # session inventory (read-only glance)
```

**4. The close gate fires on the check step.** The control dispatcher (not an
agent) runs `membrane/close-gate.sh`: routes ONLY diff + contract to ≥2
cross-family reviewer lanes via `gc session submit`, then the deterministic
finalizer rules:

| Disposition | What happens |
|---|---|
| CONFIRMED | gate closes the ralph step with the ENGINE fingerprint; workflow finalizes pass; **human merges** |
| REFUTED (hard) | builder respawned with the findings — bounded self-redo |
| DEGRADED (transient) | lane retried; never converted into a false REFUTE |

**Attempt semantics (native graph.v2, corrected 2026-07-06):** gc's dispatcher
never reads `gc.failure_class` on this path — **EVERY failed check consumes one
of `max_attempts` (now 5)**, transient DEGRADED included. Budget = ~2 transport
flakes + 3 real refute rounds. The `failure_class` stamp is evidence for
humans, not retry-budget control.

**Never touch a bead with `gc.kind=ralph`** — that is the engine-owned gate
bead (it shares the build step's title). An agent closing it bypasses the
membrane entirely; the fork finalizer rejects such closes (engine attempt_log
fingerprint required), and the formula's recovery snippet filters it, but the
rule stands for humans too.

**5. Read the verdict** at `<city>/membrane/<quest>/pawl-verdict.json`
(schema `pawl-verdict.v1`; per-round history at `pawl-verdict-round-N.json` +
`lane-<family>-round-N.json`): check `disposition`, `refuters[].family` (must
be ≥2 distinct families for CONFIRMED), `nonce` (anti-replay), findings.
On REFUTED, the redo path is automatic — **never hand-close the quest bead**.

**Observability gotcha:** the check path emits ZERO `gc events` — watch the
ralph gate bead's `gc.attempt_log` metadata (one entry per round, gate log
embedded), or set `GC_WORKFLOW_TRACE=<file>` for the dispatch trace. The check
runs in the SUPERVISOR process, so workspace env does not reach it; supervisor
plist env does.

**Lane failover (degraded-diversity mode):** if the agy/gemini lane is dead
(auth outage), keep the quorum at 2 distinct REVIEWER families with the
pack's `opus-verifier`, a fresh-context claude lane. Explicit tradeoff: one
reviewer then shares the BUILDER family (the default posture excludes it);
session isolation still gives author≠judge, and it beats single-family review
or burning attempts on DEGRADE. Temporary — restore agy when healed. Set `[workspace.env] MEMBRANE_LANE2_TARGET = "agentops-membrane.opus-verifier"`
+ `MEMBRANE_LANE2_FAMILY = "claude"`, add its `[[named_session]]`, and bounce
the supervisor. Restore agy when healed — three families beat two.

**Roll outcomes into the tracker** (read-only, never a sync):
`scripts/gc-outcomes-report.sh <city>` — closed work with outcomes/commits +
open work; paste relevant lines into a bead note.

**6. Converge.** A run has converged when: quest bead CLOSED on CONFIRMED,
verdict artifact valid, branch handed to a human. A run has **stalled** when a
lane sits idle across a round transition — go straight to the
[troubleshooting ladder](references/troubleshooting.md); the two moves that
matter most are non-obvious:

- **A draining/idle interactive pane is recovered ONLY by
  `gc session submit <target> <text>`** — `gc session kill`, `reset`, and raw
  tmux send-keys all fail. If the pane is busy and doesn't consume the submit,
  Esc-interrupt it, then submit again.
- **A codex/agy lane wedged at startup is the provider trust modal** —
  pre-trust via a city-scoped `CODEX_HOME` seed (codex) or one interactive
  provider run (agy). Until cleared the lane DEGRADES (correctly — never a
  false REFUTE).

## Non-goals

Don't wrap or re-implement `gc events`/`gc costs`/`gc doctor`/`gc dashboard`/
`gc session`/`gc mail` — point at them. Don't build stall-detection infra (gc
orders + events + dashboard already do it; the membrane keepalive order is the
one addition). Don't gate anything on `gc costs` (usage facts are absent for
sub-backed providers — it would fail-open). Don't auto-merge, ever.

## Scenarios

```gherkin
Scenario: Recover a stalled reviewer lane
  Given a membrane city whose reviewer pane sits idle in draining and the round is not advancing
  When the operator runs gc session submit <lane> with a keepalive line
  Then the pane consumes the delivery and the round advances
  And gc session kill, gc session reset, and raw tmux send-keys were never used

Scenario: Stand up a correct native city
  Given a host with bd matching gc's linked beads library and dolt at the managed floor
  When the operator follows references/standup.md end to end
  Then bd context reports dolt_mode server and gc status --json reports NativeDoltStore
  And gc doctor is green including law0-print-args and membrane-health

Scenario: A REFUTED verdict routes to bounded redo, not a manual close
  Given a quest whose pawl-verdict.json shows disposition REFUTED
  When the operator reads the verdict
  Then the builder respawn consumes one bounded attempt and the quest bead is never hand-closed

Scenario: The gate bead is engine-owned
  Given a workflow whose ralph gate bead shares the build step title
  When any agent or operator identifies their step bead
  Then beads with gc.kind=ralph are excluded and never closed by hand
  And a gate bead closed without the engine attempt_log fingerprint cannot finalize the workflow as pass
```
