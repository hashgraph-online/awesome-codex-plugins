# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in spec-superflow, please report it via GitHub's [private vulnerability reporting](https://github.com/MageByte-Zero/spec-superflow/security/advisories/new) or email **magebyte@163.com**.

**Do not open a public issue** for security vulnerabilities.

## What to Include

- A clear description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential mitigations you've identified

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Status Update**: Within 5 business days
- **Resolution**: We aim to patch confirmed vulnerabilities within 30 days

## Scope

spec-superflow is a plugin that runs locally. Security considerations include:

- **Session-start hooks**: Hook scripts execute with the user's shell privileges. Review hook changes carefully.
- **Skill instructions**: Skills contain AI agent instructions. Maliciously crafted skills could instruct the agent to execute harmful commands.
- **CLI tools**: The `ssf` command runs with Node.js privileges and reads/writes local files.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest release (`main` branch) | ✅ |
| Older releases | ❌ |

**This project does not offer long-term support (LTS) for older versions.**
