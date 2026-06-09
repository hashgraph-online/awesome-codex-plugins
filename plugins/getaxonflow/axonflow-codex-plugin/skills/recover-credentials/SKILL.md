---
name: recover-credentials
description: Help the user recover lost AxonFlow tenant credentials via the email magic-link flow, or apply a paid Pro-tier license token. Use when the user says they've lost their AXONFLOW_AUTH, lost their secret, can't authenticate, or has a new AXON- license token to install.
---

The AxonFlow agent exposes two recovery flows users sometimes need to reach from inside Codex:

1. **Email-magic-link recovery** (free, applies to any tenant). The user lost their `AXONFLOW_AUTH` / tenant secret and needs new credentials. They request a magic link, click it, copy the hex token, and the plugin persists the new credentials atomically into `~/.codex/axonflow.toml`.
2. **Pro-tier license-token install**. The user just paid for the Pro tier through Stripe Checkout and received an `AXON-`-prefixed license token by email. They paste it through the same recovery surface and the plugin persists it for the next Codex session to pick up.

Use the `exec_command` tool to invoke the recovery script that ships with the plugin:

| User intent | Command |
|---|---|
| Lost credentials, request new magic link | `bash $PLUGIN_DIR/scripts/recover.sh request` |
| Click magic link, paste hex token | `bash $PLUGIN_DIR/scripts/recover.sh verify` |
| Install paid Pro license token | `bash $PLUGIN_DIR/scripts/recover.sh apply-token` |
| Check current tier / config | `bash $PLUGIN_DIR/scripts/recover.sh status` |

`$PLUGIN_DIR` resolves to the plugin checkout the user installed.

For non-interactive use (test harnesses, CI, automation), the script also reads:

- `AXONFLOW_RECOVER_EMAIL` for `request`
- `AXONFLOW_RECOVER_TOKEN` for `verify`
- `AXONFLOW_LICENSE_TOKEN` for `apply-token`

In each case, after the script runs, advise the user that the new credentials live in `~/.codex/axonflow.toml` (mode `0600`) and that they should restart Codex (or re-export `AXONFLOW_AUTH` / `AXONFLOW_LICENSE_TOKEN` from the file) for the change to take effect.

Never paste the token or secret into chat. The script reads from stdin or env so the value never enters the model context.
