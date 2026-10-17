# Authentication

Run `sendsets auth status --json` first. If already signed in, continue. Otherwise `sendsets login --hostname sendsetsapi.com` prints a code and approval URL; pass them to the user, since browser approval is theirs. Confirm with `sendsets auth status --json` and `sendsets whoami --json`.

A supplied key can be piped to `sendsets login --hostname sendsetsapi.com --with-token`. For automation, `SENDSETS_TOKEN` overrides stored credentials without saving the token; set `SENDSETS_HOST=sendsetsapi.com` with it, because CLI v0.4.24 and older default to a retired host. Never echo a token to logs or infer one from the codebase. Exit code 4 indicates missing, invalid, or insufficient credentials; use the CLI's fix message.

The user may need to select a workspace after sign in. Read the effective scopes and agent policy from `whoami` before a sensitive operation.
