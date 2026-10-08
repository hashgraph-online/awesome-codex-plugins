---
name: orchestration
description: "Automatically use enabled Workbench Roles for useful delegation in ordinary tasks when no registered Workflow matches. The user does not need to name a Role."
---

# Use Workbench Roles in ordinary tasks

A Role is a saved way to assign one helper. It says what kind of work the helper
is suited for, which configured model to use, what it may change, and the
instructions it receives. It does not start a Workflow.

Apply this behavior whenever the plugin is loaded. The user does not need to ask
for a Role or name one. If no registered Workflow matches a concrete request and
one helper would materially help, call `workflow_role_templates`, select the one
enabled Role whose description fits the work, and call `workflow_role_template`
for that Role only. Pass the complete task boundary, owned files, constraints,
and verification. Do not load every Role's instructions.

For a native Role, launch exactly the returned `adapter.spawn_config` with
`spawn_agent` and send the returned `instructions`. Do not replace the selected
model, effort, access, or fresh-context setting. For another enabled Provider,
follow the returned adapter and its actual tool route. If the route is not
available, report that error; do not silently substitute another helper.

The primary Agent keeps responsibility for the user's intent, task split,
integration, verification, and final answer. After launch, it first completes
useful work that is independent of the helper's result and owned files. When the
next action depends on the helper, wait for an event with the longest supported
timeout, up to one hour. Completion or user input wakes the wait. Do not poll,
reread the same inputs, or repeat planning while waiting. Inspect the actual
changes and verification evidence after the helper finishes.

Use one Role for one clear assignment. Add another only for independent parallel
work or when the user requested an independent review. A failed assignment may
be corrected with the same helper when the remaining work is local to that
assignment; do not replay accepted work.

Workflow nodes are separate. Generation uses the registered Provider suitability catalog and Host routing
rules. A running node receives its pinned Provider and node task, without a
Workbench Role prompt. Never inject Role instructions into a Workflow node.
