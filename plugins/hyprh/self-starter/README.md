# Self-Starter for Codex

Define custom events in plain language and let Codex act when they happen, with no model tokens spent while waiting.

For example: "When the GPU has been idle for ten minutes, start the next experiment" or "When this training run finishes, compare it with the previous one." Codex writes and tries a small probe, then Self-Starter checks it in the background and brings the task back to your conversation when it fires. Probes can watch files, logs, commands, local services and web APIs.

## Install

Requires macOS or Linux, Node.js 20 or newer, and the Codex app or CLI.

```sh
codex plugin marketplace add hyprh/self-starter
codex plugin add self-starter@self-starter
```

Restart Codex after installation. The first start installs the matching runtime and bundled Deno from `hyprh/self-starter`, and starts its background service. Later starts use the installed runtime. No separate Self-Starter account is required; agent actions use your Codex setup, and particular probes may need credentials for the services they watch.

## Permissions

Probes run as the current user by default. An API-only probe can use `probe.access: sandbox` to restrict it to declared network hosts and environment variables. Review the probe and action before activation. Enter service credentials with the CLI, never in chat or probe source.

Read the [full guide](https://github.com/hyprh/self-starter/blob/main/docs/guide.md) and [security policy](SECURITY.md).

## Bundle layout

The manifest declares `skills`, `mcpServers`, and `scripts: ./bin`. The scripts field tells catalog generators to retain the MCP launcher's `bin/` directory when mirroring this bundle; the launcher remains `bin/start.mjs`.
