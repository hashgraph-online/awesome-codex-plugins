---
name: start
description: Begin the shift from the punch list without asking, so scheduled and headless runs behave like interactive ones.
license: MIT
---

Start a Nightshift run in the host-opened project.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/start/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls.

When a verdict names your host — permission modes, resume commands, the sandbox and identity
rules that belong to it — open
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/hosts/<host>.md` for the host you are on,
and no other. Not before a verdict names it.

## 1. Preflight — one helper, one verdict per line

**With work in the punch list, this command asks nothing.** It reads the list, arms the site and
works — which is what lets cron run it at 04:00 and lets the watchman revive it after a crash. It
promotes nothing on its own: what is in the punch list is the shift, exactly as the owner left it.

The one time it speaks is when the punch list is **empty**. Then there is no work to do silently,
so it looks at staged drafts and pending Hunt orders and asks which to promote.

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" start-preflight --host claude
```

Pass the host you are actually running on (`claude`, `codex`, or `cursor`). Every line it prints is
one verdict, and it explains itself:

- **`ok <topic> <detail>`** — a resolved fact. Report it if the owner asked; otherwise continue.
- **`warn <topic> <detail>`** — say it once in plain English, then arm anyway. The choice stays the
  owner's.
- **`refuse <topic> <detail>`** — do not arm. Print the `explain` and `repair` lines that follow it
  verbatim and stop.

Exit status 0 means the shift may arm; non-zero is a refusal; 2 is a usage error in the call you
just made. An `explain` line says what the verdict means and a `repair` line is the exact action —
relay them, do not restate them, and never invent an explanation the helper did not print.

Two rules are policy rather than mechanics, so they are yours to hold whatever a verdict says:
never kill a live watchman and never start a second shift beside one; and never clear `STOP` or
invent a time budget for a paused shift whose deadline has passed.

## 2. The punch list is the shift

**Inspect capabilities in the skill.** Read manifests, lockfiles, and `## Gates` in the work
target. `$NS/capabilities.json` is a cache the model may update after a successful tooling commit
only; no detector is required.

**Permission gaps are parked, never asked.** Run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" preflight-needs` against every item now in
`## Items`. For each item with a gap, run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" park-needs` to add its entry to
`$NS/parking-lot.md` naming the missing category, then append one `$NS/shift-log.md` line listing
every gapped item. Work everything else. If either helper exits because no JSON parser is
installed, park the gaps in the skill and continue; neither is on the armed path.

If `$NS/punch-list.md` has at least one open `- [ ]` under `## Items`, that is the work — start it.
Do not promote, cut, or add anything: parked orders and drafts stay exactly where the owner left
them. An empty `## Items` section still keeps the Shift contract and Gates; they bind whatever Hunt
or Start cuts next.

**Resume the active product cycle before rediscovery.** When the open item is product evolution,
inspect `$NS/opportunity-map.md` for its single `Status: building` entry before doing new research
or selecting work. Its `Next` action and `Verify remaining` are the continuation point. More than
one building entry is inconsistent state: keep the earliest one active, mark the others
`candidate`, record the repair in `$NS/shift-log.md`, and continue.

**Only when the punch list is empty, offer what is staged.** The `ok staged` verdict already counts
`$NS/work-orders.md` and `$NS/drafting-table.md`. Read both, show what they hold in one short list,
and ask which to work now. On the owner's choice, **cut it — move, never copy**: the item goes
under `## Items` and is removed from the file it came from, so it never exists in two places. An
imported draft (`Status: proposed` and a canonical `Source:` GitHub URL) is cut the same way in the
skill — move the item under `## Items` and remove it from the drafting table. The import-issues
helper is optional. Do not require Python. A flagged import stays refused unless the owner
overrides after seeing the flags. From a work order, remove the whole `## Work order` section
(heading, hours, and item), not just the checkbox, then write `$NS/deadline` as a UNIX epoch from
the recorded hours (`now + hours*3600`; compute now with `date +%s` on POSIX, or `Get-NSUnixTime`
after importing the module on native Windows); an order marked finite with no hours writes no
deadline.

If the punch list is empty and nothing is staged, stop and say so: Setup if the project is new,
Hunt to compose a shift, or write an item by hand. Give host-native invocation when needed: slash
commands on Claude Code, or ask Nightshift for the named skill on Codex.

The working tree should be clean enough to commit per item; warn if it is not.

## 3. Deadline — read, never asked

