# Recovery Playbooks (Symptom → Fix in ≤ 90 Seconds)

## Contents

- [Playbook A: "My build feels slow"](#playbook-a-my-build-feels-slow)
- [Playbook B: "Daemon unavailable"](#playbook-b-daemon-unavailable)
- [Playbook C: "All workers unreachable"](#playbook-c-all-workers-unreachable)
- [Playbook D: "All workers at capacity"](#playbook-d-all-workers-at-capacity)
- [Playbook E: "All workers failed preflight"](#playbook-e-all-workers-failed-preflight)
- [Playbook F: "Permission denied" during sync](#playbook-f-permission-denied-during-sync)
- [Playbook G: Worker disk pressure](#playbook-g-worker-disk-pressure)
- [Playbook H: Hook isn't being called](#playbook-h-hook-isnt-being-called)
- [Playbook I: Hook timeout / slow classification](#playbook-i-hook-timeout--slow-classification)
- [Playbook J: Worker version drift after upgrade](#playbook-j-worker-version-drift-after-upgrade)
- [Playbook K: `rch self-test` won't finish](#playbook-k-rch-self-test-wont-finish)
- [Playbook L: TOML/config edit broke things](#playbook-l-tomlconfig-edit-broke-things)
- [When the Playbook Doesn't Apply](#when-the-playbook-doesnt-apply)

Each playbook is structured as: **observed signal → one-shot diagnostic → ordered fix attempts → verification**. Run them in order. Don't skip the diagnostic. Don't ask the human if the fix is in the playbook.

For unknown symptoms or a stuck loop, fall through to the bottom of this file ("When the Playbook Doesn't Apply") for the escalation packet.

---

## Playbook A: "My build feels slow"

**Signal:** Build wall time is much higher than expected; you suspect rch fell back to local.

```bash
# Diagnostic
RCH_VISIBILITY=verbose cargo check 2>&1 | grep -E '^\[RCH\]'
```

**Fix attempts:**

1. If you see `[RCH] local (...)` — open `references/FAIL_OPEN.md` and look up the parenthetical reason. Apply the matching self-fix.
2. If you see no `[RCH]` line at all — the hook isn't intercepting. Run `rch hook status`. If not installed: `rch hook install`. If installed but not firing: `rch hook test`.
3. If you see `[RCH] remote ...` — RCH is doing what it can; the slowness is real. Inspect `rch speedscore --all` and consider whether the project warrants a faster worker.

**Verify:**

```bash
rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_$(basename "$PWD")" cargo check --workspace --all-targets 2>&1 | tail -5
```

The summary line should say `[RCH] remote <worker> (...)`.

---

## Playbook B: "Daemon unavailable"

**Signal:** `[RCH] local (daemon unavailable)` or `RCH-E500 / RCH-E502`.

```bash
# Diagnostic
rch --json daemon status 2>&1 | head -20
ls -la "${XDG_RUNTIME_DIR:-/tmp}/rch/" 2>&1
```

**Fix attempts:**

1. If `which rchd` is empty → daemon binary missing. Install rch (see project README).
2. If autostart cooldown is recent → wait 5–10 seconds and retry the original command.
3. If autostart lock is held by no process → it's stale. Ask user authorization, then `rm "${XDG_RUNTIME_DIR:-/tmp}/rch/hook_autostart.lock"`.
4. Foreground spawn to surface the real error: `rch daemon start`. Read its stderr.
5. If `rch daemon start` succeeds but the hook still doesn't see the daemon, check socket consistency: `rch --json config get general.socket_path` and `rch --json daemon status | jq '.data.socket_path'` must match. If they don't: `rch daemon restart -y`.

**Verify:** `rch check` returns `ready`.

---

## Playbook C: "All workers unreachable"

**Signal:** `[RCH] local (all_workers_unreachable)` or `RCH-E100 / RCH-E101 / RCH-E108`.

```bash
# Diagnostic
rch --json workers probe --all | jq '.data[] | {id, status, last_error}'
```

**Fix attempts (per failing worker):**

1. SSH directly: `ssh -v -i <identity_file> ubuntu@<host> 'echo OK'`. The first error you see is the real one.
2. Auth error → check `identity_file` permissions (`chmod 600`), key on agent (`ssh-add -l`), and authorized_keys on the worker.
3. Connection refused → `sshd` not running on worker, or wrong port.
4. DNS / network unreachable → host moved or networking broken.
5. Host key changed → with explicit user authorization, refresh the entry. Compare fingerprints first.

**Verify:** `rch workers probe <id>` returns ok.

---

## Playbook D: "All workers at capacity"

**Signal:** `[RCH] local (all workers at capacity)` (snake-case tag in JSON: `all_workers_busy`) or `RCH-E204` repeatedly.

**Fix attempts (in order, escalating):**

1. **Verify queueing is on** — `RCH_QUEUE_WHEN_BUSY` is **already enabled by default** in current rch (only set `=0` to disable). If you still see `all workers at capacity`, queueing didn't help — the wait timed out.
2. Bump the wait timeout for the next invocation: `RCH_DAEMON_WAIT_RESPONSE_TIMEOUT_SECS=120 <your-command>`.
3. Check whether one worker is hot and others are cold (uneven distribution): `rch --json status --workers | jq '.data.daemon.workers[] | {id, used: .used_slots, total: .total_slots}'`.
4. If aggregate capacity is the problem, raise `total_slots` on top workers in `~/.config/rch/workers.toml`, then `rch daemon reload`.
5. Watch the backlog drain: `rch queue --watch` (this is an interactive polling view, not a TUI — Ctrl-C exits cleanly).

**Verify:** Next `rch exec` lands `[RCH] remote <worker> (...)`.

---

## Playbook E: "All workers failed preflight"

**Signal:** `[RCH] local (all workers failed preflight checks)` (snake-case tag: `all_workers_failed_preflight`) or `RCH-E013..024 / RCH-E205 / RCH-E305`.

```bash
# Diagnostic
rch diagnose --dry-run "<the command>" 2>&1 | head -50
RCH_LOG_LEVEL=debug rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_diag" cargo check 2>&1 | tail -40
```

**Fix attempts:**

1. If a path-dep error (RCH-E013..016) → see `PATH_DEPENDENCIES.md` for the exact code.
2. If `RCH_TOPOLOGY_ERR_CANONICAL_NOT_DIRECTORY` or `_ALIAS_NOT_SYMLINK` in worker stderr → fix the topology on the worker (`/data/projects` should be a directory; `/dp` should be a symlink to it).
3. If `RCH-E205 Worker missing toolchain` → `rch workers sync-toolchain --all`.
4. If `RCH-E305 Remote working dir error` → typically mirror perms broken; see Playbook F.

**Verify:** `rch diagnose --dry-run "<command>"` reports `Ready` for the closure plan.

---

## Playbook F: "Permission denied" during sync

**Signal:** `[RCH] local (remote execution failed)` followed by stderr lines mentioning `Permission denied` or `Operation not permitted` under `/data/projects/<repo>`.

```bash
# Diagnostic
ssh ubuntu@<worker> "stat -c '%U:%G %a %n' /data/projects/<repo>"
```

**Fix:**

```bash
ssh ubuntu@<worker> 'sudo chown -R ubuntu:ubuntu /data/projects/<repo> && sudo chmod 775 /data/projects/<repo>'
rch exec -- env CARGO_TARGET_DIR="${TMPDIR:-/tmp}/rch_target_$(basename "$PWD")" cargo check
```

If you see this on multiple repos, audit who's doing `sudo git clone` or running things as root in `/data/projects`.

---

## Playbook G: Worker disk pressure

**Signal:** `[RCH] remote <worker> failed [RCH-E210]` (or `E211/E215/E216/E217`); or `rch status` calls out a worker as critical.

See the dedicated `DISK_AND_PRESSURE.md`. TL;DR:

```bash
rch --json status --workers | jq '.data.daemon.workers[] | select(.pressure_state != "healthy") | {id, pressure_state, pressure_reason_code, pressure_disk_free_gb}'
ssh ubuntu@<worker> 'df -h / /tmp && free -h && cat /proc/pressure/memory'
ssh ubuntu@<worker> 'sbh status --json'      # let sbh handle it
```

If `sbh` isn't installed on the worker: install it, or escalate. Don't `rm -rf` build artifacts blindly — other agents might be mid-build.

---

## Playbook H: Hook isn't being called

**Signal:** Builds run locally; `[RCH]` summary lines never appear; the hook seems silent.

```bash
# Diagnostic
rch hook status --json
rch agents status --json
which rch
cat ~/.claude/settings.json 2>/dev/null | jq '.hooks.PreToolUse'
```

**Fix attempts:**

1. Hook not installed → `rch hook install` (or `rch agents install-hook claude-code`).
2. Hook command path is wrong → `rch hook install` re-resolves to the current absolute path.
3. The Claude Code session predates the hook install → restart Claude Code (the harness only loads hooks on startup).
4. Hook installed but fires for a different agent → confirm `rch agents list --json` includes the agent you're running under.

**Verify:**

```bash
rch hook test
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"cargo check"}}' | rch
```

The second should produce a JSON `updatedInput` rewriting to `rch exec -- cargo check`.

---

## Playbook I: Hook timeout / slow classification

**Signal:** Claude Code reports the hook timed out, or the hook is logging classification budget warnings.

```bash
# Diagnostic
RCH_LOG_LEVEL=debug printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"cargo build"}}' | rch 2>&1 | grep -iE 'budget|classif'
```

**Likely causes:**

- Massive `Cargo.toml`/`metadata` and the closure preflight is slow → cache should warm; if not, the cache may be invalid: `rm -rf ~/.cache/rch/classify_cache_v*` (with explicit user authorization).
- A misbehaving CI invocation is running rch in a loop and starving the daemon.

If the hook's compilation decision exceeds 5ms, that's a budget regression worth filing.

---

## Playbook J: Worker version drift after upgrade

**Signal:** New rch features behave inconsistently across workers; `rch fleet status` shows mixed versions.

```bash
rch fleet status --json    # exact JSON shape varies by version; inspect first
rch fleet verify           # human-readable comparison of installed binaries
```

**Fix:**

```bash
rch fleet deploy --canary 25 --canary-wait 60 --verify
# observe output, then
rch fleet deploy --verify           # full rollout
rch fleet verify                    # confirm uniform
```

If rollback is needed: `rch fleet rollback --verify`.

For a single worker, `rch fleet deploy --worker <id> --verify` (deploy, single host).

---

## Playbook K: `rch self-test` won't finish

**Signal:** `rch self-test --all` runs forever or returns no output for minutes.

```bash
# Diagnostic
rch self-test --worker <id> --timeout 120 --debug 2>&1 | tail -30
rch self-test history --limit 5 --json
```

**Fix attempts:**

1. Try a single worker with `--timeout 120 --debug`. If that works, the `--all` mode is hitting a slow worker — narrow down with `rch speedscore --all`.
2. If self-test hangs against any single worker, that worker has a deeper problem. `rch workers probe <id>`, then drain it (`rch workers drain <id>`) and continue without it.
3. Capture a full doctor report: `rch doctor --json > /tmp/rch-doctor.json`. The pre-v1.0.16 hang bug `bd-w5r9` is fixed; if you reproduce on current rch, escalate with the doctor output.

---

## Playbook L: TOML/config edit broke things

**Signal:** Things were working; you edited `~/.config/rch/config.toml` or `workers.toml`; now nothing works.

```bash
rch config validate
rch config doctor
rch config show --sources
rch config diff                      # what differs from defaults
```

If `rch config validate` flags an issue, fix the indicated line and `rch daemon reload`. If you can't see what's wrong, `git diff` of the config (if you keep it under version control) is your friend. Otherwise `rch config init` writes a clean baseline you can compare against.

---

## When the Playbook Doesn't Apply

Capture the escalation packet before pinging the human:

```bash
mkdir -p /tmp/rch-escalation && cd /tmp/rch-escalation
rch doctor --json                         > doctor.json 2>&1 || true
rch --json daemon status                  > daemon-status.json 2>&1 || true
rch --json workers probe --all            > workers-probe.json 2>&1 || true
rch --json status --workers --jobs        > status.json 2>&1 || true
rch --json queue                          > queue.json 2>&1 || true
rch --json config show --sources          > config.json 2>&1 || true
rch --json hook status                    > hook-status.json 2>&1 || true
rch --json agents status                  > agents-status.json 2>&1 || true
rch --json self-test --all --timeout 120  > selftest.json 2>&1 || true
rch daemon logs -n 500                    > daemon.log 2>&1 || true
{ echo "rch=$(rch --version)"; echo "rchd=$(rchd --version 2>/dev/null || true)"; \
  echo "daemon-reported-version=$(rch --json status 2>/dev/null | jq -r '.data.daemon.daemon.version // ""')"; } > versions.txt
ls -lah
```

Then surface a one-paragraph synthesis to the human: what symptom you saw, what you tried (with playbook letter), where the packet lives. Don't ship a wall of text; the packet is the data, your message is the signal.
