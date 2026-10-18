---
name: using-gc
description: 'Operate Gas City through its own doors: Mayor, doctor and native run state. Use when: Gas City is selected or a gc run looks stuck.'
practices: [team-topologies, design-by-contract]
hexagonal_role: driving-adapter
consumes: [explicit-packets]
produces: [gas-city-runtime-evidence]
context_rel:
- kind: partnership
  with: agent-native
skill_api_version: 1
user-invocable: true
metadata:
  tier: execution
  dependencies: []
  capabilities: [dispatch_explicit_packet, observe_gc_runtime, inspect_pack_registries, drive_mayor_door]
  effects: [operate_gas_city, configure_codex_trust]
  canonical_status: canonical
  disposition: keep_optional_adapter
output_contract: runtime evidence per supplied packet
---

# Using GC

Use Gas City only when the caller explicitly selects it. Treat it as a
replaceable execution adapter, not a correctness or completion boundary.
The adapter cannot select AgentOps semantics, issue a binding verdict, or turn factory completion into delivery or validation proof.

## The operator lane

The operator lane into a city is a closed set:

- author source intent beads;
- `gc mail` to the Mayor, for work dispatch and for city tending;
- `gc session wake <run_target>`, once, for a routed bead whose worker stalled;
- `gc doctor [--fix]`, and supervisor start/stop from outside the city;
- `ao gc prepare|check|recover-affinity`;
- reading run, session, bead, pane and artifact state.

The Mayor authors workflow beads and dispatches them; it owns retries,
re-dispatch and tending for that work. Never create, scale or repair pack-owned
sessions by hand: `gc session new` for a singleton or scaled agent
(`core.control-dispatcher`, role workers) makes a mis-scoped session that
squats the canonical name in `start-pending` and blocks the reconciler from
spawning the real one. Session lifecycle belongs to the reconciler and demand
scaling. Direct `gc sling` is a debugging tool for a city with no live Mayor; a
run started that way has no coordinator, and the operator inherits its tending.

## Choose the factory first

