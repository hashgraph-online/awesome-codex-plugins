# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub security advisories](https://github.com/Cassette-Editor/oh-my-cassette/security/advisories/new), not a public issue. We will acknowledge the report and coordinate remediation and disclosure.

## Trust boundaries

Everything this repository ships runs on the user's machine and opens no port:

- Codex, Claude Code, and OpenCode launch a local stdio MCP child process.
- Hermes retains its gateway integration and `~/.hermes/.env` behavior.

The Cassette backend is a separate service that receives credentials, media, agent requests, project
state, and render requests. Do not treat the local process and the Cassette backend as the same
service — a report about rendering, storage, or account handling belongs to Cassette, not here.

The browser demo is no longer part of this repository — its network-facing server was moved out, so
nothing here listens on a socket. The hosted demo at <https://trycassette.online/agent-demo> is
operated by Cassette; it is unauthenticated and meant for evaluation, not for confidential or
regulated material, and anything about it goes to Cassette rather than this repository.

## Native MCP credentials

Run `scripts/setup_local_mcp.py` in a private terminal. The password is collected with `getpass`, verified against `/api/agent-auth/verify`, and written only after successful verification.

- Process environment takes precedence over protected local config.
- macOS config: `~/Library/Application Support/Oh My Cassette/`.
- Linux config: `${XDG_CONFIG_HOME:-~/.config}/oh-my-cassette/`.
- App-owned config directories are mode `0700`; credential files are `0600`.
- Symlinked, non-regular, wrong-owner, and overly permissive credential files are rejected.
- Access and refresh tokens are cached only in memory. A `401` causes at most one re-authentication and retry; tokens are never written to disk.
- Existing Hermes credentials are imported only when the operator explicitly runs setup with `--import-hermes`.

The credential file contains the verified account email and password, protected by OS file permissions. Anyone who can read that file can use the account. Use a dedicated account where possible, restrict backups, and rotate credentials immediately after accidental disclosure or live testing with a shared password.

## Media and artifacts

Native MCP ingestion trusts only:

- roots supplied by the active MCP host for the current project;
- project roots supplied by the Claude plugin environment; and
- absolute media roots explicitly saved by setup.

Paths are canonicalized before use. Traversal and symlink escapes are rejected. The runtime copies accepted inputs into its private data root before jobs use them.

An exported artifact is returned only when its resolved path is a regular file inside `<data-root>/cassette/exports/<job_id>/`. Results include metadata and resource links, never embedded large media bytes. The MCP server has no generic local-file read tool.

API continuation records contain private thread/run/interrupt metadata so jobs can survive host restarts. Public tool results strip continuation state, prompts, source paths, delivery targets, worker commands, and raw output paths. The shared data root should be treated as private runtime state.

## Repository hygiene

Never commit:

- `.env`, credentials, access/refresh tokens, API keys, or passwords;
- gateway tokens, account/chat IDs, or raw `wxid` values;
- protected native config or Hermes `~/.hermes/.env`;
- downloaded media, exports, manifests, job/continuation state, browser profiles/traces, or runtime caches;
- live-acceptance output containing private IDs or paths.

Before every PR, inspect staged changes and run a secret scan. Repository secret scanning and push protection should remain enabled. Live acceptance must pass credentials only through ephemeral environment variables or repository secrets, and the test password must be rotated after it has been shared outside the secret store.
