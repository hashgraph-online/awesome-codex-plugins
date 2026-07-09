# Worker Management

## Contents

- [Worker Lifecycle](#worker-lifecycle)
- [Add a Worker Manually](#add-a-worker-manually)
- [Drain / Disable / Enable](#drain--disable--enable)
- [Toolchain and Binary Management](#toolchain-and-binary-management)
- [Fleet-Level Rollout Commands](#fleet-level-rollout-commands)
- [Worker Selection Notes](#worker-selection-notes)
- [SSH Verification Shortcuts](#ssh-verification-shortcuts)

## Worker Lifecycle

### 1) Discover and add workers

```bash
rch workers discover
rch workers discover --probe
rch workers discover --add --yes
```

### 2) Complete setup

```bash
rch workers setup --all
```

This performs the standard bootstrap path (binary/toolchain setup, validation) for configured workers.

### 3) Validate runtime health

```bash
rch workers list --speedscore
rch workers probe --all
rch workers capabilities --refresh
rch check
```

---

## Add a Worker Manually

Edit `~/.config/rch/workers.toml`:

```toml
[[workers]]
id = "new-worker"
host = "203.0.113.20"
user = "ubuntu"
identity_file = "~/.ssh/new_worker_ed25519"
total_slots = 16
priority = 90
tags = ["rust", "bun"]
```

Then validate and setup:

```bash
rch config validate
rch workers probe new-worker
rch workers setup new-worker
```

---

## Drain / Disable / Enable

Use these for maintenance windows and incident isolation.

```bash
rch workers drain <worker> -y
rch workers disable <worker> --reason "maintenance" --drain -y
rch workers enable <worker>
```

State model:

- `HEALTHY`: accepting jobs
- `DRAINING`: finishing active jobs, no new jobs
- `DRAINED`: idle and not accepting jobs
- `DISABLED`: explicitly offline from scheduler

---

## Toolchain and Binary Management

```bash
rch workers sync-toolchain --all
rch workers deploy-binary --all
```

Use `--dry-run` before broad changes:

```bash
rch workers sync-toolchain --all --dry-run
rch workers deploy-binary --all --dry-run
```

---

## Fleet-Level Rollout Commands

```bash
rch fleet status
rch fleet deploy --verify
rch fleet deploy --canary 25 --canary-wait 60 --verify
rch fleet rollback --verify
rch fleet history --limit 20
```

---

## Worker Selection Notes

Selection favors availability and execution quality signals (slot capacity, health, and policy strategy).

Operational guidance:

- Keep `total_slots` realistic for CPU and memory limits.
- Prefer explicit `priority` shaping for known fast/reliable workers.
- Drain before disruptive operations.
- Keep worker toolchains synchronized to avoid fallback churn.

---

## SSH Verification Shortcuts

Single worker:

```bash
rch workers probe <worker>
```

All workers with machine-readable output:

```bash
rch --json workers probe --all
```

If probes fail:

1. Verify `identity_file` exists and permissions are restrictive.
2. Verify worker host reachability and SSH service.
3. Re-run `rch workers setup <worker>` after connectivity is restored.
