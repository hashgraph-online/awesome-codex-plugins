# Security Policy

## Supported Versions

Security updates target the latest published release only. Upgrade before
reporting an issue against an older build.

| Version | Supported |
| ------- | --------- |
| Latest release on the current major line | ✅ Active support |
| Any earlier release | ❌ Upgrade to the latest release |
| `oc-chatgpt-multi-auth` (former package name) | ❌ Renamed; migrate to `oc-codex-multi-auth` |

## Security Considerations

### OAuth Token Security

This plugin handles sensitive OAuth tokens. To protect your security:

✅ **What we do:**
- Store tokens securely via opencode's credential management
- Use PKCE-secured OAuth 2.0 flows
- Never transmit tokens to third parties
- Implement automatic token refresh
- Use industry-standard authentication practices

### Credential Storage Backends

Two backends are supported. JSON is the default; the keychain backend is opt-in.

| Backend | Enabled by | Where tokens live | Threat model |
|---------|-----------|-------------------|--------------|
| JSON (default) | always on | `~/.opencode/projects/<project-key>/oc-codex-multi-auth-accounts.json`, file mode `0o600`, directory mode `0o700` on POSIX. A `.gitignore` entry is auto-written when the storage path sits inside a git repo. | Plaintext on the local filesystem. Any local user or process that can read the file can read the refresh token. Protect the home directory like you would protect `~/.ssh`. |
| OS keychain (opt-in) | `CODEX_KEYCHAIN=1` | macOS Keychain / Windows Credential Manager / Linux libsecret, stored under service name `oc-codex-multi-auth` and account key `accounts:<project-storage-key>` (or `accounts:global`). | Token ciphertext is managed by the OS keychain. Unlocked session required to read. Credentials survive loss of the JSON file. Still only as strong as the user's OS login password / keychain unlock. |

Migration and fallback rules:

- Switching the env var ON migrates the on-disk JSON into the keychain on the next save and renames the JSON file as `<path>.migrated-to-keychain.<timestamp>` for rollback. The original is never deleted automatically.
- If a keychain call fails (native module missing, keychain locked, permission denied, unsupported Linux without a secret service), the plugin logs a warning and falls back to the JSON backend for that operation. Credentials are never silently lost.
- Turn the opt-in OFF by unsetting `CODEX_KEYCHAIN` and running `codex-keychain rollback` to restore the JSON file from the most recent `.migrated-to-keychain.<ts>` backup.

Log redaction applies uniformly to both backends. Refresh tokens, access tokens, and id tokens are replaced before any log line is written.

⚠️ **What you should do:**
- Never share your `~/.opencode/` directory
- Do not commit OAuth tokens to version control
- Regularly review authorized apps at [ChatGPT Settings](https://chatgpt.com/settings/apps)
- Use `opencode auth logout` when done on shared systems
- Enable debug logging (`ENABLE_PLUGIN_REQUEST_LOGGING=1`) only when troubleshooting

### Reporting a Vulnerability

If you discover a security vulnerability:

1. **DO NOT open a public issue**
2. Email the maintainer directly (check GitHub profile for contact)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond to security reports within 48 hours.

### Responsible Disclosure

We follow responsible disclosure practices:
- Security issues are patched before public disclosure
- Reporter receives credit (unless anonymity is requested)
- Timeline for disclosure is coordinated with reporter

### Security Best Practices

When using this plugin:

- **Personal use only:** Do not use for commercial services
- **Respect rate limits:** Avoid excessive automation
- **Monitor usage:** Review your ChatGPT usage regularly
- **Keep updated:** Use the latest version for security patches
- **Secure your machine:** This plugin is as secure as your development environment
- **Review permissions:** Understand what the plugin can access via OAuth

### Out of Scope

The following are **not** security vulnerabilities:
- Issues related to violating OpenAI's Terms of Service
- Rate limiting by OpenAI's servers
- Authentication failures due to expired subscriptions
- OpenAI API or service outages

### Third-Party Dependencies

This plugin keeps its runtime dependency surface small and reviews it regularly.
The full runtime set (`dependencies` in `package.json`) is:

| Dependency | Role |
|------------|------|
| `@openauthjs/openauth` | OAuth / PKCE handling |
| `@opencode-ai/plugin` | OpenCode plugin interface |
| `@napi-rs/keyring` | Native OS keychain access for the opt-in credential backend |
| `hono` | Lightweight HTTP routing for the local OAuth callback server |
| `zod` | Schema validation at every process boundary |
| `proper-lockfile` | Advisory locking for concurrent config/account writes |
| `@opentui/core`, `@opentui/solid`, `solid-js` | Terminal UI rendering for the account dashboard |
| `web-tree-sitter` | Syntax-aware handling in tool output |

`npm run audit:ci` gates production dependencies plus a reviewed dev-advisory
allowlist. There are no telemetry or analytics dependencies.

## Questions?

For security questions that are not vulnerabilities, open a GitHub issue without sensitive details.

---

**Note:** This plugin is not affiliated with OpenAI. For OpenAI security concerns, contact OpenAI directly.
