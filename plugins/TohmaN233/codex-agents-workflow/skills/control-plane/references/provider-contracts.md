# Provider contracts

Read the relevant connector section after selecting a Workflow node. Dispatch by `adapter.kind`,
`adapter.execution`, and `adapter.connector`; never infer a provider from its display
name.

## Shared contract

For every provider:

1. preserve the Workflow, node, access intent, approval state, workspace,
   and path boundary;
2. send only the selected compiled prompt and minimum required artifacts;
3. retain the provider's real task/session/Agent identity;
4. reject missing terminal evidence, scope expansion, or ambiguous cancellation;
5. treat provider output as a claim and independently verify it in the primary agent.

Provider output never grants publication, destructive actions outside the user request,
external messaging, permission choices, or product/governance authority.

## `native_agent`

The adapter returns exact `agent_type`, freshness, role, expected model/effort, and any
requested sandbox. A Cooperative Workflow's `workflow_start` or `workflow_native_next`
returns one scoped packet per real native subagent. Use each `spawn_config` as the
`spawn_agent` arguments and its prompt as the message. Spawn every released packet,
then call `workflow_native_spawned_batch` with no arguments. The Host journals its
precomputed packet indexes and canonical Agent paths, holds the one-hour lifecycle
event wait, validates exact terminal child turns, releases available slots, joins
results in dispatch order and seals the completed dispatch internally. The Host
constructs the completion envelope and derives
the node, lease, owner, and dispatch request ID from the Run and attempt.
For serial fan-out, each handoff exposes just the next packet. After its Agent
is journaled, call the supplied Host continuation once; do not poll or transcribe
the result.
If Host observation reports a blocked or invalid per-item result, call the exact
`followup_config` on the same child, journal it with `workflow_native_followed_up`,
and remain in the returned Host continuation. Accepted items remain journaled.
There is no manual result-submission or receipt-recovery interface.
Generic agents receive explicit model/effort overrides with a fresh context; fixed
roles receive no overrides and must match their registered model/effort. A requested sandbox is not proof of the host
policy. An inspection-only reviewer is read-only; a review-and-fix node needs
explicit bounded-write access and a write-capable Provider.
Native Provider read/write capability describes what the model may be assigned,
not authority for this invocation. The Workflow node access resolves the actual
read-only or bounded-write task intent; native `spawn_agent` does not itself prove an OS sandbox. Display names may change while Provider IDs
remain stable for existing Workflow references.

## `codex_thread`

Use the returned create-or-continue handoff through the Codex task tools. Preserve
its entire prompt, resolved workspace, access and output-write boundaries; these
are Cooperative instructions, not an OS sandbox. Record the actual `threadId` as
`receipt.thread_id`. A continuation retains that exact task and Provider; a start
requires a fresh task identity. Queued `clientThreadId` values cannot be receipts.

New Runs pin thread protocol v2. Inspect the exact dispatch marker in the task's
user prompt and its completed assistant turn. Submit the actual `turn_id` and
`dispatch_request_id` in the `codex_thread` completion observation. Earlier turns,
generic task completion, or missing host turn identity are insufficient. The host
attests this correlation; the runtime checks dispatch identity and rejects reused
turns. Existing unversioned Runs retain their original evidence requirements.

## Built-in connector operations

Both built-in connectors use:

- `codex_agents_workflow_connector_probe(provider_id, workspace?)`;
- `codex_agents_workflow_connector_start(task_type_id, stage_id, task, context, constraints, verification,
  workspace, user_approved, allowed_paths?)`;
- `codex_agents_workflow_connector_status(task_id, wait_ms?)`;
- `codex_agents_workflow_connector_control(task_id, action, exact identity fields...)`.

`probe` sends no task. `start` compiles/delivers one private template internally.
`status` is keyed only by exact `task_id`. `control` supports `reconcile`, exact
cancellation, disconnect, and acknowledged abandon; Grok also supports exact permission
and input responses.

Write tasks require Provider write capability, a `bounded_write` Stage, and non-empty
validated `allowed_paths`. An enabled Provider or Stage approval gate additionally
requires explicit current-task approval. Read-only tasks omit paths. Every task requires
an absolute Git root and acquires the workspace's single active-task reservation.

Common terminal evidence and scope fields must be inspected before use. A
`scope_violation`, `needs_attention`, `unknown_after_restart`, or `abandoned` result is
not an accepted implementation.

## `builtin_connector`: Cursor CDP

Expected connector `cursor_cdp`, transport `cdp_ui`.

The connector verifies a loopback Cursor CDP endpoint or, when Cursor is closed,
launches the configured executable with the configured loopback debugging port and
exact workspace. It does not force-close an already-running Cursor that lacks CDP.

- The supported UI profile is `agents_v2_2026_08`; a profile mismatch fails closed.
- Start creates one fresh Agent in one exact workspace and returns `task_id`,
  `agent_id`, `target_id`, and `cdp_port`.
- On the history-backed UI, Agent history and composer identity must agree. On Cursor
  3.16's Agents panel, the connector binds the one exact composer ID published after
  submission. Zero or multiple identities fail closed.
- Completion requires a stable stopped generation plus stable final reply/history
  evidence, not merely a visible Markdown fragment.
