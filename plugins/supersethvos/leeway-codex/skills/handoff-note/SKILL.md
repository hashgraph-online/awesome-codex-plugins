---
name: handoff-note
description: Leave a short hand-off note on the Leeway drive at the end of a piece of work, so the next person or agent can pick it up. Use when finishing work in a Leeway folder, or when asked to hand off, leave a note, or write up what was done.
---

# Leave a hand-off note

When you finish work in a Leeway folder, leave a note in that folder so a person, or the next agent on another computer, can carry on without asking you.

## Write it

Put it at `HANDOFF.md` in the folder you worked in.

- If there is none, `write_file` with `if_none_match: "*"`.
- If there is one, `read_file` it and keep its `rev`. Add your note at the top under a dated heading, keeping what was there, and `write_file` with `if_match` set to that rev (see save-to-drive for conflicts).

Keep it under a page:

```markdown
## 2026-11-11 · Codex

**Done:** what changed, by path.
**Why:** the request, in one line.
**Left to do:** anything unfinished, and anything you weren't sure of.
**To undo:** the version_id, deleted_id or workspace id that brings things back.
```

Only facts about the work. No secrets, tokens or links that grant access.

## Make it stick

Call `sync` with the folder's changed paths and the note, so everything is safe in storage before you say you're done. Then tell the person where the note is.
