---
name: codex-auto-resume
description: Set up, inspect and control automatic recovery of Codex tasks interrupted by a usage limit or a temporary failure on Windows. Use for requests like enable/disable auto resume, show auto resume status, show pending auto resumes, cancel auto resume for a task, start it at Windows sign-in, or uninstall it.
---

# Codex Auto Resume

Controls a small local watcher that resumes the exact Codex conversation a usage limit
interrupted, once the limit resets. This skill is a front end: every command below calls
the project's own command-line interface, which owns all detection and safety logic.

Windows only.

## Prefer the tools when they are available

This plugin also provides tools (`open_settings`, `get_status`, `list_pending`,
`update_settings`, `restore_default_settings`, `pause_auto_recovery`, `resume_auto_recovery`,
`cancel_recovery`, `disable_conversation_recovery`, `enable_conversation_recovery`,
`reset_recovery_budget`, `start_watcher`, `retry_now`, `postpone_recovery`, `release_hold`,
`get_recovery_statistics`, `get_recovery_timeline`, `clear_recovery_history`,
`preview_recovery_message`, `turn_off_power_action`). When they are
available, use them instead of the commands below: they are typed, they refuse an invalid
value instead of writing it, and `open_settings` shows the user a panel they can read and
change directly.

`preview_recovery_message` shows the exact words the watcher would send for one kind of
interruption, under the current language and style. It saves nothing and sends nothing.
The user's own Custom message text cannot be written from Codex - not through
`update_settings` and not through the preview. If the user wants to change it, tell them it
is edited in the Dashboard, under Settings > Continuation message.

`turn_off_power_action` turns off the power action after usage-limit recoveries (sleep, hibernate
or shut down once they finish), so this PC stays on. Nothing in Codex turns it on: only the
Dashboard does, and if the user asks for it, send them there.

`resume_auto_recovery`, `enable_conversation_recovery`, `update_settings`,
`restore_default_settings`, `cancel_recovery`, `reset_recovery_budget`, `start_watcher`,
`clear_recovery_history` and `release_hold` carry MCP's `destructiveHint` annotation to request
approval.
Codex and its approval settings decide whether to show a prompt; actual host approval
behavior has not been observed for v0.6.0. The annotation is not an authorization lock.
If the user declines one, do not run the matching
command below instead.

Use the commands below when the tools are not available - the plugin's server has not
started, or the user is asking to install, repair or remove the product, which the tools
deliberately cannot do.

## Installing it

**This plugin is not the product.** It carries the skills, the tools and this file; the
parts that do the work are a Windows runtime, a settings window and a background watcher,
which are not in the plugin and cannot be. So the first step is always the setup script,
which downloads the matching release, verifies it and installs it.

