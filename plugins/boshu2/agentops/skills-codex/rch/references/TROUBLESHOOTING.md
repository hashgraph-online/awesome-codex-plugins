# RCH Troubleshooting

## Contents

- [Diagnostic Flow](#diagnostic-flow)
- [Common Errors](#common-errors)
- [Debug Mode](#debug-mode)
- [Safe Reset Sequence](#safe-reset-sequence)
- [Reading `rch status` Output Correctly](#reading-rch-status-output-correctly)
- [Daemon Version Drift After Upgrade](#daemon-version-drift-after-upgrade)
- [Telemetry Corruption](#telemetry-corruption)
- ["Why did my command run locally?" (Silent Fail-Open)](#why-did-my-command-run-locally-silent-fail-open)
- [See Also](#see-also)

## Diagnostic Flow

```text
Compilation running locally instead of remotely?
│
├─ Quick health gate:
│  $ rch check
│  │
│  ├─ Not ready/degraded?
│  │   ├─ Check daemon:
│  │   │  $ rch --json daemon status
│  │   │
│  │   ├─ Check workers:
│  │   │  $ rch workers probe --all
│  │   │
│  │   └─ Check hook install:
│  │      $ rch hook status
│  │
│  └─ Ready?
│      continue below
│
└─ Ready but behavior is wrong?
   ├─ Socket alignment:
   │  $ rch --json config get general.socket_path
   │  $ rch --json daemon status
   │
   ├─ Explain routing decision:
   │  $ rch diagnose "cargo build --release"
   │
   ├─ Validate hook protocol path:
   │  $ rch hook test
   │
   └─ Force direct offload proof:
      $ rch exec -- cargo check --workspace --all-targets
```

---

## Common Errors

### Daemon not running / `check` says not ready

**Cause:** daemon process absent or startup failure.

```bash
rch daemon start
rch --json daemon status
rch daemon logs -n 200
```

### Socket mismatch between config and daemon

**Cause:** `general.socket_path` differs from active daemon socket.

```bash
rch --json config get general.socket_path
rch --json daemon status
# then align and restart:
rch daemon restart -y
```

### "No workers available" / probe failures

**Cause:** no workers configured, SSH/auth failures, or workers are disabled/drained.

```bash
rch workers list
rch workers probe --all
rch workers discover --probe
rch workers discover --add --yes
rch workers setup --all
```

### "rustup: not found" / "cargo: not found" on worker

**Cause:** missing toolchain on one or more workers.

```bash
rch workers sync-toolchain --all
rch workers capabilities --refresh
```

If still failing, SSH to the specific worker and validate `rustup`, `cargo`, and PATH.

### Hook not intercepting

**Cause:** hook missing, wrong binary path, or command classified as local.

```bash
rch hook status
rch hook install
rch hook test
rch diagnose "cargo build --release"
```

### Sync/transfer fails under active target churn

**Cause:** build artifacts changing during rsync.

```bash
# Add target-like excludes in ~/.config/rch/config.toml [transfer].exclude_patterns
rch daemon reload
rch config show --sources
```

Also inspect the worker directly:

```bash
ssh ubuntu@<host> 'df -h / /tmp'
ssh ubuntu@<host> 'du -sh /tmp/rch-* /tmp/rch_target_* 2>/dev/null | sort -h'
```

If cleanup is needed, verify inactivity first:

```bash
ssh ubuntu@<host> 'sudo lsof +D /tmp/rch_target_<name>'
```

If the directory is inactive, prefer targeted stale-artifact cleanup over broad cache deletion.

### Sync fails with `Permission denied` or `Operation not permitted` inside `/data/projects/<repo>`

**Cause:** the canonical mirror on the worker is not writable by the SSH user. This commonly happens when a repo under `/data/projects` was created or updated as `root`.

Check:

```bash
ssh ubuntu@<host> "stat -c '%U:%G %a %n' /data/projects/<repo>"
```

Fix:

```bash
ssh ubuntu@<host> 'sudo chown -R ubuntu:ubuntu /data/projects/<repo> && sudo chmod 775 /data/projects/<repo>'
```

Then retry:

```bash
rch exec -- cargo check --workspace --all-targets
```

### `rch exec` fails open for workdirs outside `/data/projects`

**Cause:** canonical-root normalization rejects workdirs outside the configured project root.

Symptoms include errors mentioning `input resolves outside canonical root`.

Fix:

```bash
pwd
rch diagnose --dry-run "cargo build --release"
```

Then run the build from a workspace under `/data/projects`. If you need a clean copy for testing, stage it under `/data/projects/<temp-repo>` instead of `/tmp/<temp-repo>`.

### Worker shows storage pressure even after cleanup

**Cause:** telemetry lag, large ballast allocation, or active live build churn.

Check:

```bash
rch status --workers --jobs
ssh ubuntu@<host> 'df -h / /tmp && free -h'
ssh ubuntu@<host> 'journalctl -u sbh -n 50 --no-pager'
```

Interpretation:

- If `df` is healthy but `rch status` still warns, give telemetry a minute and refresh.
- If `/tmp` is healthy but `/` is still low, inspect large project `target_*` trees under `/data/projects`.
- If `sbh` is active but repeatedly logging `scan channel saturated` or `scan timed out`, inspect stale build artifacts and verify the host is running the current `sbh` binary and the narrowed worker config.

### Path dependency missing remotely (`../.../Cargo.toml`)

**Cause:** required sibling repositories are not available in worker topology.

```bash
rch diagnose --dry-run "cargo test --workspace"
rch exec -- env CARGO_TARGET_DIR=/tmp/rch_target_<name> cargo check --workspace --all-targets
```

Then ensure sibling repos exist on workers under canonical roots and retry.

---

## Debug Mode

```bash
RCH_LOG_LEVEL=debug rch check
RCH_LOG_LEVEL=debug rch diagnose "cargo test --workspace"
RCH_LOG_LEVEL=debug rch exec -- cargo check --workspace --all-targets
```

Protocol-level hook test:

```bash
RCH_LOG_LEVEL=debug printf '%s\n' \
  '{"tool_name":"Bash","tool_input":{"command":"cargo check"}}' | rch
```

---

## Safe Reset Sequence

```bash
rch daemon restart -y
rch config validate
rch config doctor
rch workers probe --all
rch hook status
rch hook test
rch check
```

If still failing, capture artifacts for escalation:

```bash
rch doctor --json > /tmp/rch-doctor.json
rch --json daemon status > /tmp/rch-daemon-status.json
rch --json workers probe --all > /tmp/rch-workers-probe.json
```

---

## Reading `rch status` Output Correctly

`rch status` (and `rch check`) can simultaneously show `✓ RCH is ready (9/9 workers healthy)` AND a list of `[warning] Circuit opened for worker '<id>'` alerts. **The alerts are informational** — circuit breakers are self-healing once the worker is healthy and the half-open probe succeeds. Don't over-react.

**Wrong:** "I see warnings — better restart the daemon and reload the config."

**Right:** `rch workers probe --all && rch status --workers --jobs` — the alert clears within the next status refresh.

If a circuit doesn't auto-clear after 60 seconds and the underlying probe is healthy, then there's a real bug; capture `rch --json daemon status | jq '.data.circuit_breakers'` and `rch daemon logs -n 100`.

---

## Daemon Version Drift After Upgrade

**Symptom:** New rch CLI features behave inconsistently; `rch --version` differs from the daemon's reported version.

**Self-fix (this is safe — never ask first):**

The daemon's running version is reported by `rch --json status` at `.data.daemon.daemon.version` (the `rch --json daemon status` endpoint deliberately returns only running/socket/uptime — not version). Compare:

```bash
rch --version | awk '{print $2}'
rch --json status | jq -r '.data.daemon.daemon.version'
# If they differ:
rch daemon restart -y                                    # drains in-flight builds gracefully
rch --json status | jq -r '.data.daemon.daemon.version'  # confirm equal
```

`rch daemon restart -y` is the **documented upgrade path**. It drains active builds before stopping. The `-y` skips the interactive prompt — but it does *not* skip the drain.

If a worker shows mismatched binary version after a host upgrade:

```bash
rch fleet status              # human-readable per-worker status
rch fleet verify              # compare installed vs expected
rch fleet deploy --canary 25 --canary-wait 60 --verify
rch fleet deploy --verify
```

---

## Telemetry Corruption

**Symptom:** Recurring `RCH-E507`, `Telemetry database integrity check failed`, empty `rch speedscore --history`, daemon log lines mentioning `database disk image is malformed`.

**Self-fix:** Stop the daemon, move `~/.local/share/rch/telemetry/telemetry.db*` aside, restart. Telemetry is derived data; you lose history but nothing operational.

---

## "Why did my command run locally?" (Silent Fail-Open)

**Symptom:** `rch hook status` says installed; `rch exec` works in isolation; but a particular `cargo build` invocation runs locally without the rch wrapper. No `[RCH] local (...)` line appears because `RCH_VISIBILITY=none` is set, or because the hook never engaged at all.

**Self-fix:**

1. Force visibility: `RCH_VISIBILITY=verbose <your-command>`. If you now see `[RCH] local (...)`, follow `references/FAIL_OPEN.md` to map the reason to a fix.
2. If still no `[RCH]` line, the hook never fired. Probe the protocol directly with a hand-crafted request (see the Wire-Level Hook Protocol section of `references/MACHINE_INTROSPECTION.md`):
   ```bash
   printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"<your-command>"}}' | rch
   ```
   If stdout is empty, the classifier is rejecting your command. Common causes: shell pipe (`cargo build | tee log`), backgrounded with `&`, env-prefixed in an unusual form. Restructure or use `rch exec -- <cmd>` directly.
3. If the hook fires but the command still runs locally, the rewrite isn't being honored — check that `~/.claude/settings.json` has the right hook command path (`rch hook install` re-resolves it).

See `references/FAIL_OPEN.md` for the full taxonomy.

---

## See Also

- `references/FAIL_OPEN.md` — the canonical guide for `[RCH] local (...)` reasons
- `references/ERROR_CODES.md` — the full RCH-Exxx catalog
- `references/RECOVERY_PLAYBOOKS.md` — symptom→fix in ≤90s
- `references/MACHINE_INTROSPECTION.md` — JSON/schema/capability surfaces, wire-level hook protocol
- `references/CONFIGURATION.md` — config keys and precedence
- `references/WORKERS.md` — worker inventory and health
