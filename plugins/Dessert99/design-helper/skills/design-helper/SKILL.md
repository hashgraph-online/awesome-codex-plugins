---
name: design-helper
description: Use when several visual variants need to be compared side by side —
  mockups, layouts, or a range of one value (spacing, radius, shadow, color, motion)
  — or when you are about to ask the user to pick between visual options in prose.
  Renders every candidate in one HTML file, opens it in a browser, lets the user
  choose by eye, then applies the choice to the code. Not a design generator — it
  lays out a range, it does not invent a look. Triggers on "5가지 버전으로 보여줘" ·
  "A 랑 B 중에 뭐가 나아" · "시안 여러 개 비교해줘" · "나란히 놓고 보자". Do not use
  for ordinary UI coding, bug fixes, or implementing a design that is already decided.
---

# design-helper

The work happens in a worker agent so this conversation stays small. Reading the
project code, drawing the sheet, serving it, screenshots and applying the choice all
fill a lot of context. The worker does them; you talk to the user and pass messages.
Everything the user sees is Korean.

The worker's instructions are `worker.md`, next to this file. Do not read it unless you
end up doing the work yourself (see the last section).

## Start the worker

Spawn one worker per comparison target, right away: don't list, read or search
anything first. `worker.md` is in this skill's base directory, and the worker reads
the project itself. Its first message holds:

- the user's request, quoted as written
- the target, if you know it: files, component, route
- what the conversation already settled about this target, with values
- the project root, as an absolute path

Which agent to spawn:

- **Claude Code with this plugin installed**: subagent type `design-helper:worker`. It
  finds `worker.md` on its own.
- **Claude Code without it** (the skill was copied or linked in): a general-purpose
  subagent. Start the message with `Read <absolute path of worker.md> and follow it.`
- **Codex**: `spawn_agent` with `fork_context` false and no `agent_type`. Start the
  message the same way, with the absolute path of `worker.md`. These instructions
  are the explicit request for a subagent.

Tell the user in one short Korean line that the comparison is being drawn, then wait
for the worker's result (Claude Code notifies you; in Codex, `wait_agent`).

## Every round

- **Show the worker's final message as written.** Do not summarize, translate, add a
  next step, or answer the question it asked.
- **Forward each user reply about the comparison as written**, to the same worker:
  `SendMessage` in Claude Code; in Codex, `send_input` or `followup_task`, whichever
  your tools have. Letters, impressions, refinements, `이걸로 가자`, `끝났어`: all of
  them go to the worker, which knows what they mean. Do not interpret a letter
  yourself, and do not edit the sheet or apply a value yourself.
- A message that clearly has nothing to do with the comparison is yours to handle. If
  you can't tell, forward it.
- After a choice is applied, the worker's message ends with `변경 파일:`. Read those
  files or their diff only when your own work needs them.
- The user says it is done (`끝났어`, `됐어`): forward it, show the worker's last
  message, and close the worker if your tools can (`close_agent` in Codex).

## When the worker is gone

If the worker can't be resumed (it was closed, the session restarted, or a message to it
fails), spawn a new one. Its first message adds the settled values from the earlier
reports and the last letter used, so the letters continue instead of restarting.

## Doing it yourself

If you can't spawn a subagent (no such tool, it is turned off, or you are already a
subagent), read `worker.md` and follow it yourself. Your chat replies then take the
place of the worker's final message.
