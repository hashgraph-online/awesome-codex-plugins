# MCP-Only Bifrost Work

Use this path when Bifrost MCP tools are available but the CLI or local source filesystem is not. Treat mutations as live changes on the connected instance.

## Establish context

Use the available list/get tools to identify the target organization, existing entity, access controls, and dependencies. Do not infer instance or Solution ownership from names alone.

MCP tools primarily operate on live instance entities and `_repo` content. If an entity is Solution-managed, stop and route the change through its Solution source/deploy workflow; do not create a loose duplicate to bypass ownership.

## Discover, read, then write

Tool names can vary by installed server version. Search the available tools and use their provided schemas rather than inventing a name or argument.

Common entity patterns are:

- `list_*` and `get_*` for discovery;
- `create_*`, `update_*`, and `delete_*` for live entities;
- `list_content`, `read_content_lines`, and `get_content` for `_repo` files;
- `bifrost_file_search` for grep-style search over workspace and Solution source. It returns 25 results per page; follow its `guidance` / `next_cursor` for more, or pass `output_mode="files"` to find where something lives first;
- `patch_content` for focused source edits;
- `replace_content` for complete replacement;
- `bifrost_workflow_register`, `bifrost_workflow_validate`, and `bifrost_workflow_execute` for loose workflows;
- `bifrost_app_validate`, publish/status tools, and dependency tools for v1 apps.

Always read the current entity/file before mutation. Prefer `patch_content` when it can express the change safely; use full replacement only after preserving unrelated content. Read back and validate after writing.

## Source and registration

Editing a Python file does not create a workflow record. Register each decorated callable that should execute, including organization/access/roles. Editing an existing registered function body keeps its registration; preserve the record when renaming/moving rather than creating an accidental second workflow.

An agent tool must reference an `@tool`-decorated workflow registration. Source presence or a plain `@workflow` is insufficient.

Editing v1 app source also requires an existing `inline_v1` app record and compatible scope. Apply `apps-v1.md` and `app-quality.md`; validate and inspect the rendered app rather than stopping after source replacement.

## Entity mutations

Before create/update:

1. Get the target and its dependents.
2. Confirm organization, access level, roles, and policies.
3. Send complete list fields for agents and other replacement-style updates.
4. Re-read the result and exercise the consuming behavior.

Use exact tool descriptions for required fields. Do not translate a remembered CLI flag into a guessed MCP argument.

## Known parity boundary

Some older form, agent, table, app, and event MCP tools predate the thin HTTP-wrapper pattern and may not match every REST side effect or permission check. Roles, configs, integrations, organizations, and current workflow lifecycle tools use the newer REST-wrapper pattern.

When behavior is ambiguous or production-sensitive, inspect the tool result carefully and prefer a verified REST-wrapper tool if one is available. Do not add direct ORM/repository behavior to new MCP tools; new platform MCP tools should call the REST endpoint.

## Verification and handoff

- Validate edited code/content with the available validation tool.
- Execute the workflow or inspect the app/entity as a realistic caller.
- Test permission denial when access changed.
- Report every live mutation and any source/deploy work that MCP could not perform.
- Never claim that a Solution source change was made when only a loose live entity was changed.
