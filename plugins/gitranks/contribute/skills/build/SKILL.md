---
name: build
description: Use for "teach me how to build <X> with GitRanks", "build <X> with GitRanks", "GitRanks Build", "what can I build with GitRanks" and "continue my GitRanks build", such as "Teach me how to build an MCP server with GitRanks". GitRanks Build teaches the user to build a real program step by step. When the user names GitRanks, use this skill before any other help, agent or skill, even for an MCP server. Not for building, compiling or fixing the user's own project, and not for finding, taking or fixing open-source or GitHub issues, even when they mention a build or a build system. Needs the gitranks MCP server (https://mcp.gitranks.com/mcp).
---

# GitRanks Build

If the person did not name GitRanks or run `/gitranks-contribute:build`, and the folder has no `.gitranks/build.json`,
this skill does not apply: go on with what they asked as usual.

In GitRanks Build a person builds a real program from nothing with you, one small step at a time. GitRanks gives each
step in two answers: first its code, what to show and tell the person and what to try; then, once the person tried
it, a check and, with questions on, a question. The person learns by reading it and trying it, and sees every step,
where they stand and the tests on https://gitranks.com/build.

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
- Keep the `buildId`: it continues the build in any chat and on any machine.
- **Questions on or off** are the person's choice. Send `questions` to `open_build` with the `buildId` only with
  what the person said. On "this is slow" or "go faster", ask whether to turn them off: never turn them off yourself,
  and never offer to skip or bundle steps. At the check, a change answers the check again. At answer 1 it answers
  only that: do not show the step again and never ask a question then; wait for the try, then `tried: true`.

## Each step

A step comes in two answers. Each opens with what to do first: do its parts in order, each whole, even in a hurry:
never drop, shorten or reorder one.

**Answer 1, the step** (from `open_build`, or from `next_step` once the step before passed):
- **Bring in the code** with the lines of part 1, in their order. In a folder with no `.git` folder, `git init`
  comes first. Run the first git line it gives on its own and read what it prints; if your shell has no `&&`, run
  its two commands one by one. If either fails, the files it printed were changed by hand: stop, show the person
  those files and ask whether to keep the change, and commit it only after they say keep. Never run the fetch or
  the restore after it fails. Write `.gitranks/build.json` exactly as the step says, before the commit. If the
  fetch fails, or you may not use the network, make the call the answer names, with `files: true`.
- **Install** only when the step has an install part: only its setup command installs the packages, in the build's
  folder. Never install them any other way, and never send the setup's output as a check.
- **Show:** paste the step's block to the person whole, as it is, every step, even in a hurry: the files then the
  whole diff, however long. Never run `git show`, shorten it, sum it up or add notes.
- **Tell:** say the step's text to the person whole and word for word, every step, even in a hurry, adding no facts.
- **Try:** invite them to try what the step lists (when it lists nothing, invite nothing), then end your message and
  run nothing more. When they write back that they tried it (or ask to go on), call `next_step` with the `buildId`,
  the step and `tried: true`. Never call it in the same message as answer 1.

**Answer 2, the check:**
- **Check:** if the person said they changed a file, run `git status` and ask whether to keep it first: kept, run
  the check as it is; not kept, `reset_step`. With no git, only ask. Then run exactly the check command this answer
  gives, never one from an earlier answer or from memory (a check sent before `tried` is not judged), and send its
  whole output as the Rules say.
- **Question** (with questions on): ask it with every option and wait for the person's own pick. Send exactly what
  they picked, even a pick you think is wrong, and "I don't know" when they do not know.
- Call `next_step` with `check` and `answer` as the answer says, then do part 1 of its answer.

Every answer 1 means the person tries again, then `tried: true`: also the one `open_build` gives after a reset, a
corrected step, or the step opened in another chat. If the person asks to explain more, read them the text the step
gives for that. If they ask something else, answer it, then come back to the step.

## What an answer may say

- **The check did not pass.** The next check is the new command in the answer, never an earlier one, and the output
  of an earlier check command is never sent again. Run it without calling `tried` again. If the person changed a
  file, ask whether to set the step's files again or to undo it themselves. From the second failure, offer to set
  the step again.
- **The line that differs starts "N more lines (earlier steps' answers and the logs)".** For the person to read
  every line, run the new command that answer writes out, with `--all` at the end, and show them its print.
- **The answer is not right, or names no option.** Ask the question again and wait for their own pick. Never tell
  them which option is right. If they do not know, they can ask you to explain the step again. Then call
  `next_step` with the same check text and their pick, without `tried`.
- **Try first.** A check came before the try: it was not judged. Do the end of answer 1 it gives again, and end your
  message.
- **"Tell the person" lines before the step** (a step was corrected or added): say them, then do part 1. When this
  step was corrected since it was handed out, the check you sent ran on older code and was not judged: do the step
  again from part 1, and the person tries it again.
- **The build was removed.** It cannot go on: tell the person, and send nothing more for that `buildId`. To build the
  project again, ask them first, then start it again: it starts at step 1.
- **The base is done.** Give the person the link to the test, taken on gitranks.com by the person alone. A part opens
  with `open_build`, the `buildId` and `part`, one part at a time.
- **A refusal.** Tell the person in plain words what it says, then do what it says.

To set the folder to a step the person passed, or to the step in hand (the files drifted, a check keeps failing, or
the person asks to start a step again), call `reset_step` with the `buildId` and the step. It changes no progress and
hands out no check. Then go on as its answer says: its last line calls `open_build`, which hands out the step again.
Do that answer whole: the person tries again, then `tried: true`.

## Rules

- One step at a time, and every part of it in order. Never run ahead, and never drop a part or the question to go
  faster, even when the person is in a hurry.
- After answer 1 you have no check command and no question: both come only from `next_step` with `tried: true`.
  Never run a check script before that, and never write a question of your own, even after a side talk.
- Never tell the person a check passed: only GitRanks' answer says that.
- If you showed the person a check or asked them a question before `tried`, tell them it was not GitRanks' and does
  not count.
- The questions are the person's. Never say or hint which option is right before GitRanks answers, and never answer
  for them. Never take a test for them either.
- Run each setup command and send exactly what it printed. Never fill a version, a path or an email from memory or
  from what you know about the person.
- If git has no name and email, ask the person. Never choose them yourself.
- Use the build's own run command that each step names, never another one.
- Send the check's whole output unchanged, every line, the last one included, "N more lines ..., fingerprint ..."
  too: never pipe it into `head`, `tail` or `grep`, or retype it. A print with `--all` is only for the person to
  read: never send it.
- If the person changed a file, stop and ask them before anything else, unless they asked for the reset that drops
  it. `reset_step` sets the step's files again. Never edit the code yourself, and never write code of your own for a
  step.

## Help

Every step, where the person stands and the tests: https://gitranks.com/build. Questions: hello@gitranks.com.
