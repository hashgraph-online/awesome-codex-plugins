# Security policy

## Reporting a vulnerability

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/Cassette-Editor/oh-my-cassette/security/advisories/new), not a public issue. We acknowledge a report within three working days and coordinate the fix and its disclosure with you.

## Supported versions

| Version | Supported |
| --- | --- |
| 0.5.x (PyPI) | Yes: fixes ship in the latest 0.5 release |
| 0.4.x and earlier (git installs) | No: upgrade to 0.5 |

## Trust boundaries

Everything this repository ships runs on the user's machine. Every host (Claude Code, Codex,
OpenCode, Hermes) launches `uvx oh-my-cassette==0.5.1` as a local stdio child process. The bridge
opens no port; only an explicit `login` briefly binds an ephemeral loopback callback for the browser
sign-in.

The Cassette MCP service configured with `CASSETTE_MCP_URL` (and the backend behind it) is a
separate service that receives the access token, media, editing requests, project state and render
requests. Do not treat the local process and the service as the same thing: a report about
rendering, storage, or account handling belongs to Cassette, not here.

The service decides which tools exist and what their descriptions, instructions and results say;
the bridge passes that text to the host's agent unchanged, so the agent follows the service's
guidance as it would a tool's. What the bridge reads, writes and contacts is decided locally,
whatever the service says:

- Local files come only from the workspace or `CASSETTE_ALLOWED_ROOTS`, and only media types unless
  the user sets `CASSETTE_UPLOAD_ANY_TYPE`; a tool can narrow that set but never widen it. A host
  that starts the bridge in the whole disk or the home folder gives it no workspace to read from.
  A picture or a sound uploaded unchanged must begin like one.
- Media preparation takes only encodings the bridge knows (codec, profile, preset, pixel format,
  container), so a declaration cannot add ffmpeg filters or options. ffmpeg reads its input as a
  local file only.
- Uploads and downloads, redirects included, go only to the service's own origin or to HTTPS hosts
  whose every address is public, so the URLs the service hands out cannot reach the machine's own
  network. A PUT never carries a host, cookie, proxy or connection header the service names.
- Downloads are written only into the download directory, which stays inside the workspace unless
  `CASSETTE_DOWNLOAD_DIR` names another. Names are sanitized, an existing file or symlink is never
  overwritten or written through, and the size and SHA-256 are checked when the service declares them.

## Credentials and local state

- The bearer token (the OAuth access token, or `CASSETTE_AUTH_TOKEN`) is sent to the MCP service,
  and to upload and download URLs only when they have the same origin as the service; presigned
  URLs on other origins get no credential, and a redirect to another origin drops it. A saved
  sign-in is bound to the endpoint it was made for, so a `CASSETTE_MCP_URL` override never receives
  it. The service answers HTTP 401 without a valid token, reported as `bridge.unauthorized`.
- OAuth access and refresh tokens live only in the OS keyring (macOS Keychain, Windows Credential
  Vault, or Linux Secret Service). A file lock serializes refresh across hosts. Public connection
  metadata lives in `~/.config/oh-my-cassette` (mode 0700); it contains no token. `logout` revokes
  the grant before deleting credentials.
- Prepared media lives in a private `oh-my-cassette-job-*` directory (mode 0700) under
  `CASSETTE_TEMP_DIR` (default: the system temporary directory) only until it is uploaded.
- ffmpeg and ffprobe run as local subprocesses with argument lists, never through a shell, and are
  looked up on `PATH`, never in the working directory.

## Agent skill

The bundled skill (`skills/cassette-video-edit`) lets an agent offer Cassette for a video-editing
request even when the user does not name it. Before the first upload in a conversation where the
user did not ask for Cassette, it tells the user that the named files go to the Cassette service.
