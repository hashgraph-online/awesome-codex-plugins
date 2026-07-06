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
| 100–199 | Network | SSH, DNS, TCP — see `SSH_TUNING.md` |
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
| RCH-E001 | Config file not found | `rch config init` (creates `~/.config/rch/config.toml`). |
| RCH-E003 | Invalid TOML syntax | `rch config validate` to get the line. |
| RCH-E007 | No workers configured | `rch workers discover --add --yes && rch workers setup --all`. |
| RCH-E008 | Worker config invalid | `rch config doctor` shows which `[[workers]]` block is bad. |
| RCH-E009 | SSH key path invalid/inaccessible | Check `identity_file` exists; run `chmod 600 <key>`. |
| RCH-E013 | Cargo manifest parse failure during path-dep resolution | `cargo metadata --no-deps --format-version 1 > /dev/null` to see the parser error. |
| RCH-E014 | Path dependency declared but target dir missing | The `path = "..."` in a `Cargo.toml` points nowhere. Resolve before retry. |
| RCH-E015 | Cyclic path dependency | Break the cycle in the workspace. |
| RCH-E016 | Path dep violates canonical-root topology | Sibling repo lives outside `[path_topology] canonical_root`. Either move it under the canonical root, or set `[path_topology] canonical_root` to a parent that contains both repos. See `PATH_DEPENDENCIES.md`. |
| RCH-E017 | `cargo metadata` invocation failed | Run `cargo metadata --format-version 1` and read the error directly. |
| RCH-E019 | Closure plan computation failed | Re-run with `RCH_LOG_LEVEL=debug rch diagnose --dry-run "<command>"`. |
| RCH-E020 | Closure entered fail-open due to unverifiable data | RCH refuses to ship unsafe closure. Either fix the workspace topology or set `[deps] policy = "permissive"` (only if you accept the risk). |

### Network

| Code | Meaning | First action |
|---|---|---|
| RCH-E100 | SSH connection failed | `ssh -v ubuntu@<host>` reproduces. Check host reachability. |
| RCH-E101 | SSH auth failed | Wrong key or wrong user. `ssh-add -l` to confirm agent has the right key; `rch config get` for `identity_file`. |
| RCH-E103 | Host key verification failed | Worker rebuilt? Compare with `ssh-keygen -F <host>`; remove the old entry only if you trust the new fingerprint. |
| RCH-E104 | SSH command timed out | Network or remote slowdown. Bump `RCH_SSH_SERVER_ALIVE_INTERVAL_SECS=15` and retry. |
| RCH-E108 | Connection refused | sshd not running or wrong port. |
| RCH-E109 | TCP connect timeout | Firewall, NAT, or worker down. |

### Worker

| Code | Meaning | First action |
|---|---|---|
| RCH-E200 | No workers available for selection | See `FAIL_OPEN.md` selection-reasons table. |
| RCH-E202 | Worker failed health check | `rch workers probe <id>` reproduces; inspect `rch workers list --speedscore`. |
| RCH-E203 | Worker self-test failed | `rch self-test --worker <id>`; inspect `rch self-test history --limit 5`. |
| RCH-E204 | Worker at maximum capacity | Queueing is on by default; if seen, the wait timed out. Bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` or raise `total_slots`. |
| RCH-E205 | Worker missing required toolchain | `rch workers sync-toolchain --all`. |
| RCH-E207 | Worker circuit breaker open | Triggered by repeated failures. Inspect daemon logs; circuit auto-closes after cooldown, or `rch workers enable <id>` after fixing the underlying cause. |
| **RCH-E210** | **Worker disk usage critically high** | **Hand off to `sbh`.** See `DISK_AND_PRESSURE.md`. |
| RCH-E211 | Worker disk usage above warning threshold | `sbh` recommended. |
| RCH-E212 | Disk pressure telemetry stale | Worker not reporting; restart `rch-wkr` on the worker, or wait one telemetry tick. |
| RCH-E213 | Worker disk I/O too high | Transient — wait or `rch workers drain <id>` for maintenance. |
| RCH-E214 | Worker memory pressure too high | Same; check what else is running on the worker. |
| RCH-E215 | Disk reclaim failed | sbh ran but couldn't free enough. Manual triage. |
| RCH-E216 | Insufficient disk headroom for build reservation | Free space, or steer to a different worker via `tags`. |
| RCH-E217 | Active build protection prevented reclaim | Wait for active build, then retry reclaim. |

### Build

| Code | Meaning | First action |
|---|---|---|
| RCH-E300 | Remote compilation failed | Read the actual rustc/cargo error in stderr. |
| RCH-E303 | Build operation timed out | Raise `[compilation] build_timeout_sec` or split the build. |
| RCH-E305 | Remote working dir error | Often = mirror perms broken. See `OPERATIONS.md` chown recipe. |
| RCH-E307 | Build environment setup failed | Missing system package on worker. Detected automatically when stderr names `pkg-config` or `library .pc`. |

### Transfer

| Code | Meaning | First action |
|---|---|---|
| RCH-E400 | Rsync transfer failed | Check `rch daemon logs -n 200` for full rsync stderr. |
| RCH-E401 | Sync timed out | Big workspace + slow link. Tighten excludes or increase compression. |
| RCH-E404 | Insufficient disk on worker | `sbh` on worker. |
| RCH-E405 | Permission denied during transfer | Mirror ownership broken. Run the chown recipe from `OPERATIONS.md` §6. |
| RCH-E406 | Transfer checksum mismatch | Re-run; if persistent, suspect concurrent agent writes during sync. Use file reservations (see `MULTI_AGENT_CONTENTION.md`). |

### Internal

| Code | Meaning | First action |
|---|---|---|
| RCH-E500 | Failed to connect to daemon socket | `rch daemon start`. If it spins, see `SELF_HEALING.md` cooldown section. |
| RCH-E502 | Daemon not running | Same. |
| RCH-E506 | Hook execution failed | `rch hook test` reproduces; capture `RCH_LOG_LEVEL=debug rch hook test`. |

---

## Cross-References

- Path-dep family (RCH-E013–E024): `PATH_DEPENDENCIES.md`
- Disk-pressure family (RCH-E210–E217): `DISK_AND_PRESSURE.md` + `sbh` skill
- SSH family (RCH-E100–E109): `SSH_TUNING.md`
- Selection family (RCH-E200–E209): `FAIL_OPEN.md`
- Daemon/internal (RCH-E500–E509): `SELF_HEALING.md` + `OPERATIONS.md`

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
