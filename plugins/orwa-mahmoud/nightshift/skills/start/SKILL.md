---
name: start
description: Begin the shift — preflight, cut whatever is queued, arm the site, work the punch list. Asks nothing, so a scheduled or headless run works exactly like an interactive one.
---

Start a Nightshift run in the host-opened project.

Resolve the host-opened project folder to an absolute `$TASK_ROOT`: use `${CLAUDE_PROJECT_DIR}` on
Claude Code; on Codex honor Nightshift's `${CODEX_PROJECT_DIR}` recovery override when present,
otherwise capture `pwd -P` before any other shell call. If `$TASK_ROOT/.nightshift-link` exists,
validate the one absolute workspace path inside it and call that `$NIGHTSHIFT_WORKSPACE`; otherwise
set `NIGHTSHIFT_WORKSPACE="$TASK_ROOT"`.

Bind the Nightshift directory once: `NS="$NIGHTSHIFT_WORKSPACE/.nightshift"`. On native Windows,
`$NS = Join-Path $NIGHTSHIFT_WORKSPACE '.nightshift'`. After this bind, Nightshift files are
`$NS/<name>` for every read, write, and shell command. Catalog and owner-facing prose may use the
short names (`punch-list.md`, `parking-lot.md`, `STOP`). Never re-resolve. Helpers that take
`--project` or `-Project` still receive `"$NIGHTSHIFT_WORKSPACE"`.
Never search
surrounding folders or guess. Print both paths when linked. The shell's working directory persists
between Bash calls, so never rely on a bare relative path.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT`: use
`${CLAUDE_PLUGIN_ROOT}` on Claude Code; on Codex use `$PLUGIN_ROOT` when available; on Cursor use
`${CURSOR_PLUGIN_ROOT}` when available; otherwise derive it from the absolute path attached to
this skill (`skills/start/SKILL.md`). Substitute that absolute path in every command below; never
search for the plugin.

On native Windows, use the PowerShell tool and native paths throughout. Resolve the same values
from `$env:CLAUDE_PROJECT_DIR`, `$env:CODEX_PROJECT_DIR`, and `$env:PLUGIN_ROOT`, with
`[Environment]::CurrentDirectory` as the Codex cwd fallback. Import the bundled module when a
preflight helper is needed:

```powershell
Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force
```

Do not route a native run through WSL or Git Bash. WSL is a separate Linux runtime and follows the
POSIX commands in this skill.

If the start request itself explicitly names a different existing Nightshift workspace, that
owner-provided path is authorization to link it: print both absolute paths, run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/link-workspace.sh" --host-root "$TASK_ROOT" --workspace "$PROPOSED_WORKSPACE"`,
then continue from the resolved workspace. Without an explicit path or an existing valid link,
refuse to arm outside the task root and direct the owner to Setup; never discover a target.
On native Windows, use
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\link-workspace.ps1" -HostRoot "$TASK_ROOT" -Workspace "$PROPOSED_WORKSPACE"`
for that same authorized link.

Read `$NS/state-version` before preflight. A missing marker is legacy version `0` and
is operable — do not migrate it. Integer `1` is current. A newer integer or a malformed marker
fails closed: print the shared diagnostic, do not arm, and never rewrite or downgrade the
file. Migration is Setup/Doctor repair only
(`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/migrate-state.sh" --project "$NIGHTSHIFT_WORKSPACE"` on POSIX,
or `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\migrate-state.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`
on native Windows);
Start never writes the marker.

