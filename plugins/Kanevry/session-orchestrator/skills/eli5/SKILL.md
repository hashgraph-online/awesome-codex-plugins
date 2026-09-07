---
name: eli5
description: Explain a topic like I'm a 5 year old — restate my last output, or a named topic, in plain words without dropping a single fact. Use when the user types /eli5 [topic], or says an answer was too technical, too long, or unclear about what he now has to do.
model: inherit
tools: Read, Grep, Glob, Bash
---

# eli5

Say it again in plain words. Same facts, in the order he needs them.

## The frame

**Write for someone who knows this project but has not seen what you just saw.**

He owns this repo. He is not missing knowledge, he is missing observation — he did not watch the command run or read the file it points at. Write across, not down. `.claude/rules/ask-via-tool.md` § AUQ-006 and `skills/session-start/soul.md` § Register are the canonical statement of this register; apply them, do not restate them.

## What to restate

- `/eli5` — my last substantial output in this conversation. If there is none yet, say so instead of inventing a topic.
- `/eli5 <topic>` — that topic (`$ARGUMENTS`), grounded in what THIS session already measured: name the file, command, or record it came from. If it was never measured here, say that rather than filling the gap from memory.

Answer in the operator's language: `owner.language` in `~/.config/session-orchestrator/owner.yaml`, falling back to `en` when that file is missing, unreadable, or the key is absent — and follow the operator's own language the moment he writes in another one.

## Two limits, and they are the whole skill

**1. Say more simply what actually happens — introduce nothing that does not exist.**
Test: delete every noun the system does not contain. Sentence still true and complete → it was no analogy. Sentence collapses → describe what actually happens instead.
✓ "Waiting means the other session finishes first." ✗ "Think of the session as a level crossing."

**2. Simplifying removes words, never facts.** If a path, a number, an error code, an identifier, or an instruction to act disappears, that is data loss, not simplification. The mechanical decider: **could the token you are about to cut ever appear in a `grep`? Then it stays.** `skills/session-start/soul.md` § "Never traded for brevity" outranks every brevity instruction in this file.

## Shape

Line 1 answers the question he actually has: **do I have to do something now, and what happens if I don't?** Then the facts, in the order he needs them — not the order you found them.

This is a terminal, so there is no picture to draw. The second channel is the `preview` field on an `AskUserQuestion` option: when the options differ in something literal — a diff, a title, a config block, a file list — put that text there and he reads the thing instead of a description of it.

## What this is not

- **Not shorter by default.** Eight lines before may be eight lines after. Reorder first; cut only filler.
- **Not a children's explanation.** The label is a poster, the reader is an expert who was not in the room.
- **Not a second attempt at the answer.** If the first answer was wrong, fix the answer — `/eli5` restates, it never re-derives.
