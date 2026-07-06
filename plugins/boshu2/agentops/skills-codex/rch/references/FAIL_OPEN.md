# Detecting and Responding to RCH Fail-Open

## Contents

- [Golden Rule](#golden-rule)
- [The Fail-Open Surface](#the-fail-open-surface)
- [Fail-Open Reasons (and What To Do)](#fail-open-reasons-and-what-to-do)
- [Detection Snippets](#detection-snippets)
- [Force the Issue](#force-the-issue)
- ["Don't Ask the Human" Rules](#dont-ask-the-human-rules)

RCH's most expensive failure mode for agents is **silent fall-back to local execution**. The build "succeeded" — but it ran on the local machine, slowly, while the worker fleet sat idle. If you don't notice, you bake hours of extra latency into every iteration.

This file is the canonical guide for: (1) how to *see* a fail-open, (2) what each fail-open reason means, and (3) what to do about it before asking the human.

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
| `daemon unavailable` | Daemon socket can't be reached (and auto-start failed or is disabled) | `rch daemon start && rch --json daemon status`. If still failing, check `~/.cache/rch/rch.sock` and look for stale auto-start cooldown (see `SELF_HEALING.md`). |
| `force_local` | `[general] force_local = true` is set | This is intentional. If you didn't expect it: `rch config get general.force_local --sources` shows where it came from. `rch config set general.force_local false` to revert. |
| `invalid config: force_local+force_remote` | Both flags set simultaneously | `rch config edit` and unset one. Then `rch daemon reload`. |
| `confidence below threshold` | Classifier flagged the command but only weakly (e.g., wrapped in shell pipelines). Threshold is `[compilation] confidence_threshold` (default 0.85). | If the command really should offload, lower the threshold or set `[general] force_remote = true` in `.rch/config.toml`. Better: run `rch diagnose "<the command>"` to see classifier confidence. |
| `command '<base>' not in allowlist` | `[execution] allowlist` excludes this command base | `rch --json config get execution.allowlist` to inspect. Add the command base if you control the project's `.rch/config.toml`. |
| `dependency preflight <RCH-Exxx>: <remediation>` | The closure planner refused to ship the workspace (cycle, missing manifest, off-canonical-root path dep). See `PATH_DEPENDENCIES.md`. | The remediation message is actionable; follow it. Then re-run `rch diagnose --dry-run "<command>"`. |
| `<TransferSkipped reason>` | Transfer pipeline opted out (e.g., empty workspace, all paths excluded). | Run `RCH_LOG_LEVEL=debug rch exec -- <command>` and look for `Transfer skipped:` log lines. |
| `remote execution failed` | Generic catch-all for transfer/exec errors | Re-run with `RCH_LOG_LEVEL=debug` to surface the real error, and check `rch daemon logs -n 200` for the daemon side. |
| `toolchain missing on <worker>` | Remote `rustup`/`cargo` not present, or no default toolchain | `rch workers sync-toolchain --all` (or just for that worker). Then `rch workers capabilities --refresh`. |

### Daemon-decision fail-opens (selection reasons)

These come from the daemon's `SelectionReason` enum. The `[RCH] local (...)` summary uses the **human Display** form (verbatim from `Display for SelectionReason` in `rch-common/src/types.rs`). Machine-readable JSON output (`rch --json`) uses the **snake_case tag** instead. Match either when you grep — the human form is what appears on stderr.

| Snake_case tag (JSON) | Human form in `local (...)` summary | Self-fix |
|---|---|---|
| `no_workers_configured` | `no workers configured` | `rch workers discover --add --yes && rch workers setup --all`. |
| `all_workers_unreachable` | `all workers unreachable` | `rch workers probe --all`; fix SSH (key path, host, port). See `SSH_TUNING.md`. |
| `all_circuits_open` | `all worker circuits open` | A worker hit repeated failures and tripped its circuit. Inspect with `rch --json status --workers \| jq '.data.daemon.workers[] \| {id, circuit_state, last_error, recovery_in_secs}'` and `rch daemon logs -n 200`. Use `rch workers enable <id>` after fixing the underlying cause; circuits also auto-close after the cooldown. |
| `all_workers_busy` | `all workers at capacity` | Queueing is **on by default** (`RCH_QUEUE_WHEN_BUSY=1`); seeing this means the wait timed out. Bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` for the next invocation, or raise `total_slots`. Check `rch queue --watch` to see backlog. |
| `all_workers_failed_preflight` | `all workers failed preflight checks` | Path-topology check, repo presence, or toolchain probe failed on every candidate. Re-run with `rch diagnose --dry-run "<command>"` to see the preflight pipeline; hits `RCH-E013..024`, `RCH-E205`, `RCH-E305`. |
| `all_workers_failed_convergence` | `all workers failed repo convergence checks` | The repo updater contract couldn't bring required repos to a target state on any worker. Check that the sibling repos exist on workers under the canonical root. See `PATH_DEPENDENCIES.md`. |
| `no_matching_workers` | `no matching workers found` | The project requires tags (e.g., `tags = ["bun"]`) and no worker carries them. `rch workers list --json` to inspect tags; add the tag to a capable worker. |
| `no_workers_with_runtime` (value = runtime name) | `no workers with bun installed` (or `node`, `rust`, …) | Install the runtime on a worker, then `rch workers capabilities --refresh`. |
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

## "Don't Ask the Human" Rules

The skill exists so agents resolve these things autonomously. Concrete cases where the answer is **always do, never ask**:

- **"daemon unavailable"** → `rch daemon start && rch --json daemon status`. If the auto-start cooldown is active, wait or remove `${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.cooldown` and try again.
- **"all workers unreachable"** → `rch workers probe --all` and inspect SSH errors. Don't ask "should I fix this?" — fix what's fixable (key permissions, missing host entries, dead daemon).
- **"all workers at capacity"** → queueing is already on by default; bump `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120` to wait longer, or raise `total_slots` if the fleet is genuinely undersized.
- **"toolchain missing on X"** → `rch workers sync-toolchain --all`. The skill is designed for you to do this without confirmation.
- **Stale unix socket detected** (auto-start log message) → already handled by `try_auto_start_daemon`. Don't manually `rm` the socket; just retry.
- **Permission denied on `/data/projects/<repo>` over rsync** → if the repo on the worker is owned by `root`: `ssh ubuntu@<host> 'sudo chown -R ubuntu:ubuntu /data/projects/<repo> && sudo chmod 775 /data/projects/<repo>'`. This is a known recovery; don't escalate.

When in genuine doubt — escalate after collecting `rch doctor --json`, `rch --json daemon status`, `rch --json workers probe --all`, and the failing command's stderr. That packet lets the human resolve in one round trip.
