# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | ✅ Active  |

## Reporting a Vulnerability

**Do not open a public GitHub Issue for security vulnerabilities.**

Use [GitHub's private vulnerability reporting](https://github.com/RBraga01/a-team/security/advisories/new) to report issues confidentially.

Include in your report:
- Which agent, skill, or rule file is affected
- A description of the vulnerability and potential impact
- Steps to reproduce (if applicable)
- Any suggested fix

You can expect an acknowledgement within 48 hours and a resolution or status update within 7 days.

## Scope

A Team is infrastructure for AI coding assistants — it does not handle user authentication, store secrets, or connect to external services directly. Relevant security concerns include:

- **Prompt injection** — a rule or skill file that could be exploited to manipulate agent behaviour
- **Path traversal** — any agent instruction that could be abused to read or write outside the project directory
- **Secret exposure** — any default configuration that could inadvertently expose credentials
- **Supply chain** — compromised dependencies in the test runner (`tests/package.json`)
