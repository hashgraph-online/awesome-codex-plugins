# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| Latest release on the current major line (`6.25.2`) | ✅ Active support |
| Any earlier release | ❌ Upgrade first, then re-test |
| `oc-chatgpt-multi-auth` (former package name) | ❌ Renamed; migrate to `oc-codex-multi-auth` |

Security fixes ship on the latest published release only.

## Reporting a Vulnerability

1. **Do not open a public issue.**
2. Email the maintainer directly (see the GitHub profile for contact).
3. Include a description, reproduction steps, potential impact, and a suggested fix if you have one.

We aim to respond within 48 hours. Fixes land before public disclosure; reporters are credited unless anonymity is requested.

### Out of scope

- Violations of OpenAI's Terms of Service
- Rate limiting or outages on OpenAI's side
- Auth failures from expired subscriptions

## Credential Storage

Two backends are supported. JSON is the default; the OS keychain is opt-in.

| Backend | Enabled by | Where tokens live | Threat model |
| --- | --- | --- | --- |
| JSON (default) | always | `~/.opencode/projects/<project-key>/oc-codex-multi-auth-accounts.json` (per-project pools on by default) or `~/.opencode/oc-codex-multi-auth-accounts.json`; files `0o600`, dirs `0o700` on POSIX (Windows uses the profile's ACLs instead). `.opencode/` is added to `.gitignore` when a pool lands inside a git repo. | Plaintext on disk — protect the home directory like `~/.ssh`. |
| OS keychain (opt-in) | `CODEX_KEYCHAIN=1` | macOS Keychain / Windows Credential Manager / Linux libsecret; service `oc-codex-multi-auth`, account `accounts:<project-key>` (or `accounts:global`) | Ciphertext managed by the OS; only as strong as the login session's keychain unlock. |

- Enabling `CODEX_KEYCHAIN` migrates the JSON pool on the next save, renaming the file `*.migrated-to-keychain.<ts>` for rollback — the original is never auto-deleted.
- Keychain failures log a warning and fall back to JSON; credentials are never silently deleted. Windows Credential Manager caps blob size below a typical multi-account pool, so on `win32` an oversized write is size-checked up front and the JSON path stays authoritative.
- To leave the keychain: unset `CODEX_KEYCHAIN` and run `codex-keychain rollback`, which restores the newest migration backup (including the flagged-accounts store).
- Access, refresh, and id tokens are masked in every log line regardless of backend.

### What you should do

- Never share or commit `~/.opencode/`.
- Review authorized apps at [ChatGPT Settings → Apps](https://chatgpt.com/settings/apps); run `opencode auth logout` on shared machines.
- Enable `ENABLE_PLUGIN_REQUEST_LOGGING=1` only while debugging, and `CODEX_PLUGIN_LOG_BODIES=1` never (raw prompt/response bodies land on disk).
- Keep Node ≥ 22.19 and the plugin on the latest release.

## Third-Party Dependencies

Runtime `dependencies` in `package.json`, the full set:

| Dependency | Role |
| --- | --- |
| `@ai-sdk/openai` | AI-SDK client the OpenCode V2 adapter builds around the shared fetch |
| `@opencode-ai/plugin` | OpenCode V1 plugin interface |
| `@opencode/plugin` | OpenCode V2 plugin interface |
| `@opentui/solid`, `solid-js` | Terminal UI for the dashboard |
| `@napi-rs/keyring` | Native OS keychain access (opt-in backend) |
| `proper-lockfile` | Advisory locking for concurrent storage writes |
| `zod` | Schema validation at process boundaries |

`@opentui/core` and `web-tree-sitter` are **not** direct dependencies; they exist only transitively under the plugin/TUI packages above. `npm run audit:ci` gates production advisories plus a reviewed dev allowlist. No telemetry or analytics dependencies.

## Notes

- This plugin is not affiliated with OpenAI.
- For non-vulnerability questions, open a [GitHub issue](https://github.com/ndycode/oc-codex-multi-auth/issues) without sensitive details.
