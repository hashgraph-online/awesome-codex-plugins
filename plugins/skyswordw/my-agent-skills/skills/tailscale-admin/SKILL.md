---
name: tailscale-admin
description: Use when managing a Tailscale tailnet through the Tailscale v2 API, including devices, auth keys, users, DNS, routes, tags, ACL policy, services, logs, webhooks, or inspecting current Tailscale state from a repository.
---

# Tailscale Admin

## Scope

Use this skill for Tailscale API work where operational docs and plaintext local secrets should remain inside the target repository, not in global skill state.

Recommended target-repo conventions:

- Tailscale provider doc: `providers/tailscale.md`
- local secret env file: `secrets/local/providers/tailscale.env`
- related machine docs: `machines/*.md`
- related service docs: `services/*.md`

Do not paste API keys, generated auth keys, tailnet-private hostnames, or personal user data into tracked Markdown.

## Required Context

Before answering or changing Tailscale resources:

1. Read the target repo's Tailscale provider doc if present.
2. Load secrets from a local secret file or environment variables; never paste keys into responses.
3. If a change affects a documented machine or service, update the related doc and its change log.

## API Runner

Use the bundled helper from the installed skill directory:

```bash
bash skills/tailscale-admin/scripts/ts_api.sh <command> [args]
```

The helper loads:

- `TAILSCALE_API_KEY` from `secrets/local/providers/tailscale.env` by default;
- `TAILSCALE_TAILNET`, defaulting to `-` for the API key's default tailnet;
- `TAILSCALE_API_BASE`, defaulting to `https://api.tailscale.com/api/v2`.

If the target repo keeps the secret file elsewhere, set `TAILSCALE_ENV_FILE`:

```bash
TAILSCALE_ENV_FILE=/path/to/tailscale.env bash skills/tailscale-admin/scripts/ts_api.sh devices
```

Read-only examples:

```bash
bash skills/tailscale-admin/scripts/ts_api.sh status
bash skills/tailscale-admin/scripts/ts_api.sh devices
bash skills/tailscale-admin/scripts/ts_api.sh keys
bash skills/tailscale-admin/scripts/ts_api.sh users
bash skills/tailscale-admin/scripts/ts_api.sh dns
bash skills/tailscale-admin/scripts/ts_api.sh policy > /tmp/tailscale-policy.hujson
```

Mutation examples. Always preview first:

```bash
bash skills/tailscale-admin/scripts/ts_api.sh rename-device <device-id> <new-name> --dry-run
bash skills/tailscale-admin/scripts/ts_api.sh rename-device <device-id> <new-name> --yes

bash skills/tailscale-admin/scripts/ts_api.sh set-device-tags <device-id> '["tag:server"]' --dry-run
bash skills/tailscale-admin/scripts/ts_api.sh set-device-tags <device-id> '["tag:server"]' --yes

bash skills/tailscale-admin/scripts/ts_api.sh create-auth-key \
  '{"capabilities":{"devices":{"create":{"reusable":false,"ephemeral":false,"preauthorized":true,"tags":["tag:server"]}}},"expirySeconds":3600}' \
  --dry-run
```

## Safety Rules

- `GET` commands can run directly.
- `POST`, `PUT`, `PATCH`, and `DELETE` require `--yes`.
- Run the exact mutating command once with `--dry-run` before `--yes`.
- Treat generated auth keys as secrets. Capture them only into `secrets/local/` or a password manager, not into tracked Markdown.
- Prefer device IDs over display names for mutations.
- For ACL/policy changes, back up the current policy, validate the new file, then apply it:

```bash
bash skills/tailscale-admin/scripts/ts_api.sh policy > /tmp/tailscale-policy-before.hujson
bash skills/tailscale-admin/scripts/ts_api.sh validate-policy ./policy.hujson --dry-run
bash skills/tailscale-admin/scripts/ts_api.sh validate-policy ./policy.hujson --yes
bash skills/tailscale-admin/scripts/ts_api.sh set-policy ./policy.hujson --dry-run
bash skills/tailscale-admin/scripts/ts_api.sh set-policy ./policy.hujson --yes
```

## Operation Catalog

For less common endpoints, search the compact operation catalog:

```bash
bash skills/tailscale-admin/scripts/ts_catalog.sh --search webhook
bash skills/tailscale-admin/scripts/ts_catalog.sh --tag DNS --method GET
```

Then call by `operationId`:

```bash
bash skills/tailscale-admin/scripts/ts_call.sh listTailnetDevices \
  --params-json '{"tailnet":"-"}' \
  --jq '.devices[] | {id,name,hostname,lastSeen,tags}'
```

## References

- `references/operations.tsv`: compact Tailscale API operation list.
- Official API docs: `https://tailscale.com/docs/reference/tailscale-api`.
