# Security Policy

## Supported Versions

The latest minor release of Digital Marketing Pro receives security fixes. Older minor versions are not patched — please update first.

| Version | Supported |
|---------|-----------|
| 3.7.x   | ✅ |
| 3.6.x   | ⚠️ Security fixes only when trivially backportable |
| < 3.6   | ❌ Please upgrade |

## Reporting a Vulnerability

**Do NOT open a public GitHub Issue for security vulnerabilities.** Public Issues expose users before a fix is available.

### How to report

Use GitHub's [Private Security Advisory](https://github.com/indranilbanerjee/digital-marketing-pro/security/advisories/new) feature to report privately. The maintainer will be notified directly and can collaborate with you on a fix before disclosure.

If you cannot use Private Security Advisories, contact the maintainer via the email listed on [indranil.in](https://indranil.in) with the subject line `[DMP Security]`.

### What to include

- A clear description of the vulnerability and its impact
- Steps to reproduce (with example commands, payloads, or files if applicable)
- Affected version(s) and surface (Claude Code CLI / Claude Code IDE extension / Anthropic Cowork)
- Suggested remediation if you have one
- Whether you'd like credit in the security advisory (and how you'd like to be named)

### What you can expect

- **Acknowledgement within 48 hours** that we've received your report
- **Initial assessment within 7 days** with severity classification and tentative timeline
- **Coordinated disclosure** — we'll work with you on a disclosure date that gives users time to update
- **Credit in the published advisory** unless you prefer to remain anonymous
- **No bug bounty program** — this is an open-source project maintained by an individual. We deeply appreciate responsible disclosure.

## Scope

In scope:
- The DMP plugin itself (skills, scripts, agents, manifests, MCP catalog)
- The example C2PA signing flow (`scripts/embed-c2pa.py`)
- The Python scripts (any path traversal, command injection, or unsafe deserialization)
- Plugin manifest parsing edge cases that could be exploited

Out of scope:
- Vulnerabilities in Claude Code or Anthropic Cowork themselves — please report to Anthropic
- Vulnerabilities in third-party MCP servers (Slack, HubSpot, etc.) — please report to those vendors
- Vulnerabilities in upstream Python dependencies — please report to those projects (and let us know so we can upgrade)
- Anthropic Claude model behavior issues — please report via Anthropic's official channels
- Reports from automated scanners without proof of exploitability

## Coordinated Disclosure Timeline

For valid reports:
- **Day 0** — Report received, acknowledged within 48 hours
- **Day 7** — Initial severity assessment shared with reporter
- **Day 7–30** — Fix developed, tested, and a patch release prepared
- **Day 30** — Fix released to GitHub `main` and bumped on the marketplace; security advisory drafted
- **Day 30–45** — Coordinated disclosure window (lets users update)
- **Day 45** — Public advisory published with full details and credit

We may move faster than this timeline for actively-exploited issues. We will not move slower without explicit reporter agreement.

## Hardening Recommendations for Operators

If you are running DMP in a sensitive environment (multi-tenant agency setup, regulated industry brands):

1. **Never commit `.mcp.json` with real API keys.** Use env vars or a secret manager — `.mcp.json.example` is the safe template.
2. **Treat brand data at `~/.claude-marketing/<brand-slug>/` as sensitive.** It contains client strategy documents. Apply filesystem ACLs as you would any client PII.
3. **Rotate Anthropic API keys quarterly.** Use `/usage` to monitor for anomalous consumption.
4. **Review SKILL.md edits in PRs.** Skills run with whatever permissions Claude Code has. Treat skill modifications like code review for production systems.
5. **Pin the plugin version in agency environments.** Don't auto-update production agencies on the same day as release — let community testing happen first.
