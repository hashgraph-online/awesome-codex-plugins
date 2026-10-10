<h1 align="center">The Skill and the Plugin</h1>

---

<p align="center">Two ways to have your agent check a page it just wrote.
<strong><a href="../../docs/harnesses.md">Install steps for fifteen harnesses →</a></strong></p>

---

## Contents

- [The Skill](#the-skill)
- [The Plugin](#the-plugin)
- [Reporting, Not Fixing](#reporting-not-fixing)

---

## The Skill

The skill works in all fifteen supported harnesses.
[`skills/checking-a-page/SKILL.md`](skills/checking-a-page/SKILL.md) tells the
agent to run this after finishing a page:

```bash
assay <the page> --one-line
```

and to end its reply with the output, word for word:

```
assay: checked todo/todo.html, 8 checks, nothing flagged.
```

or, when something is wrong:

```
assay: checked notes/index.html, 12 checks, 4 flagged:
  - press Clear all: the page threw an error and stopped running, Cannot set properties of null (setting 'innerHTML')
  - press Clear all twice (same finding as press Clear all)
  - press Add, then Clear all (same finding as press Clear all)
  - press Clear all, then Add (same finding as press Clear all)
```

Those four lines are one bug. The repeats name the first finding instead of
repeating its message. The agent copies assay's output rather than
summarising it, so the numbers and wording stay exact. With the skill alone,
the agent decides when to run the check.

---

## The Plugin

The plugin adds a `Stop` hook, which runs the check at the end of every turn
that changed a page. In Claude Code it installs the skill and the hook
together. The DeepSeek Harness uses the hook on its own, through its Claude
Code bridge.

- **Which pages it checks.** A change to any web file marks the page in the
  same folder, so editing `app.js` counts. In each folder it checks the most
  recently changed `.html` file, preferring `index.html` on a tie.
- **How far it looks.** It searches at most four folders deep, skips
  `node_modules` and `.git`, only considers files changed since its last run,
  and checks at most three pages per turn.
- **It always reports** when it checks a page, so a clean result can't be
  mistaken for assay not running. A turn that changed no page reports
  nothing.
- **It keeps the turn open** so you see the result, and never does this twice
  in a row. It checks the harness's `stop_hook_active` flag and writes a
  timestamp (in the harness's scratch folder, else `.git/`, else a
  `.assay-last-run` file). If it can't write the timestamp, it reports
  without keeping the turn open.

---

## Reporting, Not Fixing

The agent shows you what assay found and doesn't change code because of it
unless you ask. assay doesn't know what the page is for, so a finding is a
place to look, not a confirmed bug. A control can correctly do nothing in the
state it was pressed in, and a value can be limited on purpose. Ask the agent
to fix something and it will.
