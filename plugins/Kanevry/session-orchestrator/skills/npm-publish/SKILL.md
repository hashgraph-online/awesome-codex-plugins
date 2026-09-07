---
name: npm-publish
user-invocable: true
model: sonnet
description: Use when publishing this package to npm — a version release (npm publish), verifying the registry/pi.dev listing, or diagnosing npm auth failures (E403 2FA/token errors). Token-based flow via NPM_TOKEN in .env.local with a temp userconfig, the leakage gate before every publish, post-publish verification and marker/badge upkeep. Trigger on "publish to npm", "npm release", "E403 publish error".
---

# npm-publish — token auth, and the calls the script cannot make

> **The release itself is `/release` → `scripts/release.mjs`.** That script mechanizes the whole sequence: version surfaces, CHANGELOG gate, drift sweep, tag/registry collision, CI, leakage gate, publish, the target-confirmed npm receipt boundary, tag-after-receipt, push to both remotes, GitHub-release handling, and live-site poll. This skill does not restate it.
>
> What lives here is the half a script cannot own: the **token setup**, the **auth failure diagnosis**, and the **judgement calls** — which version, what a leak means, when to abort rather than repair.

## Why this skill exists

npm requires 2FA **or** a granular access token with "Bypass 2FA" for every publish (policy active since 2025; legacy tokens were removed Nov 2025 — only granular tokens exist). The failure mode is confusing: `npm publish` fails with **E403 and NO OTP prompt** when the account either has no 2FA enrolled or the supplied token lacks the bypass flag. Three dead ends verified empirically: plain `npm publish` (E403), `--auth-type=web` (no web flow exists for publish), PTY-forced publish (same E403). The ONLY non-interactive path is a correctly-configured granular token.

## Token requirements (all four mandatory)

Create at https://www.npmjs.com/settings/<user>/tokens → Generate New Token → **Granular Access Token**:

1. **Permissions: Read and write** (Packages and scopes).
2. **Packages: "All packages"** for a FIRST publish (the package does not exist yet, so per-package selection cannot include it). After the first publish, re-create scoped to the single package — least privilege.
3. **"Bypass two-factor authentication (2FA)" enabled** — this is the checkbox whose absence produces the E403-without-prompt. npm shows a red security warning here and recommends Trusted Publishing for CI/CD; for interactive operator-assisted releases the short-lived bypass token is acceptable.
4. **Short expiration** — write tokens default to 7 days (90 max). Take the default.

## Auth resolution order

1. `NPM_TOKEN` in `.env.local` at the repo root (gitignored — verify with `git check-ignore .env.local` before writing; also confirm no `.env` pattern in the `files` whitelist of package.json). `scripts/release.mjs` refuses to read the token if that ignore check fails.
2. Interactive fallback: operator runs `npm publish --access public` in a real terminal (only works when account 2FA is enrolled — OTP prompt appears).

**Never** put the token in the tracked `.npmrc` (it holds `ignore-scripts=true` per SEC-020 and is committed), never persist it into `~/.npmrc`, never echo it into logs.

## The three judgement calls

The script gates mechanics. These three are yours, and it will not make them for you.

**1. Which version is the right one.** Semver per `.claude/rules/development.md` § Package Lifecycle & Versioning: patch = fixes/docs/internal refactor; minor = additive and backwards-compatible; major = removed or renamed exports, or changed runtime behaviour — and a major never merges without a migration guide and a `BREAKING CHANGE:` footer. The script validates the *shape* `X.Y.Z` and nothing about whether the number matches the diff. Read the CHANGELOG entry you just wrote and ask whether a consumer pinning `^` would be broken by it; if yes, the bump is a major regardless of how small the diff looks.

**2. What a leak means when one is found.** A hit from the leakage gate is not a pattern to silence. Decide which of two it is: a real leak (fix `package.json` `files`, re-pack, re-check) or genuine over-matching (fix `LEAKAGE_PATTERNS` in `scripts/release.mjs` **with a test**). There is no third option, and neither is "publish anyway and clean it up in the next version" — an npm publish is not revocable, and unpublishing burns the version number permanently. Operator handling detail: `docs/distribution/npm-publish-checklist.md` § 3.

**3. When to abort instead of repair.** Abort — do not patch forward — when the failure is upstream of the target-confirmed npm receipt: a red preflight row, a lagging `github` mirror, CI not green on the exact commit, a dead token, or a publish that did not issue the target receipt. These are cheap to fix and re-run from the top. Repair-in-place is only appropriate *after* that receipt, where the version is already immutable: registry propagation, a missing GitHub release, or a lagging site deploy can be reconciled because npm already has the correct artifact. When `--publish` reports **Post-publish reconciliation required**, **do not rerun `--publish`**; repair the listed state directly. `commands/release.md` § Abort criteria is the operative list.

## Failure-mode table

| Symptom | Cause | Fix |
|---|---|---|
| `E403 ... Two-factor authentication or granular access token with bypass 2fa enabled is required` — no OTP prompt | Account has no 2FA enrolled AND token (if any) lacks Bypass-2FA | Create granular token with all four requirements above, or enroll 2FA |
| Same E403 despite a fresh token | Token created without the Bypass-2FA checkbox, or Read-only, or package-scoped on a first publish | Re-create: RW + All packages + Bypass-2FA |
| `npm whoami` silent or non-zero | Token expired, or `.env.local` missing | Re-create the token; do not proceed — the preflight fails this row on purpose |
| `E404` on `npm view` after a target-confirmed publish receipt | Registry propagation (rare, seconds) | Let the script finish its tag/push/GitHub/site tail, then reconcile the registry result; do **not** rerun `--publish` |
| `ENEEDAUTH` | No login/token at all | Token flow above, or `npm login` |
| OTP prompt appears but flow is non-interactive (`!`-prefix, script) | No TTY for the prompt | Use the token flow, or a real terminal |

## Post-publish — the human half

`--publish` attempts registry verification and polls the live site itself. A target-confirmed receipt plus a delayed registry result is a reconciliation outcome, not a failed publish or a retry instruction. What still needs a person:

1. **Rotate/delete the token** at https://www.npmjs.com/settings/<user>/tokens. A token that ever transited a conversation, a screenshot, or any log is burned — rotate immediately.
2. **pi.dev gallery**: indexing is asynchronous — check https://pi.dev/packages later; do not block on it.
3. **Marker upkeep** on a first publish only (done in v3.16.0): README install matrix + npm badge, `site/index.html` install section, `docs/pi-setup.md` availability paragraph.
4. Update the release issue if the publish was part of tracked work.

## Security invariants

- `.env.local` is gitignored AND absent from the npm `files` whitelist — verify both before writing a token into it.
- Temp userconfig: `chmod 600`, deleted in a `finally` block immediately after publish.
- The leakage gate runs before EVERY publish, not only the first.
- npm's own recommendation for unattended CI/CD is **Trusted Publishing** (OIDC) — evaluate it if publishing ever moves into CI (ref: https://docs.npmjs.com/about-access-tokens).
