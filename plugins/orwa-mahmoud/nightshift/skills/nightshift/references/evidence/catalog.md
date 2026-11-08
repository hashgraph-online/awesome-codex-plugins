# Evidence catalog

Read this only after the owner says yes to evidence lines. An `Evidence:` line sits beside
`Verify:` in the item. It names what lets a reviewer see the work at a glance, without rerunning
it. Suggest from the kind that fits the item, name concrete widths, commands and figures, and
leave the owner to keep, edit or drop each line.

One line, or a list under it:

```text
  - Evidence: before/after screenshots at 375 and 1280 px, light and dark
```

```text
  - Evidence:
    - the benchmark command, the machine, and before/after figures
    - the tests added and the behaviour each covers
```

Evidence shows the work. `check` off leaves the tick alone, `report` names a missing file, and `block` keeps the stop open. `Verify:` is what must pass.

List the kinds with `ns catalog-index --catalog evidence`. Each line is the key, the title, the
description, the source, and the sources a same key replaced, tab-separated. The source is
`plugin`, `user`, `project`, or a configured folder. Then read in full only the kinds that fit
the drafted items. Where an owner's kind and a shipped kind both fit, the owner's wins. An item
that fits none is offered one draft, written only after the owner says yes. An item that fits two
kinds takes the evidence of both, trimmed to what a reviewer would actually open.

To add a kind, follow `evidence/recipe.md`.
