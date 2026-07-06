# Self-Healing: Daemon Autostart, Cooldown, Hook Bootstrap

## Contents

- [What's in `[self_healing]`](#whats-in-self_healing)
- [What `try_auto_start_daemon` Actually Does](#what-try_auto_start_daemon-actually-does)
- [Symptoms and What They Mean](#symptoms-and-what-they-mean)
- [Hook Re-installation (`daemon_installs_hooks`)](#hook-re-installation-daemon_installs_hooks)
- [Self-Test as Continuous Verification](#self-test-as-continuous-verification)
- [Auto-Start Knobs You Can Tune](#auto-start-knobs-you-can-tune)
- [Agent Operating Rules](#agent-operating-rules)

RCH ships a self-healing layer so the hook can recover from a crashed daemon without operator intervention. Understanding how it works lets agents avoid step-on-step interactions and lets you diagnose when self-healing is masking a real bug.

---

## What's in `[self_healing]`

```toml
[self_healing]
hook_starts_daemon = true       # Hook will spawn rchd if socket is unreachable
daemon_installs_hooks = true    # Daemon will reinstall missing PreToolUse hooks
auto_start_timeout_secs = 3     # How long to wait for the socket after spawn (default: 3)
auto_start_cooldown_secs = 30   # Minimum gap between consecutive autostart attempts (default: 30)
```

(Field names match `rch_common::SelfHealingConfig`. Defaults verified against
`default_autostart_cooldown_secs()` and `default_autostart_timeout_secs()` in
`rch-common/src/types.rs` at time of writing.)

If `hook_starts_daemon = false`, you're back to manual: every `rch exec` that finds the socket missing falls open with `[RCH] local (daemon unavailable)`.

---

## What `try_auto_start_daemon` Actually Does

Code path: `rch/src/hook.rs::try_auto_start_daemon`. Step-by-step:

1. **Bail if disabled.** `Err(AutoStartError::Disabled)` if `hook_starts_daemon = false`.
2. **Probe an existing socket.** If the socket file exists, do a 300ms `connect + ping`:
   - Healthy: return `Ok(())`. We're done.
   - Stale: remove the socket and continue.
3. **Check cooldown.** Read `${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.cooldown`. If the elapsed seconds since the last attempt is less than `auto_start_cooldown_secs`, bail with `Err(AutoStartError::CooldownActive(elapsed, required))`.
4. **Acquire cross-process lock.** Open-with-create-new on `${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.lock`. If another process holds it, bail with `Err(AutoStartError::LockHeld)`.
5. **Write cooldown stamp.** Persist current epoch seconds to the cooldown file.
6. **Find the binary.** `which_rchd_path()` checks the directory of the current `rch` executable first, then PATH. Fail with `BinaryNotFound` if absent.
7. **Spawn.** `nohup <rchd>` with stdio nulled. Hand off to background.
8. **Wait for socket.** Up to `auto_start_timeout_secs`, polling for the socket to come up. On timeout: `Err(AutoStartError::Timeout)`.
9. **Drop the lock** (RAII via `AutoStartLock`). Cooldown stamp persists.

So, in steady state, only **one** agent at a time gets to spawn the daemon, and after either success or failure no agent retries for `auto_start_cooldown_secs`.

---

## Symptoms and What They Mean

### Many agents see `[RCH] local (daemon unavailable)` simultaneously

Either:
- The daemon crashed and one agent is currently in the cooldown/lock window, holding off the others — wait `auto_start_cooldown_secs` and try again
- `rchd` binary is missing or not in PATH — `which rchd && rchd --version`

Diagnose:

```bash
ls -la "${XDG_RUNTIME_DIR:-/tmp}/rch/"
cat "${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.cooldown" 2>/dev/null   # epoch seconds
date +%s                                                                 # compare
which rchd
```

### Repeated cooldown-active errors but daemon never starts

`rchd` is failing to come up at all (broken binary, port in use, OOM at startup, missing $HOME for state, etc.). The cooldown is hiding the real spawn failure. Bypass the autostart path:

```bash
rch daemon start                 # foreground spawn — surfaces the real error
# or
rchd --foreground                # depending on rchd flags
journalctl --user -u rch.daemon -n 100 2>/dev/null    # if running as systemd user unit
rch daemon logs -n 200
```

### `LockHeld` perpetually

A previous `rch` invocation crashed while holding the lock. The lock file is `${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.lock`. If no process exists for it (`fuser` returns nothing), it's safe to remove. Prefer asking the user before doing so — it's a cleanup operation, not strictly an "rch" command. If authorized:

```bash
fuser "${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.lock" 2>/dev/null && echo "still held" || rm "${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.lock"
```

### Socket exists but `rch check` says not ready

A previous `rchd` died without cleanup. `try_auto_start_daemon` will detect a stale socket on next run and remove it. To force the issue:

```bash
rch daemon restart -y
rch --json daemon status | jq '.'
```

---

## Hook Re-installation (`daemon_installs_hooks`)

When `daemon_installs_hooks = true`, the daemon notices on startup whether the PreToolUse hook is registered for any detected agent (Claude Code, Codex, Gemini, etc.). If it's missing for the agent that owns the user session, it will reinstall.

This is mostly invisible. To inspect what the daemon thinks:

```bash
rch agents list --json
rch agents status
rch hook status --json
```

If you've explicitly uninstalled the hook (`rch hook uninstall`), set `daemon_installs_hooks = false` to avoid re-install on next daemon start.

---

## Self-Test as Continuous Verification

`rch self-test` runs the full classifier → daemon → worker → transfer → exec → result loop end-to-end. Schedule it (or just run it before believing the system is healthy):

```bash
rch self-test --all                               # one round on every worker
rch self-test --worker css                        # single worker
rch self-test --worker css --debug --timeout 600  # debug build, longer timeout
rch self-test --scheduled                         # use scheduled config
rch self-test status                              # last run + schedule
rch self-test history --limit 10
```

If `rch self-test --all` ever **hangs indefinitely**, that's the symptom of a known prior bug (`bd-w5r9`) — kill it and capture `rch doctor --json`. Recent versions are timeout-bounded; if you reproduce on v1.0.18+, escalate.

---

## Auto-Start Knobs You Can Tune

For test rigs or environments where you want autostart off:

```toml
[self_healing]
hook_starts_daemon = false
```

For environments where the autostart cooldown is too aggressive (rare):

```toml
[self_healing]
auto_start_cooldown_secs = 2
auto_start_timeout_secs = 5
```

Verify after editing:

```bash
rch config show --sources | grep -A6 self_healing
rch daemon reload
```

---

## Agent Operating Rules

- **Do** trust the autostart path on first failure. Re-issue the original `rch exec` once after `auto_start_cooldown_secs`.
- **Do** check `which rchd` if autostart never recovers.
- **Don't** delete `hook_autostart.cooldown` in a tight loop — that's defeating a safety. Either wait or use `rch daemon start` directly (which doesn't go through the cooldown path).
- **Don't** kill rchd to "fix" things while builds are active. Use `rch daemon restart -y` only after confirming `rch queue` is empty.
- **Don't** ask the human "should I restart the daemon?" — the daemon's own self-healing is the right answer for transient failures. Only escalate after `rch doctor --json` plus `rch daemon logs -n 200` show an actionable upstream problem.
