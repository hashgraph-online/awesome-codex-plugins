# Documentation media accuracy — finite — verify named screenshots and GIFs against a local UI

Use when the owner names documentation screenshots or GIFs that may no longer match the product. The app must be reproducible from this checkout with an identifiable build and existing dependencies. The owner wakes to a checked list of verified, corrected, or parked media, with the evidence for each result.

Typical hours: 1–3. Supported stacks: repositories with in-tree UI source, documentation media, and an existing local build, run, and capture path for the selected flow. Never select this entry in artifact mode.

Write the work receipt from `receipts/cycle-specialist-evidence.md` using `mode: doc-media-accuracy`. Record the commands, flows and assets actually checked, findings or `unavailable`, and skipped assets. Output that cannot be parsed is `unavailable`, never an empty result or "no findings".

```text
- [ ] **Verify the named documentation screenshots and GIFs against the current local UI.**
  - Discovery: use only the owner-named documentation files and media. Resolve each selected image or GIF to its tracked source file, the exact local app route or flow it depicts, and the repository's documented build and capture instructions. Identify the checked-out commit and app version before comparing anything. Use only the existing local environment and dependencies; if the app, version, or flow cannot be reproduced locally, park that asset with the missing evidence.
  - Work one asset at a time. Replay the documented flow in the locally running app with fixture or non-sensitive test data. Compare only factual UI state, visible copy, controls, and the order of steps. Replace a mismatched asset only through the repository's existing capture procedure, then reopen the changed documentation page and verify the replacement. Record the source commit, flow, and result in the item receipt; put unresolved mismatches in snag-log.md with the evidence and reason.
  - Never fetch or inspect a public website or remote asset, use credentials, enter private or customer data, or install new tools or dependencies. If the app needs a live service, authentication, or unavailable environment, park the asset.
  - Never use generated, edited, stock, or mock images as proof of product behavior. Never change product code or behavior, rewrite unrelated documentation, remove an original asset, or publish or deploy media. Do not change UI copy or captions unless the selected local flow proves the specific factual mismatch.
  - Dedupe against snag-log.md under Snag log discipline.
  - Ends when every owner-selected asset is verified against the identified local build, replaced from a reproduced local capture and reverified, or parked with a specific evidence gap.
  - Never select this entry in artifact mode.
  - Verify: run the repository's documented build and UI smoke-test commands for the selected flow, then reopen every touched documentation page and inspect its media. Report the exact commands and results. If a required command, app state, or capture path is unavailable, park the asset; never invent a substitute or claim the check passed.
```
