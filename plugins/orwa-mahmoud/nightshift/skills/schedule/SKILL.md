---
name: schedule
description: Print the launchd, cron or Task Scheduler config that starts a shift at a fixed time; registers nothing.
license: MIT
---

Get the host-opened project ready to start on a clock, then hand the owner the config. Work through
these in order; each one is a check the owner would otherwise discover at 4am.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/schedule/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

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
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" import-issues --promote …`, or write an
 item by hand. Then re-check. Never schedule an empty list without saying it will do nothing.

A parked work order is not queued work. If one exists, say so: it must be moved into the punch list
before the scheduled time, because start will not promote it.

## 3. Will the permissions hold?

A scheduled run is headless and cannot answer a prompt. On Claude Code, if neither
`$TASK_ROOT/.claude/settings.local.json` nor `$TASK_ROOT/.claude/settings.json` grants
frictionless permissions, warn
once. On Codex the grant travels in the command itself: pass the owner's Codex launch command, as
the Codex host page (`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/hosts/codex.md`)
spells it, through `--agent`. The generator's preflight warns when a Codex command carries no
headless grant, and a Codex entry generated without one will stall on the first tool that asks.
Setup offers the fix.

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
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" schedule --preflight
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" schedule --at <HH:MM>
# Codex projects add: --agent '<the Codex launch command from references/hosts/codex.md>'
# Linux user timers:  --target systemd
```

`--preflight` / `-Preflight` checks the agent binary, permissions, resolved workspace, rules, queued work,
generated paths, and scheduler syntax for Claude Code and Codex. It installs nothing, writes
nothing under LaunchAgents, and does not enable, start, or register an entry. `--list` shows what
is already registered for this project; `--remove` prints the command that unregisters it. The
generator refuses to hand over a second entry where one exists — two scheduled starts on one punch
list is two agents on one shift.

**Install nothing.** The owner runs the command it prints, or does not.

## 6. Close

Say where the run's output will land (`$NS/scheduled.log`), and
mention once that the same generator runs from a terminal with no session —
`ns schedule` is plain shell and spends no model tokens, which is
what makes it reachable on a day this command is not. On native Windows the equivalent is
; it likewise spends no model tokens and
registers nothing. The README carries the full offline note.
