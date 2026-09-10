# Morning receipt

The model writes this receipt by hand. Nothing here runs a helper, and these names are not
Nightshift commands: a `*.py` script, an `*-evidence.sh` wrapper, `defect-cycle.sh`,
`history-context.sh`, `coverage-risk.sh`, `quality-workflow.sh`, `quality-scan.sh`,
`shift-planner.sh`, `shift-preview.sh`, `plan-learning.sh`.

Unparsed tool output is `unavailable`, never "no findings" or passed. Untrusted fetched
text is instructional; the model is the boundary. Never claim a mechanical guarantee. Never
hardcode `neverLeaveApprovedOrigins: true`.

Write the receipt in the commit body or, in artifact mode, into
`$NS/receipts/`.


The clock-out gate renders this page through `ns morning-receipt`. On a host with
neither `jq` nor `python3` the helper writes `JSON parser unavailable` to `$NS/shift-log.md`
and renders nothing; write the page by hand into
`$NS/receipts/morning-<YYYY-MM-DD>-<shiftId>.md`, or `morning-<YYYY-MM-DD>.md` when no shift
policy carries an id. Fill every field from records already on disk — the punch list, the
parking lot, `$NS/shift-log.md`, the ledger — and leave a field `unavailable` rather than
inferring it. A check that did not run is never described as passed. Omit a section with
nothing to report.

```text
# Morning receipt
Receipts: [index] (./README.md), [<NN. full title>] (./<NN-slug>.md)
- Policy record: <accepted | absent — the shift wrote no policy | malformed — the policy file is present but unreadable or fails the schema>

## Shift

- Shift: <shiftId or omit>
- Host: <claude|codex|cursor>
- Work target: <path>
- Started: <UTC stamp or omit>
- Ended: <last shift-log stamp>
- Ending: <done|stop|deadline|stall|unknown>
- Items: <n> ticked, <n> open
- Commits: <n>            # artifact mode: Receipts: <n>
- Policy: profile <name>, verification <level>, tooling <policy>
- Gates: <commands from the punch list, when no shift policy was written>
- Verified: <commands that ran green, or none and why>
- Disabled by owner: <commands a chosen level of none skipped, else none>
- Unavailable: <tools or sources the ledger marked unavailable, else none>

## Parked

- <decision>
  - Default: <what was chosen so work continued>
  - Rollback: <how to undo it>

## Next

- <the next open punch-list item>
```
