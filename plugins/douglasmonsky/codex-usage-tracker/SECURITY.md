# Security Policy

## Supported versions

Security fixes target the latest public release and current `main`.

## Report a vulnerability

Use a private GitHub security advisory when advisories are available. Otherwise
contact the maintainer directly. Do not paste real Codex logs, prompts,
responses, reasoning, tool output, credentials, private repository names,
branches, or full local paths into a public issue.

## Local-data boundary

Codex Usage Tracker processes user-owned local session metadata and keeps its
database and services local. It does not add telemetry or intentionally
transmit usage data to a hosted service.

Local does not mean harmless to share. Thread labels, projects, tool names,
resource paths, timestamps, model usage, costs, and allowance observations can
reveal private work context. Review and minimize any query result, screenshot,
diagnostic, or export before sharing it.

The clean replacement:

- stores structural facts needed by accepted question contracts;
- does not copy raw prompt, response, reasoning, command, patch, or tool-output
  bodies into SQLite;
- does not promise sanitization, redaction, or secret filtering;
- treats secrets already present in local source logs as the user's
  responsibility;
- uses synthetic fixtures for tests, benchmarks, docs, and screenshots.

The public 0.28 implementation has its own frozen behavior, recorded in
`docs/archive/spike/KERNEL_STABLE_CONTRACT_0_28.md`. Those compatibility and
privacy modes are not requirements for the replacement.

## Contributor boundary

Never commit real local usage data, databases, generated local reports, raw
transcripts, credentials, or private identifiers. Security reproductions must
use the smallest synthetic fixture that demonstrates the defect.
