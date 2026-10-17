---
name: add-data-source
version: 1.0.0
description: Guide the user to add a data source, connection, or API connector to a Canvas App via Power Apps Studio, then verify and continue. USE WHEN the user asks to add a data source, add a connection, add an API, add a connector, connect to SharePoint / Dataverse / SQL / Excel / OneDrive / Teams / Office 365, or any similar request to make new data available to the app. DO NOT USE WHEN the user is asking to list or describe existing data sources — call list_data_sources or list_apis directly instead.
author: Microsoft Corporation
user-invocable: true
allowed-tools: AskUserQuestion, mcp__canvas-authoring__list_data_sources, mcp__canvas-authoring__list_apis, mcp__canvas-authoring__get_data_source_schema, mcp__canvas-authoring__describe_api
---

Data sources, connections, and API connectors cannot be added by the coding agent — they must be added through the Power Apps Studio interface. This skill informs the user, guides them to add the connection in their Studio session, verifies it is available via the MCP server, and then continues with any pending work.

## Phase 0 — Identify the Connection Type

From the user's request, determine what they want to add and how to verify it:

| Request type | Verify with |
|---|---|
| Data source (SharePoint list, Dataverse table, SQL table, Excel file, OneDrive, etc.) | `list_data_sources` |
| API / connector (Office 365 Users, Teams, custom connector, etc.) | `list_apis` |
| Unclear | Both `list_data_sources` and `list_apis` |

Note what the user is trying to add so you can look for it by name in Phase 3.

## Phase 1 — Inform the User

Explain that this step requires action in their Studio session. Tell the user:

- The coding agent cannot add data sources or connections programmatically — this must be done directly in Power Apps Studio.
- To add the connection, follow these steps in their open Studio session:
  1. Open the **Data** panel in the left sidebar
  2. Click **Add data**
  3. Search for the data source or connector they want (e.g., "SharePoint", "Dataverse", "SQL Server", "Office 365 Users")
  4. Follow the authentication prompts and select the specific table, list, file, or dataset
- Once added, the connection will be available to the MCP server and you can continue.

## Phase 2 — Wait for Confirmation

Use `AskUserQuestion` to pause until the user has completed the steps in Studio:

> "Please add the data source or connection in your Power Apps Studio session. Reply here when it's ready and I'll verify the connection before continuing."

Do not proceed until the user confirms they have added it.

## Phase 3 — Verify the Connection

Once the user confirms, call the appropriate MCP tools to check that the connection is now available:

- If the request was for a **data source**: call `list_data_sources`
- If the request was for an **API / connector**: call `list_apis`
- If the type was unclear: call both in parallel

Scan the results for the connection the user added:

**Found** — Confirm to the user that the data source or connection is now visible to the agent. Include the exact name as returned by the MCP tool (this is how it must be referenced in Power Fx formulas). If it is a data source, call `get_data_source_schema` to retrieve its column names and types, and include the schema summary in your response so it is ready for use in edits. Similarly, for APIs/connectors, call `describe_api` to retrieve the available endpoints and their parameters, and include the schema summary in your response.

**Not found** — Inform the user that the connection is not yet visible. Ask them to:
1. Confirm they completed the Studio steps and the connection appears in the Data panel there.
2. Check that their Studio session is still active (the MCP server must be connected to a live coauthoring session).
3. Let you know when ready to try again.

Use `AskUserQuestion` to wait for their follow-up, then re-run Phase 3.

## Phase 4 — Continue

After the connection is confirmed:

- If the user had a pending task (e.g., "add SharePoint as a data source, then build a gallery"), continue with that work now using the verified connection name and schema.
- If adding the connection was the only request, summarize what was confirmed (connection name, type, and schema if applicable) and suggest a natural next step (e.g., building a screen or gallery that uses the new data).
