# RCH Operations

## Contents

- [Baseline Runbook](#baseline-runbook)
- [Worker Fleet Lifecycle](#worker-fleet-lifecycle)
- [Fleet Deploy/Rollback](#fleet-deployrollback)
- [Path-Dependency and Multi-Repo Notes](#path-dependency-and-multi-repo-notes)
- [Transfer Stability (Rsync/Artifact Churn)](#transfer-stability-rsyncartifact-churn)
- [Queue and Cancellation Operations](#queue-and-cancellation-operations)
- [Anti-Patterns](#anti-patterns)
- [Debug Command Pack](#debug-command-pack)

## Baseline Runbook

Use this sequence for most production incidents.

### 1) Confirm current posture

```bash
rch check
rch status --workers --jobs
rch workers probe --all
rch queue
```

### 2) Validate config and daemon wiring

```bash
rch config show --sources
rch --json config get general.socket_path
rch --json daemon status
rch config doctor
```

### 3) Validate hook routing

```bash
rch hook status
rch agents status
rch hook test
```

### 4) Validate offload path directly

```bash
rch diagnose "cargo check --workspace --all-targets"
rch exec -- env CARGO_TARGET_DIR=/tmp/rch_target_<name> cargo check --workspace --all-targets
```

If step 4 succeeds, RCH infrastructure is healthy and remaining failures are project/toolchain specific.

### 5) If workers show storage pressure, inspect the right filesystem

RCH pressure warnings often come from `/` while the immediate churn lives in `/tmp`. Check both before deciding whether the host actually needs intervention:

```bash
ssh ubuntu@<host> 'df -h / /tmp'
ssh ubuntu@<host> 'free -h && cat /proc/pressure/memory && cat /proc/pressure/io'
```

Then inspect the usual large artifact surfaces:

```bash
ssh ubuntu@<host> 'du -sh /tmp/rch-* /tmp/rch_target_* 2>/dev/null | sort -h'
ssh ubuntu@<host> 'find /data/projects -maxdepth 2 -type d \( -name "target_rch_*" -o -name "target_*" -o -name "target-*" -o -name target \) -exec du -sh {} + 2>/dev/null | sort -h | tail -n 20'
```

Before removing anything, verify the candidate is inactive:

```bash
ssh ubuntu@<host> 'sudo lsof +D /tmp/rch_target_<name>'
ssh ubuntu@<host> 'sudo lsof +D /data/projects/<repo>/target_rch_<name>'
```

Only treat empty `lsof` results as a low-risk stale-artifact cleanup signal.

### 6) If `rch exec` fails at sync time, verify remote mirror ownership

When the canonical worker mirror under `/data/projects/<repo>` is owned by `root` or another account, rsync fails with `Permission denied` or `Operation not permitted`.

Check:

```bash
ssh ubuntu@<host> "stat -c '%U:%G %a %n' /data/projects/<repo>"
```

Fix:

```bash
ssh ubuntu@<host> 'sudo chown -R ubuntu:ubuntu /data/projects/<repo> && sudo chmod 775 /data/projects/<repo>'
```

After the fix, rerun:

```bash
rch diagnose --dry-run "cargo build --release"
rch exec -- cargo build --release
```

---

## Worker Fleet Lifecycle

### Discovery and setup

```bash
rch workers discover
rch workers discover --probe
rch workers discover --add --yes
rch workers setup --all
```

### Runtime management

```bash
rch workers list --speedscore
rch workers capabilities --refresh
rch workers benchmark
rch workers drain <worker> -y
rch workers enable <worker>
rch workers disable <worker> --reason "maintenance" --drain -y
```

### Toolchain/binary synchronization

```bash
rch workers sync-toolchain --all
rch workers deploy-binary --all
```

---

## Fleet Deploy/Rollback

```bash
rch fleet status
rch fleet deploy --verify
rch fleet deploy --canary 25 --canary-wait 60 --verify
rch fleet rollback --verify
rch fleet history --limit 20
```

For large fleets:

- Prefer canary first, then full rollout.
- Use `--dry-run` before disruptive operations.
- Use `--drain-first` if workers are heavily loaded.

---

## Path-Dependency and Multi-Repo Notes

RCH now supports dependency-closure planning and canonical topology handling, but path-based workspaces still require worker-accessible sibling repos.

Recommended checks:

```bash
rch diagnose --dry-run "cargo test --workspace"
rch exec -- env CARGO_TARGET_DIR=/tmp/rch_target_<name> cargo test --workspace --no-fail-fast
```

If remote path dependencies are missing:

- Ensure required sibling repos exist on worker hosts under canonical project roots.
- Re-run `rch workers setup --all` and then retry the `rch exec -- ...` command.

---

## Transfer Stability (Rsync/Artifact Churn)

If sync fails due to active artifact churn, extend transfer excludes:

```toml
[transfer]
exclude_patterns = [
  "target/",
  "target_*/",
  "target-*/",
  ".cargo-target/",
  ".cargo-target-*/",
]
```

Then reload daemon config:

```bash
rch daemon reload
rch config show --sources
```

Operational note:

- If you need a manual target dir for Rust builds, prefer `/tmp/rch_target_<name>`.
- If the working tree itself cannot sync because the remote canonical mirror is broken, either repair ownership on the worker or temporarily build from a clean directory under `/data/projects`, not `/tmp`, because RCH canonical-root normalization expects `/data/projects`.

---

## Queue and Cancellation Operations

```bash
rch queue
rch queue --watch
rch cancel <build-id>
rch cancel --all --yes
```

Use cancellation when builds are wedged or backlog pressure is starving high-priority work.

---

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Assume remote failures mean local failures | Some failures are worker/config topology issues | Validate with `rch diagnose` + `rch exec -- ...` |
| Hardcode `/tmp/rch.sock` in runbooks | Default socket may be runtime/cache path | Query via `rch --json daemon status` |
| Skip `rch check` and jump to manual SSH surgery | Loses quick signal on daemon/hook/worker health | Start with `rch check` and `rch status --workers --jobs` |
| Ignore queue pressure | Can cascade into timeouts and local fallback | Monitor `rch queue --watch` and cancel stale builds |
| Apply broad/destructive worker cleanup | Risks collateral damage | Prefer targeted fixes + `workers setup`/`fleet` commands |
| Assume `/tmp` pressure and `/` pressure are the same problem | They often are not; fixing the wrong one wastes time | Check `df -h / /tmp` and inspect the matching artifact surface |
| Delete large build dirs without checking for open files | Risks breaking active remote builds | Run `sudo lsof +D <dir>` first and only clean inactive candidates |

---

## Debug Command Pack

```bash
RCH_LOG_LEVEL=debug rch diagnose "cargo build --release"
RCH_LOG_LEVEL=debug rch check
rch doctor --json > /tmp/rch-doctor.json
rch --json workers probe --all > /tmp/rch-workers-probe.json
rch daemon logs -n 200
```
