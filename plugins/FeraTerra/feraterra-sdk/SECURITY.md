# Security Policy

## Supported Versions

| Version | Supported |
| :--- | :--- |
| `4.9.x` | Yes |
| `< 4.9.0` | No |

## Reporting a Vulnerability

Please **do not** open public GitHub issues for suspected security vulnerabilities.

Instead, report vulnerabilities privately via GitHub Security Advisories at:
`https://github.com/FeraTerra/feraterra-sdk/security/advisories/new`

Include a clear reproduction step, affected module/version, and impact summary. Note that client-side keys (`EthWalletSigner`, `ARENA_API_SECRET`) never leave your local process unless explicitly transmitted to an endpoint you configure, and `--max-order-notional-usd` / `--read-only` MCP guardrails are enforced locally before network dispatch.
