---
name: finishing-the-task
description: Use when you are done, or think you are, and the user will come back to the stickypane board to see that it is: check the work against what done means, tick the last step with its proof, and leave one line that says the outcome.
metadata:
  cases: checklist-C3 checklist-C10
---

# Finishing the task

```sh
# what done means, written down before you call it done
stickypane todo add done-cache "go test ./... passes"
stickypane todo add done-cache "p95 under 200 ms in bench.sh"
stickypane todo add done-cache "docs/usage.md says how to turn the cache off"

# check each against a command, then tick it
go test ./... && stickypane todo check done-cache "go test"
stickypane todo check done-cache "p95"
stickypane todo check done-cache "docs"

# the outcome in one line
stickypane log add worklog --time "cache done: p95 900 → 180 ms, 41/41 tests, docs updated"
```

Shapes: checklist for what done means; log for the outcome; a note or a
form in the recipes below.

## How

- Write the list of what done means from what the user asked, not from
  what you did. An item you cannot check with a command or a file is a
  question for the user.
- Tick an item only after its command passed or you read the file: a
  tick is a claim the user will trust.
- An item that is not met stays unticked; say which and why in the
  outcome line. Do not call the task done.
- The outcome line has the numbers that matter, so a user back from a
  break knows in ten seconds.
- Leave the notes where they are: they are the record. `stickypane note
  hide` the ones that were only for the way there.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/a-pr-summary.md`: what changed, why, how it was checked, what was not touched.
- `references/a-review-verdict.md`: the user approves the change or asks for changes, in a form.
