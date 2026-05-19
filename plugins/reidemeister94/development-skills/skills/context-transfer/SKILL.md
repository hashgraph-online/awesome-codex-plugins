---
name: context-transfer
description: Use when user asks to transfer session context to a new chat, summarize current state for a handoff, hand off work, or runs /context-transfer. Produces a structured handoff document (summary, decisions, gotchas, relevant files, current state, ready-to-paste prompt).
disable-model-invocation: true
---

# Context Transfer

Produce a handoff document in a .md file that a fresh agent session can pick up from without re-investigating. Template below. Fill every section; if a section is empty, write "None" rather than deleting it.

### Summary
[What was accomplished in this session]

### Key Decisions
- [Decision 1 and why]
- [Decision 2 and why]

### Important Context
- [Gotchas discovered]
- [Patterns to follow]
- [Things that didn't work]

### Relevant Files
- path/to/file.py - [what it does, why it matters]
- path/to/other.py - [description]

### Current State
[What's working, what's broken, what's next]

### Prompt for New Chat
[Ready-to-paste prompt with all necessary context to continue]
