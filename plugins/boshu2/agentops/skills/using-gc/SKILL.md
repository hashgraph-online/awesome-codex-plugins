---
name: using-gc
description: 'Operate Gas City through its own doors: Mayor, doctor and native run state. Use when: Gas City is selected or a gc run looks stuck.'
practices: [team-topologies, design-by-contract]
hexagonal_role: driving-adapter
consumes: [accepted-intent]
produces: [gas-city-runtime-evidence]
context_rel:
- kind: supplier-to
  with: orchestrate
skill_api_version: 1
user-invocable: true
metadata:
  tier: execution
  dependencies: []
  capabilities: [observe_gc_runtime, inspect_pack_registries, drive_mayor_door]
  effects: [operate_gas_city, configure_codex_trust]
  canonical_status: canonical
  disposition: keep_optional_adapter
output_contract: Gas City run, bead, session and pane state read through its own surfaces; never an AgentOps verdict
---

# Using GC

Use Gas City only when the caller explicitly selects it. It is a replaceable
execution adapter whose completion is never AgentOps acceptance or delivery
proof; [Orchestrate](../orchestrate/SKILL.md) owns that rule for every factory.
If the caller selects the [Agentic Coding Flywheel](https://agent-flywheel.com)
instead, follow its [native workflow](https://agent-flywheel.com/complete-guide).

## The operator lane

While a city runs work, the operator lane into it is a closed set:

- author source intent beads;
- `gc mail` to the Mayor, for work dispatch and for city tending;
- `gc session wake <session-id-or-alias>`, once, for a routed bead whose worker
  stalled: the session holding the bead (its assignee in `gc bd show <id> --json`,
  or its row in `gc session list --json`), never the bead's routing target;
- `gc doctor [--fix]`, and supervisor start/stop from outside the city;
- `ao gc prepare|check|recover-affinity`;
- reading run, session, bead, pane and artifact state.

Installing packs, upgrading, and retiring a city (`gc import`, `gc pack
registry`, `gc start|stop`, `gc unregister`) are operator setup actions taken
outside any run, never a way into running work.

The Mayor authors workflow beads and dispatches them; it owns retries,
re-dispatch and tending for that work. Never create, scale or repair pack-owned
sessions by hand: `gc session new` for a singleton or scaled agent
(`core.control-dispatcher`, role workers) makes a mis-scoped session that
squats the canonical name in `start-pending` and blocks the reconciler from
spawning the real one. Session lifecycle belongs to the reconciler and demand
scaling. Direct `gc sling` is a debugging tool for a city with no live Mayor; a
run started that way has no coordinator, and the operator inherits its tending.

## Version facts

Re-checked 2026-10-25: `--help` for every `gc` command here on the installed
`edge` build (commit 97503b2, built 2026-07-30; `gc bd` needs a city), and
Gas City v1.5.1 (2026-10-24, current stable) docs and source for wake, import,
the status API line, the run census and trust dialogs. The `gascity` pack pin
is release 0.1.6, commit `3b3b89f2011e06d84459aa7bea1552382f13930a` (still the
latest registry release), which `ao gc` enforces. If a later build's `--help`
disagrees with this skill, the help wins; report the drift.

## Operating model

Gas City 1.4 and later are run-centered. The supervisor serves the dashboard and
typed, paginated session/run APIs. Every graph-owning city or rig scope needs
its own `core.control-dispatcher`, the deterministic worker that advances
formula control beads; agent workers claim routed work. The upstream `gc.mayor`
skill is the guided coordinator; `gc.run-operator` launches and supervises
formulas. AgentOps needs no Gas City formula or role pack of its own: workers
find `plan`, `implement`, `test`, `validate` and the other AgentOps skills once
they are installed in the provider runtime (`ao gc prepare` links them into the
city and rig Codex sinks).

## Install the pack

Import the official `gascity` workflow pack at city scope and its roles pack on
every rig that runs work, both bound as `gc` and both at the pin above:

```sh
gc import add https://github.com/gastownhall/gascity-packs/tree/main/gascity \
  --name gc --version sha:3b3b89f2011e06d84459aa7bea1552382f13930a
```

```toml
[[rigs]]
name = "<rig>"   # the entry `gc rig add` wrote, in city.toml

[rigs.imports.gc]
source = "https://github.com/gastownhall/gascity-packs/tree/main/gascity/roles"
version = "sha:3b3b89f2011e06d84459aa7bea1552382f13930a"
```

Then `gc import install` resolves both into `packs.lock`. The binding name
qualifies agent and skill names, so it must be `gc`. The command that
`gc pack registry show main:gascity` prints binds `--name gascity` and adds no
roles import: that yields `gascity.mayor`, leaves the `gc.*` formula routes with
no rig roles, and fails `ao gc check`, which requires the rig import
`rig:<rig>:gc`. Keep the stock `gc.*` namespace; do not nest or rename the roles
behind an AgentOps pack. Other packs, the optional community registry, upgrading
a city to 1.5.x (including a stale registered city that blocks every start) and
retiring one are in [Setup, upgrade and retirement](references/upgrade-and-retire.md).

## Prepare and check a rig

Prepare and qualify a rig before its first build with the shipped AgentOps
CLI (no repo checkout required):

```sh
ao gc prepare --city /path/to/city --rig /path/to/rig
ao gc check --city /path/to/city --rig /path/to/rig
```

`prepare` verifies the exact official workflow and role pins, stages a
contained maintainer runtime inside the rig's `.gc` directory, links the
AgentOps skills into the city and rig Codex sinks, and pre-seeds Codex
workspace and hook trust for every session directory that exists when it runs.
Hook trust needs the Codex CLI on PATH (or `--codex-bin`). `check` is
read-only, runs no Codex subprocess, and fails before model spend when that
runtime contract is missing or drifted.

Run `prepare`, start the city, then run `prepare` again (it is idempotent)
before dispatching. Two limitations make that order necessary: `check` cannot
see a stale trust hash, so green means trust is recorded, not fresh; and a
session home created after `prepare` is not covered.
[Codex trust pre-seed](references/codex-trust-preseed.md) has the mechanism.

## Hand work to the Mayor

Work enters the city through the Mayor. The caller authors ONE source intent
bead with acceptance, then hands the Mayor its id; the Mayor decomposes,
authors the workflow beads, and dispatches.

```sh
gc bd create "Add a --json flag to the export command"
gc mail send mayor -s "Build ago-XXXX" \
  -m "Decompose and launch build-basic for bead ago-XXXX with push=false open_pr=false." --notify
```

Pass `push=true open_pr=true` only when the caller and the repository's
delivery policy authorize publishing; otherwise the approved commit stays in its
source anchor worktree. In an interactive Mayor session, `Use skill gc.mayor`
does the same.

AgentOps skills are tools for the factory's agents, not a replacement workflow.
The upstream decomposition does not carry a free-form `Required Skills` section
from the source bead into the generated work items, so when a skill's use is an
acceptance condition, inspect the decomposition and name the skill on the
actual work item or worker prompt. Skill presence and skill invocation are
different facts.

## Orchestrating through the Mayor: the tending loop

After handing intent to the Mayor, the orchestrator runs five verbs, each with
one owner; crossing owners is the recurring failure this section stops.

| Verb | Owner | Surface |
|---|---|---|
| Monitor | orchestrator | `$API/runs/census` and `$API/runs/<run-id>` on a fixed cadence, with `$API` built from the `API:` line of `gc status` (Visibility, layer 1), plus `gc mail inbox` for Mayor replies. `failed > 0` in the census, a run in `failed`/`canceled`, or unread Mayor mail is the act signal; everything else is a tick. |
| Observe | orchestrator | On an act signal, walk the visibility layers below in order and stop at the first that explains. Do not start at pane truth. |
| Nudge | orchestrator, once | The stall protocol below. |
| Redirect | Mayor | Priority, scope, cancellation, or model/provider changes travel by mail with bead/run ids. The orchestrator never re-slings, edits workflow beads, or patches a live run. |
| Rework | GC first, then Mayor | Failed review findings re-enter the run through its native fix loop (`review_fix_formula`, default `fix-loop-base`); bounded gated retries are `gc converge` loops. Only a TERMINAL `failed`/`canceled` run — or a completed run whose result misses caller acceptance — goes back: mail the Mayor the run id and the failure evidence for re-decompose and relaunch. |

Rework the orchestrator performs by hand (editing a failed run's worktree,
re-slinging its formula, closing its beads) creates a second uncoordinated
author for the same intent; the Mayor's relaunch then races it.

## Stall protocol

First classify the bead.

- Still `ready`, never dispatched: dispatch belongs to the Mayor. Mail it the
  bead id, then stop and inspect. Only with no live Mayor is
  `gc sling <target> <bead-id>`, once, the debugging fallback, where `<target>`
  is the bead's `gc.routed_to` (`gc.run_target` on older beads); the operator
  then inherits that run's tending.
- Already routed/in progress: re-slinging is a **NO-OP**. Wake the session that
  holds the bead (its assignee) once:

  ```sh
  gc session wake <session-id-or-alias>
  ```

Then capture the exact tmux pane named by session state and run `gc doctor`.
Never repair a city from inside that city. Never answer a stall with
`gc session new`; the operator lane above explains why.

A second nudge on the same subject means the diagnosis is wrong. When one wake
does not clear the stall, or the city itself needs tending (a stalled
reconciler, sessions that never leave draining, model or provider rewiring),
send the request to the Mayor with the bead or run ids:

```sh
gc mail send mayor -s "<subject>" -m "<request with bead ids>" --notify
```

The upstream pack may leave a future affinity-bound step assigned to a session
that has already drain-acked. Diagnose this only from outside the city:

```sh
ao gc recover-affinity --city /path/to/city --rig /path/to/rig
```

The default is a dry run. If every listed assignment is correct, repeat with
`--apply`. The bounded repair only clears the assignee on a currently ready
formula bead whose `gc.session_affinity=require` session is no longer live. It
does not sling, retry, close, restart, or select work.

## Visibility: four layers

1. **Supervisor/run state** — `gc dashboard`, run detail, `gc status`, and
   `gc session list --json`. Run detail unifies the stage ladder, structured
   transcripts, token rate, and estimated burn rate. A roster may still report
   active while a provider is wedged. Programmatic run status comes from the
   supervisor's typed run API, the same data the dashboard renders; `gc status`
   prints its base on the `API:` line, and no CLI subcommand (`gc status --json`
   included) carries run objects.

   ```sh
   API="http://127.0.0.1:<port>/v0/city/<city-name>"
   curl -s "$API/runs/<run-id>"   # .status: failed or canceled is terminal
   curl -s "$API/runs/census"     # .status_counts.failed > 0 is the first failure signal
   ```

   The dashboard's run page (`/city/<city-name>/runs/<run-id>`) is the human
   view of the same objects.
2. **Bead graph** — `gc bd --rig <rig> ready --json` and `show <id> --json`.
   This is workflow-state truth, but a claimed bead cannot reveal a wedged pane.
3. **Pane truth** — `tmux -L <socket> capture-pane -pt <session>`. This exposes
   trust prompts, update nags, API/DNS failures, and interactive wedges. A pane
   parked on Codex's `Do you trust the contents of this directory?` (or the
   later `Press t to trust all` hooks dialog) means that session directory was
   not pre-seeded — the workflow queues dispatches as pending with no active
   worker and reports no error. Almost always the home was created after the
   last `ao gc prepare`: re-run `prepare`, then mail the Mayor to cycle that
   session; never restart it by hand. `ao gc check` names the untrusted
   directory or hook before you spend a dispatch on it. Gas City auto-answers
   both dialogs by sending keys into the pane (the hooks dialog with "Trust all
   and continue", which trusts every listed hook), so a wedge may clear on its
   own; that is a race, not a reason to skip the pre-seed.
4. **Health machinery** — `gc doctor`, `gc order history`, storage health, and
   events. This proves metabolism, not semantic acceptance.

When layers disagree, trust the more direct observation: pane over roster for a
session wedge, bead/run state over prose for workflow completion.

`gc status` may return a partial `no_agents_running` snapshot while
`gc session list --json` shows a live Mayor or worker. Treat that as an
observability disagreement, not permission to restart. A supervisor with
abnormal CPU, a timed-out native stop, or a recurring hook rewrite is an
upstream operational defect: report it upstream; do not kill or patch GC
processes.

The caller-owned input bead and the generated workflow root have separate
lifecycles: a successful `build-basic` run may close its workflow root while
the input bead stays open, and `push=false open_pr=false` makes a successful
no-op publish while the approved commit stays in its source anchor worktree.
Neither state is semantic completion by itself.

## Boundaries

- GC quests, runs, attempts, stalls, cancellations, and internal close state
  stay in GC. They never become AgentOps Plan, Candidate, RPI, or verdict state.
- A GC close or completed run is not AgentOps completion. Only a fresh Validate
  context issues the semantic result or, when requested, persists `verdict.v2`.
- This skill performs no automatic selection, retry, semantic validation, Git,
  integration, closure, release, or delivery.
- Inside a running city, everything outside the operator lane belongs to the
  Mayor or the reconciler.
