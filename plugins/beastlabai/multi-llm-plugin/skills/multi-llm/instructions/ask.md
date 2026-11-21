# Ask Mode Instructions

Ask each configured LLM a **free-text question** about a plan and aggregate the
raw markdown answers into a single file. This is a lightweight, **read-only**
Q&A side-channel — no JSON schema, no grouping, no validation subagents, no
state-machine phases.

## Usage

```bash
/multi-llm:multi-llm --ask <plan_path> "<free text question>" [--models provider:model ...] [--quick] [--interactive] [--force] [--rerun-all] [--accept-partial <model> ...]
```

- `--force` bypasses the resume guards (e.g. acts on a stale-plan warning) but
  **keeps** existing answers: only models still missing an `answer_<model>.md`
  are asked.
- `--rerun-all` re-asks **all** models, discarding existing per-model answers
  (use after editing the plan, or to get a fresh round of opinions).
- `--accept-partial <model> [<model> …]` counts a **failed** run's kept text as
  that model's answer, with the identical question. It asks no model: it moves
  each `partial_<model>.md` to `answer_<model>.md`, regenerates `answers.md` and
  reports the run again. It refuses, changing nothing, when any named model has
  no partial or already has an answer, while this question's run is still
  running, or with `--detach` (it runs in the foreground only). Run it only when
  the user has read the partial and judged it whole.

## A question that is really a task

Ask mode is built for a question a model answers by reading the plan. A
question that asks each model to *perform* a large task — a whole-repository
audit, a full review — routinely outruns the per-model budget, and a model cut
off at its deadline is a failed slot, not an answer. When the question reads
that way, say so before launching: it needs a larger `--timeout`, or is better
run as `review-code` / `review-plan`, which are built for that work. This is
advice for the user to weigh, not a check the orchestrator makes.

## Question argument parsing rule (exact)

The question is **a single argument**, conventionally a quoted string, passed
straight through to the orchestrator. Concretely:

- The first positional token after `--ask` is the **plan path**; the next single
  argument is the **question**. The `--models` / `--quick` / `--interactive` /
  `--force` flags are **position-independent** — they may appear before the plan
  path, between plan path and question, or after the question (argparse handles
  ordering on the orchestrator side).
- **The question must be supplied as one (quoted) argument.** This preserves
  spacing, embedded quotes, and any flag-like substring inside the question.
  Because the whole question is one quoted token, text such as
  `"should we keep --quick mode?"` or `"compare --models opus vs sonnet"` is
  treated entirely as question text — the leading `--quick`/`--models` inside the
  quotes are **not** parsed as flags.
- **If multiple bare (unquoted) tokens appear where the question is expected**,
  do **not** silently re-join them (joining loses the user's quoting/spacing and
  is ambiguous against flag-like tokens). Instead **error out with the usage
  hint** and tell the user to quote the question as a single argument.
- **An empty/whitespace-only question is an error** (usage hint), not a silent
  no-op.

Parsing examples (each `<question>` is exactly one quoted argv element):

- `/multi-llm:multi-llm --ask plans/x.md "Is the rollback strategy sufficient?"`
  → plan=`plans/x.md`, question=`Is the rollback strategy sufficient?`
- `/multi-llm:multi-llm --ask plans/x.md "should we keep --quick mode?" --quick`
  → plan=`plans/x.md`, question=`should we keep --quick mode?` (the `--quick`
  **after** the quoted question is the flag; the one **inside** the quotes is
  question text), flags=`--quick`.
- `/multi-llm:multi-llm --quick --ask plans/x.md "Summarize this plan"`
  → flags may precede the plan path; question=`Summarize this plan`.
- `/multi-llm:multi-llm --ask plans/x.md Is the rollback sufficient?`
  → **error** (multi-word question not quoted) with the usage hint to quote it.
- `/multi-llm:multi-llm --ask plans/x.md ""`
  → **error** (empty question) with the usage hint.

This is the **same exact rule** every host shim states as its argument
convention, so the two layers cannot diverge — and the dispatcher enforces it
independently: an extra positional, or a question that arrives empty, is exit 3
with the offending token named.

