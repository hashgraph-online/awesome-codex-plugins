# Telemetry Database Corruption Recovery

## Contents

- [Symptom Signatures](#symptom-signatures)
- [Recovery (Safe)](#recovery-safe)
- [Verify Integrity Before Acting](#verify-integrity-before-acting)
- ["Telemetry protocol version mismatch"](#telemetry-protocol-version-mismatch)
- [Prevention](#prevention)
- [When the Recovery Doesn't Stick](#when-the-recovery-doesnt-stick)

The rch telemetry SQLite database lives at `~/.local/share/rch/telemetry/telemetry.db`. Like any SQLite file under heavy concurrent write load, it can occasionally corrupt — most often after host crashes, OOM-kills, or disk-full incidents.

This is one of the cliffs agents previously fell off (cass evidence: 30+ incidents under "Telemetry database integrity check failed"). The recovery is mechanical and safe — but the skill never previously documented it.

---

## Symptom Signatures

Any of:

- `[RCH-E507] Metrics collection error` recurring in `rch daemon logs`
- `Telemetry database integrity check failed` log lines
- `Telemetry protocol version mismatch` (related; less common)
- `rch speedscore --all` returns empty or stale data
- `rch self-test history` returns empty even though you know runs happened
- `database disk image is malformed` in daemon stderr

`rch doctor` may or may not catch this (depends on version).

---

## Recovery (Safe)

Telemetry is **purely derived data**. Losing it loses historical SpeedScores and build durations, but nothing operationally critical.

```bash
# 1. Stop the daemon (drains in-flight builds)
rch daemon stop -y

# 2. Move the corrupt db aside (don't delete; you might want it for forensics)
mv ~/.local/share/rch/telemetry/telemetry.db ~/.local/share/rch/telemetry/telemetry.db.broken-$(date +%s)
mv ~/.local/share/rch/telemetry/telemetry.db-wal ~/.local/share/rch/telemetry/telemetry.db-wal.broken-$(date +%s) 2>/dev/null || true
mv ~/.local/share/rch/telemetry/telemetry.db-shm ~/.local/share/rch/telemetry/telemetry.db-shm.broken-$(date +%s) 2>/dev/null || true

# 3. Restart — the daemon recreates the schema on first write
rch daemon start
sleep 2
rch check
```

Verify:

```bash
ls -la ~/.local/share/rch/telemetry/    # new telemetry.db should exist
rch --json daemon status | jq '.data.version'
```

You'll lose:
- SpeedScore history (`rch speedscore --history`) — rebuilds on subsequent self-tests
- Self-test history (`rch self-test history`) — same

You will NOT lose:
- Worker config
- Daemon config
- Hook installs
- Active builds (the daemon stop drains them gracefully)

---

## Verify Integrity Before Acting

Before assuming the db is broken, check it directly:

```bash
sqlite3 ~/.local/share/rch/telemetry/telemetry.db 'PRAGMA integrity_check;'
```

If that prints `ok`, the corruption is elsewhere — probably the daemon process is wedged on a different bug. Capture diagnostics and consider `Playbook B` in `RECOVERY_PLAYBOOKS.md` instead.

If it prints any error or hangs, the db is genuinely corrupt — proceed with the move-aside recovery.

---

## "Telemetry protocol version mismatch"

This is different — it means a worker is running a `rch-wkr` whose telemetry schema doesn't match the daemon's. The fix is to redeploy the worker binary:

```bash
rch fleet status                    # confirm version drift
rch fleet deploy --canary 25 --canary-wait 60 --verify
rch fleet deploy --verify           # full
```

If only one worker is affected:

```bash
rch fleet deploy --worker <id> --verify
```

---

## Prevention

- Don't kill the daemon while builds are in flight (use `rch daemon stop -y`, which drains).
- Watch disk pressure on the host (not just on workers — the host runs the daemon and the telemetry db). `df -h ~/.local/share` should never be near full.
- If you're upgrading rch on the host, restart the daemon afterwards (`rch daemon restart -y`). The `daemon_installs_hooks` self-healing covers one direction, but version drift on the daemon binary is independent.

---

## When the Recovery Doesn't Stick

If you move the file aside and the new db corrupts again within minutes, you have a deeper issue — disk failure, kernel-level bug, or another process writing to the same file. Capture:

```bash
journalctl -k --since "1 hour ago" | grep -iE 'i/o|sata|nvme|memory'
sudo dmesg | tail -50
df -h ~/.local/share/rch/telemetry/
mount | grep "$(stat -c %m ~/.local/share/rch/telemetry/)"
```

…and escalate. This is filesystem-level; the rch skill has done what it can.
