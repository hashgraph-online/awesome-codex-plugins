# Security Policy

## Supported Versions

The public VidSeeds.ai MCP connector package tracks the hosted connector version in `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `server.json`, and `README.md`. Only the latest published package is supported.

## Reporting a Vulnerability

Report security issues privately:

- Email: security@vidseeds.ai
- Security contact file: https://vidseeds.ai/.well-known/security.txt
- Contact form: https://vidseeds.ai/contact/

Do not open a public GitHub issue for vulnerabilities, leaked credentials, auth bypasses, or account-data exposure.

## Connector Security Notes

This package contains no VidSeeds.ai credentials. It references the user-provided `VIDSEEDS_PAT` environment variable so MCP clients can send `Authorization: Bearer ...` to `https://vidseeds.ai/api/mcp`.

If a Personal Access Token is exposed, revoke it at https://vidseeds.ai/settings/mcp-settings and create a new token.

The hosted MCP server rejects cookie/session auth for this connector path. Access is enforced server-side on every call.
