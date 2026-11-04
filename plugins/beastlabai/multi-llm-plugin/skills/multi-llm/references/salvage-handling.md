# Salvage Handling

When a model's review output cannot be parsed as JSON, the orchestrator writes a
salvage *request* (`salvage_{model}.json`) and, beside it, a **materialized
salvage task** (`salvage_task_{model}.json`) — printing
`[SALVAGE_NEEDED] {request_path}` and `[SALVAGE_TASK] {task_path}`.

**For each task in the task file, run `task.prompt` as a subagent, then write the
JSON it returns to `task.output_path`.** That is the whole contract; the prompt
is assembled in Python (`utils/subagent_prompts.build_salvage_prompt`) and
carries the request's `raw_output`, `expected_type` and `expected_schema` inline,
so a runner with no workspace access can serve it.

**Run the pair this run advertised, and leave the retired ones where they lie.**
A phase dir is stable per plan and `--force` clears the state file's completion
marker without deleting a byte from it, so a salvage pair outlives the attempt
that produced it. Every *fresh* attempt for a model therefore retires that
model's pair before the provider is invoked — both files, renamed to
`retired_salvage_{model}.superseded.{stamp}.json` and
`retired_salvage_task_{model}.superseded.{stamp}.json`
(`utils/review_orchestrator_base.retire_salvage_artifacts`, called from
`code_review_orchestrator.run_single_review` and from `run_all_models`'s
`per_model`). It is a rename and never a delete, because the request holds the
raw output the model actually produced and that is the evidence an operator
needs to tell a truncated answer from a dead account; and it is quiet, so what
tells you it happened is the phase dir, not a marker. Three rules follow:

- **Run the task files this run printed `[SALVAGE_TASK]` for.** If you find them
  by listing the directory instead, match `salvage_task_*.json` and take the
  prefix literally — a `retired_salvage_task_…` file is a previous attempt's,
  and its `output_path` is a result file this run has already written.
- **Never rename a retired file back, re-materialize a task from one, or write
  a document recovered from one to its `output_path`.** Do not delete one
  either: it is the evidence, and it is nobody's outstanding work.
- **A request you found by listing is only yours if this run ran that model.**
  Check the request's `model` field against the models this run actually
  dispatched. A model *skipped as already complete* on a resumed run begins no
  attempt, so it keeps its pair and that pair is genuinely outstanding. A model
  *dropped from the selection* between runs also begins no attempt, so nothing
  retires its pair either — it is stale in exactly the way its `{model}.json` is
  stale, and running it would write last run's answer over this run's file.

Neither of the two rules below can catch that one: they judge the reply in front
of them, and a superseded request arrives from an attempt that already ended —
the phantom participant walking in through the one door the gate cannot watch.

**`raw_output` is the text the salvage gate judged, and it is bounded.** It is
chosen by one rule, `utils/review_orchestrator_base.salvage_source`, on all three
losing paths — a non-zero exit, a timeout kill, and a zero exit whose output
would not parse — because a provider can write a truncated array and *then* die:

- **When the adapter reduces its stream, `raw_output` is `salvage_text`**: the
  assistant's answer text and nothing else (for an event-stream CLI, the text of
  its last assistant message — never its tool calls, its reasoning, or the event
  framing around them). The adapter reads its whole stdout to produce it, and
  the harness then redacts it and bounds it **from the answer's opening
  bracket**: text that fits the 45 KB cap is kept whole, and longer text is
  windowed forward from the `[` or `{` the answer opened, so a cut falls at the
  end, never at the start. An empty `salvage_text` is the adapter's verdict that
  there is no answer text at all, and then no salvage is requested — stderr is
  never consulted in its place, because a stream CLI's stderr holds only
  diagnostics.
- **Only when no reducer applies is it still the raw excerpt**:
  `details["stdout_excerpt"]` ahead of `details["stderr"]`, the last 20 lines of
  the stream, each line cut at 64 KB and the whole at 45 KB.

Two consequences when you read a request:

- **Judge the answer text, not the transport stream.** A document is not more
  likely to be the model's answer because of the channel it arrived on — stdout
  is precisely where a CLI's own error event appears — so both rules below apply
  to it unchanged. And when `raw_output` still holds an event stream, only the
  assistant's own text parts can hold the answer: an event's `content` array of
  `thinking`/`toolCall` parts, a tool call's arguments, or a tool's result is
  transport data, however array-shaped it looks.
- **An elision in `raw_output` is the harness's, not the model's.** Every cut
  leaves its own marker in the text, and credential-shaped values are replaced
  with `<redacted:{name}>`. So a document that stops mid-token may have been cut
  by the bound rather than by the provider, and a raw excerpt that starts
  mid-sentence may simply be missing its earlier lines. Recover what is present
  and no more: do not reconstruct a tail you cannot see, and never carry a
  `<redacted:…>` marker into the result as though it were the model's own text.

**One reply is not a result.** When the raw output holds nothing recoverable —
an authentication error, a stack trace, an empty stream — the prompt tells the
subagent to print `{"salvage_failed": true, "reason": "..."}` instead of a
document. **Do not write that object to `task.output_path`, and do not write an
empty array in its place.** That path is the model's *own* result file, so
whatever lands there is read back as that model's review: an empty array would
make a model that never produced a parseable word count as one that reviewed the
input and found nothing — and finding priority is scored partly by how many
models flagged something. Leave the file untouched, so the model stays failed,
which is the true outcome; report the subagent's `reason` beside it. An empty
array that the subagent really did recover from the raw output is a result like
any other and is written normally — **unless the request records
`"failure": "timeout"`**. A run killed at its deadline never said "I found
nothing", so an empty array recovered from it is a non-result: write nothing,
leave the model failed, and report that the run timed out before it wrote an
answer. A timed-out run's recovered findings are still written as usual.

