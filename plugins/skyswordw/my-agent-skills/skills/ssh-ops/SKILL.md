---
name: ssh-ops
description: Use when running ordinary SSH operations after access is known, including token-efficient remote execution, output trimming, raw log capture under a generic remote scratch directory, and batch commands through the bundled SSH helper.
---

# SSH Ops

## Scope

Use this skill for ordinary SSH operations after the login path is already known or has been verified by `ssh-frp-access`.

Use it for:

- token-efficient remote command execution;
- host health checks and short resource surveys;
- service status checks after login works;
- remote log collection with raw logs stored under a generic remote scratch directory such as `/tmp/ssh-ops`;
- batched command execution through the bundled SSH helper.

Do not use this skill to decide FRP/NAT/VICP reachability, off-campus/on-campus path selection, or SSH alias corrections. Use `skills/ssh-frp-access/SKILL.md` first for those.

## Read First

1. `README.md` for the machine and service index.
2. `machines/<machine>.md` for the target alias, user, host, and port.
3. `services/<service>.md` when checking a service.
4. Secret-handling docs before referencing any secret path.

## Preferred Wrapper

The canonical implementation lives inside this skill at `skills/ssh-ops/scripts/ssh-ops.sh`. If an installed project has a repo-root wrapper such as `scripts/ssh-ops.sh`, prefer that for short copyable commands; otherwise call the bundled helper directly.

```bash
skills/ssh-ops/scripts/ssh-ops.sh health <alias>
skills/ssh-ops/scripts/ssh-ops.sh run <alias> -- '<command>'
skills/ssh-ops/scripts/ssh-ops.sh batch <alias> <local-script>
skills/ssh-ops/scripts/ssh-ops.sh logs <alias> journal <unit>
skills/ssh-ops/scripts/ssh-ops.sh logs <alias> docker <container>
```

Expected behavior:

- `health` returns identity, uptime, disk, memory, CPU/GPU basics, and active containers/services in a compact summary.
- `run` executes one remote command and prints only the relevant trimmed output.
- `batch` uploads or feeds a local script for multi-step checks, avoiding repeated chat-visible SSH output.
- `logs` stores raw remote logs under a generic remote scratch directory on the remote host and prints a short summary or tail. Use `journal` for `journalctl -u <unit>` and `docker` for `docker logs <container>`.

If the bundled helper is missing, do not recreate it ad hoc during this skill. Use the fallback commands below and mention that the bundled helper is not present.

## Fallback Commands

For a short health check:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 <alias> '
set -eu
echo "__HOST__"; hostnamectl 2>/dev/null || hostname
echo "__UPTIME__"; uptime
echo "__MEM__"; free -h 2>/dev/null || true
echo "__DISK__"; df -hT | sed -n "1,12p"
echo "__CPU__"; lscpu 2>/dev/null | sed -n "1,20p" || true
echo "__GPU__"; nvidia-smi 2>/dev/null | sed -n "1,20p" || true
echo "__DOCKER__"; docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | sed -n "1,30p" || true
'
```

For a single command with bounded output:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 <alias> '<command>' | sed -n '1,120p'
```

For raw remote log capture:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 <alias> '
set -eu
mkdir -p /tmp/ssh-ops
out="/tmp/ssh-ops/<service>-$(date +%Y%m%d-%H%M%S).log"
<log-command> > "$out" 2>&1 || true
echo "raw_log=$out"
tail -n 80 "$out"
'
```

For a temporary batch script:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 <alias> 'bash -s' < /path/to/local-check.sh
```

## Output Rules

- Keep chat-visible output short. Prefer summaries, selected fields, and `sed -n '1,120p'` or `tail -n 80`.
- Preserve raw logs on the remote host under a generic scratch directory such as `/tmp/ssh-ops` when logs may be long.
- Report the raw log path when a log was captured.
- Redact secrets before showing output. Do not write tokens, passwords, private keys, cookies, or OAuth material into tracked docs.
- If a command is destructive or changes service state, explain the exact target and expected effect before running it.

## When To Hand Off

- If `ssh -G`, `nc`, authentication, FRP/NAT, or VICP reachability is unclear, switch to `ssh-frp-access`.
- If service-specific commands are needed, combine this skill with the relevant service skill, such as `sub2api-ops` or `substore-ops`.
- If connection details changed, update the machine/service docs through the relevant access or service skill.

## Future Work

- Add optional ControlMaster/ControlPersist prewarm support to reduce repeated SSH setup cost.
- Add a session mode for long-running remote operations.
- Evaluate async SSH workflow tools before adopting an asynchronous execution pattern.
- Add JSON output mode for machine-readable health, run, batch, and logs results.
