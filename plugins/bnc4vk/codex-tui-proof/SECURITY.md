# Security policy

## Supported versions

Security fixes are applied to the latest release on the `main` branch.

## Report a vulnerability

Do not open a public issue for a vulnerability. Use GitHub's private vulnerability reporting at:

https://github.com/bnc4vk/codex-tui-proof/security/advisories/new

Include affected versions, reproduction steps, impact, and any suggested mitigation. You can expect an acknowledgement within seven days.

## Security model

- The proof server binds only to `127.0.0.1` and has no remote-access mode.
- The selected executable intentionally runs with the local user's permissions. The launcher parses arguments directly; Windows uses a fixed PowerShell bridge with executable and arguments passed separately.
- The WebSocket accepts only an exact same-origin connection from the allocated `127.0.0.1` page.
- PTY input and output are written to local JSONL recordings and may contain sensitive text.
- Runtime dependencies are locked in `runtime/package-lock.json` and installed locally with `npm ci`.
- The browser page treats the local PTY as untrusted output and does not render it as HTML.

Do not type secrets into proof sessions, expose the server through a proxy or tunnel, or run commands you do not trust.
