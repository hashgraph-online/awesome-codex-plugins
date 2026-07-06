# SSH Tuning for RCH

## Contents

- [Defaults Worth Knowing](#defaults-worth-knowing)
- [ControlMaster Default Is OFF](#controlmaster-default-is-off)
- [Keepalives for Long Builds](#keepalives-for-long-builds)
- [Connect / Command Timeouts](#connect--command-timeouts)
- [Authentication Failure Triage](#authentication-failure-triage)
- [Retryable vs Fatal Transport Errors](#retryable-vs-fatal-transport-errors)
- [Known-Hosts Policy](#known-hosts-policy)
- [End-to-End Probe Recipes](#end-to-end-probe-recipes)
- [Multi-Hop / Jump Host](#multi-hop--jump-host)
- [Quick Knob Cheat Sheet](#quick-knob-cheat-sheet)

Most "intermittent worker failure" reports trace to SSH transport quirks: stale ControlMaster sockets, broken keepalives, or auth misconfiguration. RCH gives you knobs for all of them.

---

## Defaults Worth Knowing

`rch_common::ssh::SshOptions::default()`:

```text
connect_timeout       = 10s
command_timeout       = 300s
server_alive_interval = None   (OpenSSH default; keepalive disabled)
control_persist_idle  = None   (uses ControlPersist=yes when control_master is true)
control_master        = false  (default OFF — see history below)
known_hosts           = Add    (add unknown hosts to ~/.ssh/known_hosts)
```

**MAX output capture per command: 10 MB** (stdout/stderr each). Larger output is truncated to prevent OOM.

---

## ControlMaster Default Is OFF

Recent change: commit `464a25b` flipped the default to `control_master = false` because *stale local control sockets were poisoning otherwise healthy connections* — particularly painful for multi-agent fleets where one terminating session would orphan a master and the next agent would see hangs.

Opt-in if you really want connection reuse on a single-agent box:

```bash
export RCH_SSH_CONTROL_PERSIST_SECS=60       # enables persistence with 60s idle
```

If you opt in, expect to manually clean stale sockets occasionally:

```bash
ls /run/user/$(id -u)/openssh-* ~/.ssh/control-* ~/.ssh/cm-* 2>/dev/null
ssh -O check ubuntu@<host> 2>&1 || true
ssh -O exit ubuntu@<host> 2>&1 || true
```

A symptom signature for ControlMaster poisoning: probes succeed (`rch workers probe --all`), but `rch exec -- ...` hangs at "syncing" or "executing" with no progress for ~30s before failing.

---

## Keepalives for Long Builds

`cargo build --release` for a big workspace can sit idle on the SSH channel while the worker does heavy CPU work and emit nothing for minutes. NAT/firewall idle timers can drop the connection.

```bash
export RCH_SSH_SERVER_ALIVE_INTERVAL_SECS=15
```

This sets `ServerAliveInterval=15`, equivalent to a heartbeat every 15 seconds. Symptom this fixes: `RCH-E105 SSH session terminated unexpectedly` mid-build with no other apparent cause.

---

## Connect / Command Timeouts

Connect: 10s default. Command: 300s default. The command timeout is the upper bound on a single SSH command (probe, mkdir, exec wrapper). A real *build* runs through the workers' own pipeline and is bounded by `[compilation] build_timeout_sec`, not the SSH command timeout.

To raise across the board, set `[compilation] build_timeout_sec = 1800` for a 30-minute ceiling.

For ad-hoc one-shot tuning of the daemon's own SSH command timeouts, you'll need to edit the source — there's no env knob today. (If you find yourself wanting one, that's a code change worth filing.)

---

## Authentication Failure Triage

`RCH-E101 SSH authentication failed` is almost always one of:

1. Wrong key in workers config: `rch --json config get` to inspect the worker's `identity_file`.
2. Permissions on the key: `chmod 600 ~/.ssh/<key>`.
3. Agent doesn't have the key: `ssh-add ~/.ssh/<key>` (if you use ssh-agent).
4. Key not authorized on the worker: `ssh -i <key> ubuntu@<host> true` reproduces.

`RCH-E102 SSH key not found or invalid format` — the path in `identity_file` doesn't exist or isn't a private key. Check `ls -la <path>` and `head -1 <path>` (PEM vs OpenSSH).

`RCH-E103 SSH host key verification failed` — the worker's host key changed (rebuild?). Compare the new fingerprint with what's stored:

```bash
ssh-keygen -F <host>             # what we know
ssh-keyscan <host> 2>/dev/null   # what the host claims now
```

If you trust the new fingerprint, remove the old entry (with explicit user authorization) and let `KnownHostsPolicy::Add` re-add on next probe.

---

## Retryable vs Fatal Transport Errors

`is_retryable_transport_error_text` (in `rch_common/ssh_utils.rs`) classifies SSH errors. Retryable signatures include:

- `connection reset`
- `broken pipe`
- `connection refused`
- `temporary failure`
- transient DNS errors

Fatal:

- auth errors
- host key mismatch
- "no such file" inside the remote command (those are *application* errors, not transport)

The daemon retries retryable errors with backoff. If you keep seeing the same error on retry, treat it as fatal and triage with `rch workers probe <id>` and direct `ssh -v`.

---

## Known-Hosts Policy

Three modes (`rch_common::ssh::KnownHostsPolicy`):

- `Strict` — production-style, fails closed on unknown
- `Add` (default) — auto-adds first time
- `AcceptAll` — testing only

There's no env override today; this is set by the daemon's SSH session builder. If you want strict, you'd have to use a wrapper. For most agent fleets, `Add` is fine.

---

## End-to-End Probe Recipes

Single worker:

```bash
rch workers probe css --json
ssh -v -i <identity_file> ubuntu@<host> 'echo OK; df -h / /tmp; free -h'
```

All workers, parallel:

```bash
rch --json workers probe --all | jq '.data[] | {id, status, latency_ms, last_error}'
```

If a probe says ok but `rch exec` fails:

```bash
RCH_LOG_LEVEL=debug rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_probe" cargo check --quiet 2>&1 | tail -50
```

Look for the first SSH-shaped error in that tail. The structured remediation field of `RCH-E1xx` codes will point you to the right knob.

---

## Multi-Hop / Jump Host

If your workers sit behind a bastion, set it in `~/.ssh/config` and refer to the alias as the worker `host`:

```sshconfig
Host worker-css
  HostName 10.0.0.5
  User ubuntu
  ProxyJump bastion.example.com
  IdentityFile ~/.ssh/id_ed25519_workers
```

Then `[[workers]]` uses `host = "worker-css"`. The recent `464a25b` fix specifically improved alias-based path topology resolution, so multi-hop aliases work cleanly in v1.0.16+.

---

## Quick Knob Cheat Sheet

| Knob | Purpose |
|---|---|
| `RCH_SSH_KEY` | Default `identity_file` for all workers (overridden by per-worker config) |
| `RCH_SSH_SERVER_ALIVE_INTERVAL_SECS` | Keepalive interval for long-running commands |
| `RCH_SSH_CONTROL_PERSIST_SECS` | Enable ControlMaster + persist N idle seconds. `0` = disable. |
| `RCH_TRANSFER_ZSTD_LEVEL` | rsync compression level (1-22) |
| `[[workers]] identity_file` | Per-worker key path |
| `[[workers]] tags` | Selection filter |
| `[[workers]] priority` | Selection bias |