Read `$NS/work-mode` and `$NS/work-target` before preflight. A missing work-mode is
repository — the historical default. `artifact` means the work target is a persistent folder, not
a Git repository. Keep every `$NS/` read and write in the bound directory, but run project
inspection, edits, gates, Git operations, commits, and verification in that work target when the
mode is repository. In artifact mode, inspect and edit that folder and do not require Git.
Completion in that folder is `$NS/receipts/`, not a git log.
Complete each item with
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/write-receipt.sh" --project "$NIGHTSHIFT_WORKSPACE"`
(native Windows:
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\write-receipt.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`)
instead of a work-target commit. Cited reports in that folder still follow
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/cited-research.md` and
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh"` (native Windows:
`& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1"`). Validate with `ns_work_mode` / `ns_work_target` (native Windows: `Get-NSWorkMode` /
`Resolve-NSWorkTarget` after Import-Module). Refuse to arm when the mode is malformed, the target
is a disposable scratch path, or repository mode cannot resolve a Git repository. If `$NS/work-mode` is missing and Setup would propose artifact, refuse to arm and send the owner to Setup; do not `git init` a notes folder. In artifact mode, refuse to arm when `$NS/receipts` exists but is not a usable directory. If the record is
missing, use the workspace itself when it is a repository or its single immediate child
repository, and persist that resolved path as repository mode. Skip a symlink or reparse child; it is not a nested checkout. If several child repositories make
the choice ambiguous, refuse to arm until Setup records one.

**State map:** `punch-list.md` → owner-approved work active in this shift;
`drafting-table.md` → known work staged for a later shift; `parking-lot.md` → unresolved owner
decisions plus the default chosen so work continues; `work-orders.md` → timed catalog work composed
only through Hunt. Ordinary known plans never become work orders.

**With work in the punch list, this command asks nothing.** It reads the list, arms the site and
works — which is what lets cron run it at 04:00 and lets the watchman revive it after a crash. It
promotes nothing on its own: what is in the punch list is the shift, exactly as the owner left it.

The one time it speaks is when the punch list is **empty**. Then there is no work to do silently,
so it looks at staged drafts and pending Hunt orders and asks which to promote.

## 1. Preflight

- **One shift, one agent — check before touching anything.** Read `$NS/.shift-session` and
 validate `$NS/.shift-lease` with `ns_lease_valid` when it exists (on native Windows,
 `Read-NSLease "$NS"` after `Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force`;
 a null result is malformed); never print its
 capability line. Session line 5 names the host, while the lease records the current process
 generation. A malformed lease is unowned state: refuse to start and direct the owner to issue
 STOP, run the stale-lease reset command below themselves in a terminal, and retry. If either
 valid record is still alive, an agent is ALREADY working this punch list — do not start a second
 one beside it; hand the owner the running thread and stop here. The primary process tell is POSIX
 `kill -0` on a recorded numeric pid; `ps`,
 `pgrep`, and `lsof` are optional enhancers and must never be installed. If `kill -0` cannot
 classify the pid, or the optional tools are absent and no host roster or transcript/rollout
 pulse answers, treat it as `process-evidence-unavailable` and stop — missing tools are not
 a dead session. On Claude Code, a matching `ps -o lstart=` or the id in `claude agents --json`
 still means live; the handoff is `claude --resume <id>` for a terminal,
 `vscode://anthropic.claude-code/open?session=<id>` for the IDE. On Codex a recorded pid uses
 the same `kill -0` primary; otherwise a `codex` process (exact name — `pgrep -x codex` when
 available) whose cwd is this project, or a rollout (line 2) still growing, means live —
 hand the owner `codex resume <id>`. A pid that `kill -0` proves dead, with no other live
 tell, is last night's leftover.
 A live `$NS/.watchman` beside an armed list with open Items is also an active shift,
 including the gap between recovery attempts. Refuse the second Start and point the owner at
 Status or STOP; never kill that watchman as stale.
 The trusted Stop helper is the lever if they want a live shift paused first:
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/stop-shift.sh" --project "$NIGHTSHIFT_WORKSPACE"`
 on POSIX, or
 `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\stop-shift.ps1" -Project "$NIGHTSHIFT_WORKSPACE"`
 on native Windows. That disarms immediately. The panic form that only writes the marker —
 `touch "$NS/STOP"` on POSIX, or `New-Item -ItemType File -Force "$NS\STOP"` in native Windows
 PowerShell — waits for the next Stop event. A record whose process is provably dead is last
 night's leftover: fall through and clear it below.
 When Doctor reports `terminal clock-out failed without releasing the shift` and the lease is
 interactive, reopen the recorded conversation — do not run the stale-lease reset. If a recovery
 worker still holds the lease, wait or run Stop from a separate session (or the terminal helper);
 reopening stays blocked while that worker is alive.
 On native Windows, use `Get-Process -Id <pid>` plus the recorded UTC start time through
 `Test-NSRecordedProcess`; an inaccessible process is unavailable evidence, not death.
