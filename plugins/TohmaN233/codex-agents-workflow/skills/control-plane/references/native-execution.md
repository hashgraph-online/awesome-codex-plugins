# Native execution handoff

Cooperative `native_agent` nodes run as real Codex native subagents. The detached
Host advances deterministic and Main worker work, then stops at the native node.
It must not create an App Server thread or Codex task for that node.

Codex places the authenticated current conversation UUID in MCP request metadata.
The Host pins that UUID as `native_parent_thread_id`; the model never reads or passes
that field. `workflow_start` also leaves `main_actor`, `run_id`, `revision_hash` and
controller tokens to the Host.

`workflow_start` and `workflow_wait` return their exact next action. When the Host
reaches a native node, follow `workflow_native_next`. Each returned packet contains:

- a stable packet index;
- the workbench-selected native `spawn_config`;
- a small node prompt with the workspace, access, writable paths and one exact local
  task-bundle address.

The Host writes one content-checked task bundle before returning the packet. Its
bounded JSON index contains exact sidecar paths and the declared result schema;
internal item positions never enter the Agent-visible bundle. Projected list/object inputs, pinned resources and verified
absolute or workspace-relative path/hash files are separate deterministic local
files; the Host rewrites bound paths to those copies. Pass the packet prompt directly
to `spawn_agent`. Do not
copy input data, IDs, hashes, source files, or logs between conversations. `fork_turns: none`
provides fresh node context while the child retains normal Codex tools,
including file reads, edits, shell, search, and image reading.

Spawn every packet in the released window, then call
`workflow_native_spawned_batch` with no arguments. The Host already persisted the
packet positions, task names and expected Agent paths, so it journals the completed
window without model-copied receipt fields. That call remains inside the Host's
one-hour lifecycle event wait, validates the terminal structured result, releases
available fanout slots and advances the Run. Main does not poll, invoke a separate
wait tool or resubmit `workflow_native_next` while the Host call is pending.

Subagents write artifacts in the assigned workspace and return only the declared
semantic result and artifact paths. The Host binds dispatch indexes, identities,
hashes, receipts, and accepted item positions. For per-item fanout it records valid
items immediately. A blocked or invalid item continues in the same child with the
specific diagnostic; accepted siblings and accepted items are not replayed.

For a partition with `result_mode: per_item`, accepted items are journaled before
repair. A repair response materializes a new bundle containing only unresolved
items and returns `repair_recorded_agent`; use its exact `followup_config` and
`workflow_native_followed_up` arguments. For `item_delivery: incremental`, the
initial packet contains only the first unresolved item. After accepting it, the Host
materializes the next one-item task bundle and returns `continue_recorded_agent`.
Call native `collaboration.followup_task` with the exact Host-produced
`followup_config`, then call `workflow_native_followed_up` with no arguments and
enter the returned one-hour wait. If the controller stops
before journaling the follow-up, `workflow_native_next` reoffers the same
content-addressed packet after recovery. It never releases a later item first.

The three argumentless continuation calls above are the only native execution
interface. Spawn receipts, dispatch sealing and result commits are internal Host
operations and cannot accept model-transcribed IDs, indexes, hashes or results.


A `main_orchestration` stop resumes this initiating conversation. On the returned
`orchestration_handoff`, execute the Host task bundle using existing context and
normal tools, then call `workflow_orchestration_complete` with semantic `output`
only. The Host binds the exact Run and attempt; do not spawn a substitute helper
or copy its identities. Follow the returned action for subsequent nodes.
