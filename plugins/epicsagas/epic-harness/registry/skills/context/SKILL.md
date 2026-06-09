---
name: context
description: "Context window manager. Trigger: context >70% or large new task. Snapshots state, compacts, resumes via hook."
---

# Context — Context Window Management

## When to Trigger
- Context window > 70% capacity
- Long conversation with many tool calls
- Before starting a large new task in an existing session
- User asks to "clean up" or "start fresh"

## Process

### 1. Assess
- Estimate current context usage
- Identify what's consuming the most context (large file reads, verbose outputs)

### 2. Preserve
Before compacting, ensure critical state is saved:
- Current task and progress → `$HARNESS_DIR/sessions/`
- Key decisions made → note in conversation
- Files being worked on → list explicitly

### 3. Compact
Suggest or trigger compaction with a clear summary:
```
Summary for compaction:
- Working on: [task description]
- Files modified: [list]
- Current status: [what's done, what remains]
- Key decisions: [important choices made]
- Next step: [what to do after compaction]
```

### 4. Resume
After compaction, the `resume` hook will reload:
- Session snapshot from `$HARNESS_DIR/sessions/`
- Project memory from `$HARNESS_DIR/memory/`
- Evolved skills from `$HARNESS_DIR/evolved/`

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "I still have context left" | Quality degrades well before the hard limit. 70% is the trigger. | Compact proactively. Better to lose 5 min than lose coherence. |
| "Compacting will lose important context" | That's why you preserve first. The resume hook restores it. | Save state → compact → resume loads snapshot + memory + skills. |
| "I'll just re-read the files" | Re-reading 5 large files wastes 30%+ of your fresh context. | Summarize key facts before compacting. Read only what you need after. |

## Evidence Required

Before compacting, confirm ALL of these:

- [ ] Current task and progress noted in summary
- [ ] Files being worked on listed explicitly
- [ ] Key decisions recorded (not just "some decisions were made")
- [ ] Next step specified clearly
- [ ] Snapshot written to `$HARNESS_DIR/sessions/` (show file name)

**Compacting without a summary = guaranteed context loss.**

## Red Flags
- Continuing with 90%+ context without compacting (quality degrades)
- Compacting without saving state (lose track of progress)
- Re-reading large files after compaction (defeats the purpose)