- **Stand down a stale watchman before clearing its state.** Only after the checks above prove no
 shift is live, kill a still-running pid from `$NS/.watchman` and wait for it to exit. On native
 Windows, read pid and start time, and `Stop-Process -Id` only when
 `Test-NSRecordedProcess` returns Alive — a reused pid is not this watchman. A
 watchman must not be able to advance the old lease while Start removes markers.
- **Reset stale lease state through the shared library, never by reading or deleting its files
 directly.** After the liveness checks and stale-watchman shutdown above, run:
 ```bash
 bash -c '. "$1/lib/lib.sh"; ns_lease_reset_stale "$2/.nightshift"' \
  nightshift "$NIGHTSHIFT_PLUGIN_ROOT" "$NIGHTSHIFT_WORKSPACE"
 ```
 On native Windows, after the same liveness proof, run
 `Reset-NSStaleLease "$NS"` from the imported module. A false result
 is a refusal, not permission to delete the lease directly.
 Refuse to continue if it fails. For malformed state, substitute the resolved absolute paths and
 print this command for the owner to run directly after STOP; do not run it from the blocked
 session.
- **A paused shift with an expired deadline does not get a silent new budget.** If `$NS/STOP` is
 present, `$NS/.ended` is absent, and `$NS/deadline` is a UNIX epoch that has already passed,
 refuse to start. Print the helper's reason and stop here. Do not ask for hours. Do not clear
 `STOP`. Do not invent a time budget. The owner writes a new UNIX epoch to `$NS/deadline`
 (`date -d '+4 hours' +%s` or `date -v+4H +%s` on POSIX; `[DateTimeOffset]::UtcNow.AddHours(4).ToUnixTimeSeconds()`
 on native Windows) or runs Reset then Start.
 ```bash
 bash -c '. "$1/lib/lib.sh"; . "$1/lib/control.sh"; ns_control_start_refuse_reason "$2/.nightshift"' \
  nightshift "$NIGHTSHIFT_PLUGIN_ROOT" "$NIGHTSHIFT_WORKSPACE"
 ```
 On native Windows, after `Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force`,
 run `Get-NSControlStartRefuseReason $NS`. A non-empty string is the refusal.
- **Clear every stale run-control marker first**, before anything writes a new one — last night's
 leftovers would otherwise end tonight's shift at its first stop attempt. Remove them all if
 present: `$NS/STOP`, `$NS/.stall`, `$NS/.notified`, `$NS/.ended`,
 `$NS/.session-end`, `$NS/.shift-pulse`, `$NS/.mint-failed`, `$NS/.shift-session`, any
 `$NS/.shift-session.tmp.*`, `$NS/.shift-armed`, `$NS/.watchman-tick`, and
 `$NS/.lock.d/`. The reset above already removed the lease, its temporary files, and its
 internal mutex.
- **The deadline is cleared only if it has already passed.** A shift that reached the whistle
 leaves a spent deadline behind, and keeping it clocks tonight out immediately with zero items
 done. A paused Stop with a future deadline keeps that deadline. But a deadline still in the future is tonight's plan — written by the owner or by hunt's
 cut — and since this command never asks for hours, deleting it would strand a walkthrough that
 can no longer be given a clock.