## Step-by-Step Execution

1. **Validate the plan file exists** and that a **non-empty question** was
   supplied (error with the usage hint otherwise).

2. **Hand the question to the dispatcher as one argument — never build a shell
   string out of it.** The question is user-controlled free text and may contain
   quotes, `$(...)` command substitutions, backticks or other shell
   metacharacters. You do **not** have to defend against that yourself: the
   dispatcher takes the plan path and the question as its two positionals and
   normalizes them into the flags the orchestrator parses, writing the question to
   a temp file itself (and deleting it afterwards) when it outgrows the argv
   budget. Copy the user's quoted question through verbatim:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" ask "$PLAN_PATH" "$RAW_QUESTION" [--models ...]
   ```

   Three rules govern that one line:

   - **Quote both positionals.** A plan path or a question containing a space is
     one argv element or the command is wrong.
   - **Pass the plan path as given.** The orchestrator resolves it to an
     OS-native absolute path itself; do NOT wrap it in `$(realpath …)` (on Git
     for Windows `realpath` emits a POSIX `/c/…` path a native Windows Python
     process cannot use).
   - **Never re-type or re-assemble the question.** If the user's question is not
     already a single argument, error out with the usage hint (see the parsing
     rule above) instead of re-joining tokens.

   `--question`, `--question-file` and `--question-env` remain on the
   orchestrator's own parser for a caller that already holds the text in one of
   those forms; the positional above is the documented path and is what the
   dispatcher normalizes into them.

3. **Run detached.** Ask mode fans out across many models and routinely runs far
   longer than a single shell command a host is willing to wait for; a foreground
   run risks being killed mid-flight and losing the in-flight answers. Add
   `--detach` (which implies `--yes`) and poll, or — on a host whose *run
   detached* resolution is its own background mechanism — launch the same command
   through that mechanism with stdout+stderr redirected to a log file in the
   phase dir and `PYTHONUNBUFFERED=1` set. Pick exactly one of the two; never
   both.

   ```bash
   PYTHONUNBUFFERED=1 uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" ask "$PLAN_PATH" "$RAW_QUESTION" \
     [--models ...] --detach
   ```

   A detached run is not subject to your host's shell-command cap, so each
   model's own per-provider `default_timeout` (in `providers.yaml`) governs — no
   cap-vs-provider timeout reconciliation is needed. A host's own background
   mechanism has a time limit of its own, though: give that launch call the
   longest timeout the mechanism takes, as your host's *run detached* answer
   states, or the run is stopped mid-flight. `PYTHONUNBUFFERED=1` matters
   only on the host-background path: Python block-buffers a non-TTY pipe, which
   leaves the log empty for minutes. A host-background launch **without**
   redirection loses stdout (including the `answers.md` path), which is why the
   redirect is mandatory there; `--detach` writes and reports its own log path, so
   it needs neither.

   **Say which models, before the loop starts.** The launch says a fan-out began; it
   does not say what it is over. Make **one** non-waiting status call — no `--wait`,
   no `--timeout`, so it is a file read that answers in well under a second — and
   relay its `models:` table once:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" status "$PLAN_PATH" --question "$RAW_QUESTION" --host <host-id> --view run --exit-zero
   ```

   `--exit-zero` makes this read exit `0` whenever the status was read, so a host that shows a non-zero exit as an error shows none here; without it the call exits `2` while the run is live — `status`'s poll contract, not a failure. Read the table, not the code (only `1`, unreadable, is an error), and keep the flag off any poll whose loop reads the exit code.

   That table is the roster: one row per model, and a row's spec *is* the CLI and
   the model it runs, so nothing has to be derived — `codex:gpt-6-astra:xhigh` is
   the codex CLI running gpt-6-astra at xhigh effort. How many models the fan-out
   is over is the `progress:` line's own `models 0/N done`, printed directly above
   the table, so relay that line with it. It is a call of its own rather than the
   first poll's job because the first poll waits 120 to 300 s, and a roster that
   reaches the user three minutes after launch is not a roster. If it prints no
   `models:` table the run has not written its roster yet — the child writes it a
   few seconds in, behind a cold Python start — so make that same call once more
   before entering the loop; if there is still none, go on and the table arrives on
   a later poll. A table that *does* print can still be the **previous** run's: the
   phase dir is re-used, and the write that claims it for this fan-out — the one
   that drops the predecessor's `progress` — lands about 0.2 s in on a warm start
   and later on a cold one, so a call that beats it reads a checkpoint that is
   wholly the last run's and therefore agrees with itself. Two things print, and
   only one of them is a test. The head line's tense — a finished predecessor
   reads `finished in foreground (2/2 models, …)`, or a terminal verdict word,
   where this run reads `running` — is not that test: the claim write drops the
   predecessor's `progress`, but only a **detached** run's claim drops its `run`
   record as well, so over a dir an earlier detached run used a foreground
   fan-out keeps that record and the head line reads the predecessor's terminal
   verdict for this whole run. The test is the `progress:` step: this fan-out's
   is `fanout`, a finished predecessor's is `complete`. A roster whose step is
   not `fanout` is the previous run in this dir — make the call again rather than
   relaying it. The one predecessor that test does not catch is one **aborted**
   mid-fan-out, which can still look live; there the row elapsed is the only
   tell, an aged row reading at its budget (`30m00s/30m`) where a fresh one reads
   `0m00s/30m` — so read that as likely, never as certain, and let the next call
   settle it. Relay it **once**: what the loop below reports is movement, not the
   roster. The selector on that call is this mode's own `--question` too, never
   `--phase ask`, for the reason spelled out under the poll command below.

   **Poll while it runs, and relay one line per poll.** A fan-out that runs for ten
   to thirty minutes with nothing on screen reads as a hang, so launching the run is
   only half of this step; relaying its progress is the other half. Each poll is one
   foreground call:

   ```bash
   uv run {UV_RUN_FLAGS} --project "{SKILL_DIR}" -- python "{SKILL_DIR}/multi_llm.py" status "$PLAN_PATH" --question "$RAW_QUESTION" --host <host-id> --view run --wait --timeout <interval>
   ```

   The selector is `--question`, matched byte-for-byte against the question this
   run stored — you already hold that string, it is the positional you just
   passed. **`--phase ask` is never this mode's selector**: one plan holds one
   directory per question, so `--phase ask` names every question ever asked under
   the plan, and on a host that records no run every one of those historical
   checkpoints counts as non-terminal — the poll would relay a wall of unrelated
   questions' tables and hold exit `2` long after this invocation finished.

   `<host-id>` is the same host id your dispatcher command carries; `<interval>`
   is **120 to 300 seconds** (rule 5). There are two ways to reach that line.
   Where the run was launched with `--detach`, poll the `status` command the
   launcher printed rather than composing one: it carries the `--host` the
   launch itself carried — which your dispatcher command always does, and which
   is omitted when the launch recorded none — and `--run-id` on an `ask` run,
   where `--phase ask` names every question ever asked under the plan and the
   run id is the only selector left that names this one invocation; on the other
   three modes the phase selector already names exactly one dir. It carries
   `--wait` too, with no `--timeout` of its own, so its wait resolves to
   `progress.poll_s` and is clamped under the `--host` it is already carrying.
   Where *run detached* resolves to your host's own background mechanism nothing
   printed a command, so compose the line above, and keep `--host` on it — the
   wait is clamped under the shell ceiling that flag names, and without it the
   clamp falls back to the tightest ceiling on record and silently shortens
   every poll. Add `--exit-zero` to that composed line too: on such a host
   only exit `1` decides anything (rule 2), and the flag keeps every normal
   poll from showing as an error. Then give the **call itself** a timeout of at least `<interval>`
   plus 30 seconds, **in whatever unit that parameter takes** — your host's
   *run detached* answer states it, and a host whose unit is not seconds needs
   that number scaled to it rather than copied. Get it wrong and the call asks
   for a fraction of a second: it dies before `status` answers, rule 2 below
   has you re-issue it, and the loop spins instead of polling. That is a second
   number, separate from the one inside the command: a host of that shape caps
   one foreground call at about 120 s unless the call asks for longer (about
   600 s is the ceiling on the request), so without it a `--wait --timeout 300`
   is killed on every poll starting with the first and the run reads as broken
   rather than slow.

   Five rules govern the loop:

   1. **Relay the rendered line, and only that.** Per poll: the `progress:` line the
      run view already prints, the `running in foreground (…)` head line when it
      prints one, and the `just finished:` line when it prints one — all of them
      **copied through and never reworded**. A reworded count is a count you can get
      wrong, and the whole point of the status file is that the numbers *and the
      names* come from it. `just finished: codex:gpt-6-astra:xhigh (4m12s, done)` is
      the run's own answer to *which* of them finished — the CLI, the model, what
      it cost, and the reason on a slot that failed — and it is the one thing
      `models 4/5 done` cannot give; several that land in the same wait share the
      one line, joined with `; `.
      **Its absence claims nothing.** That line is a difference between two readings
      taken *inside one `--wait` call*, so a model that finishes in the gap between
      polls — your own relay turn, plus the next call's process start — is already
      terminal when that poll takes its baseline, and no poll ever names it:
      measured 2026-09-20 against the real CLI, a model finished between two polls
      and the next poll printed `progress: fanout, models 1/2 done, 1 ok, 0 failed`
      with no `just finished:` line at all. So on **every** poll, compare the
      `models:` table with the previous poll's — you are already holding that map,
      because rule 3 has you compare the two — and
      name the row or rows that are newly terminal and that no `just finished:` line
      named, **copying the spec and the state word straight out of the row**
      (`codex:gpt-6-astra:xhigh  done`) and adding nothing to either. That
      comparison is not conditional on the line being absent: one model finishing in
      the gap and a second finishing during the wait give one `just finished:` line
      naming only the second, so the first reaches the user through the comparison
      or never. That is a copy, not a recomputation: every count still comes from
      the rendered `progress:` line and is never re-derived by counting rows, which
      is the rule that has not moved. Those two are the whole of what the `models`
      table is relayed for — the roster, once, before the loop, and naming a row no
      `just finished:` line named. Never the rest: no partial results, no
      speculation about what a slow model is doing, and never the table re-listed in
      full on a later poll.
   2. **Exit code to action, never prose.** `2` — non-terminal: relay the line and
      poll again. `0` — terminal: stop polling and read the markers and output paths
      from `{plan}/ask/<question-slug>-<hash8>/orchestrator-run.log`. `3` — the run needs a human: stop and surface the
      message **verbatim**, because it names the flag or command that answers it.
      `1` — the run state is unreadable: stop and report. The loop condition is the
      exit code; the rendered text is for the user, not for the decision. **Where
      *run detached* is your host's own background mechanism only `1` holds**: no
      selector on that host names this invocation, so `2` is the steady state, a `0`
      or a `3` is an earlier run's record left in the same phase dir and names no
      verdict for this run — the exit code is read as nothing, so relay the rendered
      line exactly as on a `2` and keep polling — and the loop ends on the
      background mechanism's own completion or error signal instead.
      An **instant** return is itself a reading, and exactly one reading: `--wait`
      holds its whole deadline for a selection that is still empty and for a
      checkpoint still doing work, so the only way back early is a terminal `run`
      record over a checkpoint that has stopped as well. That is a terminal
      *record*, which is not the same claim as a finished *phase*. A phase dir is
      re-used run after run and the write that claims it for this run is what drops
      the predecessor's halves, so until that write lands the whole checkpoint is
      the earlier run's and its halves agree with each other. The `phase state:`
      line and the `models` table are the halves this run writes, and they are what
      to read before believing an instant `0`:
      `models_running` over rows with a fresh elapsed is this run,
      `complete` over rows aged to their budget is the last one. And a poll your
      host killed at its own time limit is **not** exit `1`: it returns no exit code
      at all, the two are indistinguishable afterwards, so a killed poll is relayed
      as nothing and re-issued with the right call timeout — never reported as the
      run failing.
   3. **No movement is reported, not judged.** Nothing here tells "thinking" from
      "stuck", so do not try to. The rule is mechanical: when two consecutive polls
      show the same `models` map — same states, same `attempt`, nothing newly
      terminal, and a live row's elapsed advancing on its own is not a state
      change — add one clause to that poll's line naming the row it is about, `no
      state change in the last N minutes; <model spec>'s budget runs to
      <timeout_s>`, and keep polling. With several rows still live, name the one
      that has been running longest: a bare `<timeout_s>` and no row beside it is a
      deadline the user cannot attach to anything. A silent provider is not an
      error until its slot's deadline says so.
   4. **A ceiling, and the kill path in the first line.** Stop once the longest
      slot's `timeout_s` plus one interval has passed with **no movement in
      `progress` at all** — neither a `models` transition nor a `step` change,
      because a run that is grouping or validating after its last model has a frozen
      map and is not stuck — and still no terminal verdict; report the run as
      unfinished rather than polling forever. Where the verdict can never turn
      terminal, that ceiling is the backstop for a completion signal that never
      arrives rather than the normal exit. The **first** relayed line names the kill
      path, so the user has a way out from the start without having to ask for one;
      later lines do not repeat it. Which command that is follows the *run detached*
      verb and nothing else: where the run was launched with `--detach`, it is `…
      multi_llm.py status "<plan>" --abort`; where *run detached* is your host's own
      background mechanism the run holds no `run` record for `--abort` to reach —
      it answers `nothing was running (no_run)` and exits 2 — so the kill path there
      is stopping that background job by the handle you launched it with.
   5. **The interval is a UX cost, and that is what sets it.** Each poll is one
      foreground call that blocks for its whole duration, and the user cannot
      interrupt you mid-call — at 300 s someone who wants to abort waits up to five
      minutes for you to come back. That is the argument for 120 to 300 seconds and
      against pushing the interval to your host's hard cap, and it is what
      `<interval>` is set from on the command you compose. State in the first
      relayed line the gap you will **actually** wait, so it is expected rather than
      read as a hang — and that is `<interval>` only on the command you composed. A
      poll of the command the launcher printed carries no `--timeout` of its own and
      waits whatever `progress.poll_s` resolves to, 90 s unless the project
      configured it; state that number there instead. Announcing an interval you are
      not waiting is worse than announcing none.

   **Resume**: re-invoking the identical question with `--force` RESUMES (keeps
   already-completed `answer_<model>.md` files, runs only the missing models);
   `--rerun-all` forces a full re-run discarding existing per-model answers.

4. **No validation/grouping/subagent steps.** When the poll loop above ends, read
   the `answers.md` path from the log file
   (`{plan}/ask/<question-slug>-<hash8>/orchestrator-run.log`, final line, or the
   path `status` printed), then read `answers.md` and present a brief summary per
   model plus the output file path, following `references/summary-format.md`.
   Three more things in the run are yours to relay:

   - **Every failed model, with its reason**, from `answers.md`'s
     `## Failed Models` section. A model whose run timed out or failed after
     leaving some text has that text kept in `partial_<model>.md`, and its line
     names the file and the command that counts it. A partial is not counted,
     and a resume re-asks that model. You may **offer** `--accept-partial
     <model>` — the step 2 command with the identical question and that flag
     appended — for a partial the user has read and judged whole. Never run it
     unasked.
   - **The `answered: …` counts line** the run printed, verbatim: how many
     answers came from answer files, on stdout as the adapter is asked to,
     recovered from stdout, accepted from failed runs, and how many were kept
     from an earlier run. Each answer in `answers.md` carries the same fact as
     one italic line under its heading.
   - **The all-fallback `[WARN]`**, when it printed: every model that was asked
     to write an answer file answered on stdout instead, so the answer-file
     channel is not working for this roster. Those answers are whole and count;
     the warning is about the channel.

   A host that reads only the result line takes the counts and the warning from
   `MULTI_LLM_RESULT.answer_origins` (see Exit Status below).

