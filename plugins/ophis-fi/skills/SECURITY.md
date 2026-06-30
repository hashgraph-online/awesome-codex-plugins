# Security Policy

## Supported versions

| Version | Supported |
| --- | --- |
| Latest published plugin (`ophis@ophis-fi`) and the live MCP server | yes |
| Older tagged releases | no |

## Reporting a vulnerability

If you find a security issue in the Ophis plugin, the Ophis MCP server, or the `ophis-swap` skill, please report it privately. Do not open a public issue for a vulnerability.

- Email: contact@ophis.fi
- Please prefix the subject with "SECURITY" so it is routed quickly.

Include a clear description, the affected component (plugin, MCP server, or skill), reproduction steps, and the impact you observed. We aim to acknowledge a report within 3 business days and to keep you updated while we investigate.

## Scope

The Ophis MCP server is keyless and non-custodial: it builds an unsigned order, the agent signs it with its own wallet, and the receiver is pinned to the signer. Reports about order construction, the token resolver (`resolve_token`), slippage bounds, or app-data handling are in scope. The signing key never leaves the agent, so it is never transmitted to or held by Ophis.

## Disclosure

We follow coordinated disclosure. Please give us a reasonable window to ship a fix before any public write-up, and we will credit reporters who want it.
