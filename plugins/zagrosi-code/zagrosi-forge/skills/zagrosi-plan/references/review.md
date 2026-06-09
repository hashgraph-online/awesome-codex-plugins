# Plan Review Protocol

Review for failure modes before creating sections.

Strong review files are substantial. In `standard` mode, target at least 1,000
words for a review pass; in `deep` mode, target at least 1,800 words or split
findings into the six review-board perspectives.

Check:

- requirements missed or contradicted
- ambiguous ownership between modules
- hidden migrations or data compatibility issues
- security and authorization gaps
- concurrency, idempotency, and retry behavior
- observability and operational gaps
- missing tests or untestable design
- section boundaries that would cause merge conflicts

Write findings under `reviews/`. Then create `codex-integration-notes.md` with:

- accepted changes
- rejected changes with rationale
- plan edits made
- residual risk

Update `codex-plan.md` after review. Do not leave important feedback only in
the review file.

The integration notes should be specific enough that a future reader can tell
which review findings changed the plan, which were rejected, and which residual
risks remain accepted.
