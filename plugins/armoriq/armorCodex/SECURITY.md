# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in ArmorCodex, please report it privately:

- **Email**: security@armoriq.io
- **Subject prefix**: `[ArmorCodex security]`

Please include:

- A description of the issue and the impact
- Steps to reproduce
- The plugin version affected (see `.codex-plugin/plugin.json`)
- Any proof-of-concept or sample payloads

We aim to acknowledge reports within 2 business days and to ship a fix within 14 days for high-severity issues.

Do not file public GitHub issues for security vulnerabilities. Use the email above so we can coordinate a fix before public disclosure.

## Supported Versions

Only the latest minor release on the `main` branch receives security updates. Pin the immutable git tag (e.g., `v0.2.0`) in your plugin marketplace source for reproducibility.

## Scope

In scope:

- The plugin runtime under `plugins/armorcopilot/`
- The MCP server `armorcodex-policy`
- The hook scripts under `hooks/`
- Audit pipeline + intent token issuance

Out of scope:

- The ArmorIQ backend (`api.armoriq.ai`) — report via the same email but use subject prefix `[ArmorIQ backend security]`
- Third-party dependencies (file with the respective upstream maintainer)
