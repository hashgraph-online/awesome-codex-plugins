# Security Policy

## Scope

`stark` is a documentation + reference plugin. It does not execute untrusted code or accept user data. The primary attack surface is the `scripts/` directory, which contains small Python helper utilities for platform detection and token export.

## Supported versions

The latest tagged release is supported. Earlier versions are not maintained.

## Reporting a vulnerability

If you find a security issue:

1. Do **not** open a public issue.
2. Open a private security advisory via GitHub: https://github.com/f0d010c/stark/security/advisories/new
3. Include reproduction steps and impact assessment.

You should expect an initial response within 14 days.

## Out of scope

- Vulnerabilities in third-party dependencies (file with the dependency upstream)
- Issues in user-generated output (the plugin guides design choices; it does not validate generated code for security)
- Issues in local visual QA projects that are not part of this repository
