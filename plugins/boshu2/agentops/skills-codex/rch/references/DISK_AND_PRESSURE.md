# Worker Disk & Resource Pressure

## Contents

- [Pressure Surfaces RCH Tracks](#pressure-surfaces-rch-tracks)
- [The First Mistake: `/` vs `/tmp` Confusion](#the-first-mistake--vs-tmp-confusion)
- [Inspect First, Delete Second](#inspect-first-delete-second)
- [Hand Off to `sbh`](#hand-off-to-sbh)
- [When `sbh` Doesn't Help (RCH-E215 / RCH-E216 / RCH-E217)](#when-sbh-doesnt-help-rch-e215--rch-e216--rch-e217)
- [Memory Pressure (RCH-E214)](#memory-pressure-rch-e214)
- [I/O Pressure (RCH-E213)](#io-pressure-rch-e213)
- [Telemetry Lag (RCH-E212)](#telemetry-lag-rch-e212)
- [Preventive Hygiene](#preventive-hygiene)
- [Triage Cheat Sheet](#triage-cheat-sheet)

Disk pressure on workers is the single biggest source of "rch was working, now it isn't" bug reports. This file is the canonical playbook — and the explicit handoff protocol to the `sbh` (Storage Ballast Handler) skill, which exists precisely to defend against this.

---

## Pressure Surfaces RCH Tracks

The daemon collects telemetry from each worker and exposes it as a stable enum. Visible codes:

| Code | Meaning | Severity |
|---|---|---|
| `RCH-E210` | Worker disk usage critically high | Critical — selection skips this worker |
| `RCH-E211` | Worker disk usage above warning threshold | Warning — biases scheduler away |
| `RCH-E212` | Disk pressure telemetry stale or missing | Warning — can't trust the signal |
| `RCH-E213` | Worker disk I/O utilization too high | Warning — transient, often clears |
| `RCH-E214` | Worker memory pressure too high | Warning — same |
| `RCH-E215` | Disk reclaim operation failed | Critical — sbh ran but didn't free enough |
| `RCH-E216` | Insufficient disk headroom for build reservation | Critical — even after reclaim |
| `RCH-E217` | Active build protection prevented reclaim | Informational — sbh is being cautious |

These appear in:

- `rch --json status --workers` — at `.data.daemon.workers[]`, with **flat** fields:
  `pressure_state`, `pressure_reason_code`, `pressure_confidence`,
  `pressure_disk_free_gb`, `pressure_disk_total_gb`, `pressure_disk_free_ratio`,
  `pressure_disk_io_util_pct`, `pressure_memory_pressure`,
  `pressure_telemetry_age_secs`, `pressure_telemetry_fresh`
- `rch --json workers probe --all` — `.data[].error` includes pressure-related text when probe surfaces it
- `[RCH] remote <worker> failed [RCH-E2xx]` summary line

---

## The First Mistake: `/` vs `/tmp` Confusion

By default RCH stages remote builds under `[transfer] remote_base = "/tmp/rch"`, but workspace mirrors live under `/data/projects` (canonical root) which is on `/`. If `rch status` warns about pressure on a worker, **check both filesystems separately** — fixing the wrong one wastes time.

```bash
ssh ubuntu@<host> 'df -h / /tmp && free -h && cat /proc/pressure/memory && cat /proc/pressure/io'
```

Interpretation:

- `/tmp` hot, `/` fine → stale `/tmp/rch_target_*` or `/tmp/rch-*` artifact dirs
- `/` hot, `/tmp` fine → bloated `target_*` trees inside `/data/projects`
- both hot → `sbh` reclaim, then targeted cleanup

---

## Inspect First, Delete Second

Before removing anything:

```bash
ssh ubuntu@<host> 'du -sh /tmp/rch-* /tmp/rch_target_* 2>/dev/null | sort -h | tail'
ssh ubuntu@<host> 'find /data/projects -maxdepth 2 -type d \( -name "target_rch_*" -o -name "target_*" -o -name "target-*" -o -name target \) -exec du -sh {} + 2>/dev/null | sort -h | tail -n 20'
```

Then verify the candidate is **inactive** (no open files):

```bash
ssh ubuntu@<host> 'sudo lsof +D /tmp/rch_target_<name> 2>/dev/null | head'
ssh ubuntu@<host> 'sudo lsof +D /data/projects/<repo>/target_rch_<name> 2>/dev/null | head'
```

Only when `lsof` is empty is the directory safe to clean.

---

## Hand Off to `sbh`

The `sbh` skill is the right tool for sustained disk pressure on workers. Quote from its description: "Disk-pressure defense for AI coding workloads. Use when: disk full, low space, ballast, cleanup, scan artifacts."

Pattern: detect with `rch`, remediate with `sbh`.

```bash
# Detect from rch — the actual JSON path is .data.daemon.workers[]
# and pressure fields are FLAT (e.g., .pressure_state, .pressure_reason_code).
rch --json status --workers | jq -r '
  .data.daemon.workers[]
  | select(.pressure_state != "healthy")
  | "\(.id)\t\(.pressure_state)\t\(.pressure_reason_code)"'

# Get host for a given worker id (so you can ssh to it)
worker_host() {
  rch --json workers list \
    | jq -r --arg id "$1" '.data.workers[] | select(.id == $id) | .host'
}

# For each pressure-flagged worker, hand off to sbh on that host
rch --json status --workers \
  | jq -r '.data.daemon.workers[] | select(.pressure_state != "healthy") | .id' \
  | while read -r w; do
      h="$(worker_host "$w")"
      ssh "ubuntu@$h" 'sbh status --json' 2>/dev/null \
        || echo "($w / $h) — sbh not installed or ssh failed"
    done
```

If `sbh` is installed on the worker, it can:

- Drop ballast files
- Scan and clean artifact dirs (incremental compilation, doctests, stale `incremental/`)
- Report what it freed

If `sbh` is **not** on a worker yet, you should not write `rm -rf` of your own. Either install `sbh` (one-line bootstrap) or escalate. The combination of (a) building under-resourced disks and (b) one agent's `rm -rf` colliding with another agent's active build has historically been the worst class of incidents in this fleet.

---

## When `sbh` Doesn't Help (RCH-E215 / RCH-E216 / RCH-E217)

- **`RCH-E215 Disk reclaim failed`** — sbh ran but couldn't free enough. Inspect the largest residents that sbh refused to touch (often `/var/log/journal` or `~/.cargo/registry`). For `~/.cargo/registry`, `cargo cache --autoclean` (if `cargo-cache` installed) is safer than blanket deletion.
- **`RCH-E216 Insufficient headroom for build reservation`** — the worker's free space is below the build reservation watermark even after reclaim. Either raise reservation budget (config) or steer the build elsewhere with tags / `rch workers drain <id>`.
- **`RCH-E217 Active build protection prevented reclaim`** — sbh refused to touch a path that was actively being written. Wait for the build, then retry. Don't override; this guard exists to avoid breaking other agents' builds.

---

## Memory Pressure (RCH-E214)

Memory pressure is usually transient (a big test process). Quick diagnose:

```bash
ssh ubuntu@<host> 'free -h && cat /proc/pressure/memory && ps -eo pid,user,rss,cmd --sort=-rss | head -15'
```

If a runaway `cargo test` is the culprit, use the `process-triage` skill (`pt`) — its job is exactly this. Don't `kill -9` blindly; another agent's active build might be the largest process.

---

## I/O Pressure (RCH-E213)

If you see this code repeatedly without disk pressure, the worker is likely under contention from multiple parallel builds. Either:

- Lower the worker's `total_slots` to reduce concurrency
- Route work to a less-loaded worker via `tags`
- Wait — `RCH-E213` clears as soon as I/O drops

---

## Telemetry Lag (RCH-E212)

`Disk pressure telemetry stale or missing`. The worker isn't reporting fresh pressure data. Either:

- `rch-wkr` on the worker is dead → ssh in and check, then `rch fleet deploy --workers <id> --verify`
- The worker just rebooted; wait one telemetry tick (~30s)
- Daemon is wedged — `rch daemon restart -y` (after checking `rch queue` for active builds)

---

## Preventive Hygiene

In `~/.config/rch/config.toml` on every host, keep these excludes generous:

```toml
[transfer]
exclude_patterns = [
  "target/",
  "target_*/",
  "target-*/",
  ".cargo-target/",
  ".cargo-target-*/",
  ".rch-target-*/",
  "node_modules/",
  ".git/objects/",
  "dist/",
  ".next/",
]
```

Reload after editing:

```bash
rch daemon reload
rch config show --sources | grep -A8 transfer
```

Use `${TMPDIR:-/tmp}` rather than hardcoded `/tmp` for any agent-injected target dir:

```bash
rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_$(basename "$PWD")" cargo check
```

(This is what `rch` itself uses since v1.0.17 commit `0f4158d`.)

---

## Triage Cheat Sheet

```bash
# 1. Quick view: pressure across the fleet
rch --json status --workers \
  | jq -r '.data.daemon.workers[]
           | "\(.id)  state=\(.pressure_state)  free_gb=\(.pressure_disk_free_gb)  io_util=\(.pressure_disk_io_util_pct)  mem=\(.pressure_memory_pressure)"'

# 2. Drill down on one worker (use the .host field from `rch workers list`)
ssh ubuntu@<host> 'df -h / /tmp && free -h && cat /proc/pressure/memory && cat /proc/pressure/io'

# 3. Inventory artifact directories
ssh ubuntu@<host> 'du -sh /tmp/rch-* /tmp/rch_target_* /data/projects/*/target* 2>/dev/null | sort -h | tail'

# 4. Verify candidate is inactive
ssh ubuntu@<host> 'sudo lsof +D <candidate-dir> 2>/dev/null | head'

# 5. Hand to sbh
ssh ubuntu@<host> 'sbh status --json'        # what's the situation?
ssh ubuntu@<host> 'sbh reclaim --auto'       # if available

# 6. If sbh insufficient — drain and investigate manually
rch workers drain <id> -y
# ... investigate ...
rch workers enable <id>
```
