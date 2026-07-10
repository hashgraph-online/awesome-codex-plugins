---
name: sbh
description: >-
  Disk-pressure defense for AI coding workloads. Use when: disk full, low
  space, ballast, cleanup, scan artifacts, emergency, sbh daemon, sbh status.
---

# SBH — Storage Ballast Helper

Prevents disk-full disasters via ballast files, artifact scanning, and predictive pressure monitoring. Three-pronged: ballast (instant space), scanner (stale artifacts), special locations (/tmp, /dev/shm, swap).

## Quick Check

```bash
sbh status                     # Pressure level + free space
sbh status --json | jq '.pressure'  # Machine-parseable
sbh check --need 5G            # "Do I have 5 GB free?"
sbh check --predict 30         # "Will I run out in 30 min?"
```

Exit codes: 0 = healthy, 1 = pressure, 2 = error.

---

## Daemon

```bash
sbh daemon                          # Foreground (debugging)
systemctl --user start sbh          # Systemd user scope
sbh install --systemd --user --auto # Install + start (Linux)
sbh install --launchd --auto        # Install + start (macOS)
sbh install --wizard                # Guided interactive setup
```

**Signals:** `SIGHUP` = reload config, `SIGUSR1` = force scan now, `SIGTERM` = graceful stop.

---

## Ballast

Pre-allocated sacrificial files — released in milliseconds, no scanning needed.

```bash
sbh ballast status             # Per-volume inventory
sbh ballast provision          # Create/rebuild pool
sbh ballast release 3          # Free 3 files NOW
sbh ballast replenish          # Rebuild after pressure passes
```

Defaults: 10 x 1 GiB = 10 GiB. Ensure ballast dir is on **same mount** as pressure source.

---

## Scanning & Cleanup

```bash
sbh scan /data/projects --top 20       # Rank artifacts by score
sbh clean /data/projects --dry-run     # Preview what would go
sbh clean --target-free 50G --yes      # Delete until 50 GB free
```

Scoring: Location (.25) + Name (.25) + Age (.20) + Size (.15) + Structure (.15) = 1.0.

---

## Protection

```bash
sbh protect /path              # .sbh-protect marker (subtree)
sbh unprotect /path            # Remove marker
```

Config globs: `scanner.protected_paths`. Hard vetoes (always enforced): `.git/` dirs, open files, age < 10 min, non-writable parents.

---

## Emergency Recovery

Zero-write mode for near-100% full disks. No config file needed.

```bash
sbh emergency /data --yes              # Aggressive cleanup NOW
sbh emergency --target-free 10G        # Stop at 10 GB recovered
```

---

## Observability

```bash
sbh dashboard                  # TUI: 7 screens (1-7 to jump)
sbh stats --window 24h         # Activity over last 24 hours
sbh blame --top 10             # Top 10 pressure sources
sbh explain --id <ID>          # Why was this decision made?
```

---

## Configuration

Config: `~/.config/sbh/config.toml` | Env: `SBH_` prefix | Fallback: `/etc/sbh/config.toml`

```bash
sbh config show                # Current values
sbh config validate            # Check constraints
sbh config set KEY VALUE       # Change a value
sbh tune --apply --yes         # Auto-tune for this system
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Ballast on `/tmp` | `paths.ballast_dir` on same mount as pressure source |
| Daemon as root, CLI as user | `--user` scope — avoids state file permission mismatch |
| Skip pre-build check | `sbh check --need 10G` in CI/hook |
| Delete `.sbh-protect` by hand | `sbh unprotect /path` |
| Wait for Red to act | Act at Yellow — agent swarms escalate fast |
| `min_file_age_minutes = 0` | Keep >= 5 to protect in-flight writes |

---

## Docs

Full documentation: https://github.com/Dicklesworthstone/storage_ballast_helper
