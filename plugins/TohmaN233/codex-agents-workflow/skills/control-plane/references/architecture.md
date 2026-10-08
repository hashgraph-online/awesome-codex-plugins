# Codex Agents Workflow architecture

## Objective



Keep a primary agent as the only task owner while the user defines reusable
Task Types and pins exactly one Provider to each ordered Stage. The control plane is a policy,
prompt, transport, and evidence boundary—not an autonomous manager that can accept its
own work.

## Layers

1. **Primary root session**
   - owns requirements, architecture, route declaration, scope, verification, and
     acceptance;
   - sees sanitized Task Type/Stage/Provider metadata;
   - resolves one selected Task Type and executes its fixed Stage plan in order.
2. **Human-owned configuration plane**
   - stores configuration under the user state directory outside plugin caches;
   - exposes an embedded MCP App through Extensions entrypoints and an explicitly launched token-protected browser console;
   - shares one validated Workbench API between both interfaces and agent management tools.
3. **Provider adapters and connectors**
   - native Codex role, repository-owned Cursor/Grok connector, external-MCP
     descriptor, packet web review, or direct OpenAI-compatible advisory API;
   - expose typed contracts without pretending every provider is a native subagent.
4. **Evidence and acceptance**
   - connector text is a claim;
   - exact identity, terminal evidence, scope evidence, Git state, and tests are checked
     by the root before acceptance.

## Prompt privacy

`codex_agents_workflow_status` exposes only ids, public descriptions, mappings, capabilities,
enabled/approval state, and template revision fingerprints. It does not return prompt
templates, endpoints, credential-variable names, or console tokens.

`codex_agents_workflow_resolve` interpolates only `task`, `context`, `constraints`,
`verification`, `task_type_id`, `stage_id`, and `provider_name` for the ordered Stages
of one selected Task Type. `codex_agents_workflow_connector_start` performs the same one-Stage compilation
internally for a built-in connector and persists only a prompt SHA-256.

This is minimization, not a hostile-model secrecy sandbox. A local coding agent may
have broad operating-system access. Stronger secrecy requires an OS isolation boundary
outside this plugin.

## Persistent state

The default configuration path is `$CODEX_HOME/codex-agents-workflow/control-plane.json`, or
`~/.codex/codex-agents-workflow/control-plane.json` when `CODEX_HOME` is unset. An absolute
`CODEX_WORKFLOW_CONFIG` overrides it. `SOL_CONTROL_CONFIG` is accepted only as a legacy
input alias and is translated into the canonical store. Saves are validated, atomic, restrictive-permission,
and revision-checked.
The default is user-global and independent of the repository or current working directory.
The human workbench reports the active scope and path: normal launches are
marked `global`; an explicit path override is marked `override` so test state cannot be
mistaken for the user's shared policy. This storage detail is not exposed by sanitized
agent-facing status.
The embedded App uses the host bridge without starting a loopback HTTP server. Its
bootstrap and configuration travel in UI-only metadata, outside model-visible results.
The standalone browser console uses `127.0.0.1:58712` by default. An
explicit port still overrides it, and port `0` requests an automatically selected free
port for parallel tests or exceptional local conflicts.
Version-1 and version-2 files migrate atomically to version 3. Legacy scenarios become
Task Types; untouched disabled provider-specific connector defaults are removed, while
enabled or customized provider capabilities and policy are preserved for manual editing.
Ambiguous legacy `full`
routes migrate disabled and require explicit review of both Stage bindings.

Connector task records live beside the configuration and contain task identity,
workspace, read/write mode, allowed paths, prompt digest, baseline snapshot, remote
identity, terminal/scope evidence, and bounded public errors. They do not contain the
prompt body. On MCP restart every nonterminal record becomes
`unknown_after_restart`; no task is automatically resubmitted and its workspace remains
reserved.

The headless stdio transport uses bounded general and control lanes. A shutdown first
stops intake, drains in-flight RPCs, then closes the console and Strict managers so a
signal cannot race durable reconciliation.

## Effective permission gate

A route is usable only when global, Task Type, every pinned Provider, and environment switches allow
it. A write task additionally requires all of:

- provider `capabilities.write=true`;
- Stage `access=bounded_write`;
- a non-empty validated `allowed_paths` list.

If either the selected Provider or Stage enables its approval gate, explicit current-task
`user_approved=true` is additionally required. When both gates are off, model invocation
does not add a second confirmation prompt.

Allowed paths are workspace-relative, non-glob, non-escaping boundaries. Existing or
nearest existing parents are resolved to reject symlink escape. The exact Git repository
root is required. One nonterminal connector task reserves each workspace.

Before dispatch the connector captures file fingerprints and Git HEAD, refs, semantic
index, local config, and reflog. A recursive runtime monitor records writes—including
Git-ignored paths—and requests exact cancellation as soon as an outside event is
observed. After terminal evidence the connector compares the full snapshot again.
Read-only work permits no changes; bounded-write work permits content changes only at
or below an allowed path and never permits Git metadata mutation. The public result
includes `changed_paths`, `metadata_changes`, `outside_paths`, and `prevented_attempts`.
A violation discards the submodel result and enters `scope_violation`.

