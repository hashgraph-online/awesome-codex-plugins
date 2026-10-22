# Security Policy

## Supported Versions

Security updates are provided for the current maintained release line.

| Version line | Status |
| --- | --- |
| `2.x` latest | Supported |
| `@ndycode/codex-multi-auth` (legacy scoped name) | Not supported — migrate to `codex-multi-auth` |
| pre-`1.0` historical releases | Not supported |

---

## Security Model

`codex-multi-auth` handles OAuth credentials and account metadata locally.

Key controls:

- PKCE-based OAuth flow.
- Local storage under `~/.codex/multi-auth` (or `CODEX_MULTI_AUTH_DIR`).
- Refresh-token lifecycle management and account health isolation.
- Runtime rotation proxy is loopback-only, enabled by default, and authenticated with a local client key. Users can opt out with `codex-multi-auth rotation disable` or `CODEX_MULTI_AUTH_RUNTIME_ROTATION_PROXY=0`.
- Opt-in native app binding also accepts the exact unexpired desktop token from the local file auth store, or an unexpired enabled managed-account token. These credentials authorize access to the configured local inference pool. Native binding preserves the desktop login; it does not grant upstream model entitlements.
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

- `hono`: pinned to `4.13.13` to keep builds out of the vulnerable `<=4.13.4` range. That range covers `GHSA-8j4g-w8fx-2239`, `GHSA-f23p-vx2j-j53r`, `GHSA-79qm-7rj5-m7r9`, `GHSA-54fx-42gc-7vw4`, `GHSA-gqvv-2mrq-wpjv`, `GHSA-g6gw-c38x-mqfc`, and `GHSA-crvj-82cr-hjcx` (CORS ReDoS, `memo()` cross-request SSR disclosure, proxy `Connection` header passthrough, Language middleware DoS, `toSSG()` path traversal, unbounded `parseBody()` nesting, and query parsing past the URL fragment). The pin also covers the earlier `GHSA-3hrh-pfw6-9m5x`, `GHSA-2gcr-mfcq-wcc3`, `GHSA-xrhx-7g5j-rcj5`, and `GHSA-f577-qrjj-4474` advisories (Set-Cookie injection, `app.mount()` path-decoding, IPv6 IP-restriction bypass, and JWT scheme-acceptance) plus `GHSA-hvrm-45r6-mjfj` and `GHSA-w62v-xxxg-mg59` (JSX per-request context disclosure and XSS via the `cx()` escaping bypass), both of which reach `<=4.12.26`.
- `rollup`: pinned to `^4.59.0` to keep the Vite and Vitest transitive graph above the vulnerable `<4.59.0` range surfaced by `npm audit`.
- `brace-expansion`: pinned to `5.0.12` to lift the dev graph above the ReDoS ranges `>=2.0.0 <2.1.3` and `>=4.0.0 <=5.0.11`. Transitive dev-only, so the pin is the practical fix rather than waiting on each consumer to bump.
- `postcss`: pinned to `8.5.25` to clear the `<=8.5.17` advisory reaching the dev graph through the Vite toolchain.
- `nanoid`: pinned to `3.3.18` to clear `GHSA-2v37-7h3g-55p8` (`<3.3.18`, custom generators loop forever when size is zero), which reaches the dev graph through `postcss`.

Runtime dependency pin rationale (`package.json` -> `dependencies`):

- `undici`: pinned exactly to `8.11.2`. It is the only runtime HTTP dependency (proxy `ProxyAgent` dispatch and the fetch fallback in the local bridge), it drives the published `engines.node >=22.19.0` floor (`8.x` requires Node `>=22.19.0`), and its dispatcher behavior is part of the rotation proxy's tested surface — so version movement is taken deliberately via an explicit bump, never silently through a range. The `8.x` line stays clear of `GHSA-p88m-4jfj-68fv`, `GHSA-vxpw-j846-p89q`, `GHSA-35p6-xmwp-9g52`, and `GHSA-g8m3-5g58-fq7m` (Set-Cookie header injection, WebSocket fragment DoS, keep-alive response-queue poisoning, and SameSite downgrade), which reach `<=6.26.0`, and of the `6.x` DoS and response-splitting fixes shipped through `6.29.0`.

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

## Automatic first-use checks

Automatic subscription priming is off by default and requires per-account
`account auto-prime <index> on`. A running CLI/app router checks every 15 minutes;
completion consumes subscription quota only when headers identify an unused
personal subscription. The checker uses verified current subscription credentials,
respects account/workspace disablement and pause/drain policy, and never uses
API/ZDR credentials or reset credits. A private attempt file stores hashed account
record-and-workspace keys and timestamps under a cross-process lock. It contains
no prompts or tokens. The saved workspace selection is revalidated after token
refresh; a disabled or changed selection is not replaced by another workspace.
Selected workspace quota is keyed by credential record and workspace; it is never
read as the stored organization binding. Recovery journals preserve the record
identity across token rotation so they cannot reset the automatic-check throttle.
Manual checks still require `--prime`; enabling an account policy does not change
that command's default.
