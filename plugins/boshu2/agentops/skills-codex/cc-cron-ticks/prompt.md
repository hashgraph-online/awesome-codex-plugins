# cc-cron-ticks — Codex Execution Profile

Codex runtime adapter for the `cc-cron-ticks` skill. The doctrine is in the
Codex wrapper [`SKILL.md`](./SKILL.md) and the source skill
[`../../skills/cc-cron-ticks/SKILL.md`](../../skills/cc-cron-ticks/SKILL.md) —
read both before scheduling anything. This file maps that doctrine onto Codex,
which has **none** of the source scheduler tools.

## Tool-surface delta (read first)

| Source scheduler surface | Codex equivalent |
|---|---|
| `CronCreate` | `launchctl load` (macOS) / `systemctl --user enable --now <unit>.timer` (Linux) / a `crontab` line |
| `CronList` | `launchctl list` / `systemctl --user list-timers` / `crontab -l` |
| `CronDelete` | `launchctl unload` / `systemctl --user disable --now <unit>.timer` / `crontab -e` removal |
| schedule durable routine | a persisted launchd plist / systemd-timer unit (durable by nature) |
| `Monitor` (live stream) | not cron — poll loop or `tail -f`/`inotifywait`; for "react on change" prefer a watch, not a tick |

There is no in-memory/in-session tick on Codex. Every Codex schedule is
OS-level and therefore durable — treat `durable: true` as the only mode and tell
the user the job outlives the session until explicitly removed.

## Steps

1. **Choose the shape.** Recurring loop/poll vs one-shot "at time X do Y".
   Recurring → a timer/cron entry. One-shot → `launchd`/`systemd-run --on-calendar`
   one-shot or an `at(1)` job. (Maps to Phase 1 of the source skill.)

2. **Gate the tick body (BLOCKING).** Confirm the body does NOT use
   a different agent CLI with print-style execution. On Codex the tick
   body is `codex exec "<thin driver>"` (Pro sub) or a direct shell command
   (e.g. `bash ~/dev/control-plane/tick.sh`). Confirm the triggered work is
   idempotent / atomically claimed (`bd ready` + `bd update --claim`, a lockfile,
   or an Agent Mail reservation) so a double-fire is safe. Do not proceed if
   either check fails.

3. **Design the cadence (local time, off the mark).** Use the table in
   the source skill Phase 2. `* * * * *` = the 1-min drive loop; `*/5 * * * *` =
   lighter drain; `7 * * * *` / `57 8 * * 1-5` for approximate times (avoid
   `:00`/`:30`). For launchd use `StartCalendarInterval` / `StartInterval`; for
   systemd use `OnCalendar=` / `OnUnitActiveSec=`. Confirm with the user before
   creating a once-a-minute loop.

4. **Create the schedule.** Write the launchd plist / systemd `.timer`+`.service`
   pair / crontab line whose program runs the gated tick body from step 2.
   Keep the body thin: claim one unit of work, do it, commit, else no-op and
   report "queue dry". Load/enable it.

5. **Verify + capture the handle.** List the active schedule (`launchctl list |
   grep <label>` / `systemctl --user list-timers` / `crontab -l`) and capture
   the label/unit name — it is the handle for teardown (the Codex analog of the
   returned job ID).

6. **Operate + stop.** Inspect via the list command. When the loop's goal is met
   or the session wraps, tear the schedule down (`launchctl unload` /
   `systemctl --user disable --now` / remove the crontab line) so it doesn't keep
   firing on a stale objective. Report the teardown command to the user.

## Guardrails

- **Never use a different agent CLI as the Codex tick executor.** Use `codex exec`
  or a direct shell command. An unattended OS timer must not silently run the
  wrong runtime around the clock.
- **Idempotent or nothing.** OS timers fire on schedule regardless of prior-run
  state and can overlap on a slow tick. The body must claim atomically and no-op
  cleanly when there is no work. A non-idempotent timer corrupts state on overlap.
- **Codex schedules are durable by default.** An OS timer survives session exit
  and reboot. There is no auto-expiry; it runs until removed. Always hand the
  user the exact teardown command.
- **Keep bodies short / dispatch heavy work.** A long foreground tick can overrun
  its own interval (overlap) — dispatch heavy work to a background process and let
  the tick poll-and-claim.
- **Poll vs stream.** If the need is "react the instant X changes," use a watch
  (`inotifywait`/`tail -f`), not a fixed-interval timer — the cron analog of
  choosing Monitor over CronCreate.
- **Stay current.** Verify the OS scheduler invocation against the host
  (`man launchd.plist` / `man systemd.timer` / `man 5 crontab`); verify the Codex
  `codex exec` surface before relying on flags.
