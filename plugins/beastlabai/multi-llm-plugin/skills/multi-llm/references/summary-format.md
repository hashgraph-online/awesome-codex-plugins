# Standard Summary Format

The shape of the report a mode ends with. It moved out of the Claude Code shim in
the D5c cutover: what a run reports is *workflow* prose, identical on every host,
so it belongs in the core rather than in one host's entry file.

After any mode completes, report:

```
## [Mode] Complete

**Plan**: /path/to/plan.md

### Results
- [Mode-specific statistics]

### Output Files
- [Every generated file, with its full path]

### State
- State file: [path, if the mode has one]

### Next Steps
- Start the next phase in a fresh context (recommended, for best performance) —
  use whatever context-reset command your host provides, and omit this line if it
  has none
- [The next step, copied from `user_next_step` as the next-step rule below says:
  its `command` alone in a fenced block, then any optional commands under
  "Optional, before that:" — or "Workflow complete." and any manual tasks still
  owed — or nothing]
```

Every mode ends with this report. Four rules, and a fifth for `ask`:

- **Paths come from the run, never from memory.** Take them from the orchestrator's
  own output — the `[OUTPUT_FILE]` lines, the paths a phase printed, and
  `MULTI_LLM_RESULT`'s `artifacts` array. Do not reconstruct a path from a pattern.
- **Report the one follow-up the run owes, verbatim — and tell `next` from
  `user_next_step`.** They are two different things. `MULTI_LLM_RESULT.next`,
  when it is not `null`, *continues this phase*: the phase has not finished (a
  `--reaggregate` or a `status` poll is still owed), so copy it exactly, and
  report nothing as a next step that the run did not name. Copy it character
  for character, never re-typed: its plan path as printed, no flag added or
  dropped (not a `--plan-file` spelling, not without the `--quick --yes` it
  carries), and read a foreground call's output whole (only a detached launch
  redirects its output, into the phase dir's `orchestrator-run.log`): a pipe,
  even through `tail`, hands you the pipe's exit code instead of the
  dispatcher's and drops the marker lines above the `MULTI_LLM_RESULT` line you
  must read.
  `user_next_step`
  *starts the next phase*: it is the user's to type, never yours to run, and it
  ends the report as the next rule says.
