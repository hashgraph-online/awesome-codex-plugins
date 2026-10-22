# Security policy

This repository (`@darkmoon_ai/mcp-server`, the Darkmoon MCP server and its Claude Code / Codex plugin manifests) follows the security policy of the ASC-IT organization, which also covers Darkmoon itself: <https://github.com/ASCIT31/.github/blob/main/SECURITY.md>.

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Send a report to **support@asc-it.fr** with the subject `[SECURITY]`, including:

- the repository and version (tag, commit or npm version) concerned,
- a description of the issue and its impact,
- steps or a proof of concept to reproduce it.

You will receive an acknowledgement within 3 working days. We will keep you informed of the progress, coordinate disclosure with you before any public write-up, and credit you in the release notes if you wish.

## Scope

- This MCP server (`src/`), its npm package `@darkmoon_ai/mcp-server`, and the plugin manifests in this repository.
- Darkmoon (`ASCIT31/Dark-Moon`) and its companion repositories, as listed in the organization policy.

The server never caches credentials: a dashboard JWT is requested per call from the Darkmoon Pro instance you configure (`DARKMOON_BASE_URL`). Keep `DARKMOON_USERNAME`, `DARKMOON_PASSWORD` and `DARKMOON_TOKEN` in your MCP client environment, never in a committed file.

Darkmoon is an offensive security tool and `run_pentest` starts a real assessment. Findings produced *by* Darkmoon against third-party targets are out of scope here: only test systems you are authorized to assess, and report those findings to their owners.

## Supported versions

Security fixes are shipped on the latest release.
