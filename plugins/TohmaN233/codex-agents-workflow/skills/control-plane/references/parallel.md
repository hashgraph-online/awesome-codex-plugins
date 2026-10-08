# Parallel execution

Ready read-only nodes on independent tasks may run concurrently. Continuations of
the same task, including indirect source aliases, must be serialized across
parallel branches. Mutually exclusive condition alternatives may share a task.
The runtime also fences unresolved dispatches in historical graphs.
Parallel writes require the backend's
isolated Git worktrees and qualified Strict execution. At a Join, call
`workflow_prepare_integration`, read `workflow_review_integration`, inspect the
complete patch and evidence, then submit the accepted exact hash through
`workflow_integrate_parallel`. Use the supported operations for merging and cleanup.
