# Security Policy

Agent Kit is a human-in-the-loop harness for AI-assisted IDEs. It installs prompt
and workflow files into a developer's project and ships a local CLI plus a
loopback observability panel (Mission Control). Reports about any of those
surfaces are welcome.

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest `5.x` release of `@dadado/agent-kit-cli` | Yes |
| Anything older | No — upgrade first, then re-test |

There is no long-term-support branch. Fixes land on the latest release line.

## Reporting a vulnerability

**Do not dump proof-of-concept detail into a public issue before a private channel exists.**

Use, in order of preference:

1. **GitHub private vulnerability reporting (preferred when enabled)** — on the public
   repository, go to the **Security** tab → **Report a vulnerability**. This
   opens a private advisory visible only to you and the maintainers.
2. **Public issue as a private-channel request (fallback)** — if private vulnerability
   reporting is unavailable (button missing, fork without PVR, or reporting fails),
   open a public issue that contains **no** technical detail, no proof of concept,
   and no reproduction steps. Say only that you have a security report and need a
   private channel. A maintainer will open a private advisory (or email) and invite
   you to it.

### What to include

- Affected surface: CLI command, installed L0 template, registry skill, Mission
  Control endpoint, or the sync/CI tooling.
- Version: output of `npx @dadado/agent-kit-cli --version`, plus the value of
  `version` in the project's `.cursor/agent-kit.json` if the issue is about
  installed files.
- Environment: OS, Node version, IDE (Cursor / VS Code / Windsurf).
- Reproduction steps and observed vs expected behavior.
- Impact you believe it has.

### What to expect

This project is maintained on a best-effort basis by a small team. There is no
contractual response time and no bug bounty. Reports are triaged in the order
received; a fix, a mitigation, or an explicit "won't fix, here's why" is the
intended outcome of every valid report. Please allow a reasonable window for a
fix before disclosing publicly, and tell us if you have a disclosure deadline.

Credit is given in the advisory and the changelog unless you ask otherwise.

## Scope and known posture

These are documented design decisions, not vulnerabilities. Please read them
before reporting.

- **Mission Control is local and single-developer.** It binds `127.0.0.1` by
  default. The opt-in LAN mode (`/dashboard-broadcast`) binds a non-loopback
  interface only with explicit intent and a required session token. Config writes
  stay loopback-only and allowlisted. Multi-user or internet-facing hosting is
  out of scope by design — see
  [Mission Control production-ship constraints](docs/getting-started.md#mission-control-production-ship-constraints).
- **Continuous plan execution runs with the IDE sandbox disabled.** `/run-plan`
  needs filesystem and git access to do its job. Plan to-dos and registry skills
  therefore function as direct agent instructions and must be reviewed before
  they are run — see
  [Security considerations](docs/getting-started.md#security-considerations).
- **Prompt content is not a trust boundary.** A malicious skill, plan, or rule
  that a user installs on purpose can instruct the agent. Report the *delivery*
  path (for example: a way to get unreviewed content into an install) rather than
  the fact that instructions are followed.

In scope and worth reporting: arbitrary file write or command execution from CLI
input, path traversal in install or update, credential or token leakage, the
public sync allowlist leaking private paths, an unauthenticated mutation reachable
on a non-loopback bind, and dependency issues with a practical exploit path here.

## Secrets

The public repository contains no secrets, and CI secrets live only on the
private factory repository. If you believe a credential has been committed
anywhere in the history, report it through the private channel above rather than
in an issue.

## Related

- [Code of Conduct](.github/CODE_OF_CONDUCT.md)
- [Support](.github/SUPPORT.md)
- [Contributing](docs/CONTRIBUTING.md)
