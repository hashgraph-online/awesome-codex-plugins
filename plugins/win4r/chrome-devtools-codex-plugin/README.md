# Chrome DevTools Codex Plugin

This repository wraps the upstream [`chrome-devtools-mcp`](https://github.com/ChromeDevTools/chrome-devtools-mcp) package as a Codex plugin that is ready for one-click installation in the Codex app.

It keeps the runtime thin on purpose:

- MCP server: `npx -y chrome-devtools-mcp@latest`
- Plugin metadata: `.codex-plugin/plugin.json`
- Codex MCP wiring: `.mcp.json`
- Focused skills for live browser debugging and performance work

## What This Plugin Gives You

- a Codex-native plugin manifest
- a zero-code wrapper around the upstream Chrome DevTools MCP server
- a browser debugging skill for live UI issues
- a performance skill for Lighthouse, traces, and Core Web Vitals work

## Requirements

The upstream server currently requires:

- Node.js 20.19 or a newer maintenance LTS
- npm
- Chrome stable or newer

## Install Behavior

The plugin launches the upstream MCP server with this config:

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

That means the plugin tracks upstream releases automatically and does not vendor or fork the actual MCP server.

## Customize

If you want different runtime behavior, edit [`./.mcp.json`](./.mcp.json) and add upstream-supported flags such as:

- `--headless`
- `--isolated`
- `--browser-url=http://127.0.0.1:9222`
- `--no-usage-statistics`

## Fallback Without The Plugin Layer

If you only want the MCP server and do not need plugin packaging, the upstream Codex command is:

```bash
codex mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest
```

## Repository Layout

- `.codex-plugin/plugin.json`: Codex plugin manifest
- `.mcp.json`: plugin-local MCP server definition
- `agents/openai.yaml`: plugin interface metadata
- `skills/chrome-devtools/`: live browser debugging guidance
- `skills/chrome-performance/`: performance analysis guidance
- `assets/`: plugin icons
