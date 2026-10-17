# Security Policy

## Supported Versions

epic-harness is in active development. Security fixes are applied to the latest `main` branch.

| Version | Supported |
|---------|-----------|
| `main`  | ✅        |
| < 0.1   | ❌        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Report privately via:
- GitHub Security Advisory: [Report a vulnerability](https://github.com/epicsagas/epic-harness/security/advisories/new)
- Or email the maintainer listed in `package.json`

Include:
- Type of issue (e.g., command injection, secret exposure, prompt injection)
- Affected file(s) or component
- Steps to reproduce
- Potential impact

You can expect an initial response within 7 days.

## Scope

epic-harness is a Claude Code plugin that executes hooks and skills locally. Security-relevant areas:

- **Hooks** (`hooks/`) — execute on tool events; review for command injection
- **Skills** (`skills/`) — auto-triggered prompts; review for prompt injection vectors
- **Evolved skills** (`~/.harness/projects/{slug}/evolved/`) — auto-generated; gated but worth scrutiny
- **Observation logs** (`~/.harness/projects/{slug}/obs/`) — may capture sensitive tool output; not transmitted externally
- **Custom Guard Rules** (`.harness/guard-rules.yaml`) — optional project-local rules that override or supplement global ones. Review before committing to shared repos.

## Out of Scope

- Vulnerabilities in Claude Code itself → report to Anthropic
- Issues in user-supplied scripts run via the harness
