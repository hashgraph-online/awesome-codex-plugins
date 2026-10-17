# Parallel execution

Ready read-only nodes on independent tasks may run concurrently. Continuations of
the same task, including indirect source aliases, must be serialized across
parallel branches. Mutually exclusive condition alternatives may share a task.
The runtime also fences unresolved dispatches in historical graphs.
Static parallel write branches use the backend's isolated Git worktrees and
qualified Strict execution. At a Join, call
`workflow_prepare_integration`, read `workflow_review_integration`, inspect the
complete patch and evidence, then submit the accepted exact hash through
`workflow_integrate_parallel`. Use the supported operations for merging and cleanup.

Runtime-list fan-out is an item contract for native Agents or Cooperative Main workers. It assigns one item or
a partition to each child, bounds concurrent children and joins all required
results. Cooperative fan-out can write within Host-owned per-item paths;
without those paths the compiled writable contract has `max_concurrency:1`.
Each concurrent assignment needs a disjoint home/output/receipt scope. Shared
downstream artifacts have one owner after the join. Preserve accepted siblings
and retry only failed items through the declared recovery path.

Main worker fan-out requires per-item results and an explicit worker mode; the initiating Main orchestration is never multiplied. Auto resolves item/batch count from the bound runtime list; max_concurrency limits simultaneously active sessions independently. Use the existing native Agent executor when it is selected, rather than changing execution to claim parallelism. Neither mechanism provides arbitrary video segment exports or concurrent continuation of one session. Do not change a selected executor to claim parallelism. The graph,
executor qualification and original tool interface must all support the proposed
independent work; condition alternatives alone do not run concurrently.

Cooperative native nodes may explicitly use `executor.context_inheritance: upstream` to inherit initiating-Main context. Host packets set `fork_turns: all` and omit model/effort overrides; omitted/fresh retains the existing fresh context. Keep shared semantic material upstream once and assigned work in child packets. Inheritance does not establish an exact checkpoint or reduced input billing. Native `workspace_field` qualifies Host completion-check cwd/grants, while child tools retain cooperative logical scope. A typed `host_check` may render/check the native proposal before acceptance and return full diagnostics to the same recorded child; the Host preserves accepted siblings and validates their freshness at join. Unsupported Strict/managed inheritance fails visibly.

Host lifecycle observation uses the SDK's explicit inherited-prefix ordinal and exact child/parent lineage; copied parent turns are not child work. Small declared task inputs use the shared bounded verified semantic projection directly, while large materials retain exact sidecar addresses. Changing adapter fields also requires matching producer/tool/consumer contracts; qualify the real Host runner and Runtime before measured execution.

Native completion-check qualification must include capped and refill paths through public spawn acknowledgement, authenticated child observation, rendering, accepted results and final receipt sealing. Render-size preflight uses the durable current slot and observed turn; requiring the final receipt there creates a circular dependency because final sealing waits for accepted results. Unknown future slots are placeholders only, never invented child identities or acceptance. Keep the formal complete receipt and Runtime validation after all required results.


Writable Main runtime fan-out requires `fanout.workspace_field`: every item has a Host-owned independent directory used as its actual command/resource broker cwd (fresh sessions also use it as SDK cwd; explicit shared-prefix forks retain the common SDK environment). Item writes must remain inside that directory; original project and sibling directories stay outside writable roots. The Host qualifies the owned command sandbox before model execution, rejects unenforceable roots, drains and closes each item before accepting its final effects, and keeps durable per-item retries and prior usage. Partition slots use fresh ephemeral item sessions under the same concurrency cap. A downstream Host owner may copy validated completed bytes to original user destinations. Per-item path labels and post-run filtering alone do not establish concurrent command isolation.

Explicit Main shared_prefix uses a private common-only source and Host-owned concurrent ephemeral forks. It preserves original per-item corrections and ordered join; setup usage is counted. Shared SDK cwd-dependent external tools need explicit qualification; ordinary owned command/resource brokers retain independent item directories. Do not select this mode solely to promise cache savings.