- Cancellation requires `confirm=true` and the exact returned `expected_agent_id`.
  Stop is clicked only in the exact matching generating composer and becomes terminal
  only after a stable stopped observation.
- Background inactivity termination is disabled by default (`task_timeout_ms: 0`).
  A positive value explicitly opts this Provider into an inactivity deadline; exact
  Agent activity renews it. CDP loss still enters `needs_attention` immediately.
- Timeout or CDP loss enters `needs_attention`. After restart, `reconcile` reopens the
  persisted exact Agent on history-backed surfaces. The Agents panel reattaches only
  when its currently visible composer has the persisted exact ID; it never guesses or
  creates a replacement.
- Cursor has no permission request hook in this transport. Before dispatch the
  connector validates workspace/path policy, holds a one-task lease, embeds the access
  boundary in the prompt, and monitors recursive filesystem events. Outside or
  Git-ignored writes request exact Agent cancellation. Final evidence compares changed
  content plus Git HEAD, refs, semantic index, local config, and reflog.

Automated tests use a real child process that implements loopback HTTP, WebSocket
framing, CDP commands, Agent state, cancellation, restart recovery, and workspace
mutations. Cursor 3.16.29 on Windows passed local read-only, bounded-write, and
exact-cancel smoke tests on 2026-08-20. This is a known-good baseline, not proof for a
different Cursor build, login, or UI profile.

## `builtin_connector`: Grok ACP

Expected connector `grok_acp`, transport `leader_acp_stdio`.

The connector starts a dedicated Leader and ACP child and uses `initialize`,
`session/new`, `session/load` for reconciliation, `session/prompt`, `session/update`,
`session/request_permission`, `elicitation/create`, and `session/cancel`.

- Preserve `task_id`, `session_id`, and `run_id` exactly.
- Permission/input requests remain pending until the exact returned request and option
  are answered. Never use approve-everything modes.
- A write-like permission is classified before answering. Read-only, unscoped, or
  outside-path writes are cancelled before execution and recorded under
  `scope.prevented_attempts`.
- An in-scope write permission is still surfaced for explicit option selection.
- Cancellation requires `confirm=true`, `expected_session_id`, and `expected_run_id`.
  It is terminal only after ACP prompt evidence proves the outcome.
- Background inactivity termination is disabled by default (`task_timeout_ms: 0`).
  A positive value explicitly opts this Provider into an inactivity deadline: every
  exact-session ACP update renews it, and it pauses while an exact permission/input decision is pending. A separate
  `max_task_duration_ms` bounds the underlying prompt RPC as a long absolute safety
  limit. Inactivity timeout enters `needs_attention`; no replacement run is created.
- After restart, `reconcile` attaches an ACP child to the persisted Leader socket and
  loads the exact session. Because ACP does not prove the prior run state, it reports
  `RECOVERED_RUN_STATE_UNKNOWN` and permits exact inspection/cancellation rather than
  claiming completion.
- Direct file changes, Git-ignored runtime writes, Git metadata mutations, and prevented outside permission attempts feed the common scope verdict.

Automated tests use real Leader/ACP child processes and NDJSON request/notification
exchange. They do not prove the user's Grok binary, authentication, proxy environment,
or desktop behavior. Grok CLI 1.0.4 on Windows passed local read-only, bounded-write,
and exact-cancel smoke tests on 2026-08-20.

## `external_mcp`

An external MCP provider is a descriptor only. Its `availability` is unverified until
the host exposes the configured tools. Preserve the provider's own identity and
terminal contract, but do not call nearby tools, simulate terminal typing, or describe
the external integration as bundled.

`mcp_tool` remains only a legacy configuration alias for `external_mcp`.

## `packet_review`: ChatGPT web Pro

The built-in **GPT reviewer** Role binds to the existing `chatgpt-web-pro` Provider;
it does not create another Provider or another Role when that Provider is edited.
Both are disabled by default. A compiled Role returns the exact `packet_review`
adapter below after both have been enabled.

Follow the installed `chatgpt-agent` skill in reviewer role using its `packet.inspect`
route. Build the frozen ZIP packet with that skill's packet builder, upload it in the
ChatGPT side/in-app browser, and instruct the reviewer to use only the packet. The ZIP
is the evidence boundary. Wait for the newest completed answer, capture that exact
response, and save it. Missing browser control or reviewer availability fails the lane
without substitution. A web review never proves code execution or correctness.

## `direct_api`: OpenAI-compatible advisory model

Call `codex_agents_workflow_invoke`; do not bypass it with shell HTTP. The endpoint must be HTTPS
except loopback HTTP, credentials come from an environment variable, redirects are
rejected, response/time are bounded, and no host/file tools are supplied. The Stage
must be read-only and all switches/approval gates must be satisfied.

## Primary acceptance

Before accepting connector work, the primary agent must inspect:

- exact remote identity and terminal evidence;
- `scope.read_only`, `allowed_paths`, `changed_paths`, `outside_paths`, and
  `prevented_attempts`;
- the actual Git diff, including pre-existing user changes;
- tests/checks actually run rather than merely claimed.

The primary agent alone decides ship, correction, escalation, or rethink.
