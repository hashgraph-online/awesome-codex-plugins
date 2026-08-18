# Security Policy

## Scope

This repository ships public-safe Codex desktop skin packs and a Codex Skill that downloads and stages those packs from GitHub Releases.

The project does not require API keys, OAuth tokens, cookies, private screenshots, private chats, or private Codex workspace files.

## Reporting a Vulnerability

Please report security issues by opening a GitHub issue with the `security` label or by contacting the repository owner through GitHub.

Do not include secrets, private workspace screenshots, private task names, file paths, or emails in public reports. If a report requires sensitive evidence, first open a minimal issue describing the class of problem and ask for a private handoff path.

## Safety Expectations

- Do not publish private Codex screenshots or workspace data.
- Do not modify `app.asar` or signed Codex application bundles.
- Do not run shell installers from untrusted URLs.
- Verify downloaded packs contain the expected `theme.json`, `background.png`, and `README.md` files before use.
- Restore the default Codex appearance if readability or interaction is degraded.

## Supported Versions

Only the latest GitHub Release and the current `main` branch are actively maintained.
