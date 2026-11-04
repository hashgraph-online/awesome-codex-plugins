# Recording a code batch's own check

A subagent that edited code — an implement task that declares files, or an apply-code-fixes batch — ends its reply with a `check` object saying which checks it ran on its edits. Record it on that batch's `util batch-done` call with `--own-check`, by the first rule below that fits the object. The `--exec-subagents` leg reads the same object by the same rules (`subagent_executor.batch_check_findings`), so both legs record the same result.

## Words the rules use

- **A finding**: an entry of its `findings` (a bare string or object is one entry) that is not empty. Beside a `passed` that is true, an entry that only says nothing was found (`"none"`, `"n/a"`, `"no problems found"`, `0`) is no finding either.
- **`passed` is true** when it reads `true`, `"true"`, `"yes"`, `"pass"`, `"passed"` or `1`; **false** when it reads `false`, `"false"`, `"no"`, `"fail"`, `"failed"` or `0`; anything else (missing, `null`, `"maybe"`) is **neither**.
- **`ran` maps a command to failed** when that command's outcome reads `"failed"`, `"fail"`, `"fails"`, `"failing"` or `false`; to **passed** for `"passed"`, `"pass"`, `"ok"`, `"success"` or `true`; to **not run** for `"not run"`, `"skipped"` or `"could not run"`. A list of `"<command>: <outcome>"` strings, or of `{"command": …, "outcome": …}` objects, is read the same way.
- **It ran nothing** when its `ran` is there and names no command it ran: `ran` is empty (`{}` or `[]`), or each entry is not run or the result shape's placeholder `<each check command you ran>` copied as it is (as a key, a string, or an object's `command`); or it has no `ran` at all but gives a `not_run` reason (a non-blank string).

## The rules

1. **No `check` object** (none at all, `null`, or not an object): leave `--own-check` out.
2. **`could_not_run` is true**: `--own-check findings --finding "its check could not run: <its findings, joined with "; ">"` (just `--finding "its check could not run"` when it names none).
3. **It ran nothing** — its `passed: true` is then a pass of nothing, never a pass:
   - it names a finding: `--own-check findings` and one `--finding` per finding, whatever `passed` says;
   - else, `passed` is false: `--own-check findings` with no `--finding` (it said its check failed and named nothing);
   - else: `--own-check none` — it ran no check, which is never a pass.
4. **Otherwise** — its `ran` names a command it ran, or its `check` has neither `ran` nor a `not_run` reason (an older reply):
   - `passed` is true: `--own-check passed` (what it lists beside a pass, such as `npm test: 12 passed`, is not a failing check), unless `ran` maps a command to failed: then `--own-check findings` and one `--finding "<command>: failed"` per such command;
   - `passed` is false: `--own-check findings` and one `--finding` per finding, plus one `--finding "<command>: failed"` per command `ran` maps to failed that no finding names (no `--finding` at all when there is neither);
   - `passed` is neither: as for false when it names a finding or `ran` maps a command to failed; else `--own-check passed` when `ran` maps a command to passed; else `--own-check none`.

Each `--finding` is a finding as the reply wrote it, character for character, with no words of yours added: a finding that repeats one the user accepted for a check counts as accepted only when it says nothing more. A `note` in the `check` (the subagent's own words about its checks, such as that a failure is the accepted one) is recorded with `--note "<its note>"` beside `--own-check`, never as a `--finding`; the `--exec-subagents` leg records the same note, and neither leg reads it as a finding. A note is a comment, never a failure: every failure the check printed stays a `--finding`, so a `[FINDING_RESTATE]` call is run only when the words it moves to `--note` are a comment, never when they report something the check printed beyond the accepted finding (another value, test or line).

`--own-check findings` is recorded with `--status completed`: the edits are kept and the check is reported as failing. An apply-code-fixes batch's `listed` is recorded beside it, one `--listed-check "{command}={outcome}"` per entry (step 6 of its runbook): a command it lists as failed is a failing check whatever the rules above gave, and a `passed: false` that names no finding beside a `listed` naming no failure is read as no failing check.
