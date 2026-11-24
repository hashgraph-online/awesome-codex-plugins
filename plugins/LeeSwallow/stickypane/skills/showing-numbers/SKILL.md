---
name: showing-numbers
description: Use when you have numbers the user should see at a glance: test counts, a value over runs or commits, a distribution, or how far along a task is. Shows them as a chart on the stickypane board, updated in place, and leaves counting to the board where it can.
metadata:
  cases: chart-C4 chart-C7
---

# Showing numbers

```sh
# the latest numbers, in the same place each run: set replaces
stickypane chart set tests pass 41
stickypane chart set tests fail 2
stickypane chart set tests skip 3

# how far along: the board counts the checklist, you count nothing
stickypane note write progress --type chart --open <<'EOF'
---
from: refactor
---
EOF
```

Shapes: chart (bars; `view: spark` a trend line; `view: heat` a calendar
when the labels are dates); log when each value needs a sentence.

## Which command

| The number | Write |
| --- | --- |
| the current value, replacing the last | `stickypane chart set <name> <label> <n>` |
| a count that grows | `stickypane chart add <name> <label> <n>` |
| one value per run, for a trend | `chart set` with the run as the label: `chart set flaky run-12 4` |
| how much of a checklist or board is done | a chart with `from: <note>` |

## How

- Only numbers you measured: a test count, a time from a run. Not
  numbers you estimate (tokens, cost): a chart makes a guess look exact.
- Say how many runs a rate or a time comes from.
- `from:` counts for you, and keeps up as the steps are ticked: prefer it
  to keeping a count yourself. More on `from:`: `connecting-notes`.
- Never write the numbers of a `from:` chart.
- `${CLAUDE_PLUGIN_ROOT}/rules/touching-the-board.md` applies.

## Recipes

- `references/a-trend-over-runs.md`: a rate over many runs, as a trend line.
- `references/a-benchmark-report.md`: many numbers in one table, read once.
- `references/a-script-that-charts.md`: a script the user runs that writes its own result into a chart.
