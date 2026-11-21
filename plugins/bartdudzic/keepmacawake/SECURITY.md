# Security of the Keep Mac Awake plugin

## Reporting a vulnerability

Send reports to **hi@keepmacawake.com**, with "Security" in the subject. Include the agent and its version, the plugin version and steps to reproduce. Please do not open a public issue for a vulnerability.

## Supported versions

Only the latest version of the plugin, in the `main` branch of this repository, gets fixes. Update the plugin in your agent to get them.

## What the plugin can do

- The skill tells the agent to run the `keepmacawake` command of the Keep Mac Awake app on this Mac, and `sysctl` and `sw_vers` to check that the Mac fits. It never downloads or runs an installer or a script, never uses `sudo` and never pays.
- The session-start hook runs `keepmacawake status --json` once, with a short timeout, and prints a few sentences of its own. It is read only: it makes no network connection and never starts, stops or changes anything.

The app's own security model is in the repository's [SECURITY.md](../../SECURITY.md).
