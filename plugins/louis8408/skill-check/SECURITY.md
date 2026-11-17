# Security policy

## Reporting a vulnerability

Please report security problems privately. Go to **Security → Report a vulnerability** on [github.com/louis8408/skill-check](https://github.com/louis8408/skill-check/security/advisories/new). Don't open a public issue.

Include what you found, how to reproduce it, and which version you used (`skill-check --version`, or the version in the plugin's `plugin.json`). You should get a first reply within a week. This is a one-person, spare-time project, so please allow time for a fix before you disclose.

## Supported versions

Only the latest release gets fixes. Update the plugin from its marketplace to get it.

## What skill-check does, for reviewers

- **It runs as hooks.** It runs `node dist/cli.js hook` at session start (in the background), when a skill is used, and when you type or mention a skill. It prints at most one warning, never blocks, approves or denies a tool call, and never edits a skill.
- **It reads** your skill folders, `.specify/` in the project (Spec Kit), and the `npx skills` lock file.
- **It fetches** only public files: the upstream copy of a skill from the `https://` URL in its `metadata.source`, its commit history from `api.github.com`, Spec Kit's latest release, and folder hashes for `npx skills` installs. A `metadata.source` is treated as a hint, never as identity.
- **It sends** an optional GitHub token only to `api.github.com` and `raw.githubusercontent.com`.
- **It writes** only its cache (`status.json`) to the plugin's data folder.
- **It has** no server, no telemetry, and no runtime dependencies: the plugin is one bundled JavaScript file.