Run the plugin's own setup script **by its absolute path**. This file is
`<plugin root>\skills\codex-auto-resume\SKILL.md`, so the script is
`<plugin root>\scripts\bootstrap.ps1` - two directories up from this file, then
`scripts`. Before running it, check that `<plugin root>\.codex-plugin\plugin.json` exists
and names `codex-auto-resume`; if it does not, stop and say the plugin files could not be
found.

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File '<plugin root>\scripts\bootstrap.ps1'
```

Never run it as a relative `scripts/bootstrap.ps1`. The working directory is usually the
user's project, and a project can contain a script of the same name - running that one
with `-ExecutionPolicy Bypass` would run someone else's code in the user's name.

It needs nothing installed first: no Python, no administrator rights, no manual download.
It is safe to run again - that is also the repair path and the upgrade path. Add
`-NoStartup` if the user does not want it to run at Windows sign-in.

The product comes in two editions, standard and advanced, and an installation stays in
its own: the script repairs and updates standard as standard and advanced as advanced.
Change the edition only when the user asks for the other one by name, and say first what
changes. Then add `-Edition Advanced -Force`, or `-Edition Standard -Force` to go back;
the script says what the change means before it downloads anything, keeps their
settings and pending recoveries, and starts every advanced capability off. Never add
`-Edition` on your own, and never together with `-Update`, which refuses it. Never pass
`-Version` either: it installs a pre-release, and a pre-release is installed only when the
user says yes to it in the Dashboard's Check for updates. Never run `-Versions` or `-Pick`:
they are the Dashboard's Install another version..., which shows the user every version,
asks them and passes on only what they confirmed. If the user wants another version or
edition, point them to it on the Diagnostics page.

Tell the user plainly what it is about to do before running it: it downloads this
version's release archive from the project's GitHub releases over HTTPS, checks its
SHA-256, checks the contents are this product at this version, and only then installs,
for their Windows user only and without administrator rights. Besides the files in
`%USERPROFILE%\.codex-auto-resume` it registers the watcher to start at sign-in (unless
`-NoStartup`), a Start Menu entry and a notification sender, an entry in Windows' Apps list and a link handler
for its notification buttons, and this plugin with Codex.

Nothing this project builds is code-signed, so Smart App Control may block its two small
programs, and SmartScreen may warn about a downloaded `Install.cmd`. Say so plainly if it
happens, and do not suggest turning either off.

If they would rather do it themselves, the same archive is on the project's GitHub
releases page and the ZIP contains `Install.cmd`. `Install.cmd` does not check the archive
it came in, so tell them to verify the ZIP before extracting it, as described in
https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/VERIFY.md.
Never state a digest yourself.

If it reports that it could not download, say so and stop. Do not look for another
source for the archive, do not offer a different URL, and do not try to assemble an
installation by hand.

## Running commands

Everything below needs the product to be installed, because it runs through the
interpreter the installer deploys:

```bash
%USERPROFILE%\.codex-auto-resume\runtime\python.exe %USERPROFILE%\.codex-auto-resume\app\scripts\plugin_setup.py <command>
```

If that interpreter is not there, the product is not installed: run the setup script
above instead of looking for another Python. A system Python can run these files, but it
would configure a *second*, lesser installation - a different interpreter, no settings
window, no panel - which is why `setup` refuses to do it.

Commands:

| Request | Command |
| --- | --- |
| Set up / turn on for the first time | the setup script above |
| Set up without Windows sign-in autostart | the setup script above, with `-NoStartup` |
| Turn auto resume on | `enable` |
| Turn auto resume off | `disable` |
| Show status | `status` |
| Show what is waiting to resume | `pending` |
| Stop auto resume for one task | `cancel <thread-uuid>` |
| Stop the background watcher now | `stop` |
| Check the installation | `doctor` |
| Show recent activity | `logs` |
| Turn it off and unregister it (program files stay) | `uninstall` |
| The same, and also delete settings and pending recoveries | `uninstall --purge` |

## Cancelling one task

Two kinds of id, and they are not interchangeable. `cancel_recovery`, `reset_recovery_budget`,
`retry_now` and `get_recovery_timeline` take an `interruption_id`: one interruption's own
64-character hex id, as `list_pending` returns it. `disable_conversation_recovery` and
`enable_conversation_recovery` take a `thread_id`, the conversation's UUID, and so does the
`cancel` command. Never guess either, and never pass one where the other belongs: the wrong
shape is refused outright, and the right shape would act on something the user did not ask
about. `postpone_recovery` and `release_hold` take both, the `interruption_id` and the
`thread_id` from the same `list_pending` entry, and are refused if the two do not belong
together. The `pending` command prints the conversation UUID in full but only the first 16
characters of the interruption id, so take the whole interruption id from `list_pending`.
Never pass `--last`, and never pick "the most recent thread".

1. Run `list_pending`, or `pending`, and read the entries.
2. If the user means "this conversation" and the environment variable `CODEX_SESSION_ID`
   is set and exactly equals one of the listed thread IDs, use that one.
3. Otherwise show the pending entries and ask which one to cancel.

`cancel_recovery` stops one interruption and every continuation of it, and nothing else: the
conversation stays switched on, so a later interruption in it is still recovered.
`disable_conversation_recovery` is what switches a whole conversation off and cancels what it
has waiting, and the `cancel <thread-uuid>` command does the same from the command line. Only
`enable_conversation_recovery` switches one conversation back on again; the `enable` command
here is the global one. In every case a recovery that was never sent is cancelled outright, a
continuation already in Codex's queue is withdrawn when the watcher next checks it, if it is
still queued, and a turn already running in Codex is not stopped. What a cancel stopped stays
stopped. None of this turns off auto resume globally.

## Reporting results

Report what the command actually printed. Useful fields from `status` and `pending`:

- `auto-resume` — whether it is on at all.
- `watcher` — `running` means it is waiting in the background. `not running` means nothing
  will be resumed; offer the `start_watcher` tool, or `enable`, which also starts it but
  switches auto resume back on if the user had paused it. A watcher `start_watcher` starts runs
  inside Codex; where Codex ends what its plugins start, as Codex 26.915 was measured to, it
  stops when Codex closes, if not sooner, and the reply reads that from the job each time. When
  the reply says so (`ends_with_codex`), pass it on with the way out it names: once Codex has
  closed, open Codex Auto Resume from the Start menu and start it there, or turn on Run at
  Windows sign-in in the Dashboard. Not a Dashboard opened from that watcher's own icon: it is
  inside Codex's job too. `unknown` means the check itself could not answer; do not report it
  as running, and offer `doctor`.
- the `status` line on a pending entry — the stable public code, which is what `pending`
  prints there and what `list_pending` returns as `code`. It never depends on a setting, so
  prefer it to `state` when telling the user what is happening.
- `overlays`, on a `list_pending` entry — circumstances that change what a waiting recovery
  will do next: `paused`, `thread_disabled`, `held`, `engine_unavailable`,
  `watcher_not_ticking`, `compatibility_blocked`, `cancel_pending`. A recovery can be waiting
  exactly as it should and still never run because of one of these, so say which. `held` means
  its conversation asks the user first, or only notifies - or its project, or a conversation
  seen for the first time, is set to wait for them: nothing is sent for it until the user lets it
  continue (`release_hold`, or Let it continue on its row in the Dashboard).
- `observe_only` in `get_status` — Observe only is on: every check runs and nothing is sent, and
  a pending entry's `would_send_at` says when it would have been. Say so plainly; never describe a
  recovery as about to resume while it is true. Turning it off is `update_settings` with
  `observe_only` false, which asks the user first.
- `state` on a pending entry — the engine's own name for where that recovery is:
  - `waiting_reset` / `waiting_poll` / `waiting_for_usage` — waiting for the usage limit to
    reset.
  - `waiting_backoff` / `waiting_retry` — a temporary failure; waiting out a short bounded
    delay.
  - `waiting_for_loaded_thread` — the limit has reset, but that conversation is not open
    in the app. Tell the user to open it; the watcher will then resume it.
  - `waiting_for_app` — the ChatGPT/Codex app or its server is not available to the
    watcher, which is also what a Codex-version or lock problem looks like. Tell the user
    to start the app, and offer `doctor` if it is already running.
  - `submitting` / `queued` / `withdrawn_unconfirmed` — the message may already have reached
    Codex. Never describe one of these as safe to send again.
  - `turn_started` / `turn_completed` — the continuation started a turn, and the engine is
    following that exact turn to see how it ends.
  - `recovered` — that turn ran and made progress. This is what a recovery that worked looks
    like, also when the turn then failed, or Codex closed or the PC restarted before it ended.
  - `completed_no_progress` — that turn ran and produced nothing.
  - `handed_over` — a person started or joined that turn, or edited the queued message before
    it ran. This is correct, not a fault.
  - `recovery_turn_failed` — the recovery turn itself failed; a new record continues the same
    chain.
  - `outcome_unverified` — what that turn did could not be established. Not a success; tell
    the user to check that conversation.
  - `resumed` — a v0.5 row. This version never writes it; treat it as delivered but never
    confirmed.
  - `submission_unknown` — the result could not be confirmed, so it will never be resent.
    Tell the user to check that conversation themselves.
  - `superseded_by_user` / `superseded` — a later turn exists in that conversation, so the old
    failure was dropped rather than replayed on top of newer work. This is correct, not a fault.
  - `cancelled` / `stopped_by_user` — someone stopped it. Nothing restarts a cancelled recovery.
  - `failed` / `terminal_failure` — stopped for good.
  - `retry_budget_exhausted` / `no_progress_exhausted` — recovery gave up on purpose, either
    after too many attempts or after repeated attempts that produced nothing. Tell the user to
    look at that conversation first. If they want it to keep trying anyway, `reset_recovery_budget`
    gives that one interruption its attempts back — it sends nothing, and every check runs again
    from the top. It does not switch a conversation back on: if that conversation was switched
    off, the reply says so, and `enable_conversation_recovery` is what turns it on. It works at
    most three times for one task; after that, tell the user to continue that task in Codex
    themselves. Never offer it as a way to "force" a resume.

If a tool or a command refuses with "an older watcher still owns the state", an upgrade is
waiting for the watcher that is running to exit. What still works is pausing and resuming,
switching a conversation off or on, and `get_status`; the rest refuses until that watcher
exits. That is not a fault; the setup notes below say what to do.

`retry_now` brings a waiting recovery's next attempt forward. It is not a send: the watcher still
revalidates the interruption, still needs the conversation open, still waits for usage, and still
refuses anything uncertain. Do not describe it as making a resume happen. It never shortens a
postponement or an objection window that is still ahead; its reply gives that later time.

`postpone_recovery` makes one waiting recovery wait longer - 30 minutes, an hour, three hours,
tomorrow at 09:00, or a number of minutes up to a week - and only ever later. It sends nothing.
Quiet hours, a setting, make any recovery that falls due in them wait until they end.
`release_hold` lets one held recovery continue; it sends nothing either, and every check still
runs. Offer it only when the user asks for that recovery to go ahead. There is no tool that takes a
postponement away again: that is **Don't postpone**, on the task's row menu in the Dashboard or the
notification-area popup, because it brings a send nearer. If the user asks, say where it is. In
`list_pending`, `postponed_until` is the time the user postponed a task to, or null; `not_before`
may also be an objection window's time, which nobody takes away.

From v0.6.11 two more settings can hold a recovery back, both off by default. With
`ask_after_sleep_minutes` set, a recovery that fell due while the PC slept for longer than that waits
for the user, as a held one does (`hold` is `after_sleep`). With `wait_for_network` true, a due
recovery waits while Windows reports no internet connection; its reason is `offline`. Neither sends
anything or makes a recovery sooner. Keeping the PC awake while a task waits is a Dashboard setting,
not one these tools change; `watcher.awake_since` in `get_status` says since when the watcher keeps it
awake, or is null.

From v0.6.11 `get_status` also says, of a watcher that is not running, how it ended:
`watcher.ended` is `unexpected` (it stopped without saying so, in this Windows sign-in, at
`watcher.ended_at`), `memory_guard` (the memory guard stopped it, as the user chose), `clean`, or
null when nothing can be said. Report it as it is, never as a crash you have diagnosed, and offer
`start_watcher`; nothing restarts it on its own. `watcher.memory_peak` is the most memory it has used,
in bytes. The memory guard and the status file for other tools are Dashboard settings, not ones
these tools change.

`get_status` carries a Codex compatibility summary under `watcher.compatibility`, as codes. Its
`overall` is one of `verified` (a real recovery on that exact Codex version confirmed it),
`checked` (the maintainer's own checks passed on that exact version), `structurally_compatible`
(this machine's checks pass and nothing more is claimed), `failed_here`, `incompatible` or
`unknown`. Say what it says and add nothing to it. What other people report about a Codex version,
shown as *Reported by others* on the Dashboard's Diagnostics page, is in nothing these tools
return. If the user asks about it, send them to that page. Never describe other people's reports as verified,
checked or compatible, or as a check made on this machine; if the user quotes the counts, speak
of them only as other people's reports, which change nothing this product does.

From v0.6.11 `get_status` also carries, under `watcher.usage`, Codex's usage as the watcher last read
it: `read_at`, and each window's `bucket`, `window`, `used_percent`, `window_minutes` and
`reset_at` - or null until usage has been read. It is only the last reading, made when a recovery
was due; say how old it is, never present it as current, and never read a count of credits into it.

Do not restate the reset time the Codex usage-limit notice already shows.

## Looking further back

- `get_recovery_statistics` — content-free counts over the last `days` days, or over all of
  it when no `days` is given: how many interruptions were detected, how many continuations
  were sent, how they ended, and the median waits. The success rate appears only once five
  recoveries have ended, and says so until then.
- `get_recovery_timeline` — one interruption and everything that continued it, as codes and
  times. No prompt, no reply and no error text is kept there, so there is nothing to quote
  back from it.
- `list_pending` with `include_finished: true` — finished recoveries as well as waiting ones.
- `clear_recovery_history` — hides finished recoveries from the history view. It deletes
  nothing and cancels nothing, a recovery that may still change stays visible, and hidden
  rows still count for every cap and duplicate check. Nothing brings a hidden row back, and
  it makes nothing run again; do not offer it as a way to retry anything.

## Settings

There are three ways to change a setting, and all three write the same file through the same
validator, so a value set in one is the value the others show:

- `open_settings` — the panel, in this conversation. Best when the user wants to look.
- `update_settings` — one or more named settings. Only the named ones change, and it accepts
  only the settings described below.
- **Start Menu → Codex Auto Resume** — a standalone window that works with Codex closed. It
  has six pages: Overview, Pending, History, Statistics, Diagnostics and Settings. Its
  Diagnostics page is where "Export diagnostics..." lives, which writes a redacted JSON file
  the user can read before sending it anywhere; no tool and none of the commands above do
  that.

Never edit `settings.json` by hand, and never tell the user to. A hand-written file is
validated on read, so a bad value is silently replaced by the default and the user is left
believing they changed something.

What `update_settings` can change: which classified failure categories are recovered, how many
attempts each interruption gets, how many continuations one task gets in total (six by default,
one to ten), when to stop after repeated no-progress recoveries, the retry timing (a preset, or
Custom with its five waits and optional jitter - the watcher still sends to one conversation at most
every 15 minutes and five times a day, whatever is chosen), a time after which a task that keeps
failing stops, the task-changed and context-cost guards (off by default; each only holds a recovery
for the user or adds a line to its notification, and never sends anything sooner), which
notifications appear, the interface language, the theme (light, dark, or following the system), the
panel's own theme in Codex (`panel_theme`: the same as the theme, Codex's, light or dark), the
continuation language, the message style
(Minimal, Standard, Detailed or Custom), and whether
a Custom message is one message for every
interruption or one per kind. From v0.6.11 a setting chosen from a list also takes a value of the
user's own in the same words, within the range its schema description gives - quiet hours at any
minute (`13:15`) and on any days (`mon,wed,fri`), a custom wait, the time ceiling, the stall or the
sleep as `m45` or `h36`, the context-cost limit as `above_300k` - and a value past that range is
refused; never offer one past it or say a safety limit can be lifted. The window has things
`update_settings` does not offer: the
notification-area icon, Reduce motion (the one way to stop the animations), the Design (Soft, Classic
or Plain), the notification card, and, from v0.6.11, Keep this PC awake while a task waits (and for how
many hours at most), the memory guard (and its limit), and the status file for other tools - each a
question of this PC rather than of recovery - and, from v0.6.16, which notifications stay on screen until
clicked, and the Custom message text itself.
If the user asks for any of them, say it is changed in the Dashboard, under Settings. If the user wants to
change what a Custom message says, tell them it is written in the Dashboard, under Settings >
Continuation message. A message for one conversation alone (`custom_message_by_thread`, from v0.6.11)
is written from that conversation's row in the Dashboard's Pending page, **Message for this
conversation...**, and nowhere else; do not try to set it.

What cannot, and is not an oversight: there is no setting that retries an unclassified failure,
resolves a conversation by title, resends an uncertain submission, or forces a send. If the user
asks for one, say plainly that it does not exist by design and do not look for a way around it.

## Notifications

Windows notifications cover the lifecycle: an interruption is detected, recovery starts, how it
turned out, and when recovery stops for good. The first one carries a **Don't resume** button
(**Don't retry** for a temporary failure) and an **Open Dashboard** button, which only opens the
Dashboard's Pending page; doing nothing resumes, which is the default. Each event has its own
switch, and there is a master switch for all of them.

Turning notifications off changes nothing about whether a task is recovered - say so, because
people reasonably assume otherwise.

From v0.6.11 there is one more, off by default: *When a conversation needs you*. It tells the user,
once, of a failure this product never resumes - the request was refused or the conversation is too
long, a content policy stopped the turn, Codex needs a new sign-in, or Codex gave up - and, if a time
is chosen for it, of a turn that has recorded nothing new for that long. Its one button, **Open
Dashboard**, opens the Settings page, where each kind is switched off. It never resumes, sends or
records anything. A turn that has not moved may simply still be working: never say it is waiting
for an approval.

While the watcher runs there is an icon in the notification area. It belongs to the watcher
process, so it cannot show a watcher that is not there. Hovering over it says whether recovery
is paused, how many recoveries are waiting and how many are running in Codex, and how long
until the next check - which is when the watcher looks again, not when anything is sent. A
single click opens a small popup beside it with the same state, the next check, up to three
waiting tasks - each with a switch that turns automatic recovery off or on for that
task's conversation, refused if the task has since finished or changed - Pause or Resume, and
Open Dashboard. Its right-click menu opens the Dashboard, pauses or resumes recovery, and stops
the watcher. Nothing in the popup or the menu sends a continuation. It is on by default and can
be switched off on the Dashboard's Settings page.

Do not offer to build any other interface. There is no checkbox inside the Codex usage-limit
notice and none can be added through the Codex plugin API; see
https://github.com/songyb111-gachon/codex-auto-resume-windows/blob/main/docs/PLUGIN.md if asked
why.

## What it does and does not do

- Recovers a **usage limit**, and failures it can positively classify as temporary from the
  error code Codex records: connection failures, rate limits, server errors and overloads, and
  stream disconnections. A code this product does not list is still classified from the HTTP
  status the record carries, if it carries one: 429 as a rate limit, 408 and 425 as a timeout,
  500 to 599 as a server error - all retried - and any other 4xx as permanent. Only when Codex
  recorded no error information at all does it match a short list of transport-failure phrases.
  A code it does not list that carries no status counts as unknown and is not retried.
- It is **not** a general retry tool. User cancellation, permission, approval, policy, invalid
  requests, context-length errors and permanent authentication failures are never retried — and
  neither is any failure it cannot classify. If asked to "retry everything", explain that
  unknown failures are deliberately left alone, and do not try to work around it.
- Resumes only the **exact** interrupted conversation.
- Sends nothing while any part of the situation is uncertain. It prefers missing a resume
  over resuming twice.
- The conversation must be **open in the Codex app** at reset time. If it is not, the entry
  waits at `waiting_for_loaded_thread` until the user opens it. This is a real limitation;
  state it plainly rather than promising fully unattended recovery.
- Its own code opens Codex's databases and files read-only and never reads credentials.
  What changes in Codex, Codex makes itself when asked: its command-line queue adds the
  continuation to that one conversation, and its App Server withdraws that same message
  when it has to.
- Its own runtime has no network code and no telemetry. It never checks for updates on its
  own: the Diagnostics page has a button that asks GitHub which release is newest and reads
  this repository's list of releases on api.github.com for a newer pre-release, and those
  requests happen only when a person presses it; Install another version... on the same page
  reads that whole list there only when a person opens it and confirms a version. The setup script
  downloads the release from GitHub. The Codex processes it starts use the user's existing
  sign-in to check usage, and the resumed turn goes to OpenAI like any turn the user starts.
  What these tools and commands return becomes part of this conversation.

## Setup notes

- The setup script is safe to run again; it does not reset existing settings or lose
  pending entries. Run again when the user asks to repair or update it: if the installed
  version already matches this plugin it re-checks the registration rather than
  downloading anything.
- An upgrade asks the running watcher to stop and waits up to a minute; it never ends it by
  force. If setup says the previous watcher is still running, it will exit when it finishes
  what it is doing; then `start_watcher` starts the new version. Do not end the process
  yourself.
- There is one installation, in `%USERPROFILE%\.codex-auto-resume`, and everything points
  at it: the watcher, the sign-in entry, the notification buttons, the settings window,
  this plugin's tools and the command line. If the user has two, that is a fault worth
  reporting, not a configuration.
- If setup reports that another auto-resume installation is already registered to start at
  sign-in, do not force it. Two watchers could resume the same task twice. Tell the user to
  remove the other installation first.
- The watcher keeps running after the Codex app is closed, and starts again at Windows
  sign-in once `setup` has registered it.
- No Codex restart is needed for these commands to take effect. Only say a restart is
  required if Codex itself reports that a newly installed plugin is not active yet.

## Removing it

`codex plugin remove` removes this skill but does not stop a watcher that is already
running, does not remove the `codex-auto-resume-windows` marketplace the setup script
registered, and does not remove the installation the setup script made.

To remove everything, in this order:

1. `uninstall` - stops the watcher, then removes the Windows registrations that belong to
   this installation (sign-in entry, notification sender, Start Menu entry). If it cannot
   confirm the watcher stopped it removes nothing and says so; report that and stop. It also
   deletes its logs. Add `--purge` to delete settings and pending recoveries too; without it
   they are kept so a later setup picks them up.
2. `codex plugin remove codex-auto-resume@codex-auto-resume-windows` - takes away this skill.
3. Run `codex plugin marketplace list --json`. If `codex-auto-resume-windows` is listed and its
   `root` is inside the installation folder, remove it with
   `codex plugin marketplace remove codex-auto-resume-windows`. If it points anywhere else,
   leave it and tell the user where it points.
4. Tell the user to delete `%USERPROFILE%\.codex-auto-resume`, which still holds the
   application, the bundled Python and the settings window. If Windows reports a file in use,
   Codex or the Dashboard still has it open: close both and try again. Do not delete it
   for them without asking - if they skipped `--purge` it also holds their pending recoveries.

Say which of the four you did. "Removed completely" is only true after all four.
