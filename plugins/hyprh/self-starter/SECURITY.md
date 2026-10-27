# Security policy

Security fixes target the latest Self-Starter release. When possible, check whether an issue also occurs on the current `main` branch.

## Reporting a vulnerability

Use [GitHub's private vulnerability reporting](https://github.com/hyprh/self-starter/security/advisories/new) to contact the maintainer. Include the affected version, operating system, reproduction steps, expected behavior, and impact. Remove credentials and personal data from examples and logs.

If private reporting is unavailable, open an issue asking the maintainer for a private reporting channel, without publishing exploit details or secrets. Ordinary bugs and documentation issues can be reported in [GitHub Issues](https://github.com/hyprh/self-starter/issues).

## Trust and permissions

- A custom event includes probe code and the action to perform when it fires. Review what it checks and what the agent will do before activating it.
- By default, probes run as the current user and can read files, invoke commands, use the environment, and access the network. For API-only checks, `probe.access: sandbox` restricts network hosts and declared environment variables and denies file and command access.
- Event data is passed to the agent as untrusted data. A trigger fire cannot create or change triggers, except to make its own trigger quieter.
- Background agent actions use workspace write access by default. Use read-only access when the action only needs to inspect information; broader permissions require an explicit choice.
- Secrets entered with the CLI are stored locally in files restricted to the current user. They are not encrypted against other processes running as that user. Never put secrets in probe source, trigger definitions, issue reports, or chat.
- Installation downloads the runtime matching the plugin version from this repository and installs its dependencies with npm. Updates should come from this repository or a marketplace you trust.

See the [guide](https://github.com/hyprh/self-starter/blob/main/docs/guide.md) for configuration and the [design](https://github.com/hyprh/self-starter/blob/main/docs/design.md) for execution boundaries.
