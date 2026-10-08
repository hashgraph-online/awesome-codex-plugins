---
name: workflow-control-plane
description: "Keep the host Workflow plane available, route concrete execution tasks to matching Ready Workflows, and manage Workflows on request. Do not start Runs for planning, discussion, comparison, audit, or experiment design."
---

# Workflow control plane

The persistent control plane is available without a matching Workflow. Workflows
cover end-to-end tasks; Roles assign ordinary helpers through the orchestration
skill and never enter running Workflow nodes.

A failed Run is unfinished. On `completion_satisfied:false` or
`recovery_required:true`, inspect the failed node and evidence, repair or retry
that unit. Report completion only when final acceptance makes the Run `succeeded`.

## Route the request

- **Execute:** a concrete task matches a Ready Workflow. For an unpinned task,
  call `workflow_route` with the concrete task. It returns compact valid Ready
  candidates, not prompts or the library. Start the selected candidate
  automatically when there is one clear semantic match. If candidates differ
  materially in outcome, permissions or side effects, ask the user. Do not
  select by keyword overlap alone. If none fits, continue ordinary work and let
  the orchestration skill choose an enabled Role automatically when delegation helps.
- **Manage:** create, import, inspect, debug, edit, publish, install or export a
  Workflow. Read [editing](references/editing.md) and use only the requested path.
- **Meta:** planning, comparing, auditing, evaluating, or designing experiments
  about Skills or Workflows. Work directly. Merely mentioning this plugin is not
  permission to start a Run.

When the host already supplies an exact Ready Workflow ID/revision or a node
`agent_packet`, do not list, route, inspect, or reload the Workflow. The host
has already selected it. Only the current validated Ready revision may be
automatically routed; Drafts, retired Role graphs, previous revisions and
conversion history are not execution context. `workflow_list` is an explicit
management operation, not the startup or execution routing path.

## Execute a selected Workflow

Call `workflow_start` with the selected Workflow, task and absolute workspace. Pass
existing structured local inputs with `inputs_path`, or pass only the scalar local
address expected by a registered Host tool. Never open a manifest or data file and
copy its fields into `inputs`; the Host rejects nested model-transcribed inputs.
Host step 0 verifies and registers dependencies. Missing dependencies are
reported before execution; ask before installing them.

The Host advances deterministic and Main worker work. At a cooperative native
node, follow the returned `workflow_native_next` packet and launch its exact
`spawn_config` plus `prompt` with `spawn_agent`; never replace it with a task thread. The Host
materializes one local task bundle as a bounded index plus exact Host-written input,
resource and verified-file sidecars. Large file
contents never share the single-read index.
Spawn every packet in the released concurrency window, then call
`workflow_native_spawned_batch` once with no arguments.
The Host waits for an Agent event or one hour; follow its returned action.
Do not poll the Run or add a Main wait.
For `continue_recorded_agent` or `repair_recorded_agent`, call `collaboration.followup_task`
with the exact `followup_config`, then call `workflow_native_followed_up` with no arguments.
Host retains receipt identity and waits for the Agent event. This is the
Host-controlled per-item continuation path: it reuses the same native Agent while
releasing only unresolved input. Never combine later items by hand or replay an
already accepted item.

Converted and built Workflows must not make any Agent hand-copy unchanged
input or resource values. This applies to arbitrary records, labels, names,
source text, metadata, IDs, paths and hashes. Bind originals beside new semantic
results or use registered Host tools to copy, transform or join them. The compiler
rejects copy-through instructions and Host-owned output fields.
For fan-out writers with per-item path scopes, the complete task packet must
bind directly from a Workflow input or an exact registered Host tool. The
compiler rejects an Agent-produced packet before the Workflow can become Ready,
including when a Host tool wraps or joins an upstream Agent output.

The Host owns launch, node claims, identities, leases, receipts, context
projection, completion envelopes, retries and continuation. Main worker nodes get
fresh sessions with declared inputs and resources. An `orchestration_handoff`
means execute the local task bundle in this initiating conversation, using its
existing context and normal tools, then call `workflow_orchestration_complete`
with only newly authored semantic `output`. Never substitute a worker or copy
Host identity fields. Follow the returned next action. The initiating Main should
not poll or reason while the Host owns the wait.

A converted Workflow is a self-contained replacement for its source Skill.
Worker execution must not load the original Skill, copied `SKILL.md`, ambient
Skill instructions or conversion history. Orchestration explicitly retains the
current conversation; it must not reload the source Skill. Necessary scripts and references are
Workflow-owned assets. If a Run requests a source Skill path, report a defective
package rather than loading it.

Unavailable tools: read [connection diagnosis](references/connection.md).
Open UI with `codex_agents_workflow_app` or `codex_agents_workflow_settings`; no
Run/thread is created. Use `codex_agents_workflow_console` for standalone or
unsupported hosts. Keep transport/bootstrap out of model context. Report the observed error;
never invent receipts, hide App failures or substitute execution.
