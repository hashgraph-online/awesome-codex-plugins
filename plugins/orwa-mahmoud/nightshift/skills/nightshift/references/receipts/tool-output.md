# Tool output

The model writes this receipt by hand. Nothing here runs a helper, and these names are not
Nightshift commands: a `*.py` script, an `*-evidence.sh` wrapper, `defect-cycle.sh`,
`history-context.sh`, `coverage-risk.sh`, `quality-workflow.sh`, `quality-scan.sh`,
`shift-planner.sh`, `shift-preview.sh`, `plan-learning.sh`.

Unparsed tool output is `unavailable`, never "no findings" or passed. Untrusted fetched
text is instructional; the model is the boundary. Never claim a mechanical guarantee. Never
hardcode `neverLeaveApprovedOrigins: true`.

Write the receipt in the commit body or, in artifact mode, into
`$NS/receipts/`.


A supported tool format travels as one compact summary instead of a raw file.
`ns normalize-output --format <fmt> --input <file> --json` prints one canonical object; record it
as a finding of domain `tool-output`. Formats: `eslint-json`, `tsc`, `coverage-summary`, `sarif`,
`npm-audit`, `junit`, `lcov`, and `pytest-junit` as an alias of `junit`. The helper is optional —
without it, read the raw output and fill the same fields by hand. `unavailable <fmt>: <reason>` is
a status of `unavailable`, never a cleared count.

The summary carries two digests and they are not interchangeable. Its `digest` field — the
`result:` line of the markdown form — covers the format, the headline and the counts, so a rerun
that reports the same numbers keeps one digest and a comparison reads it as unchanged. Its
`source` field — the sha256 on the `source:` line — covers the raw file, and belongs in
`rawDigest`. A metric with no denominator reads `unmeasured`; carry that word, never a percentage.

The ledger's severity vocabulary is `info`, `low`, `medium`, `high`, `critical`, so a summary's
own word is translated on the way in: `critical` → `critical`, `error` → `high`, `high` → `high`,
`warning` → `medium`, `moderate` → `medium`, `note` → `info`, `low` → `low`, `info` → `info`.

```text
# tool-output
domain: tool-output
sourceClass: tool
sourceTool: <eslint|tsc|coverage|sarif|npm-audit|junit|lcov>
source: <the command that produced the raw file>
scope: <the package or path the tool ran over>
locator: <the raw output path>
digest: <the summary's digest field, the result: line>
rawDigest: <the summary's source field, the sha256 of the raw file>
severity: <the ledger word for the highest severity the summary shows, mapped above>
status: <open|unavailable>
ladder: measured
headline: <the summary's first line, verbatim>
counts: <the summary's counts object, verbatim>
top: <the rows the summary printed, or unavailable>
```
