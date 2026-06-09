# Security Policy

## Supported Versions

Security updates are provided for the current maintained release line.

| Version line | Status |
| --- | --- |
| `2.x` latest | Supported |
| pre-`1.0` historical releases | Not supported |

---

## Security Model

`codex-multi-auth` handles OAuth credentials and account metadata locally.

Key controls:

- PKCE-based OAuth flow.
- Local storage under `~/.codex/multi-auth` (or `CODEX_MULTI_AUTH_DIR`).
- Refresh-token lifecycle management and account health isolation.
- Runtime rotation proxy is loopback-only, enabled by default, and authenticated with a local client key. Users can opt out with `codex-multi-auth rotation disable` or `CODEX_MULTI_AUTH_RUNTIME_ROTATION_PROXY=0`.
- Packaged Codex app bind is reversible and stores backup/router metadata under `~/.codex/multi-auth/app-bind/`.
- No project-owned telemetry backend.

---

## Operator Security Practices

- Do not share `~/.codex/` directories.
- Never commit auth files, logs, or cache artifacts.
- Review connected apps in ChatGPT settings periodically.
- Enable debug/body logging only for short-lived troubleshooting sessions.

Sensitive logging toggles:

- `ENABLE_PLUGIN_REQUEST_LOGGING=1` (metadata)
- `CODEX_PLUGIN_LOG_BODIES=1` (raw bodies; sensitive)

---

## Vulnerability Reporting

If you discover a vulnerability:

1. Do not open a public issue.
2. Contact the maintainer privately via GitHub profile contact channel.
3. Include:
   - vulnerability description
   - reproduction steps
   - impact assessment
   - suggested mitigation (optional)

Target response time: within 48 hours.

---

## Responsible Disclosure

- Fixes are prepared before public disclosure.
- Reporter attribution is provided unless anonymity is requested.
- Disclosure timing is coordinated to reduce user risk.

---

## Out of Scope

The following are not treated as vulnerabilities in this repository:

- OpenAI platform outages.
- Account/subscription entitlement limitations.
- Expected upstream rate limiting.
- Requests to bypass OpenAI terms or controls.

---

## Dependency and Release Hygiene

Security override rationale (`package.json` -> `overrides`):

- `hono`: pinned to `4.12.21` to keep builds out of the vulnerable `<4.12.21` range reported in `GHSA-3hrh-pfw6-9m5x`, `GHSA-2gcr-mfcq-wcc3`, `GHSA-xrhx-7g5j-rcj5`, and `GHSA-f577-qrjj-4474` (Set-Cookie injection, `app.mount()` path-decoding, IPv6 IP-restriction bypass, and JWT scheme-acceptance advisories).
- `rollup`: pinned to `^4.59.0` to keep the Vite and Vitest transitive graph above the vulnerable `<4.59.0` range surfaced by `npm audit`.

Before release and after dependency changes:

```bash
npm run audit:ci
npm run lint
npm run typecheck
npm test
npm run build
```

---

## Questions

For non-vulnerability security questions, open a GitHub discussion.

---

This project is not affiliated with OpenAI.
For OpenAI platform security concerns, contact OpenAI directly.
