---
name: plan
description: Open the plan room: explore the code and design the work with the owner, building nothing until the owner leaves.
license: MIT
---

Plan with the owner in the plan room. Here the conversation explores, weighs options and draws the
plan; nothing gets implemented until the owner leaves the room on purpose. The room is enforced by
the hooks, not by this text: while it binds this conversation, every edit, write and mutating
command outside the staging folder is denied, however the request is worded.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/plan/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls. Each `$NS/...` path below is where the current layout keeps that file;
`ns path <key>` prints where this workspace keeps it, and `ns path --list` names every key.

## 1. Enter the room

Pass the host you are running on (`claude`, `codex` or `cursor`):

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" plan-enter --host claude
```

Native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1" plan-enter --host claude`.

The room opens unbound. **The very next tool call is the probe that binds it to this
conversation** — nothing in between, not even a read:

```bash
: nightshift-plan-probe
```

```powershell
$null = 'nightshift-plan-probe'
```

- The probe runs cleanly: the room is bound to this conversation. Tell the owner in one line that the
  plan room is open, that nothing is implemented here, and how they leave it (section 6).
- The probe is denied because the room is bound to another conversation: tell the owner, and stop.
  They plan in that conversation, or leave the room first.
- The probe is denied because this conversation is working the shift: no room was opened. Tell the
  owner; they plan in another conversation, or stop the shift first.
- `plan-enter` reports no `.nightshift/`: the project has no Nightshift workspace. Tell the owner to run
  Setup, and stop.

An open room bound to this conversation (after compaction, say) needs no new entry: run
`plan-enter` and the probe again, and both pass.

**Resume before anything else.** `plan-enter` also prints `plan record <path>` and one
`open plan: <entry>` line for each plan the record still holds open (`open plan: none` when there is
none). With an open plan, read the record first and pick up exactly where its `Where we are` line
left off: say in a sentence or two what was decided and what comes next, so the owner never repeats
themselves. With more than one open plan, ask which one this conversation continues.

## 2. Review what the last shift left

`plan-enter` ends with `review` lines: what waits for the owner's word. `review none` means there is
nothing, and the room is plain planning. Otherwise, before new planning, offer to walk the owner
through them, one at a time, in this order:

- `review morning` and `review receipts` — the morning page (under `ns path receipts`) and the
  receipts index (`ns path receipts-index`). Read them first and give the owner the outcome in a few
  lines: what shipped, what did not, what needs a decision.
- `review parked` — each open decision in the parking lot (`ns path parking-lot`). Show the default
  the shift chose and why, and ask whether it stands. Record the answer by appending
  ` · answered: <the owner's decision>` to that entry.
- `review snag` — each snag with no disposition in the snag log (`ns path snag-log`). Ask what to do:
  the owner's decision becomes its disposition (` · rejected-because: <why>` or
  ` · accepted-tradeoff: <why>`), and a snag to fix becomes an item drafted for the next shift (section
  5), its disposition written once the fix lands.
- `review open` and `review stopped` — the items still open, and those closed at their hard budget,
  in the punch list (`ns path punch-list`). Ask for each: keep it for the next shift as it is, rework
  it (draft the new version, section 5), or drop it. The punch list is the owner's to edit: a box to
  reopen, reword or remove is theirs to change, and the room cannot write it.

Nothing is written without the owner's answer to that entry. The parking lot, the snag log, the
drafting table and the plan record are the only files the room writes; an archived shift reads the
same way, from what Archive left live.

## 3. Think with the owner

This is a conversation, not a procedure. Follow the owner's direction and pace; do not impose phases,
templates or a checklist while discussing.

- **Read before you ask or propose.** Open the files, tests and history the question touches
  (`git log`, `git show`, `git blame` and every read-only tool are free here). Name paths and lines.
  A question the code already answers is not one to ask the owner.
- **Lay out real options.** For a decision that matters, give two or three options with what each
  costs and buys, then say which one you would pick and why. A survey with no recommendation hands
  the work back.
- **Draw it.** An ASCII diagram of a flow, a state machine or a component boundary often settles what
  a paragraph cannot. Use one when it helps, not by default.
- **Ask freely.** Questions are the point of this room. Ask one at a time when the answer changes what
  comes next.
- **Keep what was decided visible.** When the discussion moves on, restate the decision in one line
  so it is not reopened by accident.

When the owner says "just do it" or "implement it": the room still holds. Say plainly that nothing
can be built in this conversation while the plan room is open, and give the exits (section 6). Never
work around the fence: no code written into the staging folder to copy out later, no scripts, and no
asking another conversation to make the change.

