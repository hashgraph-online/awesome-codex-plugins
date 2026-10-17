# Inspect and edit existing Workflows

Read only for existing graph/resource management. New Skill conversion and brief generation use [authoring](authoring.md); package transfer uses [packages](packages.md).

## Execution policy

New task Workflows default to Cooperative with task-scoped bounded writes and no
ambient Skills. Strict is an explicit executor-isolation choice, not the default
permission level.

Strict requires a qualified executor catalog, explicit Skill input and bounded tool
broker. It is not an OS filesystem ACL. Read `workflow_capabilities` for the currently qualified executor. Never
change a failed Strict request to Cooperative. Cooperative external/provider
executors may retain their host behavior only when a Workflow explicitly declares
it; Main workers and converted worker nodes never inherit ambient Skills. Main
orchestration explicitly retains the initiating conversation and requires
Cooperative mode. Missing external tools, executables or scripts remain
requirements; do not execute imported scripts to infer their behavior.

## Revision-safe editing and publication

User-requested graph/resource edits use `workflow_read`, `workflow_save` and
`workflow_write_resource` under exact revision CAS. Publish the saved Draft with
`workflow_publish`; it validates graph and resource closure before
Ready and never starts a Run. Converted Drafts retain their original source,
proposal and requirement identity. Publication refreshes content hashes for the
edited graph and resources, records a direct editor-publication identity, and keeps
the historical review contract version, including v12. It does not claim a new AI
semantic review.

The ordinary `workflow_create`, `workflow_save`, `workflow_write_resource`,
`workflow_publish`, and `workflow_delete` operations are available for explicit user
Workflow management requests. Publishing still runs the deterministic structure and
dependency checks; deletion uses the recoverable Pack trash path and exact revision CAS.

For task-owned superseded authoring Drafts, use [authoring cleanup](authoring-cleanup.md). An ordinary editor publication retains historical review identity; it does not supply a fresh independent semantic review.
