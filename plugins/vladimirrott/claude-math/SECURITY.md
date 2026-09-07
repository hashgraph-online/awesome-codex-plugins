# Security Policy

## Supported versions

Only the latest published version of `claude-math` on npm is supported. Fixes
ship in a new release rather than as patches to older versions.

## Scope

`claude-math` is a Claude Code / Codex CLI skill plus a small Node installer. It
has no network calls and no runtime service. The installer only symlinks or
copies the skill into your agent's local plugin directory. The main surface
worth reporting is anything that would let the installer write outside that
directory or execute untrusted code.

## Reporting a vulnerability

Please report privately. Do not open a public issue for security reports.

- Preferred: open a [GitHub security advisory](https://github.com/vladimirrott/claude-math/security/advisories/new).
- Or email the maintainer at the address on the npm package page.

You will get an acknowledgement within a few days. Once a fix is released, the
advisory will be published with credit to the reporter unless you prefer to stay
anonymous.