- **The punch list is the shift.** If `$NS/punch-list.md` has at least one open `- [ ]`
 under `## Items`, that is the work — start it. Do not promote, cut, or add anything: parked
 orders and drafts stay exactly where the owner left them. An empty `## Items` section still
 keeps the Shift contract and Gates; they bind whatever Hunt or Start cuts next.
- **Resume the active product cycle before rediscovery.** When the open item is product evolution,
 inspect `$NS/opportunity-map.md` for its single `Status: building` entry before doing new
 research or selecting work. If present, its `Next` action and `Verify remaining` are the
 continuation point. More than one building entry is inconsistent state: do not guess between
 them; keep the earliest one active, mark the others `candidate`, record the repair in
 `$NS/shift-log.md`, and continue.
- **Only when the punch list is empty, offer what is staged.** Read `$NS/work-orders.md`
 and `$NS/drafting-table.md`. If either holds work, show it in one short list and ask
 which to work now. On the owner's choice, **cut it — move, never copy**: the item goes under
 `## Items` and is removed from the file it came from, so it never exists in two places. An
 imported draft (`Status: proposed` and a canonical `Source:` GitHub URL) is cut with
 `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/import-issues.sh" --project "$NIGHTSHIFT_WORKSPACE" --promote …`
 (on native Windows,
 `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\import-issues.ps1" -Project "$NIGHTSHIFT_WORKSPACE" -Promote …`)
 — never by editing the two markdown files by hand. A flagged import stays refused unless the
 owner overrides after seeing the flags (`--allow-flagged` / `-AllowFlagged`). Ordinary drafts
 keep the manual cut. From a work order, remove the whole `## Work order` section (heading,
 hours, and item), not just the checkbox, then write `$NS/deadline` as a UNIX epoch from the
 recorded hours (`now + hours*3600`; compute now with `date +%s` on POSIX, or
 `Get-NSUnixTime` after
 `Import-Module "$NIGHTSHIFT_PLUGIN_ROOT\lib\Nightshift.psm1" -Force` on native
 Windows); an order marked finite with no hours writes no deadline.
- If the punch list is empty and nothing is parked, stop and say so: use Setup if the project is
 new, Hunt to compose a shift, or write an item by hand. Give host-native invocation when needed:
 slash commands on Claude Code, or ask Nightshift for the named skill on Codex.
- The working tree is clean enough to commit per item (warn if not).
- **Rotate the journal before it becomes one.** If `$NS/shift-log.md` is larger than
 ~500 KB, move it to `$NS/archive/<YYYY-MM-DD>/shift-log.md` (today's date with
 `date +%Y-%m-%d` on POSIX, or `Get-Date -Format yyyy-MM-dd` on native Windows) and start a fresh one
 with the same one-line header. Only the mechanical journal auto-rotates — `snag-log.md` and
 `parking-lot.md` are the owner's review material; Archive files those on the owner's order.
- **Require an exact JSON parser for tool rules.** `jq` or `python3` must be available before
 arming; without either, refuse to arm and name the missing prerequisite. The hardhat never
 approximates `toolDeny` with text matching. Native Windows uses PowerShell's built-in
 `ConvertFrom-Json`, so neither external parser is required there.
- **New knobs check:** if `$NS/rules.json` exists, compare the shipped template's
 top-level keys and nested `toolDeny` keys against the same objects in the file (`jq -r 'keys[]'`
 on each, or equivalent Python when jq is absent; on native Windows,
 `(Get-Content -Raw -LiteralPath "$NS\rules.json" | ConvertFrom-Json).PSObject.Properties.Name`
 and `.toolDeny.PSObject.Properties.Name`). Keys the template has that the file lacks mean
 a plugin update brought new knobs — say so once and point at Setup to review them; never add
 them yourself here. A missing native question-tool key must be repaired before an ask tool can
 run. (The hooks read the file live — there is no drift to check and no restart to suggest.)
