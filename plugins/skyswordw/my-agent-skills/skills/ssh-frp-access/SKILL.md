---
name: ssh-frp-access
description: Use when resolving SSH aliases, FRP/NAT/VICP reachability, off-campus or on-campus path selection, serial retry, or synchronizing machines/*.md and scenarios/*.md connection details.
---

# SSH FRP Access

## Scope

Use this skill for machine access path work in a server-ops repository: resolving SSH aliases, choosing direct vs FRP/NAT/VICP routes, diagnosing reachability, retrying flaky access serially, and synchronizing connection documentation.

Use `skills/ssh-ops/SKILL.md` after login works for ordinary remote execution, resource surveys, service checks, and log collection.

Use placeholders in publishable docs and examples:

- SSH alias: `<alias>`
- user: `<user>`
- FRP host: `frp.example.com`
- port: `<port>`
- machine doc: `machines/<machine>.md`

Never write private keys, passwords, tokenized URLs, or personal machine secrets into tracked docs.

## Read First

1. `README.md` for the machine index.
2. `machines/<machine>.md` for the target machine truth.
3. `scenarios/on-campus.md` or `scenarios/off-campus.md` when the network path matters.
4. Secret-handling docs before referencing any key path or secret.

## Fast Path

For an existing alias:

```bash
ssh -G <alias> | sed -n '1,80p'
nc -vz <host> <port>
ssh -o BatchMode=yes <alias> 'hostname; uptime'
```

If the command above succeeds and the task is about host resources, service status, or logs, switch to `ssh-ops` before collecting larger output.

For FRP paths that close early, retry serially before changing assumptions:

```bash
for i in 1 2 3; do
  echo "attempt $i"
  ssh -o BatchMode=yes -o ConnectTimeout=8 <alias> 'hostname; uptime' && break
  sleep 2
done
```

Publishable placeholder examples:

```bash
nc -vz frp.example.com <port-a>
ssh -p <port-a> <user>@frp.example.com

nc -vz frp.example.com <port-b>
ssh -p <port-b> <user>@frp.example.com
```

## Diagnosis Order

1. Resolve local config: `ssh -G <alias>`.
2. Check network path: `nc -vz <host> <port>`.
3. Probe authentication without hanging: `ssh -o BatchMode=yes -o ConnectTimeout=8 <alias> 'true'`.
4. If authenticated, confirm identity with a small command:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 <alias> 'hostname; uptime'
```

5. For resource surveys, service checks, or logs, hand off to `ssh-ops`.

## Document Updates

When changing connection details:

- Update `machines/<machine>.md` login commands, FRP/NAT mapping, and change log.
- Update `README.md` machine index if alias, host, port, or recommended method changed.
- Update `scenarios/*.md` if the scenario-level command changed.
- Only reference existing local secret paths such as `secrets/local/...` or `~/.ssh/...`; do not include key contents.

Use date format `YYYY-MM-DD` in change logs.

## Common Pitfalls

- A first FRP failure can be misleading. Serial retries are safer than parallel probes for flaky FRP paths.
- HTTP frontend behavior does not prove SSH health.
- If `ssh -G` and repo docs disagree, verify live behavior first, then update docs.
- Do not collect long remote logs in this skill. Once access is proven, use `ssh-ops` so raw logs stay under a generic remote scratch directory and chat-visible output remains short.
