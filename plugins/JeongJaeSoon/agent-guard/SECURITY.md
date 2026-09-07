# Security Policy

## Supported versions

Agent Guard ships fixes on the latest release line. Use the most recent tag:
`@v3` for the GitHub Action, and the latest release for CLI and plugin installs.

| Version | Supported |
|---|---|
| Latest release (3.x) | ✅ |
| 2.x / `@v2` | Security fixes only |
| 1.x / `@v1` | Best effort |

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue for a
sensitive report.

- Preferred: GitHub [private vulnerability reporting](https://github.com/JeongJaeSoon/agent-guard/security/advisories/new).
  This keeps the details private until a fix ships.

We aim to acknowledge reports within a few days and to coordinate disclosure
once a fix or mitigation is available.

## Scope

Agent Guard is a deterministic, thin guardrail — not a DLP system, EDR, or
vault. It has documented blind spots by design (see
[Known Limitations](https://github.com/JeongJaeSoon/agent-guard#known-limitations)):
gitignored files are not scanned, only the git work tree is covered,
path/command blocking uses fixed lists, tool-output masking is best-effort,
Bash detection is pattern-based, and commands a user runs through the host's
interactive shell escape (for example, a `!`-prefixed command) never reach a
tool hook and so are not scanned or masked.

Behavior that falls within those documented limitations is expected, not a
vulnerability. Suggestions to narrow a blind spot are welcome as regular
issues or pull requests. Reports of a bypass that defeats a control the project
claims to enforce are in scope — please report those privately as above.
