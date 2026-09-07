# Documentation writing — finite — sourced docs from an outline or tree

Use when the owner wants a scoped document created, revised, consolidated, or gap-analyzed from
explicit sources, repository evidence, or an approved outline — not a silent rewrite of product
policy, and not documentation-drift (that entry only restores docs to the current tree).

Supported on any repository or artifact folder that can hold the deliverable. Follow
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/cited-research.md`. Typical hours: 2–4.

```text
- [ ] **Documentation writing — turn named sources into a scoped, cited deliverable.**
  - Discovery: read only the owner-approved outline, URL list, and local files. Write a dated
    source manifest (`ok` / `unavailable`) first. Repository evidence is files in the work
    target; do not invent flags, commands, or behaviour those files do not show.
  - Work one deliverable: create, revise, consolidate, or write a gap analysis. Every important
    claim is cited `[ID]`. Observations stay in Observations; policy or UX recommendations stay
    in Inferences. Never silently change project policy, licensing, or safety wording.
  - Verify relative links, fenced examples, and commands against `ok` sources and the tree.
    Project-native doc checks (the item gate) run before each commit or artifact receipt.
    A command that only appeared in an `unavailable` source is a gap, not a documented feature.
  - Repository mode: one conventional commit in the work target. Artifact mode: write-receipt into `$NS/receipts/`
    for the deliverable and manifest. Both leave the cited-research report beside the doc.
  - Review first writes the deliverable only. Direct mode may edit authorized local doc files
    named in the report; it never publishes or deploys.
  - Inherit cited-research.md. Keep private code, secrets, customer data, and unpublished
    material out of external fetches and out of the deliverable.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every supplied source is `ok` or `unavailable` with a reason, check-report passes,
    and named links/examples in the deliverable resolve or are marked unavailable.
  - Verify: `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh" --project "$NIGHTSHIFT_WORKSPACE"
    --report <doc.md> --manifest <sources.tsv> --output <doc.md>` (native Windows:
    `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1"`); the item gate is green at
    every commit or artifact receipt.
```
