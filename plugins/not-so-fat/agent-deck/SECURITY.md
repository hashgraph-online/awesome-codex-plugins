# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| Latest release on npm (`agent-deck` / `@agent-deck/*`) | Yes |
| Older published semver tags | Best-effort; please upgrade |

Security fixes ship in new releases on GitHub and npm. Pin to a current release when possible.

## Reporting a vulnerability

**Do not** open a public GitHub issue for security reports.

Use [GitHub Security Advisories](https://github.com/not-so-fat/agent-deck/security/advisories/new) for private disclosure.

Include:

- Affected version and install path (npm global, monorepo, Codelink plugin bundle)
- Impact (secret exposure, remote code execution, unauthorized local network access, etc.)
- Reproduction steps or a minimal PoC
- Whether the issue is already public

### Response SLA

| Stage | Target |
|-------|--------|
| Acknowledge receipt | Within **3 business days** |
| Initial severity triage | Within **7 business days** |
| Fix or mitigation plan for confirmed High/Critical | Within **30 days** (or coordinated disclosure timeline) |

We will confirm when a fix is released and credit reporters who want attribution (unless you prefer anonymity).

## Scope notes

Agent Deck is a **local** product:

- The MCP daemon binds to **`127.0.0.1` only** (default ports: MCP `1110`, OAuth callback `1111`, dashboard as configured). It is not intended as a public internet service.
- API keys and secrets are stored in the **OS keychain / local vault**, not in the repo or the Codex/Claude plugin bundle.
- The marketplace plugin bundle (`.codex-plugin/`, `skills/`, `.mcp.json`) points at the local HTTP MCP URL; the daemon must already be running (`agent-deck setup` / `agent-deck start`). Skills are thin protocol stubs — they do not mirror playbook bodies or embed credentials.

Out of scope for this policy: third-party MCP servers registered on a deck, host IDEs (Codex, Claude Code, Cursor), and Hol/Hashgraph Online marketplace infrastructure.

## Hardening expectations for contributors

- No hardcoded secrets in source, fixtures that look like live tokens, or CI workflows with `write-all` without justification
- Prefer SHA-pinned GitHub Actions
- Dangerous shell patterns in skills or MCP `command` entries will fail marketplace scanners — keep skills read-only guidance and let the user run install commands
