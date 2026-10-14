# Execute a Workflow

Read only for a concrete execution task. For failed or interrupted Runs, also read [recovery](recovery.md).

- **Execute:** a concrete task matches a Ready Workflow. For an unpinned task,
  call `workflow_route` with the concrete task. It returns compact valid Ready
  candidates, not prompts or the library. Start the selected candidate
  automatically when there is one clear semantic match. If candidates differ
  materially in outcome, permissions or side effects, ask the user. Do not
  select by keyword overlap alone. If none fits, continue ordinary work and let
  the orchestration skill choose an enabled Role automatically when delegation helps.

When the host already supplies an exact Ready Workflow ID/revision or a node
`agent_packet`, do not list, route, inspect, or reload the Workflow. The host
has already selected it. Only the current validated Ready revision may be
automatically routed; Drafts, retired Role graphs, previous revisions and
conversion history are not execution context. `workflow_list` is an explicit
management operation, not the startup or execution routing path.

## Start and advance the Run

Call `workflow_start` with the selected Workflow, task and absolute workspace. Pass
existing structured local inputs with `inputs_path`, or pass only the scalar local
address expected by a registered Host tool. Never open a manifest or data file and
copy its fields into `inputs`; the Host rejects nested model-transcribed inputs.
For a supplied inputs_path, let the Host read it; the initial semantic handoff supplies any content Main needs. Do not reread it before startup.
Host step 0 verifies and registers dependencies; no separate workflow_prepare_environment call is needed. That tool is optional dependency diagnosis, not a startup prerequisite. Missing dependencies are
reported before execution; ask before installing them.

When the Host supplies a direct MCP invocation descriptor, call its exact `tool`
with its typed `arguments` and fill only the named semantic/business `slot`.
Its tool and fixed arguments are already bound; a schema lookup adds
no missing call contract. Otherwise load only the exact tool schema needed by
the current Host action. A pinned start needs `workflow_start`; a returned continuation names its next tool.
Listing adjacent management, recovery and legacy operations adds no execution
evidence and must not become a repeated preparation step.

The Host advances deterministic and Main worker work. The dedicated
`caw-execution` MCP server exposes six long-call tools plus startup-contract
preparation under `mcp__caw_execution__` and binds typed direct invocation.
Management retains its historical code-mode contract. Each launcher binds the
catalog and all returned adapters to the same transport; use the exact returned
descriptor. A `kind:functions_exec` descriptor supplies the Host's executable
adapter and fixed resume parameters. A prepared startup belongs to its original
launcher and cannot be transferred between transports.
At subsequent Workflow call boundaries, use the Host's
`invocation_adapter`: `kind:direct_mcp` supplies the exact tool, fixed argument
object and one optional typed slot. `slot:arguments` supplies the complete public
business argument object; `slot:output` or `slot:initial_output` supplies that
argument value; `slot:none` uses the complete returned arguments. Startup
capabilities also expose `startup_invocation_adapter` for clients. No preliminary
capabilities call is needed. If the named direct tool is unavailable, report the
missing execution interface. These descriptors provide no alternate invocation.
Public startup prepares the first semantic handoff inside the same authenticated
call; a ready orchestration task or native spawn window does not require a relay
`workflow_native_next` call. Approval, attention and terminal results retain their
existing boundaries.
Ordinary startup uses business workspace/access/input arguments; the Host binds
the current revision and returns the real initiating Main's first semantic handoff.
Submit that decision through `workflow_orchestration_complete`; the original node
checker remains required. An optional `workflow_startup_contract` provides an
eligible initial decision before launch without creating a Run or model turn.
The Host retains a sealed immutable preparation outside the business workspace;
its adapter calls `workflow_start_prepared` with an opaque `startup_reference`.
Revision, original-input identity and launch arguments remain in Host storage.
Supplying
typed `initial_output` to this existing tool validates the actual initial node
schema and returns a complete `slot:none` invocation; call its tool with the returned arguments.
Omitting that value preserves the unfilled semantic slot. Preparation creates no
Run or model turn; the original lifecycle and checker still execute during start.
Changed inputs, revision or preparation fail before Run creation. Retry the same
reference and semantic result, rather than preparing a new invocation. The
installed exposure policy still requires real host qualification; a parsed
plugin declaration does not prove that a client exposes the direct tool.
The same adapter is returned for orchestration completion and cooperative
continuations. These are typed call parameters, not node prompt settings.
At a cooperative native
node, follow the returned `spawn_calls`: invoke each named tool with its exact
`arguments`. The Host supplies `collaboration.spawn_agent` arguments including the
selected context mode and semantic message. The Host
materializes one local task bundle as a bounded index plus exact Host-written input,
resource and verified-file sidecars. Small semantic inputs are in the message;
large inputs retain verified sidecars. Canonical paths and hashes stay internal.
Execute every spawn call in the released concurrency window, then call
the returned fixed `workflow_native_spawned_batch` acknowledgement adapter.
The Host waits for an Agent event or one hour; follow its returned action.
Do not poll the Run or add a Main wait.
For `continue_recorded_agent` or `repair_recorded_agent` with a Host
`followup_config`, call `collaboration.followup_task` with that exact config,
then call the returned acknowledgement descriptor for `workflow_native_followed_up`.
Host retains receipt identity and releases only unresolved per-item input to
the same Agent. Never combine later items by hand or replay an accepted item.
An ordinary repair without `followup_config` instead continues the exact
`agent_id` with its `repair_prompt`, then calls the returned
`workflow_native_next` adapter to collect the repaired turn.