- **Watchman recovery keys.** When `watchMinutes` is a positive whole number (and
 `NIGHTSHIFT_WATCH` is not `0`), resolve `watchRetrySeconds`, `revivalPrompt`, and
 `freshRevivalPrompt` the same way the watchman does — file plus matching env override,
 expanding the two prompts. If any is empty, refuse to arm and point at Setup to restore the
 shipped template. Doctor reports those keys; Start does not write them. `watchMinutes` `0`
 leaves the watchman disarmed and does not require them.
- The night cannot click Allow. On Claude Code: if neither
 `$TASK_ROOT/.claude/settings.local.json` nor `$TASK_ROOT/.claude/settings.json` grants
 frictionless permissions (`bypassPermissions` default mode or an
 allowlist covering the gates' commands), warn once — a permission prompt mid-shift freezes the
 night, and a headless revival is denied outright; Setup offers the fix. On Codex:
 approvals are per launch — a shift meant to run unattended is started
 `codex -a never -s danger-full-access` — the workspace-write sandbox blocks `git commit`
 (`.git` is protected). A contract that does not commit needs only `workspace-write`; ticks
 alone finish a night. The guards remain the fence either way.
 Warn and proceed; the choice stays the owner's.

## 2. Deadline — read, never asked

The deadline is written when the work is composed, not here.

- `$NS/deadline` already exists (hunt wrote it at the cut, or the owner wrote it by hand):
 use it as is.
- No deadline and the list is entirely **finite** items: correct — their natural end is the last
 tick, and a stuck run is red-flagged in the shift log and held for review.
- No deadline and `## Items` contains an `Ending: open-ended` marker: **refuse to start.** A
 walkthrough with no clock never ends. Say so in one line and point at Hunt, which
 asks for hours; never invent a number. The marker copied from the entry is authoritative; do not
 maintain a hardcoded list of open-ended entry names here.
- One deadline governs the whole shift: finite items first, the walkthrough soaks up the rest.

## 3. Arm the gate

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
session that writes items while planning still stops freely.

Write it only after every preflight check. A marker left behind by a preflight that stopped early
would put the next session on a shift it never started.

### Bind this session — before any other tool

Immediately after writing `$NS/.shift-armed`, make this the next tool
call on either host:

```bash
: nightshift-binding-probe
```

On native Windows, the immediate PowerShell probe is:

```powershell
$null = 'nightshift-binding-probe'
```

This harmless host-shell probe makes the hardhat record this conversation in
`$NS/.shift-session` and claim generation 1 in
`$NS/.shift-lease` before item work or the watchman begins. Its
distinctive marker also
makes a concurrent second Start fail explicitly if another session won the atomic session-file
claim. Do not read files, search, call MCP, or yield between the marker and the probe. Catch-all
tool rules observe those calls, but passive tools cannot make the first session claim; the explicit
probe can. Never create or edit the lease directly. A watchman advances it atomically before
recovery, which fences the older process without restricting unrelated conversations in the
project.

The probe must execute cleanly with no hook denial or hook error. On native Windows this is also
the live check that the filesystem can make an atomic private session claim and lease. If it fails,
remove `$NS/.shift-armed`, run Stop, and use the stale-lease reset
procedure above; do not begin item
work or arm a watchman on an assumed claim.

### Codex identity checkpoint — before the watchman

Codex exposes the current task identity to Nightshift through hook payloads, not as a shell
environment variable. After the binding probe, classify
`$NS/.shift-session` line 1 with
`ns_codex_identity_kind` from `$NIGHTSHIFT_PLUGIN_ROOT/lib/lib.sh` **before arming the watchman or beginning item work**.
On native Windows, call `Get-NSCodexIdentityKind` from the imported PowerShell module instead.

- `resumable` — continue.
- `missing` — continue only with the already-documented fresh-session fallback; say plainly that
 same-thread recovery is unavailable until an identity is recorded.
- `unsupported` or `malformed` — refuse the unattended start. Remove only the markers created by
 this attempted start (`$NS/.shift-armed` and its new
 `$NS/.shift-session`) and reset the lease with
 `ns_lease_reset_stale` in the same Bash call, so no hook call between those operations can
 bootstrap the aborted lease again. On native Windows, `Reset-NSStaleLease "$NS"` with no other command between marker removal and the reset. Append one failed-preflight line to
 `$NS/shift-log.md`, and stop
 before the watchman or item work. Never pass the value to Codex, print it, guess a replacement,
 or start a fresh unrelated task.

This capture-and-check is part of Start, not an owner instruction to remember. An attended session
that does not request an unattended shift remains unaffected.

## 4. Heads-up

Surface any still-unanswered entries in `$NS/parking-lot.md` (read-only) so the owner sees
what the last shift parked — printed, never waited on. Append a `shift started` line to
`$NS/shift-log.md`.

## 5. Arm the night watchman

Each host arms its own; both read their cadence from the rules file, and each stands down on a
shift the other host owns. Unless the rules file's `watchMinutes` is `0` (or
`NIGHTSHIFT_WATCH=0` overrides), arm it in the background.

