---
name: technical-book-lab-design
description: Design hands-on technical nonfiction chapters as runnable labs, worked examples, exercises, checkpoints, troubleshooting paths, and reader outcomes. Use when turning technical book sections, tutorials, self-hosting chapters, DevOps guides, programming lessons, or infrastructure explanations into practical labs that readers can complete and verify.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Technical Book Lab Design
  category: Writing
  tags: writing,books,nonfiction,technical-writing,tutorials
---

# Technical Book Lab Design

## Core Lens

A technical book lab is not a pile of commands. It is a guided reader transformation with a clear starting state, safe path, visible progress, expected output, and exit criteria. The reader should know what they built, why it works, how to verify it, and what to do when it fails.

Use this skill to design or improve:

- Self-hosting chapters.
- DevOps, infrastructure, programming, data, or security tutorials.
- Worked examples and exercises.
- Lab prerequisites and environment assumptions.
- Checkpoints, expected outputs, and troubleshooting branches.

## Reference Routing

| Need | Read |
|------|------|
| Core lab concepts and terminology | `references/core/knowledge.md` |
| Lab design rules | `references/core/rules.md` |
| Before/after examples | `references/core/examples.md` |
| Lab review checklist | `references/core/checklist.md` |
| Step-by-step lab design | `workflows/design-runnable-lab.md` |

## Workflow

### 1. Name The Reader Outcome

State what the reader will be able to do, decide, deploy, debug, or explain after the lab.

If the outcome is only "learn about X," sharpen it until there is visible proof of progress.

### 2. Define The Starting State

List what the reader already has and knows:

- Required concepts.
- Accounts, hardware, software, versions, and operating system.
- Network, domain, DNS, permissions, credentials, or safety constraints.
- Files or repo state.

Move missing prerequisites earlier, compress them, or link them to companion material.

### 3. Design The Path

Structure the lab as small checkpoints:

- Explain the purpose before each action.
- Give the smallest safe command or change.
- Show expected output or state.
- Add a quick verification.
- Explain the next decision.

### 4. Add Failure Handling

Technical readers do not only need the happy path.

- List likely errors and what they mean.
- Add rollback or cleanup steps where changes are risky.
- Mark steps that expose services, change permissions, spend money, or affect data.
- Tell readers when to stop and ask for help.

### 5. Close The Loop

End every lab with:

- Final verification.
- What the reader should understand now.
- What they can safely change next.
- Cleanup, maintenance, or security follow-up.

## Output Format

When designing or reviewing a lab, return:

1. Reader outcome and starting-state assumptions.
2. Lab sequence with checkpoints.
3. Expected outputs and verification steps.
4. Troubleshooting table.
5. Safety notes and cleanup.
6. Suggested companion resources or prerequisites.

## Quality Bar

Make the lab useful to a real reader in a real environment. Prefer concrete outputs, checkpoints, and failure handling over abstract explanation or untested command sequences.