Bind unchanged input and resource records directly from their originals; return only newly authored semantic results. Do not hand-copy existing fields into Agent inputs or outputs.

The Host owns launch, node claims, identities, leases, receipts, context
projection, completion envelopes, retries and continuation. Main worker nodes get
fresh sessions with declared inputs and resources. An `orchestration_handoff`
means execute the local task bundle in this initiating conversation, using its
existing context and normal tools, then call `workflow_orchestration_complete`
through its returned adapter with only the newly authored semantic value in the
`output` slot in the public `{output: ...}` argument envelope. Direct tool calls retain the public
schema requiring `output`. For `task_delivery:inline`, use the
supplied `task_bundle` directly. Small declared inputs are included under the Host's
shared byte budgets; large inputs remain hash-bound local sidecars. Read only needed sidecars; do not reread its
index file. `task_delivery:file` explicitly requires reading the local index.
Never substitute a worker or copy
Host identity fields. Follow the returned next action. The initiating Main should
not poll or reason while the Host owns the wait.

A Main handoff with `host_check.automatic=true` accepts only the new semantic
output. On completion the Host runs the exact registered checker against the
projected originals and that output, records durable evidence, and checks required
artifacts after its effects. Assess content and requested scope in the initiating
conversation; let completion perform the declared mechanical handoff. A rejection
is a visible failure with its exact diagnostic, not permission to forge a receipt.
An explicit schema-valid final `accepted:false`, or a false declared success
field, is a durable failed decision: the Host retains its hashed semantic output
and skips the success checker. Missing or malformed output uses the existing
bounded correction path.

Read the small instruction/syntax references needed for the node. Execute pinned
programs using their materialized addresses. Whole-resource reads above 12,000
bytes are rejected; inspect only necessary ranges/chunks when debugging. Do not
read a complete renderer or archive merely to invoke it.

A converted Workflow is a self-contained replacement for its source Skill.
Worker execution must not load the original Skill, copied `SKILL.md`, ambient
Skill instructions or conversion history. Orchestration explicitly retains the
current conversation; it must not reload the source Skill. Necessary scripts and references are
Workflow-owned assets. If a Run requests a source Skill path, report a defective
package rather than loading it.

Unavailable tools: read [connection diagnosis](connection.md).

Host worker completion preserves each exact turn's scrubbed command audit in a
hashed local audit file before closing the session; its receipt records the path,
digest, count and pending command IDs. Main also saves the existing command audit
artifact before closure. A completed model turn alone does not prove execution
has stopped. Shutdown journals command and session phases, and each command's
local lifecycle records control consumption, child exit, stream closure and its
receipt without command or output text. Child exit permits at most two seconds
of normal stdio drain; held pipes fail visibly. Broker shutdown permits two
seconds of command settlement, then closes only its owned App Server (eight
second bound) and requires settlement within one more second. Forced closure,
Host cancellation of unfinished work or unconfirmed shutdown cannot produce a
successful node completion; retain the failure evidence. Main, managed sessions
and Strict client closure use the same bounded owned-client boundary.
Receipt writes and notification failures do not skip owned cleanup; all failures
remain visible after its bounded stages, and explicit recovery can retry later
writes. Runner lifecycle appends have immediate rejection handlers and a
one-second bound per write. After stream/output cleanup, the queue gets at most
one second to flush, followed by one bounded independent receipt write. Failed
or stalled evidence cannot poison later writes or block cleanup: the control
receipt reports `CODEX_COMMAND_LIFECYCLE_FAILED`, preserves the child exit code,
and contains phase/error-code summaries without exception text. Zero-wait broker
calls also attach a rejection handler immediately; their original settlement
promise and notification errors remain available to explicit progress and close.
Command RPC completion and notification settlement are separate states. Stop
controls target only unfinished commands; pending IDs, progress retention and
forced owned-client selection use unsettled notifications on both success and
failure. A notification that outlives owned-client closure remains unconfirmed,
with its exact session and failure evidence retained for explicit recovery.
Confirmed owned-client closure is recorded once, so late callback settlement
cannot cause a second close or erase the original command error.
If closure was forced while a command RPC was unfinished, that execution failure
stays latched across recovery; a late normal receipt cannot turn it into a normal
completion.
Item attribution retains official item IDs, tool/server names and actual
durations. Tool requests retain their real call IDs, linked to broker process IDs;
arguments and web queries are hashed rather than copied into diagnostics. Missing
protocol fields stay missing. Response usage counts alone do not establish polling.
These defaults and process identities do not depend on a particular machine,
Codex version or binary allowlist; platform stop signals are recorded explicitly.

Open UI with `codex_agents_workflow_app` or `codex_agents_workflow_settings`; no
Run/thread is created. Use `codex_agents_workflow_console` for standalone or
unsupported hosts. Keep transport/bootstrap out of model context. Report the observed error;
never invent receipts, hide App failures or substitute execution.
