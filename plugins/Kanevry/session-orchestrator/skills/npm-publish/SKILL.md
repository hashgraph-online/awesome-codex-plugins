---
name: npm-publish
user-invocable: true
model: sonnet
description: Use when publishing this package to npm — a version release (npm publish), verifying the registry/pi.dev listing, or diagnosing npm auth failures (E403 2FA/token errors). Token-based flow via NPM_TOKEN in .env.local with a temp userconfig, leakage-gate greps before every publish, post-publish verification and marker/badge upkeep. Trigger on "publish to npm", "npm release", "E403 publish error".
---

# npm-publish — Token-based publish runbook

> Companion to `docs/distribution/npm-publish-checklist.md` (the original 7-step operator runbook). This skill adds the token-auth mechanics and the failure-mode diagnosis learned during the v3.16.0 first publish (2026-07-19).

## Why this skill exists

npm requires 2FA **or** a granular access token with "Bypass 2FA" for every publish (policy active since 2025; legacy tokens were removed Nov 2025 — only granular tokens exist). The failure mode is confusing: `npm publish` fails with **E403 and NO OTP prompt** when the account either has no 2FA enrolled or the supplied token lacks the bypass flag. Three dead ends verified empirically: plain `npm publish` (E403), `--auth-type=web` (no web flow exists for publish), PTY-forced publish (same E403). The ONLY non-interactive path is a correctly-configured granular token.

## Token requirements (all four mandatory)

Create at https://www.npmjs.com/settings/<user>/tokens → Generate New Token → **Granular Access Token**:

1. **Permissions: Read and write** (Packages and scopes).
2. **Packages: "All packages"** for a FIRST publish (the package does not exist yet, so per-package selection cannot include it). After the first publish, re-create scoped to the single package — least privilege.
3. **"Bypass two-factor authentication (2FA)" enabled** — this is the checkbox whose absence produces the E403-without-prompt. npm shows a red security warning here and recommends Trusted Publishing for CI/CD; for interactive operator-assisted releases the short-lived bypass token is acceptable.
4. **Short expiration** — write tokens default to 7 days (90 max). Take the default.

## Auth resolution order

1. `NPM_TOKEN` in `.env.local` at the repo root (gitignored — verify with `git check-ignore .env.local` before writing; also confirm no `.env` pattern in the `files` whitelist of package.json).
2. Interactive fallback: operator runs `npm publish --access public` in a real terminal (only works when account 2FA is enrolled — OTP prompt appears).

**Never** put the token in the tracked `.npmrc` (it holds `ignore-scripts=true` per SEC-020 and is committed), never persist it into `~/.npmrc`, never echo it into logs.

## Publish flow

```bash
# 1. Pre-flight (first publish: expect E404 = name free; upgrade: expect the previous version)
npm view session-orchestrator version

# 2. Leakage gate — every grep MUST print 0 (from docs/distribution/npm-publish-checklist.md)
npm pack --dry-run 2>&1 | grep -cE "npm notice.* tests/"
npm pack --dry-run 2>&1 | grep -c "npm notice.*\.orchestrator/"
npm pack --dry-run 2>&1 | grep -cE "npm notice.*[[:space:]]\.claude/"
npm pack --dry-run 2>&1 | grep -c "npm notice.*\.github/"
npm pack --dry-run 2>&1 | grep -c "node_modules"
npm pack --dry-run 2>&1 | grep -ci "\.env"
npm pack --dry-run 2>&1 | grep -ci "owner\.yaml"

# 3. Publish via temp userconfig (never a persistent npmrc)
NPM_TOKEN=$(grep '^NPM_TOKEN=' .env.local | cut -d= -f2-)
TMPRC=$(mktemp) && printf '//registry.npmjs.org/:_authToken=%s\n' "$NPM_TOKEN" > "$TMPRC" && chmod 600 "$TMPRC"
npm publish --access public --userconfig "$TMPRC"; rm "$TMPRC"

# 4. Verify
npm view session-orchestrator version   # must print the new version
```

Success marker: `+ session-orchestrator@<version>` on the publish output.

## Post-publish checklist

1. **Verify registry**: `npm view session-orchestrator version dist.unpackedSize keywords` — `pi-package` keyword must be present.
2. **pi.dev gallery**: indexing is asynchronous — check https://pi.dev/packages later; do not block on it.
3. **Marker upkeep** (first publish only — done in v3.16.0): README install matrix + npm badge, `site/index.html` install section, `docs/pi-setup.md` availability paragraph.
4. **Rotate/delete the token** at https://www.npmjs.com/settings/<user>/tokens once the release is done — especially if the token value ever transited chat, a screenshot, or any log. A token pasted into a conversation is burned: rotate immediately after use.
5. Update the release issue / CHANGELOG if the publish was part of a tracked release.

## Failure-mode table

| Symptom | Cause | Fix |
|---|---|---|
| `E403 ... Two-factor authentication or granular access token with bypass 2fa enabled is required` — no OTP prompt | Account has no 2FA enrolled AND token (if any) lacks Bypass-2FA | Create granular token with all four requirements above, or enroll 2FA |
| Same E403 despite a fresh token | Token created without the Bypass-2FA checkbox, or Read-only, or package-scoped on a first publish | Re-create: RW + All packages + Bypass-2FA |
| `E404` on `npm view` after publish | Registry propagation (rare, seconds) or publish actually failed | Re-check the publish output for `+ <name>@<version>` |
| `ENEEDAUTH` | No login/token at all | Token flow above, or `npm login` |
| OTP prompt appears but flow is non-interactive (`!`-prefix, script) | No TTY for the prompt | Use the token flow, or a real terminal |

## Security invariants

- `.env.local` is gitignored AND absent from the npm `files` whitelist — verify both before writing a token into it.
- Temp userconfig: `chmod 600`, deleted immediately after publish.
- The leakage gate runs before EVERY publish, not only the first.
- npm's own recommendation for unattended CI/CD is **Trusted Publishing** (OIDC) — evaluate it if publishing ever moves into CI (ref: https://docs.npmjs.com/about-access-tokens).
