# Security

## Reporting a vulnerability

For ordinary bugs and feature requests, [open a GitHub issue](https://github.com/martinille/codex-tasklist/issues/new).

For security vulnerabilities, use [Report a vulnerability](https://github.com/martinille/codex-tasklist/security/advisories/new) to contact the maintainer privately on GitHub. Include the affected version, reproduction steps, and impact. Do not include credentials or private task data. Avoid publishing exploit details in a public issue before a fix is available.

Security fixes target the latest release. Update to the latest version before reporting a problem.

## Scope

Codex Tasklist runs locally with the permissions of its Codex session. It stores task titles and statuses in SQLite and invokes local terminal CLIs or macOS AppleScript to manage its panel. It does not upload task data. Review hooks before trusting them and keep secrets out of task titles.

The plugin uses only the Python standard library. Optional terminal tools (tmux, WezTerm, kitty and macOS automation) are supplied by the user. The Linux/macOS/WSL launcher never installs software or edits shell profiles. Native Windows runs Codex directly and does not create a batch wrapper. Its tmux fallback uses a private server and ignores user tmux configuration. Panel commands target identified panes; inherited outer terminal IDs are not used inside another multiplexer. A failed integration preserves the local task queue.
