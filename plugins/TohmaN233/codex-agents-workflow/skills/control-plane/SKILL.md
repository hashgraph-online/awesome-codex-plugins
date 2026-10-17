---
name: workflow-control-plane
description: "Keep the host Workflow plane available and route concrete tasks to matching Ready Workflows. Automatically use enabled Workbench Roles for useful ordinary subtasks when no Ready Workflow matches; the user need not request a Role. Manage Workflows on request. Do not start Runs for planning, discussion, comparison, audit, or experiment design."
---

# Workflow control plane

**Automatic Roles are the default.** When no Ready Workflow matches a concrete
request and a helper would materially help, automatically select an enabled
Workbench Role and launch its returned adapter. Follow [Role orchestration](../orchestration/SKILL.md).

The persistent control plane is available without a matching Workflow. Workflows
cover end-to-end tasks; Roles assign ordinary helpers through the orchestration
skill and never enter running Workflow nodes.

A failed Run is unfinished. On `completion_satisfied:false` or
`recovery_required:true`, inspect the failed node and evidence, repair or retry
that unit. Report completion only when final acceptance makes the Run `succeeded`.

## Read the route for this request

Read only the relevant route; do not load authoring instructions into execution context.

- **Exact Ready startup or node packet already supplied:** call its named tool with the supplied business arguments and that tool's Host invocation preset. Follow the returned action. The tool and packet supply the execution contract; Host reads the supplied inputs_path and checks/registers dependencies during startup. No input-file reread, prepare_environment call, execution-reference read, tool inventory, capabilities call, listing or routing is required. Read a reference only for a missing detail or an observed failure.
- **Execute an unselected concrete task:** read [execution](references/execution.md) to select its Ready Workflow and start it.
- **Generate from a Skill or brief:** read [authoring](references/authoring.md). It links the semantic contract, independent review, and mandatory completion cleanup.
- **Inspect, edit, publish or delete an existing Workflow:** read [editing](references/editing.md).
- **Export or install a Workflow package:** read [packages](references/packages.md).
- **Recover a failed/interrupted Run or its control:** read [recovery](references/recovery.md).
- **Remove superseded authoring Drafts:** read [authoring cleanup](references/authoring-cleanup.md).
- **Unavailable tools or UI connection failures:** read [connection diagnosis](references/connection.md).
- **Meta:** planning, comparing, auditing, evaluating, or designing experiments about Skills or Workflows. Work directly. Merely mentioning this plugin is not permission to start a Run.

Open UI with `codex_agents_workflow_app` or `codex_agents_workflow_settings`; no Run/thread is created. Use `codex_agents_workflow_console` for standalone or unsupported hosts. Keep transport/bootstrap out of model context. Report the observed error; never invent receipts, hide App failures or substitute execution.