This is stronger than a prompt-only boundary but is not represented as an operating-
system sandbox. Cursor offers no permission callback in the chosen UI transport, so its
pre-execution controls are exact workspace binding, validated paths, one-task lease,
the delivered access envelope, and immediate runtime-write observation. Grok ACP
additionally allows write-like permission requests to be path-checked and rejected
before the tool executes. These controls improve containment but are not described as
an operating-system sandbox.

## Minimal Cursor connection

The repository owns a deliberately small Cursor connector:

```text
Codex Agents Workflow MCP -> loopback HTTP /json/version + /json/list
                -> loopback CDP WebSocket
                -> Runtime.evaluate / Input.dispatchKeyEvent
                -> one pinned Cursor Agents UI profile
```

It keeps the reliability mechanisms derived from the reference Bridge:

- verify that the loopback port belongs to Cursor rather than another Electron IDE;
- never force-close Cursor when it is already running without CDP;
- launch with a loopback debugging port only from an explicitly approved start;
- bind one exact Git workspace and fail on ambiguous pages/workspace sections;
- create one fresh Agent and bind one exact `agent_id`/`target_id`, including an ID
  exposed only after submission by Cursor 3.16's Agents panel;
- require stable reply plus exact composer/history terminal evidence;
- cancel only the exact generating composer;
- preserve timeout/connection-loss/restart ambiguity and reconcile by persisted identity.

It intentionally omits CCE semantic search, parallel Agent queues, hidden-window mode,
workbench compatibility layers, broad selector fallbacks, and lifecycle supervisors.
The current UI profile is version-sensitive. Cursor 3.16.29 on Windows passed local
read-only, bounded-write, and exact-cancel smoke tests on 2026-08-20; automated CDP
fixtures and that baseline do not prove a different installation is compatible.

## Minimal Grok connection

The repository owns a Grok connector with:

```text
Codex Agents Workflow MCP -> dedicated Grok Leader
                -> Grok ACP child over stdio NDJSON
                -> initialize, session/new|load, prompt, update,
                   permission, elicitation, cancel
```

It preserves exact `task_id`, `session_id`, and `run_id`, one active task per workspace,
permission/input identity, precise cancellation, bounded waits, diagnostic redaction,
and restart reconciliation. Write-like ACP permission requests are classified before
answering: read-only, unscoped, or outside-path requests are cancelled and recorded as
prevented scope attempts.

It intentionally omits the reference Supervisor daemon, Windows Terminal/TUI,
Named-Pipe clients, writer fencing, proxy discovery, cross-host continuity, process
adoption, and large event/artifact journals. It inherits the environment present when
the plugin MCP starts. A reconciled session does not prove the old run's state; the
connector reports `RECOVERED_RUN_STATE_UNKNOWN` until exact cancellation or other
terminal evidence is available.

## Unified states and operations

Both built-in connectors expose `probe`, `start`, `status`, and `control` through the
same four MCP tools. Their common states are `starting`, `running`,
`needs_permission`, `needs_input`, `cancelling`, `completed`, `failed`, `cancelled`,
`scope_violation`, `needs_attention`, `unknown_after_restart`, and `abandoned`.

Timeout and lost transport are unconfirmed, not terminal. `reconcile` never creates a
replacement task. `abandon` only releases the local reservation after explicit
acknowledgement that the remote work may still run.

## Other providers

External MCP entries remain descriptors whose availability is unverified. ChatGPT web
Pro stays packet-first. Direct OpenAI-compatible calls remain read-only, text-only,
credential-from-environment, no-redirect, bounded-time/response advisory lanes.

The route model remains `solo`, `delegate`, `audit`, and sequential `full`. Route is derived
from the ordered Stage structure and is not a second editable field: `solo` has no Stages,
`delegate` has one implementation Stage, `audit` has one review Stage, and `full` has
implementation then review. New Task Types default to delegate; difficult work adds an
independent review Stage and derives full. Task Type prompts
contain reusable work semantics; Provider adapters own transport and provider-specific
safety behavior. Each Stage has one pinned Provider—there are no candidate lists or
automatic fallbacks.


## Main context modes and history

`executor: {kind: "main", mode: "worker"}` starts a fresh session using the calling
chat model and effort, with declared inputs and pinned resources. Legacy Main
nodes without `mode` retain this behavior. `mode: "orchestration"` yields to the
exact initiating conversation instead. The Host authenticates that conversation,
materializes a local bundle and validates its semantic result through
`workflow_orchestration_complete`. It never substitutes a worker or task Thread;
normal conversation context and tools remain available. Orchestration requires
Cooperative execution. Skill2Workflow and Build Workflow share both profiles.

At Run startup, the store removes eligible succeeded/failed history older than
24 hours after termination. Manual Workbench cleanup removes eligible history
immediately. Interrupted/unfinished Runs and unresolved effects remain; task
workspace outputs are never removed. Cleanup and mutations share writer locks,
and deleted Runs cannot be recreated by queued executor writes.
