# Generate a Workflow or Role

Read for Skill conversion or brief-based generation. Existing graph edits use [editing](editing.md); execution uses [execution](execution.md).

Read [the semantic contract](authoring-contract.md) before planning or compiler work, and [review and repair](authoring-review.md) before submitting or revising a proposal. Track task-owned temporary Draft IDs from the first import; finish with [authoring cleanup](authoring-cleanup.md). Reuse the selected Draft and exact Run for repairs rather than creating another temporary Workflow for each finding.

For independent production or performance claims, read [parallel conversion and
cost evidence](authoring-parallel-cost.md). Context isolation, actual concurrency
and cache-priced cost require separate evidence.

## Select and snapshot the source

Generation keeps current Main orchestration for conversation decisions and final
acceptance. Ordinary workers use existing Provider subagents. Main worker is an
explicit user option. Choose worker difficulty using the actual configured model
descriptions in the planning packet: routine reads and audits do not justify
Astra. See [the profile table](authoring-contract.md#host-execution-defaults).

For an explicit Strict isolation request, also read [execution policy](editing.md#execution-policy); preserve the requested isolation and check its qualified executor before authoring.

Use `workflow_skill_inventory` for default Codex-folder import discovery; pass
`discovery: folders` and an optional absolute `folder` for a custom source. This
is not a list of executor-enabled Skills. Explicit `discovery: host` with a
workspace retains qualified host discovery. Preserve the discovery selection
when importing. Skill authoring uses editable skill2workflow classification rules
pinned to the authoring Run; configured eligible Providers are assigned per node
by the compiler, never inherited from the planner. Read `workflow_routing_defaults`
for current rules; shared defaults are edited in the workbench. Import only the selected
entry through `workflow_import_skill`; the result is a full-resource Draft with
visible provenance and unresolved dependencies. Never modify the original Skill.

## Select the authoring route

There are two built-in authoring Workflow configurations. Read them with
`workflow_authoring_workflows`: `system.skill2workflow` snapshots a selected Skill,
while `system.build-workflow` snapshots an ordinary brief created with
`workflow_build_workflow`. After that input adapter they use the same semantic
planner, deterministic WorkflowForge compiler, review contract and publication
boundary. Do not pretend a from-scratch code-check or other brief is a Skill import.

`workflow_build_workflow` accepts `template_kind: workflow | role` (default:
`workflow`). Choose `role` only when the brief describes one reusable agent
behavior; set its read-only or bounded-write access and optionally pin a native
Provider. This path creates a reviewable Role Draft directly from the brief;
it does not claim to have run the multi-step semantic compiler. Choose
`workflow` for an end-to-end sequence; it retains the shared Skill-conversion
compiler and independent review contract. If the user did not state a kind,
decide from whether they want one agent behavior or a full task process.

## Host pipeline and completion

The Workbench exposes the actual authoring compiler pipeline: pinned source snapshot,
planner-filled semantic inventory, Host graph assembly, Host execution/permission
binding, Host deterministic validation, independent semantic review, and Host
completion. The Run stores bounded counts, hashes, bindings and validation results
for the Host stages. A planner or reviewer marked `read_only` cannot mutate the task
workspace; it still produces the structured semantic result consumed by the Host.

Start the selected system authoring Workflow through `workflow_start`, with
`inputs: {source_workflow_id, source_revision}` identifying the exact imported
Skill or brief Draft. The Host materializes its private authoring Run using the
stored planner and reviewer bindings. The Workbench's Generate action uses the
same Host path. `create_authoring_run` and result application are internal Host
operations, not model tools. Continue by executing the returned complete
`invocation_adapter` unchanged. It binds the exact authoring Run/controller to
`workflow_drive`, with no fields for the model to fill. Each advancing response
supplies its next complete adapter; attention and terminal responses stop.
Authorized recovery supplies separate resume and cancellation adapters. Execute
the one matching the user's continue or discard instruction; recovery itself
does neither and invokes no model. The Host routes the Run through the pinned planner, deterministic
compiler and fixed `authoring_reviewer`; it must not treat the authoring `final`
stage as a current-main packet or replace the reviewer with the controller model.
New authoring Runs default to automatic completion. A passing independent review
is followed by source-independent deployment, resource and import reconciliation,
exact temporary-artifact cleanup, then Ready publication and enablement only when
the result is `launch_ready`. The Host owns this sequence and its durable retry
evidence. Report completion from the final saved revision; display its complete
graph by default. `validation.valid` on an import scaffold or Draft is insufficient.

Select `completion_policy: manual` only when the user asks to retain a reviewed
Draft or wait for acceptance. Historical Runs without a completion policy retain
their original human acceptance boundary. Review dispatch, result, acceptance and
application must retain one exact proposal hash, source revision and planner
attempt ID. Generic completion and model-side Strict collection cannot accept an
authoring finalizer. A mechanical completion failure requires fixing or resuming
the exact Host step, without another planner or reviewer submission.
