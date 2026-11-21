# Prewalk for Codex

This plugin uses the active root Codex session to explore, plan, and complete
the first verified task, then hands the work to a configured executor. Presets
never select or replace the root model.

The [Prewalk README](https://github.com/TardisBooo/prewalk) covers
the shared workflow and presets. This document covers the Codex adapter.

## Install

Python 3.10+ and Codex CLI 0.146.0+ are required. This repository is the
marketplace catalog: add it, then install `prewalk@prewalk-marketplace`.
Codex uses `plugin add` (not `plugin install`). There is no project-scaffold
setup step.

```sh
codex plugin marketplace add TardisBooo/prewalk
codex plugin add prewalk@prewalk-marketplace
```

From a local clone, pass the checkout path instead of `TardisBooo/prewalk`.
Restart Codex. For custom model routes, save the
[example presets](https://github.com/TardisBooo/prewalk/blob/main/hosts/codex/presets.example.toml)
as `~/.codex/prewalk-presets.toml` and edit them.

## Use

```text
$prewalk:prewalk <task>
$prewalk:pw-go
```

Use `$prewalk:pw-revise <changes>` to change the plan. Operational skills are
`pw-status`, `pw-retry`, `pw-reconcile`, `pw-off`, `pw-doctor`, and the explicit
manual-model fallback `pw-resume`. `--fast` automatically requests the same
validated handoff at the Stop checkpoint.

## Capability-safe route

Codex hooks validate the native subagent request without rewriting it. `pw-go`
inspects the live `spawn_agent` schema before creating a one-time route:

```text
durable Stop checkpoint -> handoff_requested
  -> schema has model + fork_turns or fork_context controls
     -> token-bound PreToolUse validation
     -> spawn once with the preset's fork behavior (default "all")
     -> PostToolUse binds returned agent_id -> executor_running
  -> required model control is absent
     -> retain checkpoint without spawning
```

### fork_turns: trajectory vs packet

When the live schema accepts an explicit model, Codex starts the configured
executor in a fresh context with the verified packet. If the preset allows
routing without model selection, `fork_turns` controls the starting context:

- `"all"` — the spawn inherits the planner's full turn history, so
  the handoff message is a short phase-2 note: the exploration, todo list, and
  the verified first edit are already in the executor's context. This matches
  the stencil.so prewalk write-up ("hand off a trajectory, not a fairytale")
  and avoids re-reading files the planner already read.
- `"none"` — fresh-context executor that receives the full persisted Handoff
  Packet in the spawn message (the packet-minimal preset). Cheaper context,
  but everything the planner learned has to be re-derived from prose.

Presets with `require_model_routing=true` never silently spawn on an unknown
model. A spawn failure remains retryable. Only the bound agent's SubagentStop
can finish the run. Executors report
`PREWALK_COMPLETE` or `PREWALK_INCOMPLETE: <reason>`; incomplete work restores
the checkpoint.

## Hooks

`hooks.json` registers:

- `PostToolUse` plan/todo tools: track the current snapshot.
- `PreToolUse`/`PostToolUse` `spawn_agent`: validate the exact route and bind
  the returned agent identity.
- `SubagentStop`: accept a final marker only from the bound executor.
- Root `Stop`: capture the exact checkpoint, trigger `--fast`, and recover an
  explicitly interrupted bound route.

Skills call `_arm.py` and `_pw.py`; hook entry points use shell wrappers because
Codex runs plugin hooks with the plugin root as the working directory.
All helpers prefer `CODEX_THREAD_ID`; hook payload `session_id` must match it.
Legacy callers may still pass an explicit id when `CODEX_THREAD_ID` is absent.
Prewalk never guesses identity from the newest rollout file.

## State

State lives in `~/.codex/prewalk-state.json`, or under `CODEX_HOME`.
`PREWALK_STATE_FILE` may point to an absolute writable state file when a project
sandbox cannot write to that directory. `pw-doctor` probes the same lock path
used by the store. The plugin uses locked atomic writes and quarantines
malformed JSON with a `.corrupt` suffix.

## Update

```sh
codex plugin marketplace upgrade prewalk-marketplace
codex plugin add prewalk@prewalk-marketplace
```

Restart Codex after updating.
