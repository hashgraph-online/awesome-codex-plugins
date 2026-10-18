# Native execution handoff

Cooperative `native_agent` nodes run as real Codex native subagents. The detached
Host advances deterministic and Main worker work, then stops at the native node.
It must not create an App Server thread or Codex task for that node.

Codex places the authenticated current conversation UUID in MCP request metadata.
The Host pins that UUID as `native_parent_thread_id`; the model never reads or passes
that field. `workflow_start` also leaves `main_actor`, `run_id`, `revision_hash` and
controller tokens to the Host.

`workflow_start` and `workflow_wait` return their exact next action. When the Host
reaches a native node, follow `workflow_native_next`. Its model-facing handoff has
ordered `spawn_calls`, each naming `collaboration.spawn_agent` with complete Host-generated
`arguments`. Those arguments include the selected native configuration and semantic
`message`; canonical packet indexes, file hashes and receipts remain internal.

The Host writes and verifies the canonical task bundle before projecting each call.
Native semantic task indices up to the Host's fixed 1,024 UTF8 byte budget are
delivered directly. Larger indices use the verified public semantic-task file;
Main executes the supplied short spawn call without copying its body. The child
reads that exact file once. Current-Main preparation keeps its separate budget.
Large inputs, pinned
resources and verified files retain exact materialized sidecars. The public message
contains the applicable task as readable text, scope and result schema once;
mechanical completion checker names and receipt fields stay private. The Host selects
`fork_turns: none` for fresh context or `all` for explicit upstream inheritance;
inherited calls omit model/effort overrides. Native children retain normal Codex tools,
including file reads, edits, shell, search, and image reading.

Execute every spawn call in the released window, then execute the returned fixed
`workflow_native_spawned_batch` acknowledgement adapter. The Host already persisted the
packet positions, task names and expected Agent paths, so it journals the completed
window without model-copied receipt fields. Its embedded batch identity and durable
receipt let the same adapter resume after partial acknowledgement or a collector
failure without spawning again or acknowledging a later unseen window. That call remains inside the Host's
one-hour lifecycle event wait, validates the terminal structured result, releases
available fanout slots and advances the Run. Main does not poll, invoke a separate
wait tool or resubmit `workflow_native_next` while the Host call is pending.

Subagents write artifacts in the assigned workspace and return only the declared
semantic result and artifact paths. The Host binds dispatch indexes, identities,
hashes, receipts, and accepted item positions. For per-item fanout it records valid
items immediately. A blocked or invalid item continues in the same child with the
specific diagnostic; accepted siblings and accepted items are not replayed.

New native Runs also bind a Host-owned dispatch span before releasing runnable
tasks. Its original task-root snapshot covers producer work before any later
completion checker. The Host tracks exact material publications separately,
validates disjoint item grants and accounts for aggregate observed workspace
changes after all possibly started slots have exact terminal proof. It does not
attribute every change to one child, reset the baseline after production, or
allow a broad material-directory exemption. Hashes and span receipts remain
private. This is Cooperative evidence, not an OS sandbox or whole-machine audit.

An unfinished span retains its task-root admission owner through cancellation,
failure or uncertain shutdown. Explicit retry may abandon only a fully audited
failed span with durable terminal proofs and no pending observed spawn, followup,
producer or checker intent; abandonment records failure and does not accept its
semantic result. Uncertain work requires exact mechanical reconciliation. A
settled successful span releases the exact owner for successors. Historical Runs
without the new pins epoch retain their original protocol. State-only same-root
admission reads do not confer resource or execution authority.

For a partition with `result_mode: per_item`, accepted items are journaled before
repair. A repair response materializes a new bundle containing only unresolved
items and returns `repair_recorded_agent`; its same-child message carries the exact
diagnostic and required remaining-item ordering without replaying the known task.
Use its exact `followup_config` and
`workflow_native_followed_up` arguments. For `item_delivery: incremental`, the
initial packet contains only the first unresolved item. After accepting it, the Host
materializes the next one-item task bundle and returns `continue_recorded_agent`.
Call native `collaboration.followup_task` with the exact Host-produced
`followup_config`, then call `workflow_native_followed_up` with no arguments and
enter the returned one-hour wait. If the controller stops
before journaling the follow-up, `workflow_native_next` reoffers the same
content-addressed packet after recovery. It never releases a later item first.

The three continuation calls above are the only native execution
interface. Spawn receipts, dispatch sealing and result commits are internal Host
operations and cannot accept model-transcribed IDs, indexes, hashes or results.


A `main_orchestration` stop resumes this initiating conversation. On the returned
`orchestration_handoff`, execute the Host task bundle using existing context and
normal tools, then call `workflow_orchestration_complete` with semantic `output`
only. The Host binds the exact Run and attempt; do not spawn a substitute helper
or copy its identities. Follow the returned action for subsequent nodes.
Accepted native results already advance through deterministic successors in the
same Host call and return the real next current-Main handoff when applicable.

An explicitly declared native text-amendment repair returns the supplied
`amendments` schema instead of retransmitting a complete known manuscript.
Follow the exact field and physical-line scopes in that same-child handoff.
Replacement text covers complete lines, including their delimiters; nonempty
replacement before EOF must end with a delimiter. The Host binds the rejected
baseline, verifies and merges the edits, and reruns the original result schema
and checker. Invalid or stale edits fail visibly. Undeclared nodes retain the
existing complete-result protocol; do not invent an amendment mode or copy
baseline hashes, receipts or checker identities into model output.
