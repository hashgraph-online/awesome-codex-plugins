# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :---: |
| 1.0.x | Yes |

## Reporting a Vulnerability

Please report security issues privately to `agentarenastudio@proton.me`. Do not open public GitHub issues for undisclosed vulnerabilities. We acknowledge reports within 48 hours and ship verified fixes promptly.

## Security Design

- All bundled skills and the remote MCP connector (`https://brand-checker.appwrite.network/mcp`) are strictly read-only (`readOnlyHint: true`, `destructiveHint: false`).
- Zero credentials, private keys, or source files are uploaded.
