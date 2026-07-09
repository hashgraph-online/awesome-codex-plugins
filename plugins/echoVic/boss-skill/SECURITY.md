# Security Policy

## Supported Versions

Security fixes are applied to the latest published release of
`@blade-ai/boss-skill`. Please upgrade to the most recent version before
reporting an issue.

| Version | Supported |
| ------- | --------- |
| 3.9.x   | ✅        |
| < 3.9   | ❌        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately so it can
be addressed before public disclosure.

- **Preferred:** Open a [GitHub Security Advisory](https://github.com/echoVic/boss-skill/security/advisories/new)
  for this repository.
- **Alternative:** Email the maintainer at `137844255@qq.com` with the subject
  line `[SECURITY] boss-skill`.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce (proof-of-concept, affected commands, or configuration).
- The affected version(s).

Do **not** open a public issue for security reports.

## Response Process

- We aim to acknowledge a report within **5 business days**.
- We will work with you to confirm the issue and determine its severity.
- Once a fix is available, we will publish a patched release and credit the
  reporter (unless anonymity is requested).

## Scope

This project orchestrates coding-agent pipelines and ships hooks and a CLI.
Of particular interest are:

- Command injection or arbitrary code execution via hooks, the CLI, or
  workflow definitions.
- Path traversal or unintended file writes outside the `.boss/` workspace.
- Leakage of secrets or credentials through logs or generated artifacts.

## Security-Sensitive Capabilities

Boss is intentionally packaged with a minimal marketplace manifest. The Codex
manifest declares the bundled skills only; MCP servers, app manifests, and asset
references should be added only when the corresponding files exist and are
reviewed. Codex hook installation is handled by `boss-skill install`, not by the
plugin marketplace manifest.

The npm package intentionally excludes local development agent settings such as
`.claude/settings.json` and `.claude/settings.local.json`. Publishable plugin
metadata lives under `.claude-plugin/`, `.codex-plugin/`, and
`.agents/plugins/marketplace.json`.

Release provenance lives in `.agents/plugins/provenance.json`. It records the
repository HTTPS URL, immutable source commit SHA, publisher attribution, and
SHA-256 digests for plugin manifests and security-sensitive components. Run
`npm run provenance:verify` before publishing to confirm the references still
match the bundled files.

Publisher verification is completed on external registries. For the HOL
registry, the repository owner should claim the plugin with GitHub OAuth at
`https://hol.org/guard/plugins`.

Review these surfaces before installing or publishing:

- `boss-skill install` can copy the Boss skill bundle into agent configuration
  directories and merge Boss-managed entries into `~/.codex/hooks.json`.
- Hook entries call `boss hooks run ...`, which dispatches scripts under
  `scripts/hooks/`.
- Runtime plugins in `.boss/plugins/<name>/plugin.json` may register gate or
  reporter hooks. Treat project-local plugins as executable extension points.
- Use `BOSS_HOOK_PROFILE=minimal` or `BOSS_DISABLED_HOOKS=<ids>` to reduce hook
  behavior in sensitive environments.

Thank you for helping keep the project and its users safe.
