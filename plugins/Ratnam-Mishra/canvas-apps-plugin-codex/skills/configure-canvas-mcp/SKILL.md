---
name: configure-canvas-mcp
version: 1.0.0-codex
description: Configure the Canvas Authoring MCP server for Codex CLI. USE WHEN the user says "configure MCP", "set up MCP server", "MCP not working", "connect Canvas Apps MCP", "canvas-authoring not available", "set up canvas apps". DO NOT USE WHEN prerequisites are missing — direct the user to install .NET 10 SDK first.
author: Microsoft Corporation (adapted for Codex by setup plan)
---

# Configure the Canvas Authoring MCP Server for Codex

This skill registers the Canvas Authoring MCP server with Codex CLI by writing to
`~/.codex/config.toml`.

## Step 0 — Check Prerequisites

Run:
```bash
dotnet --list-sdks
```

If no SDK version starting with `10.` is listed, tell the user:

> ⚠️ .NET 10 SDK is required to run the Canvas Authoring MCP server.
> Please install it from https://dotnet.microsoft.com/download/dotnet/10.0 before continuing.

Wait for the user to install it. Re-run the check to confirm before proceeding.

## Step 1 — Ask for the Studio URL

Ask the user:

> What is the URL of your Power Apps Studio session?
>
> Copy the full URL from your browser while your canvas app is open in Power Apps Designer.
> It should look like:
> `https://make.powerapps.com/e/Default-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/canvas/?action=edit&app-id=...`
>
> Also confirm that coauthoring is enabled: Settings → Updates → Coauthoring → ON.

## Step 2 — Extract Parameters from the URL

From the URL the user provides, extract:

- **ENV_ID**: the path segment between `/e/` and the next `/`
  - Example: `Default-91bee3d9-0c15-4f17-8624-c92bb8b36ead`
- **APP_ID**: URL-decode the `app-id` query parameter, then take the last segment after the final `/`
  - Example from `%2Fproviders%2FMicrosoft.PowerApps%2Fapps%2F6fc3e3d1-292b-4281-8826-577f78512e56` → `6fc3e3d1-292b-4281-8826-577f78512e56`
- **MAKER_HOSTNAME**: the hostname portion of the URL (e.g., `make.powerapps.com`)
- **CLUSTER_CATEGORY**: derive from MAKER_HOSTNAME:
  - `make.powerapps.com` → `prod`
  - `make.preview.powerapps.com` → `prod`
  - Any other hostname → `test`

Echo the extracted values to the user for confirmation before writing anything:
> Extracted:
> - ENV_ID: `<value>`
> - APP_ID: `<value>`
> - CLUSTER_CATEGORY: `<value>`
>
> Shall I write these to `~/.codex/config.toml`? (yes/no)

## Step 3 — Write to ~/.codex/config.toml

After user confirms, read the existing `~/.codex/config.toml` if it exists. Preserve all
existing content. Add or replace only the `[mcp_servers.canvas-authoring]` block.

The block to add (substituting the actual extracted values):

```toml
[mcp_servers.canvas-authoring]
command = "dnx"
args = [
  "Microsoft.PowerApps.CanvasAuthoring.McpServer",
  "--yes",
  "--prerelease",
  "--source",
  "https://api.nuget.org/v3/index.json"
]

[mcp_servers.canvas-authoring.env]
CANVAS_ENVIRONMENT_ID = "<ENV_ID>"
CANVAS_APP_ID = "<APP_ID>"
CANVAS_CLUSTER_CATEGORY = "<CLUSTER_CATEGORY>"
```

Write the full updated file back to `~/.codex/config.toml`.

## Step 4 — Confirm and Give Next Steps

Tell the user:

> ✅ Canvas Authoring MCP server configured in `~/.codex/config.toml`.
>
> **You must restart Codex for the MCP server to activate.**
>
> After restarting, verify the setup by asking:
> "List available Canvas App controls"
>
> This should invoke `list_controls` via the `canvas-authoring` MCP server.
> If it does not respond, ensure your Power Apps Studio session is still open
> with coauthoring enabled, then run `$configure-canvas-mcp` again with a fresh URL.
