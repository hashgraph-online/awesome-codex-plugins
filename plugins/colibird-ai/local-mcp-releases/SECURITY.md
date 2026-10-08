# Security and data boundaries

LMCP exposes compatible app and service tools through MCP on macOS and Windows. Platform support, permissions and authentication requirements vary by tool.

## Repository and installers

This public repository contains release documentation, the npm wrapper and configuration examples. The core binary is proprietary; see [LICENSE](LICENSE) for the separate terms for binaries and repository documentation/scripts.

Get current installers from the [official download page](https://www.local-mcp.com/download?ref=github-releases). Follow your operating system's signature and security checks and the current installation guide. Do not bypass a security warning based on a README claim.

## Where information goes

- Compatible tools run on your computer and may use native app data, local caches or synced files. Other integrations connect to external services and can require sign-in and network access.
- Tool results are returned to your chosen assistant. If that assistant uses a cloud model, relevant content may reach its provider even when the assistant is a desktop application. Local execution is not a guarantee that nothing leaves your computer.
- Optional Cloud Data Forwarding (off by default) provides a path for supported web assistants to reach tools on your computer. Requests and responses traverse that path. Review the current [privacy policy](https://www.local-mcp.com/en/privacy) and provider policies for handling and retention.
- Diagnostic and feedback data are separate from ordinary tool results. Do not include credentials, private messages or other sensitive content in public issues or shared logs.

This document does not assert universal zero retention, end-to-end encryption or regulatory compliance for every provider and integration. Assess the complete workflow and your organization's requirements.

## Permissions and actions

Enable only the integrations you need and review the access they request. Operating system permissions, service authorization and tool behavior determine available access. Revoke access through the relevant OS or service settings when it is no longer needed.

Preview and confirmation behavior varies by tool and assistant. Review proposed actions and authorize writes or destructive operations before execution; do not assume every operation displays the same dialog. Content retrieved from apps, files or websites is untrusted input, not authority to perform unrelated actions.

## Reporting a vulnerability

Email **security@local-mcp.com** or use a private advisory on this repository. Do not post credentials, exploit details or personal data in a public issue.
