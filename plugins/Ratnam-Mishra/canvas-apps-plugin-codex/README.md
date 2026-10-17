# canvas-apps-plugin-codex

![Version](https://img.shields.io/badge/version-2.0.0--codex-blue)
![Platform](https://img.shields.io/badge/platform-Power%20Apps-742774)
![License](https://img.shields.io/badge/license-MIT-green)
 
Power Apps Canvas Apps development with Codex CLI — adapted from Microsoft's
[power-platform-skills](https://github.com/microsoft/power-platform-skills) canvas-apps plugin.

This repository is now packaged as a local Codex plugin via
[`.codex-plugin/plugin.json`](./.codex-plugin/plugin.json).

> Microsoft's official canvas-apps plugin was built for Claude Code.  
> This is a port for **ChatGPT Codex CLI** — giving you the same  
> Power Apps generation workflow with significantly more usage per  
> session on the Plus plan.

## Quick Start

### 1. Install Prerequisites

- [.NET 10 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- [PAC CLI](https://learn.microsoft.com/power-platform/developer/cli/introduction)
- [Codex CLI](https://developers.openai.com/codex/cli)

### 2. Install the Local Plugin

Install or link this directory as a local Codex plugin. The plugin manifest is at
`.codex-plugin/plugin.json`, and the public entrypoints are the `$...` skills in `skills/`.

### 3. Open Your Canvas App in Power Apps Studio

1. Go to [make.powerapps.com](https://make.powerapps.com)
2. Open your canvas app in the designer
3. Enable coauthoring: **Settings → Updates → Coauthoring → ON**
4. Copy the full URL from your browser

### 4. Configure the MCP Server

Then run:
```
$configure-canvas-mcp
```

Paste your Studio URL when prompted. Restart Codex after configuration.

### 5. Generate or Edit Apps

**New app:**
```
$generate-canvas-app Create a canvas app for tracking employee leave requests
```

**Edit existing app:**
```
$edit-canvas-app Add a dark mode toggle to the settings screen
```

**Add a data source:**
```
$add-data-source I need to connect to a SharePoint list called "Projects"
```

## What Gets Generated

Each app is written as `.pa.yaml` files in a subfolder named after your app.
These files are validated by the Canvas Authoring MCP server and auto-synced
to your live Power Apps Studio session.

## Status

This is an adaptation of Microsoft's canvas-apps plugin (preview) for use with
Codex CLI. The core workflow remains the same; this repository now exposes the
workflow through plugin-packaged Codex skills.

Issues with the underlying Canvas Authoring MCP server:
[aka.ms/power-skills-canvas-issues](https://aka.ms/power-skills-canvas-issues)
