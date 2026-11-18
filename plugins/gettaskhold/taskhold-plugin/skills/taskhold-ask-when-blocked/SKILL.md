---
name: taskhold-ask-when-blocked
description: When you need a decision, access or approval from the person, ask it on Taskhold's board as one question they can answer from their phone, then keep working on something else instead of stopping in the terminal. Use when the user says "ask me if you get stuck", "don't wait for me", "I'll answer from my phone", "check with me before deleting or deploying", or whenever a choice is hard to undo. Needs the Taskhold MCP tools (taskhold_*); if they are missing, use the taskhold skill to set up.
---

# Ask the person through Taskhold

A blocked task moves to the top of the person's board under Needs you, with your question and up to four one-tap answers.

## Ask

`taskhold_block` on the task (or on the step if only that step is stuck) with:
- `reason`: one question, starting with its type. "Decide: keep /v1 for 30 days (safer) or remove it now?" Other types: "Answer:", "Approve:" (say how to undo it), "Access:" (exactly what is missing). Include what they need to answer without opening the code.
- `options`: 2 to 4 short, different answers when the answer is a choice.
- `recommended`: the index of the option you would pick (0 = the first).
- `if_no_answer`: what you will do meanwhile, for example "I'll use SQLite and keep going in 30 min."

## Wait

`taskhold_updates` with `task_id`, `since` (the cursor from the block result) and `wait: 50`, repeated until the reply arrives. A tapped option reads `Reply to "<question>": chose "<option>"`. Meanwhile, work on anything that doesn't depend on the answer.

## After the reply

- Clear answer: `taskhold_unblock` (or `taskhold_start`) and continue.
- Unclear answer: block again with one narrower question. After two unclear rounds, leave it blocked and move on.

## Always ask before

Deleting data, spending money, touching secrets or credentials, and deploying to production. Never guess on these.