## Output Files

```
plans/todo/my-feature/ask/<question-slug>-<hash8>/
├── answers.md            # aggregated markdown answers (regenerated each run)
├── answer_<model>.md     # per-model raw markdown answer
├── origin_<model>.txt    # how that answer was obtained: file, stdout, fallback or accepted
├── partial_<model>.md    # text a failed run left (not counted; --accept-partial counts it)
├── log_<model>.txt       # per-model provider debug log (bounded; never read as an answer)
├── error_<model>.log     # per-model error log (only on failure)
└── .status.json          # resume detection + collision/freshness guard
```

An answer counts only when its model's run ended by itself with a finished
answer. A run that timed out, exited non-zero or reported a cut answer is a
failed slot whichever channel carried its text — an answer file it wrote
included, since nothing shows that file is finished — and the text is kept as
`partial_<model>.md` under `## Failed Models`.

## Resume & Freshness

- Re-asking the **byte-for-byte identical** question maps to the same directory
  and resumes: models with a non-empty `answer_<model>.md` are skipped and
  `answers.md` is regenerated from all current answers. Use `--rerun-all` to
  re-ask every model; `--force` on its own only bypasses the resume guards and
  still keeps existing answers.
- On resume, if the plan file changed since the answers were generated, the
  orchestrator prints a stale-plan warning recommending `--rerun-all` (it does
  not auto-invalidate answers).
