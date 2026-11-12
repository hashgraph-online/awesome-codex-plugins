---
name: bro
description: "Use when the user says something was too technical or full of jargon, or asks you to speak and write plainly from now on."
---

# Bro

Invoked right after your reply with no argument: the user did not understand it. Restate that reply and keep every fact.
Invoked by another skill, such as `explain-diff`: apply the rules to that skill's output only.
Invoked any other way: apply the same rules to everything you say and write from now on, code excepted.

Follow the [writing contract](../../shared/writing.md), and add these:

- Write for someone who knows almost nothing about the project or the problem. Give the missing context in simple words.
- Explain what is happening and why, with a real case whose values come from the code, data, tests, or logs.
- Say what happens when something fails.
- Keep technical terms as the writing contract says, and explain each one the first time.
- Leave out everything that does not help the reader understand.
