# Security Policy

Never commit or report OAuth tokens, cookies, account data, or local Codex configuration files.

The plugin connects to Exa's official remote MCP OAuth endpoint. It does not require an API key in this repository and must not add credentials to `.mcp.json`.

For a vulnerability in this packaging, open a private GitHub security advisory when available. Security issues in Exa MCP should also be reported to the upstream [Exa MCP](https://github.com/exa-labs/exa-mcp-server) project.
