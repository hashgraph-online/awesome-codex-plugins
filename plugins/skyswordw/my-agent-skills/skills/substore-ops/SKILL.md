---
name: substore-ops
description: Use when operating a Sub-Store deployment, editing remote subscription config, diagnosing missing subscription prefixes, validating exported subscriptions, checking cacheKey/cacheTtl behavior, or updating service documentation.
---

# SubStore Ops

## Scope

Use this skill for a documented Sub-Store deployment. Adapt the placeholders to the target repository's service docs before running commands:

- service doc: `services/substore.md`
- machine doc: `machines/<host>.md`
- SSH alias: `<substore-host-alias>`
- runtime directory: `/opt/example/substore`
- public export URL: `https://substore.example.com/subs/<profile>`

Do not paste full subscription URLs, hidden paths, node passwords, tokens, or expanded cache contents into tracked docs.

## Read First

1. `services/substore.md`.
2. `machines/<host>.md`.
3. DNS or HTTPS provider docs if public routing is involved.
4. Secret-handling docs before referencing subscription URLs, tokens, hidden paths, or node credentials.

## Health Check

```bash
ssh <substore-host-alias>
cd /opt/example/substore
docker compose ps
docker logs --tail=100 <substore-container>
curl -sSI http://127.0.0.1:<local-port>/ | head
curl -sSI https://substore.example.com/subs/<profile> | head
```

## Config Edit Flow

Before editing remote persisted config:

```bash
cd /opt/example/substore
cp -a data/sub-store.json "data/sub-store.json.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp -a data/root.json "data/root.json.bak.$(date -u +%Y%m%dT%H%M%SZ)" 2>/dev/null || true
```

Edit only the target section. Restart when needed:

```bash
cd /opt/example/substore
docker compose restart <substore-service>
docker logs --tail=100 <substore-container>
```

## Export Validation Is Required

Raw JSON looking correct is not enough. Validate the rendered/exported result:

```bash
curl -fsS https://substore.example.com/subs/<profile> -o /tmp/substore-profile.yaml
wc -c /tmp/substore-profile.yaml
rg -n "\\[AIR\\]|\\[PRO\\]|<expected-node-fragment>" /tmp/substore-profile.yaml
```

When prefixes are wrong, inspect the processing chain:

- Source-entry metadata such as `tag:["PRO"]` may not survive later rename stages.
- Collection-level scripts can rewrite visible node names after source-level settings.
- Prefer matching stable endpoint fragments or provider identifiers instead of display names that may be rewritten.
- Explain both raw config and final rendered subscription behavior.

## Cache Rules

- `#cacheKey=<name>&cacheTtl=<seconds>` lives in URL fragments and is not sent upstream.
- Custom cache material can contain expanded node credentials; never copy it into Git-tracked files.
- If cache policy changes, document the new policy and validation result without exposing cached node data.

## Documentation Rules

Update `services/substore.md` when any of these change:

- public export URLs,
- runtime directory or container name,
- reverse proxy paths,
- cache policy,
- node grouping or prefix semantics,
- backup file names created during a remote change,
- validation counts or visible export behavior.

Update `machines/<host>.md` only when host access, ports, or deployment ownership changes.
