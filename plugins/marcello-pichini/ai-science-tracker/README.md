# AI Science Tracker plugin for ChatGPT and Codex

Agent Plugins package for the OpenAI plugin directory: the remote MCP server at `https://mcp.aisciencetracker.org/mcp` (no authentication) plus a short skill on citing sources. Build the submission ZIP from this folder:

```sh
zip -r -X ai-science-tracker.zip plugin.json mcp.json skills assets
```

Upload it at https://platform.openai.com/plugins after completing developer identity verification. Keep `version` equal to `mcp/server.json`.