**Not every non-result announces itself.** A stream that was cut off mid-answer
often still carries a relayed provider error — `{"error": {"code": 401,
"message": "User not found"}}`, or the `{"type": "error", "message": "..."}`
record an `opencode`/`codex` run prints as an event — and a subagent can recover
that object perfectly faithfully, report success, and never print the sentinel,
because as far as it can tell it found something. It is still not this model's
review. So before writing: if what came back is neither an array, nor an object
wrapping one, nor an object carrying the answer's own fields (`title`, `desc`,
`importance`, …), treat it exactly as `salvage_failed` — write nothing, leave the
model failed, and report that the raw output held a provider error rather than a
document, which points at the provider's login instead of at a JSON repair.

The same holds for a reply recovered out of an event stream's transport data.
An array a subagent lifted from an event's `content` field — `thinking` and
`toolCall` parts, a tool call's arguments, a tool's output — passes the shape
test, because it *is* an array, but it is not findings the model wrote. It is a
non-result, like a relayed provider error: write nothing, leave the model
failed, and report it as `salvage_failed`, naming it as transport data.

**On this lane both checks are yours, and the second one is the write itself.**
Nothing stands between the subagent's reply and `task.output_path` except you:
under `--exec-subagents` that position is held by
`utils/subagent_executor._salvage_gave_up`, and here there is no such reader. So
apply them in the prompt's own order — the sentinel first, because a subagent
that read the raw output and named what was in it gives a better diagnostic than
anything the shape test can reconstruct from the reply alone; then the shape
test. Decide **before** you back up, not after: a
`{filename}-BEFORE-SALVAGE-{timestamp}.json` sitting beside an unchanged result
file records a salvage that never happened. A near-miss is not a non-result —
a single record where an array was asked for names the answer's own fields, so
it passes the shape test and is a mis-packaged recovery to repackage, not a
provider error to report.

`--exec-subagents` applies both rules on its own lane: the task is recorded in
`subagent_batch_report.json` as `salvage_unrecoverable`, carrying that `reason`,
with nothing written and no retry. The second rule is one shared predicate,
`json_extractor.is_answer_shaped` — the same one that decides whether a salvage
is worth dispatching at all, asked again of what came back. What it buys *there*
is the diagnostic rather than the write: the salvage result shape
(`subagent_executor._salvage_result_errors`) already refuses a top-level object
for not being an array, so an error envelope never reached disk on that lane —
it was reported as `schema_invalid`, "expected a JSON array of suggestions, got
dict", which reads as a botched repair pass and invites another one when the fix
is the provider's login. On *this* lane the same rule stops the write, because an invoker
following the paragraph above it would faithfully persist the envelope. Same
predicate, two different failures prevented.

**A salvage that recovered nothing is finished, and re-running it is the loop to
avoid.** The same raw output through the same prompt has the same answer, which
is why `salvage_unrecoverable` sits in none of the executor's retry sets. Under
`--exec-subagents` the run closes the case for you: the pair is retired as
`retired_salvage_{model}.unrecoverable.{stamp}.json`, and
`[SALVAGE_UNRECOVERABLE] {model}: {reason}` prints on stdout in the place the
`[SALVAGE_NEEDED]` marker would have held — so there is no `SALVAGE NEEDED`
block, no `[REAGGREGATE_AFTER_SALVAGE]` line and nothing recorded as the run's
next command, because the artifacts those blocks look for are gone, not because
a second reporting site re-derived the verdict. Only the terminal verdict is
retired this way; every other salvage failure has a retry rung, stays on disk,
and goes on being advertised precisely so it can be re-run.

**Without `--exec-subagents` none of that fires, and the flow above is unchanged
byte for byte** — this is your lane and it keeps working exactly as documented:
the two markers print, you run each task, you write what is recoverable, you run
the reaggregation the run prints. What is yours by hand is the ending. When a
salvage recovered nothing, write nothing, report the `reason` (or your own
finding from the shape test), and do **not** dispatch that request again. Then
finish the run anyway: reaggregation is still mandatory, because the models that
*did* parse depend on it, and the unrecovered model simply stays failed in the
result. That request is still listed under `SALVAGE NEEDED` in the run output
you are working from — the block was printed by the fan-out, before anyone knew
what the salvage would find, so answering it does not remove it. Treating a
request you have already answered as work still outstanding is what turns a dead
provider account into an endless salvage-and-reaggregate loop.

Two steps that used to live in this prompt are the invoker's, not the subagent's:

1. **Back up before overwriting.** Immediately before writing `task.output_path`,
   run `utils/backup.py` on it; an existing file is copied to
   `{filename}-BEFORE-SALVAGE-{timestamp}.json`.
2. **Delete the salvage request** after reaggregation, not after extraction — the
   request is what the task's `inputs.salvage_request_sha256` binds to. Delete
   only the request you actually consumed: a `retired_salvage_…` file is not
   yours to remove, and deleting one destroys the raw output that says why that
   model failed.

After ALL salvage tasks complete, run reaggregation. The orchestrator prints a
`[REAGGREGATE_AFTER_SALVAGE]` marker with the exact command — copy and run it.
This is mandatory: reaggregation regenerates grouped.json, validation.json and
the report files to include the salvaged data. Do NOT report results to the user
until reaggregation is complete.
