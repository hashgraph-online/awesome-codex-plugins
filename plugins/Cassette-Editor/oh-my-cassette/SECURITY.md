# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub security advisories](https://github.com/Cassette-Editor/oh-my-cassette/security/advisories/new), not a public issue. We will acknowledge the report and coordinate remediation and disclosure.

## Trust boundaries

Everything this repository ships runs on the user's machine. The stdio bridge opens no port; an explicit `login` command temporarily binds an ephemeral loopback callback: every host (Claude
Code, Codex, OpenCode, Hermes) launches `uvx oh-my-cassette` as a local stdio child process.

The Cassette MCP service configured with `CASSETTE_MCP_URL` (and the backend behind it) is a
separate service that receives the access token, media, editing requests, project state and render
requests. Do not treat the local process and the service as the same thing — a report about
rendering, storage, or account handling belongs to Cassette, not here.

The service decides which tools exist, but not what the bridge may read: local files come only from
the workspace or `CASSETTE_ALLOWED_ROOTS`, only media types unless the user sets
`CASSETTE_UPLOAD_ANY_TYPE`, and a tool can narrow that set but never widen it. Downloads are written
only into the download directory, under sanitized names that never overwrite a file.

## Credentials and local state

- `CASSETTE_AUTH_TOKEN` is sent as a bearer token to the MCP service, and to upload and download URLs
  only when they have the same origin as the service; presigned URLs on other origins get no
  credential. The service answers HTTP 401 without a valid token, reported as `bridge.unauthorized`.
- OAuth access and refresh tokens live only in the OS keyring (macOS Keychain, Windows Credential Vault, or Linux Secret Service). A file lock serializes refresh across hosts. Public connection metadata lives in `~/.config/oh-my-cassette`; it contains no token. `logout` revokes the grant before deleting credentials. Prepared media lives in `CASSETTE_TEMP_DIR`
  (default: the system temporary directory) only until it is uploaded.
- ffmpeg and ffprobe run as local subprocesses with argument lists, never through a shell.

## Supported versions

Only the latest release on PyPI receives fixes.
