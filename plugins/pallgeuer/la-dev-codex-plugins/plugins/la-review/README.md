# Loupe Code Review

Loupe is the `la-review` Codex plugin. Invoke `$la-review:loupe` to run independent specialist reviewers, verify their candidate findings, and consolidate the evidence for a selected Git scope.

Loupe requires stable Codex CLI 0.137.0+, Python 3.6+, Bash, Git, `jq`, and at least one authenticated `codex` or `claude` reviewer executable. It supports Ubuntu 18.04+ and macOS 14+; native Windows and WSL are not supported.

The plugin has no hosted service, authentication flow, telemetry collector, or external data store. Reviewers operate through the user's local tools, provider accounts, Codex session, and granted permissions.

- [Complete Loupe guide](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/loupe.md)
- [Installation](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/docs/installation.md)
- [Privacy](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/PRIVACY.md)
- [Terms](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/TERMS.md)
- [Security](https://github.com/pallgeuer/la-dev-codex-plugins/blob/main/SECURITY.md)
- [Support](https://github.com/pallgeuer/la-dev-codex-plugins/issues)
