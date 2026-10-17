# Security

Desktop agent: MIT. Mobile apps: separate paid product.

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.6.x   | yes |
| < 0.6.0 | no — upgrade; 0.5.0 has no inject/spawn guards |

Canonical index (FAQ + GitHub + trust): https://grokbuildremote.com/integrations.html

## Threat model (pairing)

- `gbr-agent pair` binds a **mailbox for this PC**, not a single CLI tab.
- After `gbr-agent run`, the phone can **list and inject every discovered terminal window** on that machine (roster, soft max 255).
- Headless HTTP agents are **not** in that roster. Pointing a sidecar at `127.0.0.1:8788` shows Bot API JSON, not a transcript.
- Anyone with the mailbox key (phone **Settings → Bot API**) can inject. Treat it like a password. Never commit it.
- `POST /v1/inject` types **arbitrary text** into listed TTYs and can submit.

## Trust boundary (loopback vs relay)

| Surface | Bind | Auth |
|---------|------|------|
| Bot API on this PC | `http://127.0.0.1:8788` after `gbr-agent run` | **Unauthenticated by default** (MCP/loopback clients). Set `GBR_BOT_REQUIRE_KEY=1` / `true` / `on` to require the mailbox key even on loopback. **Hub and `gbr-agent service install` should set this** — `POST /v1/devices` upserts remote mailbox keys. |
| HTTPS relay | `https://gbr-relay.ekobrott.workers.dev/v1/mb/{id}/…` | `X-GBR-Key` (or Bearer) on **push / poll / ack / Bot API**. `POST /v1/mb/:id/pair` is **unauthenticated** and throttled (12/hour/mailbox) — that is where the key is issued. See [relay/README.md](relay/README.md). |
| MCP stdio | `gbr-mcp` on the same machine | Local process; still talks to loopback `:8788` |

“Attach only loopback / stdio” is not the whole story. Anyone local on that PC can inject unless `GBR_BOT_REQUIRE_KEY=1`/`true`/`on`. Felanmälan / QA PC Android titles are hard-denied (bind and inject). Inbox comments inject only from `LinespottingPrivate` (`GBR_INBOX_AUTHORS`). Details: [docs/BOT-API.md](docs/BOT-API.md).

## Install

Prefer [docs/PINNED-INSTALL.md](docs/PINNED-INSTALL.md): checksum **the installer** (GitHub Release tag `v0.6.2`), then run it; it checksums the binary. Do not mutate v0.6.0 or v0.6.1. Website `curl | bash` is a mutable convenience URL for humans on grokbuildremote.com only — refuse `VERSION=latest`. Do not publish pipe-to-shell in other projects’ official trees.

## Report

info@linespotting.com — no mailbox keys or `device.json` in the mail.

## External merges

Malicious-code review gate for outside PRs and third-party drops: [SECURITY-EXTERNAL-MERGES.md](SECURITY-EXTERNAL-MERGES.md) (process [#56](https://github.com/LinespottingOrg/GrokBuildRemote-Agents/issues/56)).