AgentOps supports both Gas City and the
[Agentic Coding Flywheel](https://agent-flywheel.com) as external
software-factory runtimes. Use this skill only for Gas City. If the caller
selects the Flywheel, follow its [native workflow](https://agent-flywheel.com/complete-guide) instead of wrapping it in Gas City.

AgentOps supplies skills and evidence contracts to either factory. It does not
need its own Gas City formula or role pack. Install or link AgentOps skills into
the provider runtime before starting workers; the upstream Mayor, coordinator,
and workers can then discover and select `plan`, `implement`, `test`,
`validate`, and other AgentOps skills normally.

## Version facts

Status on 2026-10-04: the `gascity` pin (0.1.6, commit
`3b3b89f2011e06d84459aa7bea1552382f13930a`) is the commit `ao gc` enforces, and
it matches the registry's 0.1.6 release. The Gas City 1.4.0 command facts in
this skill were not re-verified for this release. When `gc version` reports
anything other than 1.4.0, confirm each command with `gc <command> --help`
before relying on it.

## Gas City 1.4 operating model

Gas City 1.4 is run-centered. The supervisor serves the dashboard and typed,
paginated session/run APIs. Every graph-owning city or rig scope needs its own
`core.control-dispatcher`; that deterministic worker advances formula control
beads. Agent workers claim routed work. The upstream `gc.mayor` skill is the
guided coordinator; `gc.run-operator` launches and supervises formulas.

The normal AgentOps path is:

1. Install and pin the upstream `gascity` workflow and rig-role imports.
2. Add the project as a rig, prepare its stock maintainer runtime, and make
   AgentOps skills visible to its provider sessions.
3. Create a caller-owned source intent bead and hand its id to the Mayor,
   which authors the workflow beads and dispatches the upstream `build-basic`,
   continuation, review, or implementation formula that matches the available
   artifacts.
4. Read run, session, bead, artifact, and verdict state. Completion is never
   inferred from chat or pane prose.

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

## Preferred pack and registries

The built-in `main` registry catalogs official packs. The community registry is
optional configuration:

```sh
gc pack registry list
gc pack registry refresh
gc pack registry search --all
gc pack registry show main:gascity
gc pack registry add community https://registry.gascity.com/registry.toml
gc pack registry search --registry community --all
```

`search` reads the local registry cache; `show` reports release provenance and
exact import commands. `gc import add` declares a source/version, and `gc import
install` resolves it into `packs.lock`. Prefer an exact accepted release for
reproducible cities.

AgentOps prefers the official `gascity` build pack, the workflow family visible
in the public Maintainer City factory, at the accepted reference above:

- dashboard: `https://factory.gascity.com`;
- workflows: `build-basic`, `build-from-*`, `implement`, review, issue, and PR
  flows;
- stock rig roles: `gc.run-operator`, `gc.implementation-worker`, planners,
  reviewers, and publisher;
- scope-local formula control: `core.control-dispatcher`;
- guided coordination: the upstream `gc.mayor` skill.

Install the workflow pack at city scope and its sibling roles pack on every rig
that runs work, following the exact commands returned by
`gc pack registry show main:gascity`. Keep the stock `gc.*` namespace; do not
nest or rename the roles behind an AgentOps pack.

## Hand work to the Mayor

Work enters the city through the Mayor. The caller authors ONE source intent
bead with acceptance, then hands the Mayor its id; the Mayor decomposes,
authors the workflow beads, and dispatches.

```sh
gc bd create "Add a --json flag to the export command"
gc mail send mayor -s "Build ago-XXXX" \
  -m "Decompose and launch build-basic for bead ago-XXXX with push=true open_pr=true." --notify
```

Or, in an interactive Mayor session:

```text
Use skill gc.mayor
```

AgentOps skills are tools available to those factory agents, not a replacement
workflow. Explicitly name a skill in the bead or prompt when its behavior is
required. The current upstream decomposition does not automatically propagate a
free-form `Required Skills` section from the caller-owned source bead into every
generated work item. Inspect the decomposition before implementation; put a
required skill name on the actual work item or worker prompt when its use is an
acceptance condition. Skill presence and skill invocation are different facts.

## Upgrade an existing city to 1.4

Before starting its orchestrator, run once per city:

```sh
gc doctor --fix
gc import install
gc supervisor stop --wait   # macOS when an older direct supervisor remains
gc start
```

Then confirm:

- `gc version` reports `1.4.0` from the intended path;
- `gc doctor` has no blocking failures;
- each graph-owning rig has an unsuspended `core.control-dispatcher`;
- imports and `packs.lock` resolve;
- `ao gc check` accepts the contained maintainer runtime and
  AgentOps skill links;
- on macOS, the supervisor LaunchAgent resolves to the same executable as the
  selected `gc` binary;
- old standalone-dashboard bookmarks or reverse proxies are removed.

A stale registered city may block every start. Repair that city with `gc doctor
--fix`, or explicitly unregister it if it is intentionally retired.

Retire an old HQ/canary by exact registered name or path, without stopping the
machine-wide supervisor needed by its replacement:

```sh
gc cities --json
gc stop /path/to/old-city --timeout 45s
gc unregister /path/to/old-city
gc cities --json
```

`unregister` fails rather than silently accepting an unknown target. Preserve
the city directory until its Beads state is backed up or confirmed disposable.
Create the replacement from the upstream Gas City template, install its pinned
imports, and verify it with `gc cities --json`, `gc --city <new-city> status`,
and `gc --city <new-city> doctor --json`.

## Orchestrating through the Mayor: the tending loop

After handing intent to the Mayor, the orchestrator runs five verbs. Each verb
has one owner; crossing owners is the recurring failure class this section
exists to stop.

| Verb | Owner | Surface |
|---|---|---|
| Monitor | orchestrator | `$API/runs/census` and `$API/runs/<run-id>` on a fixed cadence, plus `gc mail inbox` for Mayor replies. `failed > 0` in the census, a run in `failed`/`canceled`, or unread Mayor mail is the act signal; everything else is a tick. |
| Observe | orchestrator | On an act signal, walk the visibility layers in order — census, run detail, bead graph, session roster, pane truth — and stop at the first layer that explains. Do not start at pane truth. |
| Nudge | orchestrator, once | A routed bead with a live session: `gc session wake <run_target>` once. A `ready` bead nobody dispatched goes to the Mayor by mail with its id; dispatch is the Mayor's. A second nudge on the same subject means the diagnosis is wrong — mail the Mayor instead. |
| Redirect | Mayor | Priority, scope, cancellation, or model/provider changes travel by mail with bead/run ids. The orchestrator never re-slings, edits workflow beads, or patches a live run. |
| Rework | GC first, then Mayor | Failed review findings re-enter the run through its native fix loop (`review_fix_formula`, default `fix-loop-base`); bounded gated retries are `gc converge` loops. Only a TERMINAL `failed`/`canceled` run — or a completed run whose result misses caller acceptance — goes back: mail the Mayor the run id and the failure evidence for re-decompose and relaunch. |

Rework the orchestrator performs by hand (editing a failed run's worktree,
re-slinging its formula, closing its beads) creates a second uncoordinated
author for the same intent; the Mayor's relaunch then races it.

## Stall protocol

First classify the bead.

- Still `ready`, never dispatched: dispatch belongs to the Mayor. Mail it the
  bead id, then stop and inspect. Only with no live Mayor is
  `gc sling <run_target> <bead-id>`, once, the debugging fallback, and the
  operator then inherits that run's tending.
- Already routed/in progress: re-slinging is a **NO-OP**. Wake its owning worker
  once:

  ```sh
  gc session wake <run_target>
  ```

Then capture the exact tmux pane named by session state and run `gc doctor`. A
pane parked on a Codex trust dialog means its home missed the pre-seed (see
pane truth below). Never repair a city from inside that city. Never answer a
stall with `gc session new`; the operator lane above explains why.

When one wake does not clear the stall, or the city itself needs tending (a
stalled reconciler, sessions that never leave draining, model or provider
rewiring), send the request to the Mayor with the bead or run ids:

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
   active while a provider is wedged.

   Programmatic run status comes from the supervisor's typed run API — the
   same data the dashboard renders. `gc status` prints the API base; neither
   `gc status --json` nor any other CLI subcommand carries run objects.

   ```sh
   API="http://127.0.0.1:<port>/v0/city/<city-name>"
   curl -s "$API/runs/<run-id>"   # {run_id, title, status, target, scope, started_at, updated_at}
   curl -s "$API/runs/census"     # {status_counts: {pending, active, waiting, canceling, completed, failed, canceled, skipped}}
   ```

   Poll run status and census for progress; a nonzero `failed` count is the
   first machine-readable failure signal. The dashboard's run page
   (`/city/<city-name>/runs/<run-id>`) is the human view of the same objects.
2. **Bead graph** — `gc bd --rig <rig> ready --json` and `show <id> --json`.
   This is workflow-state truth, but a claimed bead cannot reveal a wedged pane.
3. **Pane truth** — `tmux -L <socket> capture-pane -pt <session>`. This exposes
   trust prompts, update nags, API/DNS failures, and interactive wedges. A pane
   parked on Codex's `Do you trust the contents of this directory?` (or the
   later `Press t to trust all` hooks dialog) means that session directory was
   not pre-seeded — the workflow queues dispatches as pending with no active
   worker and reports no error. Almost always the home was created after the
   last `ao gc prepare`; re-run `prepare`, then restart that session.
   `ao gc check` names the untrusted directory or hook before you spend a
   dispatch on it. Gas City also appears to auto-answer this dialog by sending
   keys into the pane, so a wedge may clear on its own — treat that as a race
   you do not want to depend on, not as a reason to skip the pre-seed.
4. **Health machinery** — `gc doctor`, `gc order history`, storage health, and
   events. This proves metabolism, not semantic acceptance.

When layers disagree, trust the more direct observation: pane over roster for a
session wedge, bead/run state over prose for workflow completion.

`gc status` may return a partial `no_agents_running` snapshot while
`gc session list --json` shows a live Mayor or worker. Treat that as an
observability disagreement, not permission to restart. Use session and pane
truth for liveness, bead/run state for workflow progress, and Doctor for
metabolism. A supervisor with abnormal CPU, a timed-out native stop, or a
recurring hook rewrite remains an upstream operational defect; this helper
reports it but never kills or patches GC processes.

The caller-owned input bead and the generated workflow root have separate
lifecycles. A successful `build-basic` run may close its workflow root while
leaving the input bead open. Likewise, `push=false` and `open_pr=false` produce
a successful no-op publish while the approved commit remains in its source
anchor worktree. Neither state is semantic completion by itself.

## Boundaries

- GC quests, runs, attempts, stalls, cancellations, and internal close state
  stay in GC. They never become AgentOps Plan, Candidate, RPI, or verdict state.
- A GC close or completed run is not AgentOps completion. Only a fresh Validate
  context issues the semantic result or, when requested, persists `verdict.v2`.
- This skill performs no automatic selection, retry, semantic validation, Git,
  integration, closure, release, or delivery.
- Everything outside the operator lane above belongs to the Mayor or the
  reconciler.
