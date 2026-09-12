---
name: context
description: "Working-state snapshot guidance. Restates task/files/decisions in one block so state survives context compaction. Compaction timing is the host's job."
---

# Context — Working-State Snapshot

Compaction timing belongs to the host (native auto-compaction; the harness
already snapshots state on the PreCompact hook). This skill is about WHAT
survives, not WHEN to compact.

## Process

Before or during compaction, restate the working state in one block:

```
- Working on: [task description]
- Files modified: [explicit list]
- Status: [what's done, what remains]
- Key decisions: [important choices made, with why]
- Next step: [what to do after compaction]
```

Keep it terse — this block is what you (and the `resume` hook) reload after
compaction. Re-reading large files afterwards costs more than summarizing the
key facts beforehand.

## Evidence Required

- [ ] Task, files, decisions, and next step all present in the summary block
- [ ] Snapshot written by the PreCompact hook (show file name if asked)
