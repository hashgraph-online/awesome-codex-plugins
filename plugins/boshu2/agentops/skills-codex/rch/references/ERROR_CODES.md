# RCH Error Code Catalog

## Contents

- [Live Catalog](#live-catalog)
- [Categories](#categories)
- [High-Frequency Codes (with the right reaction)](#high-frequency-codes-with-the-right-reaction)
- [Cross-References](#cross-references)
- [Schema Discovery](#schema-discovery)

RCH ships a stable error catalog of 94 codes in the `RCH-Exxx` namespace. Every user-visible failure that is *expected and explainable* carries one of these codes. They appear in:

- `[RCH] remote <worker> failed [RCH-Exxx] <summary>` (build env failures)
- `[RCH] local (dependency preflight RCH-Exxx: <remediation>)` (closure planner)
- `rch doctor --json` (`.checks[].code`)
- `rch --json` responses on errors (`.error.code`)
- Daemon log lines

Treat the code as the **stable handle**. Don't grep for the human-readable summary, which can be reworded between releases.

> **Authority:** only read-only diagnosis is autonomous. Every "First action"
> below that starts/restarts/reconfigures the daemon, adds/provisions/drains/
> enables a worker or its toolchain, edits config, or mutates a remote host
> requires explicit caller authorization first — see `FAIL_OPEN.md` §"Autonomous
> Remediation Envelope". Mutating first actions are marked **(authorize first)**.

---

## Live Catalog

The authoritative catalog is shipped with the binary. Always prefer this over what's quoted below:

```bash
rch schema export -o /tmp/rch-schemas
jq -r '.errors[] | "\(.code) | \(.message)"' /tmp/rch-schemas/error-codes.json | sort
```

Per-code remediation steps:

```bash
jq '.errors[] | select(.code=="RCH-E210") | {code, message, remediation}' /tmp/rch-schemas/error-codes.json
```

---

## Categories

| Range | Category | Lives in |
|---|---|---|
| 001–099 | Configuration | TOML, env vars, profile resolution, path topology, closure plan validation |
| 100–199 | Network | SSH, DNS, TCP — see the Network rows below and `RECOVERY_PLAYBOOKS.md` Playbook C |
| 200–299 | Worker | Selection, health, slots, disk pressure |
| 300–399 | Build | Compilation, toolchain, process triage, cancellation |
| 400–499 | Transfer | rsync, checksums, disk space, perms |
| 500–599 | Internal | Daemon, IPC, hook execution, metrics |

---

## High-Frequency Codes (with the right reaction)

These are the codes agents actually see in practice. The rest are in the schema export.

### Configuration

| Code | Meaning | First action |
|---|---|---|
| RCH-E001 | Config file not found | `rch config init` creates `~/.config/rch/config.toml` — **(authorize first)**. |
| RCH-E003 | Invalid TOML syntax | `rch config validate` to get the line (autonomous). |
| RCH-E007 | No workers configured | `rch workers discover --add --yes && rch workers setup --all` adds/provisions workers — **(authorize first)**. |
| RCH-E008 | Worker config invalid | `rch config doctor` shows which `[[workers]]` block is bad (autonomous). |
| RCH-E009 | SSH key path invalid/inaccessible | Check `identity_file` exists (autonomous); `chmod 600 <key>` mutates a local file — **(authorize first)**. |
| RCH-E013 | Cargo manifest parse failure during path-dep resolution | `cargo metadata --no-deps --format-version 1 > /dev/null` to see the parser error. |
| RCH-E014 | Path dependency declared but target dir missing | The `path = "..."` in a `Cargo.toml` points nowhere. Resolve before retry. |
| RCH-E015 | Cyclic path dependency | Break the cycle in the workspace. |
| RCH-E016 | Path dep violates canonical-root topology | Sibling repo lives outside `[path_topology] canonical_root`. Either move it under the canonical root, or set `[path_topology] canonical_root` to a parent that contains both repos. See the path-dep section of `TROUBLESHOOTING.md`. |
| RCH-E017 | `cargo metadata` invocation failed | Run `cargo metadata --format-version 1` and read the error directly. |
| RCH-E019 | Closure plan computation failed | Re-run with `RCH_LOG_LEVEL=debug rch diagnose --dry-run "<command>"`. |
| RCH-E020 | Closure entered fail-open due to unverifiable data | RCH refuses to ship unsafe closure. Fix the workspace topology, or set `[deps] policy = "permissive"` (a config edit that accepts the risk) — **(authorize first)**. |

### Network

| Code | Meaning | First action |
|---|---|---|
| RCH-E100 | SSH connection failed | `ssh -v ubuntu@<host>` reproduces. Check host reachability. |
| RCH-E101 | SSH auth failed | Wrong key or wrong user. `ssh-add -l` to confirm agent has the right key; `rch config get` for `identity_file`. |
| RCH-E103 | Host key verification failed | Worker rebuilt? Compare with `ssh-keygen -F <host>` (autonomous); removing the old `known_hosts` entry mutates local state — **(authorize first)**, and only if you trust the new fingerprint. |
| RCH-E104 | SSH command timed out | Network or remote slowdown. Bump `RCH_SSH_SERVER_ALIVE_INTERVAL_SECS=15` and retry. |
| RCH-E108 | Connection refused | sshd not running or wrong port. |
| RCH-E109 | TCP connect timeout | Firewall, NAT, or worker down. |

### Worker

| Code | Meaning | First action |
|---|---|---|
| RCH-E200 | No workers available for selection | See `FAIL_OPEN.md` selection-reasons table. |
| RCH-E202 | Worker failed health check | `rch workers probe <id>` reproduces; inspect `rch workers list --speedscore`. |
| RCH-E203 | Worker self-test failed | `rch self-test --worker <id>`; inspect `rch self-test history --limit 5`. |
| RCH-E204 | Worker at maximum capacity | Queueing is on by default; if seen, the wait timed out. Bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` (autonomous); raising `total_slots` edits config — **(authorize first)**. |
| RCH-E205 | Worker missing required toolchain | `rch workers sync-toolchain --all` mutates the worker — **(authorize first)**. |
| RCH-E207 | Worker circuit breaker open | Triggered by repeated failures. Inspect daemon logs (autonomous); circuit auto-closes after cooldown, or force `rch workers enable <id>` after fixing the cause — **(authorize first)**. |
| **RCH-E210** | **Worker disk usage critically high** | **Hand off to the `sbh` skill.** See the disk rows in this table and `RECOVERY_PLAYBOOKS.md` Playbook G. |
| RCH-E211 | Worker disk usage above warning threshold | `sbh` recommended. |
| RCH-E212 | Disk pressure telemetry stale | Worker not reporting; wait one telemetry tick (autonomous). Restarting `rch-wkr` on the worker is remote mutation — **(authorize first)**. |
| RCH-E213 | Worker disk I/O too high | Transient — wait (autonomous), or `rch workers drain <id>` for maintenance — **(authorize first)**. |
| RCH-E214 | Worker memory pressure too high | Same; check what else is running on the worker. |
| RCH-E215 | Disk reclaim failed | sbh ran but couldn't free enough. Manual triage. |
| RCH-E216 | Insufficient disk headroom for build reservation | Free space, or steer to a different worker via `tags`. |
| RCH-E217 | Active build protection prevented reclaim | Wait for active build, then retry reclaim. |

### Build

| Code | Meaning | First action |
|---|---|---|
| RCH-E300 | Remote compilation failed | Read the actual rustc/cargo error in stderr. |
| RCH-E303 | Build operation timed out | Splitting the build is autonomous; raising `[compilation] build_timeout_sec` edits config — **(authorize first)**. |
| RCH-E305 | Remote working dir error | Often = mirror perms broken. See `RECOVERY_PLAYBOOKS.md` Playbook F — the chown fix is a remote `sudo` command, authorize first. |
| RCH-E307 | Build environment setup failed | Missing system package on worker. Detected automatically when stderr names `pkg-config` or `library .pc`. |

### Transfer

| Code | Meaning | First action |
|---|---|---|
| RCH-E400 | Rsync transfer failed | Check `rch daemon logs -n 200` for full rsync stderr. |
| RCH-E401 | Sync timed out | Big workspace + slow link. Tighten excludes or increase compression. |
| RCH-E404 | Insufficient disk on worker | `sbh` on worker. |
| RCH-E405 | Permission denied during transfer | Mirror ownership broken. See `RECOVERY_PLAYBOOKS.md` Playbook F — the chown fix is a remote `sudo` command, authorize first. |
| RCH-E406 | Transfer checksum mismatch | Re-run; if persistent, suspect concurrent agent writes during sync. Coordinate writers with file reservations via the `agent-mail` skill. |

### Internal

| Code | Meaning | First action |
|---|---|---|
| RCH-E500 | Failed to connect to daemon socket | Wait out the auto-start cooldown and retry; manually starting the daemon needs caller authorization. If it spins, see `RECOVERY_PLAYBOOKS.md` Playbook B (cooldown/stale-socket). |
| RCH-E502 | Daemon not running | Same. |
| RCH-E506 | Hook execution failed | `rch hook test` reproduces; capture `RCH_LOG_LEVEL=debug rch hook test`. |

---

## Cross-References

- Path-dep family (RCH-E013–E024): the path-dep section of `TROUBLESHOOTING.md`
- Disk-pressure family (RCH-E210–E217): the disk rows above + the `sbh` skill
- SSH family (RCH-E100–E109): `RECOVERY_PLAYBOOKS.md` Playbook C
- Selection family (RCH-E200–E209): `FAIL_OPEN.md`
- Daemon/internal (RCH-E500–E509): `RECOVERY_PLAYBOOKS.md` Playbook B + `TROUBLESHOOTING.md`

---

## Schema Discovery

For agents that need to consume the catalog programmatically (e.g., to build a remediation table at runtime):

```bash
rch schema list                  # human-readable
rch schema export -o ./schemas   # writes api-response, api-error, error-codes
rch --schema config lint         # JSON Schema for one command's output
rch --capabilities               # full capability description
```

Every command also accepts `--help-json` to dump its argument tree as JSON.
