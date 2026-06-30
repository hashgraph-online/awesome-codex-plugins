# Security Policy

## Supported Versions

Security fixes are applied to the latest published release of
`@blade-ai/boss-skill`. Please upgrade to the most recent version before
reporting an issue.

| Version | Supported |
| ------- | --------- |
| 3.9.x   | ✅        |
| < 3.9   | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately so it can
be addressed before public disclosure.

- **Preferred:** Open a [GitHub Security Advisory](https://github.com/echoVic/boss-skill/security/advisories/new)
  for this repository.
- **Alternative:** Email the maintainer at `137844255@qq.com` with the subject
  line `[SECURITY] boss-skill`.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce (proof-of-concept, affected commands, or configuration).
- The affected version(s).

Do **not** open a public issue for security reports.

## Response Process

- We aim to acknowledge a report within **5 business days**.
- We will work with you to confirm the issue and determine its severity.
- Once a fix is available, we will publish a patched release and credit the
  reporter (unless anonymity is requested).

## Scope

This project orchestrates coding-agent pipelines and ships hooks and a CLI.
Of particular interest are:

- Command injection or arbitrary code execution via hooks, the CLI, or
  workflow definitions.
- Path traversal or unintended file writes outside the `.boss/` workspace.
- Leakage of secrets or credentials through logs or generated artifacts.

Thank you for helping keep the project and its users safe.
