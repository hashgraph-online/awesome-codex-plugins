# Security Policy

## Supported Versions

| Version | Status |
|---------|--------|
| 0.1.x | Actively maintained |
| 0.0.x | End of life |

## Reporting Vulnerabilities

Do not open public GitHub issues for security vulnerabilities. Email `security@kreuzberg.dev` instead with:

- Plugin name and version
- Vulnerability description
- Steps to reproduce (if applicable)
- Suggested fix (if you have one)

## Response Timeline

- **Initial response**: within 72 hours
- **Verification and assessment**: within 7 days
- **Fix and patch release**: within 30 days of initial report (or risk disclosure)
- **Public disclosure**: after patch release, or 30 days from receipt, whichever comes first

If you would prefer coordinated disclosure, let us know in your initial report.

## Scope

Security reports are in scope for:

- Skill definitions and execution logic
- Hook scripts and shell commands in the plugins
- MCP server wiring and configuration
- Manifest schema validation

Out of scope:

- Vulnerabilities in upstream binaries (`kreuzberg`, `kreuzcrawl`, `kreuzberg-cloud`) — report those to their respective repositories
- Dependency vulnerabilities in the binaries themselves

For vulnerabilities in the kreuzberg core, kreuzberg-cloud, or kreuzcrawl, report to their respective repositories:

- [kreuzberg](https://github.com/kreuzberg-dev/kreuzberg)
- [kreuzberg-cloud](https://github.com/kreuzberg-dev/kreuzberg-cloud)
- [kreuzcrawl](https://github.com/kreuzberg-dev/kreuzcrawl)

## General Security Practices

- Keep your harness (Claude Code, Cursor, etc.) and all plugins up to date
- Rotate API keys if you suspect compromise
- Review skill manifests before installing plugins from untrusted sources
- Use environment variables or configuration files for sensitive credentials, never embed them in prompts

## Acknowledgments

Thank you for helping keep Kreuzberg Plugins secure.
