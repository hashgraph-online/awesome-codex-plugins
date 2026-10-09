---
name: plan-exit
description: Leave the plan room and name the next step toward building what was planned.
disable-model-invocation: true
license: MIT
---

The owner typed this command to leave the plan room. Typing it is what closes the room: the host's
prompt hook removes the room's marker before this skill runs. This skill removes nothing. It reports
whether the room is closed and what comes next.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/plan-exit/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls. Each `$NS/...` path below is where the current layout keeps that file;
`ns path <key>` prints where this workspace keeps it, and `ns path --list` names every key.

## 1. Check the room

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" status
```

- **No `Plan room:` line** — the room is closed. Tell the owner in one line that the plan room is
  closed and this conversation can build again.
- **A `Plan room:   open` line** — the command did not reach the host's prompt hook, so the room is
  still open. On Codex the hook runs only after it has been reviewed and trusted. Tell the owner the
  room is still open and give them the terminal exit to run themselves:
  `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" plan-exit` (native Windows:
  `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1" plan-exit`), with the plugin root written out in
  full. Never run it yourself: the hooks refuse it, and the exit is the owner's.

## 2. Name the next step

Read it off the same status output: the `Items:` line (`open=N`) and the `staged` fact
(`drafts=N`). Do not count boxes yourself.

- Drafts staged and no open items: the next step is Start — `/nightshift:start` on Claude Code
  and Cursor, `$nightshift:start` on Codex. Start offers the staged items to promote and begins the
  shift.
- Drafts staged and open items already in the punch list: Start works those first. The owner can
  move the planned items into the punch list themselves before starting.
- No drafts staged: say so. The discussion stays in this conversation, and nothing was staged.

Begin no work in this skill. Building starts when the owner asks for it or starts a shift.