- **End the report with the next phase's command — copied, never composed.**
  Python builds it as `user_next_step`; your part is to fetch it and copy it.
  - *Where it comes from.* While the last result's `next` is not `null`, the
    phase is unfinished: report that follow-up under the rule above and look
    nothing up. A phase whose run exited `1` or `3` failed and has no next
    step either: report the failure, and look nothing up. Otherwise take
    `user_next_step` from the last result (its `MULTI_LLM_RESULT` line, or the
    tool result that relays it) when that result carries the key. When it does
    not, the host decides:
    - *On Codex and OpenCode* (file shim and tool alike), the key arrives in
      the phase's own result, so a result without it means there is no next
      step — the phase stopped short (at a `[…_PENDING]` marker, say), or the
      run is not one that names a next phase. Look nothing up, and write
      nothing under `### Next Steps`. `--after` does not check that the phase
      finished, so a lookup here could name the successor of a phase that
      never did.
    - *On Claude Code* only, the phase's last call is often a `util` step that
      cannot know the phase, so the report's first step is one read-only
      lookup, run after every command the core told you to run — the phase's
      own completion write included, because run earlier it answers from a
      phase not yet recorded: the dispatcher's
      `util next-command "<plan-path>" --after <the mode you ran>`, behind the
      same `uv run … multi_llm.py` prefix as every command in the core, with the
      plan path as the user typed it. Run it even when a `[NEXT_COMMAND]` line
      is already on screen: a `--reaggregate` (or any other `next`) run can name
      the plan by its absolute path, and the command is printed with the path
      the user typed. Its `MULTI_LLM_RESULT` line carries `user_next_step`, and
      the `[NEXT_COMMAND]` lines above it hold the same strings.
    - *When a lookup answers nothing.* A lookup whose output has no
      `[NEXT_COMMAND]` or `[WORKFLOW_COMPLETE]` line, and whose result line has
      no `user_next_step`, found no next command: that is its whole answer.
      Write nothing under `### Next Steps` for it, and do not fill the gap: not
      with a status view's `suggested next:` (a phase name, not a command), not
      with a default, and never with a command assembled from the plan path.
      (2026-10-02: a Claude Code `--status` ran the lookup, got nothing, and
      the report invented a command from the plan path.)

    `ask`, `init` and `status` are not workflow phases: on every host they run
    no lookup and end with no command.
  - *What to write under `### Next Steps`.* `user_next_step.markdown`, copied
    as it is (on Claude Code the lookup prints it between `[NEXT_STEP_MARKDOWN]`
    and `[NEXT_STEP_MARKDOWN_END]`): it is this section already written, as the
    rest of this rule describes it. Copy it word for word, never wrapped in a
    fenced block of your own (its commands are fenced already), and say none of
    it twice: its whys, notes, manual tasks and "Workflow complete." appear only
    in it, never above it. A notice you report goes above it and repeats none
    of it. Without it, `user_next_step.command` alone in a
    fenced block, copied character for character, and never "Workflow
    complete." beside it, however much of the work is done: while there is a
    command, the workflow goes on (its `why`, the `[NEXT_COMMAND_WHY]` line,
    goes above it as plain text). Any `optional_before`
    entries follow it, never precede it: the line "Optional, before that:",
    then each entry in the order the key lists them — its `why` as plain text
    outside the fence, then its `command` alone in its own fenced block. When
    the lookup also printed `[NEXT_COMMAND_ANSWERS_WHY]` /
    `[NEXT_COMMAND_ANSWERS]` pairs (`user_next_step.answers`: a stopped
    implement's `--human-task` answers, the one command carrying every answer
    first when more than one task waits, then each answer alone), write every
    pair, in the order printed,
    last: its why as plain text, then its command alone in its own fenced
    block. A stopped implement's lookup can also print a `[TESTS_NOT_RUN]`
    line above them, saying what ran the repository's tests: give the text
    after its tag verbatim in the report, above `### Next Steps`; it is never a command. When
    `complete` is `true` (its `command` is then `null`), write
    "Workflow complete." instead, and when it carries `manual_tasks`, list
    each one under it, its `id` and `title`, as the user's to do: implement
    deferred them to the user, and one with `waits_on` is a task skipped with
    that manual task, which implement runs once that one is recorded done (the
    `[MANUAL_TASK]` lines below `[WORKFLOW_COMPLETE]` are the same tasks, and
    such a line says what it waits on), then its `manual_tasks_note`
    (the `[MANUAL_TASK_NOTE]` line) verbatim as plain text and its
    `manual_tasks_command` (the `[MANUAL_TASK_COMMAND]` line) alone in its own
    fenced block: they say how to record them done.
    A `user_next_step` that names a `command` can carry `manual_tasks` and
    `manual_tasks_note` too, while the run's manual tasks are still owed (on
    Claude Code the same lines follow the `[NEXT_COMMAND]` block): list them
    after the commands the same way, with the note and its command, but never
    write "Workflow complete." for it. When there is no `user_next_step` at all,
    write neither a command nor "Workflow complete.": an absent key is not a
    completion.
  - *A failed lookup prints no command.* When `util next-command` exits
    non-zero, write no fenced command and no "Workflow complete.": write one
    line under `### Next Steps` saying the next-step lookup failed, quoting the
    stderr line it printed.
  - Never build, shorten, recall or rephrase a command yourself — not from a
    phase name, a mode flag, a usage line or an earlier report. A paraphrased
    command is the failure this rule exists to remove.
- **Name every model that produced nothing, with its reason.** A review
  phase's `report.md` lists them on its `**Models failed:** N of M requested — …`
  line, directly under `**Models:**`, on the fan-out and after `--reaggregate`
  alike; a `--reaggregate` also prints one `[MODEL_FAILED] <model>: <reason>`
  line per requested model that still has no result. When
  `MULTI_LLM_RESULT.state` is `"partial"`, the same models and reasons are the
  `failed` rows of `progress.models` (a `status` poll carries them). List each
  one under Results with its reason; never report the run as if only the models
  that answered had been requested. **In `ask` mode** they are the
  `## Failed Models` section of `answers.md`. A failed model whose run left some
  text has it kept in a `partial_<model>.md` that its line names; say so, since
  a partial is not counted and a resume re-asks the model. You may offer
  `--accept-partial <model>` for a partial the user has read and judged whole —
  never run it unasked.
- **In `ask` mode, say how the answers were obtained.** Report the run's
  `answered: …` counts line verbatim, and the `[WARN]` it prints when every
  model asked to write an answer file answered on stdout instead. A host that
  reads only the result line takes both from `MULTI_LLM_RESULT.answer_origins`
  (its integers are the counts line's; `warn_all_fallback` is the warning).
