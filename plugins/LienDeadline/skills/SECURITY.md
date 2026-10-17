# Security policy

Report security issues privately to [support@liendeadline.com](mailto:support@liendeadline.com),
not in public issues or pull requests. Include the affected file or release, what an agent or a
user could do with it, and steps to reproduce.

## Scope

- This repository: the `liendeadline` skill, the plugin and extension manifests, and the CI
  scripts. Skill instructions that could make an agent send data anywhere other than
  LienDeadline's API, or act without the user's authorization, count as security issues.
- The [`liendeadline-mcp`](https://github.com/LienDeadline/liendeadline-mcp) server that the
  manifests pin, and LienDeadline's API at `secure-api-v1.liendeadline.com`: report these to the
  same address.

## Supported versions

Fixes land on `main` and ship in the next release. Only the latest release is supported.
