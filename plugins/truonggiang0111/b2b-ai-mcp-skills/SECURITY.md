# Security Policy

## Supported Versions

Security fixes and manifest hardening updates are actively maintained on the `main` branch and latest tagged release series of `b2b-ai-mcp-skills`:

| Version | Supported |
| --- | --- |
| `1.6.x` | :white_check_mark: Active |
| `1.5.x` | :white_check_mark: Security fixes |
| `< 1.5.0` | :x: Unsupported |

## Reporting a Vulnerability

Please report suspected security vulnerabilities privately before public disclosure:

- **Maintainer:** `@truonggiang0111`
- **Email:** [giang12aa3@gmail.com](mailto:giang12aa3@gmail.com)
- **GitHub Security Advisories:** [Report via GitHub](https://github.com/truonggiang0111/b2b-ai-mcp-skills/security/advisories/new)

Please include:
1. A clear description of the vulnerability and affected file, skill, workflow, or MCP configuration.
2. Reproduction steps or minimal payload.
3. Potential impact (e.g., SSRF, command injection, credential exposure, or prompt injection).

### Response Timeline

- **Initial acknowledgment:** within 48 hours.
- **Triage & fix plan:** within 5 business days.
- **Coordinated disclosure:** once a patched commit and tag are published.

## Security Architecture Notes

- **Zero-key vs optional `APIFY_TOKEN` separation:** Local zero-key examples and companion STDIO tools (`b2b-market-intel-mcp`) query public endpoints (`news.google.com`, `contractsfinder.service.gov.uk`, `clinicaltrials.gov`, `api.wordpress.org`, Atlassian Marketplace REST) with zero API keys; scaled batch execution via `mcp.apify.com` requires an explicit user-supplied `APIFY_TOKEN` or Apify OAuth login at runtime and never stores credentials in this repository.
- **Read-only automation:** Skills, workflows, and remote MCP endpoints perform read-only public intelligence retrieval without shell-command execution defaults or approval bypasses.