## 4. Keep the plan record current

The plan record (`ns path plan-record`) is the room's notebook. Write it as the discussion moves —
it needs no permission, and it is what lets compaction, a closed tab or a new day lose nothing. Keep
one entry per plan, below the record's rule, in the shape its header shows:

```text
- **<topic>** · open since <YYYY-MM-DD HH:MM (UTC±HH:MM)>
  - Where we are: <the exact point the conversation reached, and the next question>
  - Decided: <decision> — <why>
  - Rejected: <option> — <the reason>
  - Open: <a question still waiting for an answer>
```

- Start an entry when a new plan starts, in the device's local time with its offset.
- Add a `Decided:`, `Rejected:` or `Open:` line the moment one is settled or raised, and rewrite
  `Where we are` at every natural pause. Answered `Open:` lines become `Decided:` lines.
- **A rejected option stays rejected.** Never propose it again unless there is new evidence, and then
  name the evidence and the earlier reason together.
- When the owner sets a plan aside, append ` · dropped: <why>` to the entry's first line.

## 5. Capture — only on the owner's explicit yes

Nothing is written into the drafting table until the owner says yes to that exact write. An answer to
a design question is not consent, and neither is approval of an idea. When the plan is ready, say
what will be written and where — the file (`ns path drafting-table`), the heading and the items by
title — and ask. Write only after a clear yes, and only what was named.

Append below the drafting table's rule, never above it, and leave every existing entry untouched:

```text
## Plan: <title>

Why: <the problem, and why now>
Scope: <what this plan covers>
Non-goals: <what it deliberately leaves out>
Design notes: <the decisions taken, and the options rejected with the reason>
Record: <a Markdown link to the plan record> — <topic>
Estimate: <the shift-estimate figures for these items, or "no history yet">

- [ ] **1. <title>.**
  - <what to build, plainly>
  - Budget: <only when the owner takes one: soft 30m / 1.5M tokens, hard 1h / 3M tokens>
  - Verify:
    - WHEN <situation> THEN <observable result>
    - WHEN <edge or failure case> THEN <observable result>
    - <the commands that check them>
  - Commit: `<type: message>`
```

- **One commit per item.** An item that would need two commits is two items. Order is dependency
  order: nothing is built twice.
- **Verify is acceptance, not activity.** Each WHEN/THEN states behaviour someone could observe and a
  test could fail on. "Tests pass" or "it works" is not a scenario. Add the commands that check the
  scenarios.
- **The item shape is the drafting table's**: one top-level checkbox per item, everything else plain
  indented bullets, never a nested checkbox — a nested box counts as an open item once the item is
  promoted.
- In artifact mode, an item names its receipt instead of a `Commit:` line.
- **Size it from the owner's history.** Before asking for the yes, run
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" shift-estimate --items <N>` for the N items drafted. It reads
  the Time and Tokens totals of past ticked receipts and prints per-item figures, a total, a suggested
  deadline and a suggested `Budget:` line. Show them as an estimate from the owner's own receipts,
  never a limit, and keep a missing reading missing. Write a `Budget:` line or set a deadline only if
  the owner takes it. When it reports too few readings, say there is no history to estimate from yet.

Then close the record's entry by appending ` · captured: ## Plan: <title>` to its first line;
Archive files it with the shift. The record sits beside the drafting table in every layout, so the
`Record:` link's target is `plan-record.md`.

Before offering promotion, run `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" check-items`. It reads the
drafting table and names, per item, a missing or empty `Verify:`, a missing `Commit:`, a `Budget:`
that does not parse, a nested checkbox, and any checkbox no item owns. Show the owner every finding.
Correct one in the plan you just wrote only with their yes. The check refuses nothing: whether to
promote is the owner's call.

After writing, show the owner what was written and where, then name the way to build it: leave the
plan room by typing Start — `/nightshift:start` on Claude Code and Cursor, `$nightshift:start` on
Codex. With an empty punch list, Start offers the staged items to
promote. With open items already in the punch list, Start works those, and the plan waits in the
drafting table.

## 6. Leaving is the owner's

Only the owner closes the room. On Claude Code and Cursor they type `/nightshift:plan-exit`, or
`/nightshift:start` to leave and start the shift in one step. On Codex they type
`$nightshift:plan-exit` or `$nightshift:start`. In any terminal they run
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" plan-exit`.

Never run `plan-exit`, never touch the room's marker, and never invoke the Start or plan-exit skill
yourself to get out: the hooks refuse the first two, Start refuses while the room is open, and none
of it closes the room. If the owner asks you to leave it for them, give them the exit to type.