- A model that only has a `partial_<model>.md` is re-asked on resume; the
  re-ask replaces or removes that partial, so the one a `## Failed Models` line
  names is always from the model's latest run. An answer keeps its
  `origin_<model>.txt` across any number of resumes, so its provenance line
  never turns into "resumed".

## Exit Status

`ask` reaches only three D6 decision sites — the uv preflight (row 1), model
selection (row 2) and partial results (row 3) — and every one of them resolves
without a question, so this mode is unattended on every host:

- **Exit 3** when zero models succeed (all failed): there is nothing to
  aggregate, so this is "needs a human", not a generic error. The retry command
  is named on stdout, and `answers.md` / `.status.json` are still written (with a
  `## Failed Models` section) so the failure is diagnosable. A run that timed
  out or failed never counts as an answer, whatever text it left, so a run in
  which every slot timed out is exit 3 too.
- **Exit 0** on partial success (≥ 1 model answered): `[PARTIAL_RESULTS: <model>,…]`
  on stdout, `MULTI_LLM_RESULT.state: "partial"`, and the `## Failed Models`
  section enumerating the failures. A partial answer set is usable output, so it
  is deliberately never exit 3 (D6 row 3).
- **Exit 3** when models cannot be resolved (no `--models`, no `--quick`, no
  `defaults.models`) — never a rendered picker (D6 row 2).
- **`--accept-partial`** ends with the same report and the same codes once it
  has counted the partials; a refusal (a named model with no partial or with an
  answer already, a run still in progress, or `--detach`) is exit 3 and changes
  nothing.
- **`MULTI_LLM_RESULT.answer_origins`** is on the result line of every `ask` run
  that reaches its report, a zero-answer run included (all zeros, flag
  `false`), and on the `status … --question … --view run` poll of a finished
  detached run. No other mode carries it. Its keys are `answered`, `file`,
  `stdout`, `fallback`, `accepted`, `unrecorded`, `kept` and
  `warn_all_fallback`. The integers are the counts line's numbers: answers from
  an answer file, answered on stdout by an adapter that is asked for stdout,
  recovered from the stdout of a model that was asked for the file and did not
  write it, counted by `--accept-partial`, with no origin record, and — across
  all of those — kept from an earlier run rather than produced by this one.
  `warn_all_fallback` is the `[WARN]`'s own predicate. **An all-fallback run
  does not change the exit code**: its answers are whole answers from runs that
  ended cleanly, so it stays `done` or `partial`, exit 0, and this field is how
  a host or CI tells it apart.
