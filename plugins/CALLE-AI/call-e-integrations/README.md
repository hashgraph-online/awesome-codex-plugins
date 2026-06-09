# CALL-E for Codex

Use CALL-E from Codex through the `calle` CLI.

This plugin provides the `$calle` skill for setup checks, authentication
recovery, phone call planning, planned call execution, and call status checks.
It reuses the `@call-e/cli` package so authentication, token caching, JSON
output, and MCP error handling stay owned by the CLI.

## Install

The official marketplace install command requires `codex-cli >= 0.122.0`.
Check your version with `codex --version`; older Codex releases are outside the
primary support path for this command.

Add the latest released CALL-E Codex marketplace from the repository root:

```bash
codex plugin marketplace add CALLE-AI/call-e-integrations \
  --ref '@call-e/codex-plugin@latest' \
  --sparse .agents/plugins \
  --sparse packages/codex-plugin/plugin
```

`@call-e/codex-plugin@latest` is a Git tag updated by the release workflow after
`@call-e/codex-plugin` publishes. For a reproducible install, replace it with a
package-level release tag such as `@call-e/codex-plugin@<version>`.

Open Codex, run `/plugins`, choose the `CALL-E` marketplace, and install
`CALL-E`.

If you are pinned to a Codex CLI older than `0.122.0` and cannot use
`codex plugin marketplace add`, upgrade Codex when possible. As a manual
fallback, add the equivalent sparse payload from the same Git ref to your
workspace root:

```text
.agents/plugins/marketplace.json
packages/codex-plugin/plugin/
```

Keep those paths exactly as shown so the marketplace entry can resolve
`./packages/codex-plugin/plugin`.

## Authentication

The plugin uses the repository-local CLI when available, then a global `calle`
command when available, then falls back to `npx -y @call-e/cli`.

To authenticate before using the plugin:

```bash
npx -y @call-e/cli auth login
```

When `$calle` is invoked, the skill checks authorization first. If login is
missing or expired, it runs blocking `calle auth login`, shows the brokered
authorization link, and continues automatically after browser authorization
completes.

## ChatGPT App Boundary

This Codex plugin is intentionally CLI-based. If you also publish or install a
same-name CALL-E ChatGPT App, keep it disabled in Codex when you want `$calle`
to use the plugin path:

```toml
[apps.<app-id>]
enabled = false
```

You can also disable all ChatGPT Apps/connectors for a Codex profile:

```toml
[features]
apps = false
```

The bundled `$calle` skill tells Codex not to call ChatGPT App/connector tool
namespaces while the plugin skill is active, but disabling the App in Codex
configuration is the hard isolation boundary.

## Safety

CALL-E can place real phone calls. The skill plans first, uses returned
credentials exactly as provided, and does not place a call unless the user
clearly intends to do so.
