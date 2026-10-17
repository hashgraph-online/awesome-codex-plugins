# Security Policy

## Scope

This plugin is instruction-only: it ships a single `SKILL.md` (plus manifest metadata) and
contains no MCP servers, hooks, executables, or network calls. The optional
`install-other-tools.sh` script is user-run, transparent, and only copies the skill into
`~/.codex/skills/` / `~/.kimi-code/skills/` and appends a clearly-labeled section to those
tools' global `AGENTS.md`.

## Reporting a Vulnerability

If you find a security issue (for example, a way this plugin's instructions could be abused
for prompt injection), please open a GitHub issue at
https://github.com/jananthan30/ml-pipeline/issues or use GitHub's private vulnerability
reporting on the repository. Reports are typically triaged within a week.

## Supported Versions

Only the latest release on `main` is supported.
