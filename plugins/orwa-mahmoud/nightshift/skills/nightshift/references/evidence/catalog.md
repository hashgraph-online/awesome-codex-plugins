# Evidence catalog

Read this only after the owner says yes to evidence lines. Each kind of item below names the
evidence that lets a reviewer see the work at a glance, without rerunning it. Suggest from the row
that fits the item, name concrete widths, commands and figures, and leave the owner to keep, edit
or drop each line.

An `Evidence:` line sits beside `Verify:` in the item. One line, or a list under it:

```text
  - Evidence: before/after screenshots at 375 and 1280 px, light and dark
```

```text
  - Evidence:
    - the benchmark command, the machine, and before/after figures
    - the tests added and the behaviour each covers
```

Evidence shows the work; it never decides a tick. `Verify:` is what must pass.

| Kind of item | Evidence |
| --- | --- |
| UI | Before/after screenshots at named widths (for example 375 and 1280 px), light and dark. A short recording for a flow of more than one step. |
| Performance | The exact command, the machine and its load, before/after figures with units, and the run count behind each figure. |
| Tests | The tests added, the behaviour each one covers, and the coverage change for the touched files. |
| API or contract | A sample request and response, and the schema diff. For a breaking change, the old and new shape side by side. |
| Docs | The rendered page, or a screenshot of it, and the link check output. |
| Data or migration | Row or record counts before and after, the migration's own output, and the rollback command. |
| Security | The scan command and its output, and each finding's disposition: fixed, accepted with a reason, or not applicable. |
| Refactor | What moved where, what stayed behaviour-identical, and how that was shown: the unchanged tests, a before/after output diff, or both. |
| CLI or tooling | The command run and its output before and after, including the error a user sees. |
| Configuration or infrastructure | The resolved config diff, the plan or dry-run output, and how the change is undone. |

An item that fits no row needs no line. An item that fits two rows takes the evidence of both,
trimmed to what a reviewer would actually open.
