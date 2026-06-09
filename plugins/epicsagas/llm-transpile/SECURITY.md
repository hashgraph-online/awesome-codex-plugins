# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not report security vulnerabilities through public GitHub issues.**

Instead, use [GitHub Private Vulnerability Reporting](https://github.com/epicsagas/llm-transpile/security/advisories/new).

### Response SLA

| Stage | Target |
|-------|--------|
| Acknowledgement | 48 hours |
| Initial assessment | 5 business days |
| Patch / advisory | 90 days or coordinated disclosure |

### What to include

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact

### Scope

- Memory safety issues (buffer overflows, use-after-free, etc.)
- Input validation bypasses
- Path traversal or injection vulnerabilities
- Supply chain concerns in CI/CD

### Out of scope

- Denial of service via abnormally large inputs (the 10 MiB input limit mitigates this)
- Issues in dependencies not triggered by this project's code
