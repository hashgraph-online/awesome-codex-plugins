# Security policy

## Supported versions

Security fixes target the latest source plugin on the default branch and the latest published
Release. Upgrade before reproducing an issue. Older releases may not receive backports.

## Reporting a vulnerability

Use the repository Security tab to report a vulnerability privately when private reporting is
available. Otherwise open an issue containing only a request for a private contact channel.
Do not include credentials, private conversations, or an exploit against another user in a public issue.
Include the affected version, operating system, impact, and minimal reproduction steps.

## Local runtime and data

Goal Progress runs on the user computer. Its Helper stores checklists, progress, settings, and
logs in the plugin data directory. It uses a private Unix socket and a loopback CDP connection
to the local Codex desktop app. Codex application files and signatures are not modified.

The source plugin requires Node.js 22.12+ and pnpm 11. First use downloads locked npm dependencies
and builds the runtime locally. Update checks contact GitHub. The plugin does not send checklist
contents to its maintainers or start a separate model request to calculate progress.

The explicit uninstall command removes this plugin and its progress data. Native Codex Goals,
chat history, and other plugins remain. Codex manages its own permissions and authentication.
