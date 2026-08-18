---
name: openproject-codex
description: Use the OpenProject Codex plugin to inspect and manage work in Codex through the OpenProject API.
---

# OpenProject Codex

Use this plugin when the user wants to work with OpenProject from Codex instead of using the OpenProject UI.

The plugin is intended to cover common project-management actions directly and then fall back to the generic authenticated API tool for any OpenProject module that is not yet represented by a dedicated MCP tool.

## Behavior

- Prefer the MCP tools from this plugin for project, team, membership, and work package operations.
- Default to the configured `OPENPROJECT_DEFAULT_PROJECT` when present, unless the user explicitly asks for another project.
- Use `openproject_connection_status` first if credentials or connectivity are uncertain.
- If configuration is missing, use `openproject_setup_connection` to capture the base URL and API token directly from chat before attempting other actions.
- Use `openproject_test_connection` or `openproject_whoami` after setup when you need a quick verification step.
- API token authentication is preferred, but UI-session authentication is supported when `OPENPROJECT_UI_USERNAME` and `OPENPROJECT_UI_PASSWORD` are configured.
- Use `openproject_list_types`, `openproject_list_statuses`, `openproject_list_priorities`, and `openproject_list_project_assignees` before write operations when a value needs to be discovered.
- Use `assignee_name`, `responsible_name`, `status_name`, `priority_name`, and `customer` on `openproject_create_work_package` and `openproject_update_work_package` when the user provides human-readable values.
- Use `openproject_list_custom_field_options` or `openproject_resolve_custom_field_option` for Customer or other list-style custom fields instead of using the browser UI.
- Use dedicated tools first for projects, users, groups, memberships, versions, categories, queries, work packages, relations, watchers, comments, documents, news, time entries, attachments, file links, boards, wiki pages, meetings, reporting, and bulk task operations.
- Prefer `openproject_my_work` for “my items” or “items assigned to me” requests.
- Prefer the query tools when the user refers to saved views or wants bulk actions across a query result set.
- Prefer the bulk tools for repeated edits instead of issuing many single-item calls one by one.
- Prefer the reporting tools for workload, overdue, burndown, and project health export requests instead of assembling ad hoc summaries by hand.
- If the user needs an OpenProject action that does not yet have a dedicated tool, use `openproject_call_api` against the relevant `/api/v3/...` endpoint instead of sending the user back to OpenProject UI.
- The official OpenProject `/mcp` endpoint is read-only, so write operations should continue to use this plugin's API tools.
- Boards, wiki pages, and meetings may use authenticated UI-backed workflows when the public API surface is incomplete; ensure the UI credential env vars are configured before relying on those tools.

## Required configuration

- `OPENPROJECT_API_TOKEN` is the preferred credential.
- `OPENPROJECT_API_TOKEN_FILE` is supported for local secret-file storage and is the recommended Codex desktop setup.
- `OPENPROJECT_BASIC_API_TOKEN` is supported as a fallback for legacy Basic auth with the `apikey` user.
- `OPENPROJECT_BASIC_API_TOKEN_FILE` is supported for the same legacy Basic-auth fallback.
- `OPENPROJECT_BASE_URL` is required.
- `OPENPROJECT_DEFAULT_PROJECT` is optional.
- `OPENPROJECT_UI_USERNAME` and `OPENPROJECT_UI_PASSWORD` are required for UI-session API fallback and the boards/wiki/meetings UI-backed tools.

The plugin can now persist this configuration locally through `openproject_setup_connection`, so the user does not have to edit `.mcp.json` manually on first use.

## Typical flow

1. Check connection status.
2. Inspect projects, users, groups, memberships, versions, categories, or work packages.
3. Create, update, relate, watch, comment on, assign, or delete work through the MCP tools.
4. Use the bulk tools when the same change must be applied to many items.
5. Use `openproject_call_api` for unsupported modules or advanced API workflows.
