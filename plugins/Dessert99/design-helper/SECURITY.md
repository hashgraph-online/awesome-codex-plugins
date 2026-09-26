# Security Policy

design-helper is a skill made of instructions. The only code it runs is what those
instructions tell the agent to write: a small Python server bound to `127.0.0.1` that
serves the comparison sheet from a temporary folder (see
[`liveview.md`](skills/design-helper/references/liveview.md)). Report anything that could
make it expose files, listen beyond localhost, or leave processes or files behind.

## Supported versions

Only the latest release receives fixes.

## Reporting a vulnerability

Report privately through GitHub:
[Security → Report a vulnerability](https://github.com/Dessert99/design-helper/security/advisories/new).
Please don't open a public issue for a security problem.

You can expect a first response within a week.
