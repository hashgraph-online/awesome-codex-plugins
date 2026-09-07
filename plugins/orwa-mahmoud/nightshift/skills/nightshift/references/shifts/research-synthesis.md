# Research synthesis — finite — decision-ready comparison of named sources

Use when the owner hands an explicit URL list or local files and needs one synthesis they can
act on: agreement, contradiction, confidence, and limits — not a stack of isolated summaries.

Supported on any repository or artifact folder. Follow
`$NIGHTSHIFT_PLUGIN_ROOT/skills/nightshift/references/cited-research.md`. Keep the source
manifest and working notes on disk so a later shift resumes without losing provenance.
Typical hours: 2–4.

```text
- [ ] **Research synthesis — compare named sources into one cited decision brief.**
  - Discovery: read only the owner-approved URLs and local files. Write a dated source manifest
    (`ok` / `unavailable`) and a notes file that quotes or paraphrases each `ok` source with its
    `[ID]` before drafting the brief. Do not add sources from memory.
  - Synthesize: compare sources, expose agreement and contradiction, separate observations from
    inferences, and state confidence and limits on every important conclusion. Cite `[ID]` on
    every important claim. An `unavailable` source is recorded, never filled in.
  - Leave the manifest and notes in the work target (repository commit or artifact receipt) so
    a later shift can resume from the same provenance. Do not replace them with a summary that
    drops locators or retrieval times.
  - Review first writes the brief, manifest, and notes only. Direct mode may update those local
    files; it never publishes. Artifact mode completes with write-receipt into `$NS/receipts/`
    on the brief, notes, and manifest.
  - Inherit cited-research.md. Keep private code, secrets, customer data, and unpublished
    material out of external fetches and out of the brief.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected).
  - Ends when every supplied source is `ok` or `unavailable` with a reason, contradictions among
    `ok` sources are named, check-report passes, and the notes file still lists each `ok` id.
  - Verify: `"$NIGHTSHIFT_PLUGIN_ROOT/runtime/check-report.sh" --project "$NIGHTSHIFT_WORKSPACE"
    --report <synthesis.md> --manifest <sources.tsv> --output <synthesis.md> --output <notes.md>`
    (native Windows: `& "$NIGHTSHIFT_PLUGIN_ROOT\runtime\windows\check-report.ps1"`); the item gate
    is green at every commit or artifact receipt.
```
