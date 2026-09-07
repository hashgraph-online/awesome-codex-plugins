---
name: schedule
description: Set a shift to start at a fixed time — check the work is queued, then print the launchd or cron config for this project and the one command that installs it. Generates; registers nothing.
---

Get the host-opened project ready to start on a clock, then hand the owner the config. Work through
these in order; each one is a check the owner would otherwise discover at 4am.

Resolve the host-opened project folder to an absolute `$TASK_ROOT`: use `${CLAUDE_PROJECT_DIR}` on
Claude Code; on Codex honor Nightshift's `${CODEX_PROJECT_DIR}` recovery override when present,
otherwise capture `pwd -P` before any other shell call. Resolve `$TASK_ROOT/.nightshift-link` when
present and call the validated absolute target `$NIGHTSHIFT_WORKSPACE`; otherwise set
`NIGHTSHIFT_WORKSPACE="$TASK_ROOT"`.

Bind the Nightshift directory once: `NS="$NIGHTSHIFT_WORKSPACE/.nightshift"`. On native Windows,
`$NS = Join-Path $NIGHTSHIFT_WORKSPACE '.nightshift'`. After this bind, Nightshift files are
`$NS/<name>` for every read, write, and shell command. Catalog and owner-facing prose may use the
short names (`punch-list.md`, `parking-lot.md`, `STOP`). Never re-resolve. Helpers that take
`--project` or `-Project` still receive `"$NIGHTSHIFT_WORKSPACE"`.
Never search or guess. The shell's working directory persists
between Bash calls, so never use a bare path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available, otherwise derive
it from the absolute path attached to this skill (`skills/schedule/SKILL.md`). Substitute that
absolute path in every command below; never search for the plugin.

On native Windows, use the PowerShell tool, `$env:` host variables, and native paths. Do not invoke
the POSIX generator through Git Bash or WSL; the Task Scheduler generator is bundled separately.

## 1. Is there a site at all?

No `$NS/` — stop and point at Setup (`/nightshift:setup` on Claude Code, or ask Nightshift
to set up on Codex). Nothing below is meaningful without it.

Read `$NS/work-mode`. Artifact mode is a persistent folder, not a Git repository; the scheduled
agent still starts in that work target. A malformed mode or a scratch work target is a refuse —
fix it with Setup before installing a job. In artifact mode, refuse to print or install a job when `$NS/receipts` exists but is not a usable directory.
If `$NS/work-mode` is missing and Setup would propose artifact, refuse to print or install a job; a scheduled start will refuse to arm.
If the work target cannot be resolved, refuse to print or install a job; a scheduled start will refuse to arm.

## 2. Is there work queued?

A scheduled start works the punch list it finds and **promotes nothing** — parked work orders and
drafting-table entries stay exactly where they are. So an empty `## Items` means the scheduled run
does nothing at all, and this is the moment to fix that, not 4am.

Count the open `- [ ]` in `$NS/punch-list.md`:

- **Items present** — say what they are in one line and carry on.
- **None** — say so plainly and offer the ways to fix it: compose a shift now with
 Hunt (answer **later**, not **now** — a shift started here defeats scheduling it), cut an
 ordinary draft from `$NS/drafting-table.md`, cut a `Status: proposed` import with
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/import-issues.sh" --project "$NIGHTSHIFT_WORKSPACE" --promote …`
 (on native Windows,
 `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\import-issues.ps1" -Project "$NIGHTSHIFT_WORKSPACE" -Promote …`),
 or write an item by hand. Then re-check. Never schedule an empty list without saying it
 will do nothing.

A parked work order is not queued work. If one exists, say so: it must be moved into the punch list
before the scheduled time, because start will not promote it.

## 3. Will the permissions hold?

A scheduled run is headless and cannot answer a prompt. On Claude Code, if neither
`$TASK_ROOT/.claude/settings.local.json` nor `$TASK_ROOT/.claude/settings.json` grants
frictionless permissions, warn
once. On Codex the grant travels in the command itself — the generator's
`--agent 'codex exec -s danger-full-access'` (POSIX) or
`-Agent 'codex exec -s danger-full-access'` (native Windows) carries it — so a Codex entry generated
without that agent will stall on the
first tool that asks. Setup offers the fix.

## 4. Confirm the queued work is unarmed

Open `- [ ]` Items do not activate the clock-out gate by themselves. `.shift-armed` does, and
scheduling must not create it: the work stays queued until the scheduled Start preflight clears
stale markers and arms the shift.

If `$NS/.shift-armed` already exists, stop here. This workspace has an active or stale shift,
not merely queued work. Report that state and point the owner to Status (`/nightshift:status` on
Claude Code, or ask Nightshift for status on Codex); do not tell them to create a STOP marker just
to schedule the list. Continue only after the existing shift has been ended or its stale state has
been diagnosed.

## 5. Print the config

Ask for the time if the owner has not given one — 24-hour `HH:MM`, local — then run the generator
and show its output as it comes:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/schedule.sh" --project "$NIGHTSHIFT_WORKSPACE" --preflight
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/schedule.sh" --project "$NIGHTSHIFT_WORKSPACE" --at <HH:MM>
# Codex projects add: --agent 'codex exec -s danger-full-access'
# Linux user timers:  --target systemd
```

Native Windows:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\schedule.ps1" `
 -Project "$NIGHTSHIFT_WORKSPACE" -Preflight
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\schedule.ps1" `
 -Project "$NIGHTSHIFT_WORKSPACE" -At <HH:MM>
# Codex projects add: -Agent 'codex exec -s danger-full-access'
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\schedule.ps1" `
 -Project "$NIGHTSHIFT_WORKSPACE" -List
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\schedule.ps1" `
 -Project "$NIGHTSHIFT_WORKSPACE" -Remove
```

`--preflight` / `-Preflight` checks the agent binary, permissions, resolved workspace, rules, queued work,
generated paths, and scheduler syntax for Claude Code and Codex. It installs nothing, writes
nothing under LaunchAgents, and does not enable, start, or register an entry. `--list` / `-List` shows what
is already registered for this project; `--remove` / `-Remove` prints the command that unregisters it. The
generator refuses to hand over a second entry where one exists — two scheduled starts on one punch
list is two agents on one shift.

**Install nothing.** The owner runs the command it prints, or does not.

## 6. Close

Say where the run's output will land (`$NS/scheduled.log`), and
mention once that the same generator runs from a terminal with no session —
`$NIGHTSHIFT_PLUGIN_ROOT/runtime/schedule.sh` is plain shell and spends no model tokens, which is
what makes it reachable on a day this command is not. On native Windows the equivalent is
`$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\schedule.ps1`; it likewise spends no model tokens and
registers nothing. The README carries the full offline note.
