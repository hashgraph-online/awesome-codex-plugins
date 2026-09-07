# Detecting and Responding to RCH Fail-Open

## Contents

- [Golden Rule](#golden-rule)
- [The Fail-Open Surface](#the-fail-open-surface)
- [Fail-Open Reasons (and What To Do)](#fail-open-reasons-and-what-to-do)
- [Detection Snippets](#detection-snippets)
- [Force the Issue](#force-the-issue)
- [Autonomous Remediation Envelope (and Where It Stops)](#autonomous-remediation-envelope-and-where-it-stops)

RCH's most expensive failure mode for agents is **silent fall-back to local execution**. The build "succeeded" — but it ran on the local machine, slowly, while the worker fleet sat idle. If you don't notice, you bake hours of extra latency into every iteration.

This file is the canonical guide for: (1) how to *see* a fail-open, (2) what each fail-open reason means, and (3) how to remediate it within the autonomous envelope — and where that envelope stops and explicit caller authorization begins.

---

## Golden Rule

**Never say "build done" until you've checked stderr for `[RCH] local (...)`.**

If you see that string, the build did not run remotely. It might still be a correct build, but RCH chose to fall back, and the parenthetical reason is a contract telling you exactly why.

---

## The Fail-Open Surface

`rch exec` and the PreToolUse hook print exactly one summary line on stderr at the end of every routed compilation. The visibility is controlled by `[output] visibility = "summary"|"verbose"|"none"` (env: `RCH_VISIBILITY`).

There are five summary forms:

| Pattern | Meaning |
|---------|---------|
| `[RCH] remote <worker> (<ms>)` | Successful remote build. Worker name + wall-clock time. |
| `[RCH] remote <worker> failed (exit <N>)` | Build ran remotely and the build itself failed. Treat as a normal compiler error. |
| `[RCH] remote <worker> failed [RCH-Exxx] <summary>` | Build environment failure on the worker (missing system package, etc.). See `ERROR_CODES.md`. |
| `[RCH] local (<reason>)` | **Fail-open.** Compilation ran locally instead of remotely. Read the reason. |
| *(no summary)* | Visibility is `none` or RCH never engaged. Re-run with `RCH_VISIBILITY=summary` to confirm. |

To force a summary banner without changing config:

```bash
RCH_VISIBILITY=verbose cargo check
```

---

## Fail-Open Reasons (and What To Do)

Every reason in the parens comes from one of two sources:

1. **Hook decision points** in `rch/src/hook.rs::process_hook` and `run_exec` — short, hand-written reason strings
2. **Daemon selection reasons** (`SelectionReason` enum in `rch-common/src/types.rs`) — stable machine reasons from worker selection

### Hook-decision fail-opens

| Reason text | Triggered when | Self-fix |
|---|---|---|
| `daemon unavailable` | Daemon socket can't be reached (and auto-start failed or is disabled) | Wait out the auto-start cooldown and retry (autonomous). If still failing, confirm with `rch --json daemon status` and check `~/.cache/rch/rch.sock`; manually starting the daemon needs caller authorization. See `RECOVERY_PLAYBOOKS.md` Playbook B. |
| `force_local` | `[general] force_local = true` is set | This is intentional. `rch config get general.force_local --sources` shows where it came from (autonomous). Reverting with `rch config set general.force_local false` edits config — **(authorize first)**. |
| `invalid config: force_local+force_remote` | Both flags set simultaneously | `rch config edit` to unset one, then `rch daemon reload` — both mutate config/daemon, **(authorize first)**. |
| `confidence below threshold` | Classifier flagged the command but only weakly (e.g., wrapped in shell pipelines). Threshold is `[compilation] confidence_threshold` (default 0.85). | Run `rch diagnose "<the command>"` to see classifier confidence (autonomous). Lowering the threshold or setting `[general] force_remote = true` in `.rch/config.toml` are config mutations — **(authorize first)**. |
| `command '<base>' not in allowlist` | `[execution] allowlist` excludes this command base | `rch --json config get execution.allowlist` to inspect (autonomous). Adding the command base to `.rch/config.toml` is a config mutation — **(authorize first)**. |
| `dependency preflight <RCH-Exxx>: <remediation>` | The closure planner refused to ship the workspace (cycle, missing manifest, off-canonical-root path dep). See the RCH-E013–E020 rows in `ERROR_CODES.md` and the path-dep section of `TROUBLESHOOTING.md`. | The remediation message is actionable; follow it. Then re-run `rch diagnose --dry-run "<command>"`. |
| `<TransferSkipped reason>` | Transfer pipeline opted out (e.g., empty workspace, all paths excluded). | Run `RCH_LOG_LEVEL=debug rch exec -- <command>` and look for `Transfer skipped:` log lines. |
| `remote execution failed` | Generic catch-all for transfer/exec errors | Re-run with `RCH_LOG_LEVEL=debug` to surface the real error, and check `rch daemon logs -n 200` for the daemon side. |
| `toolchain missing on <worker>` | Remote `rustup`/`cargo` not present, or no default toolchain | Diagnose the gap (autonomous). `rch workers sync-toolchain --all` (or one worker) mutates the worker — get caller authorization first; then `rch workers capabilities --refresh`. |

### Daemon-decision fail-opens (selection reasons)

These come from the daemon's `SelectionReason` enum. The `[RCH] local (...)` summary uses the **human Display** form (verbatim from `Display for SelectionReason` in `rch-common/src/types.rs`). Machine-readable JSON output (`rch --json`) uses the **snake_case tag** instead. Match either when you grep — the human form is what appears on stderr.

| Snake_case tag (JSON) | Human form in `local (...)` summary | Self-fix |
|---|---|---|
| `no_workers_configured` | `no workers configured` | `rch workers discover --add --yes && rch workers setup --all` adds and provisions workers — a fleet mutation; get caller authorization first. |
| `all_workers_unreachable` | `all workers unreachable` | `rch workers probe --all` and read the SSH errors (autonomous). Any fix beyond reading — repairing a local key's permissions included — is a host mutation → **(authorize first)**; changing anything on a worker is remote mutation → **(authorize first)**. See `RECOVERY_PLAYBOOKS.md` Playbook C and the Network rows of `ERROR_CODES.md`. |
| `all_circuits_open` | `all worker circuits open` | A worker hit repeated failures and tripped its circuit. Inspect with `rch --json status --workers \| jq '.data.daemon.workers[] \| {id, circuit_state, last_error, recovery_in_secs}'` and `rch daemon logs -n 200` (autonomous). Circuits auto-close after the cooldown; forcing `rch workers enable <id>` mutates worker state — **(authorize first)**. |
| `all_workers_busy` | `all workers at capacity` | Queueing is **on by default** (`RCH_QUEUE_WHEN_BUSY=1`); seeing this means the wait timed out. Bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` for the next invocation (autonomous). Raising `total_slots` edits worker config — **(authorize first)**. Check `rch queue --watch` to see backlog. |
| `all_workers_failed_preflight` | `all workers failed preflight checks` | Path-topology check, repo presence, or toolchain probe failed on every candidate. Re-run with `rch diagnose --dry-run "<command>"` to see the preflight pipeline; hits `RCH-E013..024`, `RCH-E205`, `RCH-E305`. |
| `all_workers_failed_convergence` | `all workers failed repo convergence checks` | The repo updater contract couldn't bring required repos to a target state on any worker. Check that the sibling repos exist on workers under the canonical root. See the RCH-E013–E020 rows in `ERROR_CODES.md` and the path-dep section of `TROUBLESHOOTING.md`. |
| `no_matching_workers` | `no matching workers found` | The project requires tags (e.g., `tags = ["bun"]`) and no worker carries them. `rch workers list --json` to inspect tags (autonomous); adding the tag edits worker config — **(authorize first)**. |
| `no_workers_with_runtime` (value = runtime name) | `no workers with bun installed` (or `node`, `rust`, …) | Installing the runtime on a worker and `rch workers capabilities --refresh` both mutate worker state — **(authorize first)**. |
| `selection_error` (value = error text) | `selection error: <msg>` | An internal error during selection. Check `rch daemon logs -n 200`. Likely a code-side bug; capture `rch doctor --json` and `rch --json daemon status` for escalation. |

Two more variants — `affinity_pinned` and `affinity_fallback` — are *success* paths (a worker was assigned via affinity), not fail-opens, so they never appear in `[RCH] local (...)` output.

### "Build" succeeded but nothing went remote

If the command exited 0, the agent often calls the work done. **Check the summary line first.** A common pathology:

```
   Compiling foo v0.1.0
    Finished `dev` profile in 38.41s
[RCH] local (all workers at capacity)
```

That's a 38-second build that should have been 2 seconds remote. Queueing is on by default; if you still see this, bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` so the next iteration waits longer for a slot rather than burning local CPU.

---

## Detection Snippets

Single-shot check after a build:

```bash
# Show the last RCH summary line from this shell's stderr capture
grep -E '^\[RCH\] (remote|local)' /tmp/rch_last_run.stderr | tail -1
```

Wrapper that runs a build and asserts remote:

```bash
out=$(RCH_VISIBILITY=summary cargo check 2>&1)
if grep -qE '^\[RCH\] local' <<<"$out"; then
  echo "RCH FELL BACK TO LOCAL:" >&2
  grep -E '^\[RCH\] local' <<<"$out" >&2
  exit 99
fi
echo "$out" | tail -3
```

JSON-mode check (for scripted agents):

```bash
rch --json check | jq -r '.data.status'   # ready | degraded | unhealthy
```

---

## Force the Issue

When you absolutely need to know whether remote works at all (for example, before deciding to file an issue), bypass the hook entirely:

```bash
rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_$(basename "$PWD")" cargo check --workspace --all-targets
```

If that prints `[RCH] remote <worker> (...)`, the offload path is healthy and the failures are coming from the hook classifier (or some shell wrapper around your command). If it also prints `[RCH] local (...)`, follow the reason above.

---

## Autonomous Remediation Envelope (and Where It Stops)

The skill resolves diagnosis autonomously — but the SKILL.md authority boundary
governs, and this file does not widen it. Two tiers:

**Autonomous (no need to ask) — the blast-radius ceiling is read-only.** Only
diagnosis and inspection that mutates no host, worker, daemon, config, or
filesystem state:

- reading summary lines, stderr, and `rch daemon logs`;
- status/inspection commands: `rch check`, `rch status`, `rch --json daemon
  status`, `rch diagnose`/`--dry-run`, `rch --json workers probe|list`, `rch
  config get|show|validate|doctor|diff`, `rch hook status|test`, `rch fleet
  status|verify`, `rch queue`, `rch self-test`;
- tuning env vars for the *next* invocation (`RCH_VISIBILITY`, `RCH_LOG_LEVEL`,
  `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120`, `RCH_SSH_SERVER_ALIVE_INTERVAL_SECS`);
- re-running the original command *only when that command is itself read-only*,
  including waiting out an auto-start cooldown (the built-in
  `try_auto_start_daemon` handles stale sockets — do not `rm` them). A
  mutating original command re-runs only under the authorization that covered
  it in the first place.

**Requires explicit caller authorization first — even when a reason maps
straight to one of these commands.** Every host, worker, daemon, config, or
filesystem mutation crosses the ceiling. It does not matter that a table cell
below lists the command — a listed command is not a pre-authorized one:

- **local host mutation** — `rch hook install|uninstall` (writes
  `~/.claude/settings.json`), `chmod` on a local key file, `rch config
  set|edit|init`, and any edit to `~/.config/rch/*.toml`;
- **remote host mutation** — any `ssh … sudo …`, remote `chown`/`chmod`/`rm`,
  remote installs, restarting `sshd` or `rch-wkr` on a worker, changing a
  worker's `authorized_keys` or its host-key entry;
- **worker / fleet operations** — `rch workers
  sync-toolchain|setup|deploy-binary|discover --add|drain|disable|enable|capabilities --refresh`,
  `rch fleet deploy|rollback`;
- **daemon lifecycle** — `rch daemon start|restart|reload|stop`;
- **destructive cleanup** — removing sockets, cooldown/lock files, caches, or
  moving the telemetry DB aside.

For each reason, run the autonomous diagnosis, then, if the fix is above the
ceiling, capture the evidence and get authorization before running it:

- **"daemon unavailable"** → confirm with `rch --json daemon status`; wait out
  the auto-start cooldown and retry (autonomous). Manually starting/restarting
  the daemon, or removing the cooldown file, needs authorization.
- **"all workers unreachable"** → `rch workers probe --all` and read the SSH
  errors (autonomous). Every fix mutates state and needs authorization first:
  `chmod` on a local key, and anything **on** a worker (host-key entry,
  `authorized_keys`, restarting `sshd`).
- **"all workers at capacity"** → queueing is on by default; bump
  `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` for the next run (autonomous).
  Raising `total_slots` edits worker config → authorization.
- **"toolchain missing on X"** → diagnose the gap (autonomous); running `rch
  workers sync-toolchain` mutates the worker → get authorization first.
- **Permission denied on `/data/projects/<repo>` over rsync** → the fix is a
  remote privileged command (`ssh … 'sudo chown -R …'`). Report it to the
  caller with the failing `stat` and get explicit authorization before running
  it — remote `sudo` is never autonomous.

When a fix is above the ceiling or you are in genuine doubt, surface the packet —
`rch doctor --json`, `rch --json daemon status`, `rch --json workers probe
--all`, the failing command's stderr, and the exact command you propose — so the
caller can authorize (or decline) in one round trip.
