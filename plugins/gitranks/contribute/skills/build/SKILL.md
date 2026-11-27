---
name: build
description: Use for "teach me how to build <X> with GitRanks", "build <X> with GitRanks", "GitRanks Build", "what can I build with GitRanks" and "continue my GitRanks build", such as "Teach me how to build an MCP server with GitRanks". GitRanks Build teaches the user to build a real program step by step. When the user names GitRanks, use this skill before any other help, agent or skill, even for an MCP server. Not for building, compiling or fixing the user's own project, and not for finding, taking or fixing open-source or GitHub issues, even when they mention a build or a build system. Needs the gitranks MCP server (https://mcp.gitranks.com/mcp).
---

# GitRanks Build

If the person did not name GitRanks or run `/gitranks-contribute:build`, and the folder has no `.gitranks/build.json`,
this skill does not apply: go on with what they asked as usual.

In GitRanks Build a person builds a real program from nothing with you, one small step at a time. GitRanks gives
each step: its code, what to show and tell the person, what to try, a check, and with questions on, a question. The
person learns by reading it and trying it, and sees every step, where they stand and the tests on
https://gitranks.com/build.

Each answer of the server is complete in itself and says exactly what to do, in its own words: follow them. Some
agents keep only the start of the server's instructions, so this skill states the rules once.

## When Build is not open

Build's tools on the `gitranks` server are `list_projects`, `open_build`, `next_step` and `reset_step`. Decide by
the tools you see:
- **No `gitranks` tools at all, or a call answers that sign-in is required:** the server is not connected. Connect it
  first (see Connecting in the `contribute` skill), then look again.
- **Other `gitranks` tools (such as `find_issues` or `my_contributions`) but none of Build's:** GitRanks Build is not
  open to this person yet. Tell them so, and do nothing more for GitRanks Build.

If the person names GitRanks Build or asks to (learn to) build something (even an MCP server) with GitRanks, call
`list_projects` or `open_build` before any other help, agent or skill. Never teach the project, write its code or
make up its steps without the server. GitHub issues are not Build.

## Start or continue

- **Which projects.** When the person asks what they can build, or wants to start one without naming it, call
  `list_projects` and let them pick.
- **Start.** If the folder's `.gitranks/build.json` names that project, continue that build instead (below). Else
  call `open_build` with `project` (its slug, such as `mcp-server`). Its answer lists what to ask and run before the
  start: one at a time, asking the person and waiting for each answer. Then call `open_build` again with the answers,
  as it says. Work only inside the build's folder from then on.
- **Continue.** When the folder has `.gitranks/build.json`, call `open_build` with its `build` as `buildId`. Else
  call `open_build` with nothing: it lists the person's builds and what to ask. Never pick a build for them.
- Keep the `buildId`: it continues the build in any chat and on any machine. To turn questions on or off later, call
  `open_build` with the `buildId` and `questions`.

## Each step

An answer that hands out a step opens with "Do part 1 now", before anything you write to the person. Do part 1
first, then every other part in order, each whole, even in a hurry: never drop, shorten or reorder one. Each part
says what to do and ends with "Done when ...". After `next_step`, do part 1 of its answer.

- **Bring in the code** with the lines of part 1, in their order. In a folder with no `.git` folder, `git init`
  comes first. If the `git status` it gives prints anything, a file was changed by hand: stop and ask the person
  (to keep their change, commit it first, then go on). Write `.gitranks/build.json` exactly as the step says, before
  the commit. If the fetch fails, or you may not use the network, make the call the answer names, with `files: true`.
- **Install** only when the step has an install part: only its setup command installs the packages, in the build's
  folder. Never install them any other way, and never send the setup's output as the check.
- **Show:** paste the step's block to the person as it is, the files then the whole diff, however long. Never run
  `git show`, shorten it, sum it up or add notes.
- **Tell:** say the step's text to the person word for word, adding no facts.
- **Try:** invite them to try, and wait until they say they are done.
- **Check:** run exactly the check command the step gives, with the build's own run command named in the step, never
  another one (never choose between `python`, `python3` and `py`). Send its whole output unchanged, every line, the
  last one included, "N more lines ..., fingerprint ..." too.
- **Question** (with questions on): ask it with every option and wait for the person's own pick. Send exactly what
  they picked, even a pick you think is wrong, and "I don't know" when they do not know.

If the person asks to explain more, read them the text the step gives for that. If they ask something else, answer
it, then come back to the step.

## What an answer may say

- **The check did not pass.** The next check is the new command in the answer, never an earlier one, and the output
  of an earlier check command is never sent again. If the person changed a file, ask whether to set the step's files
  again with `reset_step` or to undo it themselves. From the second failure, offer to set the step again.
- **The line that differs starts "N more lines (earlier steps' answers and the logs)".** For the person to read
  every line, run the check command with `--all` at the end and show them its print. Never send that print.
- **The answer is not right, or names no option.** Ask the question again and wait for their own pick. Never tell
  them which option is right. If they do not know, they can ask you to explain the step again.
- **"Tell the person" lines before the step** (a step was corrected or added): say them, then do part 1. When this
  step was corrected since it was handed out, the check you sent ran on older code and was not judged: do the step
  again from part 1.
- **The build was removed.** It cannot go on: tell the person, and send nothing more for that `buildId`. To build the
  project again, ask them first, then start it again: it starts at step 1.
- **The base is done.** Give the person the link to the test, taken on gitranks.com by the person alone. A part opens
  with `open_build`, the `buildId` and `part`, one part at a time.
- **A refusal.** Tell the person in plain words what it says, then do what it says.

To set the folder to a step the person passed, or to the step in hand (the files drifted, a check keeps failing, or
the person asks to start a step again), call `reset_step` with the `buildId` and the step. It changes no progress and
hands out no check. Then go on as its answer says.

## Rules

- One step at a time, and every part of it in order. Never run ahead, and never drop a part or the question to go
  faster, even when the person is in a hurry.
- The questions are the person's. Never say or hint which option is right before GitRanks answers, and never answer
  for them. Never take a test for them either.
- Run each setup command and send exactly what it printed. Never fill a version, a path or an email from memory or
  from what you know about the person.
- If git has no name and email, ask the person. Never choose them yourself.
- Send the check's whole output unchanged, every line: never pipe it into `head`, `tail` or `grep`, or retype it. A
  print with `--all` is only for the person to read: never send it.
- If the person changed a file, stop and ask them. `reset_step` sets the step's files again. Never edit the code
  yourself, and never write code of your own for a step.

## Help

Every step, where the person stands and the tests: https://gitranks.com/build. Questions: hello@gitranks.com.
