# Security Policy

## Supported versions

Security fixes land on the latest release of magents. Upgrade with Homebrew,
APT, or the latest GitHub release binary.

## Reporting a vulnerability

Open a private GitHub security advisory on
https://github.com/abnegate/magents/security/advisories/new.

Please include:
- Affected version / install method
- Steps to reproduce
- Impact (data exposure, remote code, privilege escalation, etc.)

Do not file public issues for unfixed vulnerabilities.

## Scope notes

magents reads and writes local coding-agent session files and can inject into
live agent sessions when those tools are available. Treat foreign transcripts
and memories as untrusted inert history. The MCP server runs as the installing
user; keep `magents` on a trusted PATH.
