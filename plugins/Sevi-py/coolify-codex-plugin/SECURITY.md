# Security Policy

## Supported Versions

Security fixes are handled on the default branch until the plugin publishes tagged releases.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately through GitHub security advisories for this repository, or by contacting the repository owner directly if advisories are unavailable.

Do not include Coolify API tokens, server IPs, private keys, environment variable values, deployment logs containing secrets, or other sensitive Coolify Cloud or instance data in public issues.

## Operational Notes

- The plugin can save a local Coolify connection so users do not need shell environment variables.
- Saved tokens use the operating system credential store when available: macOS Keychain, Windows Credential Manager, or Linux Secret Service via `secret-tool`. Otherwise, they are stored in a local config file under `CODEX_HOME` or `~/.codex` with owner-only permissions.
- The plugin still reads `COOLIFY_API_TOKEN` and `COOLIFY_BASE_URL` as fallbacks for automation.
- If no base URL is configured, the plugin uses Coolify Cloud at `https://app.coolify.io`.
- Tool responses redact sensitive-looking fields by default.
- Use a scoped Coolify token with only the permissions needed for the task.
