---
name: agent-memory-discipline
description: "Teaches when to recall from long-term memory before acting and when to save durable decisions, corrections and failures afterwards. Use when a memory tool or MCP memory server is connected but the agent is not using it consistently, when the user complains that the assistant forgets preferences, conventions or past decisions between sessions, or when setting up persistent memory for a project. Works with any memory backend: a folder of Markdown files, a local MCP server, or a managed service. Trigger with \"remember this\", \"what did we decide\", \"recall\", or \"save this for next time\"."
allowed-tools: Read, Write
argument-hint: "[optional topic to recall or decision to save]"
version: 1.1.0
author: Mnemoverse <hello@mnemoverse.com>
license: CC0-1.0
compatibility: Designed for Claude Code
tags: [agent-memory, long-term-memory, context-engineering, mcp, agent-skills]
---

# Agent memory discipline

## Overview

Connecting a memory tool does not make an agent use it: tools register, the session runs, and nothing gets recalled or saved. This skill supplies the missing part, standing rules for when to read memory and when to write it.

The problem it solves is specific. An agent with memory available still repeats settled questions, reverts corrected habits, and loses decisions between sessions, because nothing tells it when recall and save are due. The rules below make both moments explicit.

## Prerequisites

- A memory tool the agent can call. Any backend works, and the rules are identical for each:
  - **Files.** A `memory/` folder of Markdown notes, one fact per file. No dependencies, fully greppable, versionable in git.
  - **A local MCP memory server.** Keeps everything on the local machine; several open-source options exist.
  - **A hosted memory service over MCP.** Adds portability across tools and machines at the cost of the data living elsewhere.
- Authentication is whatever the chosen backend requires: none for a local folder, the server's own configuration for a local MCP server, an API key or OAuth sign-in for a hosted service. This skill never handles credentials itself and never writes them into memory.

## Instructions

### Step 1: Recall before acting

Read memory **before** doing any of these, not after:

- starting work on a project touched before
- choosing a library, pattern, or tool
- writing tests, commits, or documentation, where conventions apply
- answering "how do we usually do X here"
- anything the user phrases as "again", "like last time", or "as we agreed"

Skip recall for one-off factual questions, arithmetic, or anything fully specified in the current message. Recall costs a tool call and context; spending it on a self-contained question is waste.

Search with the words the user actually used, plus the project or repository name. If the first search returns nothing useful, try one broader query, then stop and proceed without memory rather than looping.

Do not recall what the conversation already holds. An entry that is already in the context window is not read again, and when a later turn needs a fresh recall, the memory block in the prompt is replaced, not appended, so the model never sees two copies of the same entry. A hosted memory server cannot do this for the agent: it does not know what the conversation contains, so the guard belongs to the client that builds the prompt.

### Step 2: Save after deciding

Write to memory when one of these has just happened:

- a **decision** was made and will still matter next week ("we use pnpm", "the billing module stays untouched")
- the user **corrected** the agent, which is the strongest signal there is
- an approach **failed**, and why it failed
- a preference was stated that applies beyond this task
- a fact about the environment was discovered the hard way (a port, a flag, a service that must be running)

Do **not** save: the contents of files that can be read again, restatements of the current task, transient state, anything the user marked as temporary, and anything containing secrets, tokens, or personal data.

One memory, one fact. A paragraph containing four decisions cannot be superseded cleanly when one of them changes.

### Step 3: Write it so it survives

A memory that is useless in three weeks was written wrong. Give each entry, in the text if the backend has no fields for it:

- **what** was decided or observed, in one sentence
- **why**, briefly, because the reason outlives the decision
- **when** it became true, and when it stopped being true if it has
- **where it came from**: a file, a commit, a conversation, a test run

Prefer the user's own words over a paraphrase. Paraphrase drifts.

### Step 4: Close the past instead of overwriting it

When something changes, the old memory is not wrong. It is **closed**.

If the project moved from Redux to Zustand, "we use Redux" was true from January to June. Deleting it destroys the explanation for every component written in that window. Mark it superseded, keep its validity window, and write the new one alongside.

This is the single most destructive habit in agent memory, and it stays invisible until someone asks a question about old code.

### Step 5: Keep contradictions visible

If recall returns two entries that disagree, do not pick the closer match and proceed. Surface both, with their dates, and ask or flag. A convention that a recent failure contradicts is exactly the situation where the user needs to be told, not smoothed over.

### Step 6: Weigh evidence and policy differently

- **Evidence** is what happened: one run, one failure, one observation. Cheap, plentiful, individually unreliable.
- **Policy** is what should happen: a convention, a decision, a rule. Expensive, and should be hard to change by accident.

An observation becomes policy when a human confirms it, when it lands in a merged decision record, or when it has worked repeatedly. Never promote a single observation to a rule without one of those.

## Output

Following this skill produces two things, and nothing else:

- **Recalled context, stated before the work starts.** The relevant entries are named with their dates and sources, so the user can see what the agent is relying on. Conflicting entries are shown side by side, not merged.
- **New memory entries after decisions, corrections and failures.** One fact each, in this shape:

```text
Project uses pnpm, not npm. Stated by the user on 2026-08-11 after a lockfile conflict. Applies to all packages in this repo.
```

A superseded entry keeps its text and gains an end date and a pointer to the entry that replaced it. The full format, with closing and evidence examples, is in [references/entry-format.md](references/entry-format.md).

## Error Handling

- **Memory tool unavailable or failing.** Proceed without memory, say so in one line, and do not retry in a loop. Save the pending decision as soon as the tool is back, rather than dropping it.
- **Recall returns nothing.** Run one broader query, then continue without memory. An empty result is information: the topic is new, so a decision made now is worth saving.
- **Recall returns too much.** Keep the entries that match the current project and task; ignore the rest rather than pasting them into context.
- **Two entries disagree.** Show both with their dates and ask which holds. Do not resolve the conflict silently.
- **A save is rejected or filtered by the backend.** Report it once. Do not rephrase the same fact repeatedly to get it through.
- **The user asks to forget something.** Close or remove the entry as the backend allows, and confirm what was removed.

## Examples

### A correction

The user says: *"stop using npm here, we're on pnpm."*

1. This is a correction, which is the strongest save signal. Save it.
2. Write: `Project uses pnpm, not npm. Stated by the user on 2026-08-11 after a lockfile conflict. Applies to all packages in this repo.`
3. Do not also save "the user was annoyed", "ran npm install", or the lockfile contents.
4. Next session, before running any package command in this repo, recall first and find it.

### A contradiction

Recall returns two entries: `Integration tests run against the staging database (2026-06-02)` and `Integration tests use a local container; staging is off limits after the incident (2026-08-19)`.

1. Do not pick one and continue. State both, with dates.
2. Ask: *"Memory has two rules for integration tests; the August one says staging is off limits. Use the local container?"*
3. After the answer, close the entry that no longer holds, with its end date, and keep the other.

## Resources

Checklist to keep in the loop:

- Before acting on project-specific work: recalled first?
- After a decision, correction, or failure: saved in one sentence, with its reason?
- When something changed: closed the old entry instead of deleting it?

Related reading on the underlying ideas: [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Claude Code skills](https://code.claude.com/docs/en/skills), and the [Model Context Protocol](https://modelcontextprotocol.io) for connecting memory servers.

*Written and maintained by the team behind [Mnemoverse](https://mnemoverse.com), which is one hosted implementation. The rules above are deliberately backend-neutral and were written to be useful without it.*