The deadline value is decided when the work is composed (Hunt's cut, the owner's own edit, or
Start's own start-defaults), never asked here. **The deadline is cleared only if it has already passed** — the preflight does that, because a shift that reached the whistle
would otherwise clock tonight out at zero items. A deadline still in the future is tonight's plan and is kept.

Act on the deadline verdict:

- `ok deadline <epoch> (policy …)` — the shift policy is the authority. Write that epoch to
  `$NS/deadline`.
- `ok deadline <epoch> (file …)` — keep the file as it is and record that epoch as the policy's
  `deadlineEpoch`, logging the adoption in `$NS/shift-log.md`. Never delete the marker.
- `ok deadline none (finite list …)` — correct. Their natural end is the last tick, and a stuck run
  is red-flagged in the shift log and held for review.
- `refuse deadline` — an `Ending: open-ended` marker with no clock. Refuse to start, say so in one
  line, and point at Hunt, which asks for hours; never invent a number.

One deadline governs the whole shift: finite items first, the walkthrough soaks up the rest.

## 4. Arm the gate

Every check has passed and the work is known, so the shift begins here. Create the marker:

```bash
touch "$NS/.shift-armed"
```

Native Windows:

```powershell
New-Item -ItemType File -Force "$NS\.shift-armed" | Out-Null
```

**This, and nothing else, is what puts a session on shift.** Until it exists the punch list is an
ordinary to-do file: the clock-out gate holds nobody and hardhat's guards apply to no one, so a
session that writes items while planning still stops freely. Write it only after the preflight
returned zero. A marker left behind by a preflight that stopped early would put the next session on
a shift it never started.

### Bind this session — before any other tool

Immediately after writing `$NS/.shift-armed`, make this the next tool call on either host:

```bash
: nightshift-binding-probe
```

On native Windows, the immediate PowerShell probe is:

```powershell
$null = 'nightshift-binding-probe'
```

This harmless host-shell probe makes the hardhat record this conversation in `$NS/.shift-session`
and claim generation 1 in `$NS/.shift-lease` before item work or the watchman begins. Its
distinctive marker also makes a concurrent second Start fail explicitly if another session won the
atomic session-file claim. Do not read files, search, call MCP, or yield between the marker and the
probe: catch-all tool rules observe those calls, but passive tools cannot make the first session
claim. Never create or edit the lease directly.

The probe must execute cleanly with no hook denial or hook error. On native Windows this is also
the live check that the filesystem can make an atomic private session claim and lease. If it fails,
remove `$NS/.shift-armed`, run Stop, and follow the stale-lease reset the preflight prints as a
repair; do not begin item work or arm a watchman on an assumed claim.

### Codex identity checkpoint — before the watchman

Codex exposes the current task identity through hook payloads, not as a shell environment variable,
so this runs after the probe and before the watchman:

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" start-preflight --phase bind
```

It classifies `$NS/.shift-session` line 1 with `ns_codex_identity_kind` (native Windows:
`Get-NSCodexIdentityKind` after
`Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force`).

- `ok codex-identity resumable`, or `not-applicable` on another host — continue.
- `warn codex-identity missing` — continue with the fresh-session fallback and say plainly that
  same-thread recovery is unavailable until an identity is recorded.
- `refuse codex-identity` — stop the unattended start.
  Remove only the markers this start created (`$NS/.shift-armed` and its
  new `$NS/.shift-session`) and reset the lease with `ns_lease_reset_stale` in the same Bash call,
  so no hook call in between can bootstrap the aborted lease again. On native Windows,
  `Reset-NSStaleLease "$NS"` with no other command between marker removal and the reset. Append one
  failed-preflight line to `$NS/shift-log.md` and stop before the watchman or item work. Never
  pass the value to Codex, print it, or guess a replacement.

This capture-and-check is part of Start, not an owner instruction to remember. An attended session
that does not request an unattended shift remains unaffected.

## 5. Heads-up

Surface any still-unanswered entries in `$NS/parking-lot.md` (read-only) so the owner sees what the
last shift parked — printed, never waited on. Append a `shift started` line to `$NS/shift-log.md`.
The preflight rotates that journal itself when it grows past ~500 KB, into
`$NS/archive/<YYYY-MM-DD>/shift-log.md` (`date +%Y-%m-%d` on POSIX, `Get-Date -Format yyyy-MM-dd`
on native Windows). Only the mechanical journal auto-rotates — `snag-log.md` and `parking-lot.md`
are the owner's review material, and Archive files those on the owner's order.

## 6. Arm the night watchman

Each host has its own watchman and the verb resolves to it; all of them read their cadence from
the rules file, and each stands down on a shift another host owns. Unless the
`ok watch-minutes 0 (watchman disarmed)` verdict says otherwise, arm it in the background.

```bash
nohup "$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" watchman >/dev/null 2>&1 &
```

It revives a session that DIES mid-shift — an API outage, a crash, a killed terminal — by spawning
a fresh session that resumes from the punch list. Every host stands down on done, a stop-work
order, or quitting time; per-host revival detail is in `hosts/<host>.md`. `STOP` remains the
stop-work order on every host, and the only stop a headless run can receive.

## 7. Work

Read `$NS/punch-list.md` in full, then begin item 1 and follow the nightshift skill, which owns the loop, the gates, the receipts, cited
research and the shift report: one item at a time, tick only after the item is complete, park don't
ask, leave pushing to the owner unless the punch list says otherwise. From here the clock-out gate
owns the session — it will not let you stop while any box is open. When the gate logs
`JSON parser unavailable`, write the morning page by hand from
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/receipts/morning.md`, which names the file
to write and the fields to fill. Every shift leaves a receipt.
