# Security Policy

## Supported Versions

Security fixes are handled on the default branch until the project publishes a
separate long-term support policy.

## Reporting a Vulnerability

Please do not open a public issue for vulnerabilities.

Report privately by emailing `fanjingwen50@gmail.com` with:

- affected version or commit
- reproduction steps
- impact assessment
- any relevant logs, stack traces, or proof-of-concept details

You can expect an initial response within 7 days. If the report is valid, the
maintainers will coordinate a fix and public disclosure timeline.

## Scope

Security-sensitive areas include:

- command execution and sandbox boundaries
- MCP server inputs and workspace path handling
- plugin installation hooks
- secret handling in logs, errors, docs, and examples
- generated repository knowledge artifacts that may contain private source
  details
