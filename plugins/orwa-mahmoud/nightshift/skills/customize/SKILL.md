---
name: customize
description: Show every setting, template and catalog entry on one screen, and change only what the owner names.
license: MIT
metadata:
  internal: true
---

Show the owner everything they can customise in the host-opened project, on one screen, and change
only what they name. This skill is a convenience, never a gate: editing `$NS/rules.json` or a
template by hand, or asking for a change in plain words in an ordinary conversation, works exactly
the same. Say so once, at the top of the screen.

Resolve the installed plugin root to an absolute `$NIGHTSHIFT_PLUGIN_ROOT` — `${CLAUDE_PLUGIN_ROOT}`
on Claude Code, `$PLUGIN_ROOT` on Codex when set, otherwise the absolute path this skill was
attached from (`skills/customize/SKILL.md`). Run every command below through
`"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns"` — native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\ns.ps1"`
in the PowerShell tool, same verbs — which resolves the host and the workspace; `ns help` lists the
verbs, and `ns bind` prints the six resolved facts (`TASK_ROOT`, `NIGHTSHIFT_WORKSPACE`, `NS`,
`NIGHTSHIFT_PLUGIN_ROOT`, `HOST`, `SOURCE`); `$NS` below is that `NS`. Never a bare relative path: the working
directory persists between calls. Each `$NS/...` path below is where the current layout keeps that file;
`ns path <key>` prints where this workspace keeps it, and `ns path --list` names every key.

If `$NS/` does not exist yet, run Setup's flow (`skills/setup/SKILL.md`) first, then come back.

## 1. Read what is in force

```bash
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" shift-policy resolve --table
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" catalog-index --catalog shifts
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" catalog-index --catalog evidence
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" catalog-index --catalog gates
"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" catalog-index --catalog edge-cases
```

The resolved table gives every setting with its value and where it came from (`built-in`,
`rules`, or tonight's policy). The shipped value of each is in
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/nightshift-rules-template.json`, and the
schema beside it (`nightshift-rules.schema.json`) says what each one means. The four catalog
listings name each entry's source; an entry whose source is not `plugin` is the owner's.

## 2. Show one screen

One grouped list. Each line carries the current value, the shipped value when it differs, and one
line of meaning. Nothing is asked line by line.

- **Guards** — `forbiddenCommands`, `protectedDirs`, `neverCommitPatterns`, `expectedEmail`,
  `toolDeny`, and the five `elevation` categories (all allowed when shipped).
- **Recovery and watching** — `recovery.launchScope`, `recovery.cursorFlags`, `watchMinutes`,
  `idleWindowMinutes`, `stallMax`, `notifyCommand`.
- **Shift defaults** — the `shift` block: verification profile, typical hours, execution, tooling
  policy, worktree isolation, prepare command, copy-in files, item budget.
- **Evidence** — `receipts.evidence`: default, file map, architecture, check, unavailable, review.
- **Receipts, handoff and archive** — the `receipts`, `handoff` and `archive` blocks, including
  each `templatePath`: the owner's own receipt, morning-page and archive templates.
- **Retention** — `retention.runtimeLogDays`, `retention.archiveDays`.
- **Catalogs** — for each of shifts, evidence kinds, gate stacks and edge-case packs: the owner's
  entries and what each replaces, `catalogs.<catalog>.paths`, and the template in force
  (`ns catalog-index --catalog <catalog> --template`).
- **Profiles** — the shipped examples in
  `$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/profiles/`, any one of which can fill in
  or replace the shift defaults.

The owner names what to change ("deny sudo, 6 hours, my own receipt template") or asks what a line
does. Answer a question from the schema description; never invent a meaning.

## 3. Change only what the owner named

**Refuse while a shift is armed** (`$NS/run/.shift-armed` exists, as `ns path armed` prints): the
night is held to the settings it started with. Say so, and name what to change once it ends.

Write through the existing helpers, and nothing else:

- **Shift defaults** — `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" shift-policy defaults-set` with only
  the fields the owner named.
- **A profile** — `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" apply-profile --profile <name> --mode fill|replace`
  previews; apply with `--apply` only after the owner says yes.
- **A new catalog entry or template** — `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/ns" catalog-new --catalog <catalog> --key <key>`
  (`--user` for every project) starts one from the template in force; show the file, fill it with
  the owner, and check it with `ns catalog-index --catalog <catalog> --check-draft <file>`. An owner
  template is a file the owner keeps anywhere in the workspace; set its path in
  `catalogs.<catalog>.template`, `receipts.templatePath`, `handoff.templatePath` or
  `archive.templatePath`.
- **Any other setting** — keep a copy of `$NS/rules.json`, then edit it in the skill, changing
  only the keys the owner named and keeping every other value byte for byte.

Show each change as it stands afterwards, from `ns shift-policy resolve --table`. That command is
also the check: exit 5 means the runtime cannot load the edited file, and its message says why.
Put the copy back, tell the owner what failed, and never leave a half-applied file. Ask nothing
twice: one round of changes, then the result.