**Cursor:** arm the Cursor watchman, never the Claude or Codex watchman. Record the Cursor
conversation id in `.shift-session` (host line `cursor`). That id is the origin IDE tab.
Revival mints or resumes a CLI worker in `.shift-worker`; never pass the IDE id to
`agent --resume`. `watchMinutes` `0` still disarms every watchman. Say that plainly once,
then continue to Work.

On Claude Code:

```bash
nohup "$NIGHTSHIFT_PLUGIN_ROOT/runtime/claude/watchman.sh" --project "$NIGHTSHIFT_WORKSPACE" >/dev/null 2>&1 &
```

On Codex:

```bash
nohup "$NIGHTSHIFT_PLUGIN_ROOT/runtime/codex/watchman.sh" --project "$NIGHTSHIFT_WORKSPACE" >/dev/null 2>&1 &
```

On Cursor:

```bash
nohup "$NIGHTSHIFT_PLUGIN_ROOT/runtime/cursor/watchman.sh" --project "$NIGHTSHIFT_WORKSPACE" >/dev/null 2>&1 &
```

On native Windows, start the same bundled PowerShell watchman for the active host:

```powershell
& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\start-watchman.ps1" `
 -Project "$NIGHTSHIFT_WORKSPACE" -HostName claude
# Codex uses: -HostName codex
# Cursor uses: -HostName cursor
```

The Codex identity checkpoint above has already passed before this command is reached. Codex
SessionEnd (reason `other`) is pause-recovery: closing, archiving, or an idle unload stands the
watchman down; Start re-arms; the punch list stays. A crash that never fires SessionEnd still
revives, but only when `$NS/.shift-session` holds a resumable session id (a UUID or a long hex
token). ChatGPT thread/conversation handles, rollout paths, and other non-resumable identities
are refused: the watchman stands down rather than guessing or starting an unrelated conversation.
A missing id (a 500 before the first record) still falls back to a fresh session whose handover
is the punch list. The stop-work order (`$NS/STOP`) is the off switch, on every host.

It revives a session that DIES mid-shift — an API outage, a crash, a killed terminal — by
spawning a fresh session that resumes from the punch list. Both hosts stand down on done, a
stop-work order, or quitting time. Claude Code additionally records clean session ends and Esc;
its watchman stands down for either rather than resuming. Codex SessionEnd is the close signal
above. `STOP` remains the stop-work order on every host, and the only stop a headless run can
receive.

## 6. Work

Begin item 1 and follow the nightshift skill: one item at a time, gate before each commit or artifact receipt, tick only
after the item is complete, park don't ask, leave pushing to the owner unless the punch list says
otherwise. From here the clock-out gate owns the session — it will not let
you stop while any box is open.
