# Build When Missing

Use this when a repository has no clear harness inventory. Pattern sources include full harness repositories with root docs and checks, medium harness repositories with generated reports, and thin repositories that only have an entrypoint plus task board.

## Equivalent Artifacts

- Existing entrypoints, architecture docs, validation docs, trackers, ledgers, reports, or dashboards may already satisfy harness roles.
- Record the chosen artifacts under `Detected Mapping` before recommending new files.
- Use `references/harness-profiles.json` to choose a minimum role set for the repository archetype.

## Minimum Files

- `AGENTS.md` or an explicitly mapped equivalent agent entrypoint.
- `ARCHITECTURE.md`, `docs/architecture/index.md`, or a mapped architecture source.
- `docs/validation.md`, a validation section in README, or a mapped validation command surface.
- `docs/harness-assessment.md` for the first inventory if no generated report exists.

## Bootstrap Steps

1. Identify the repository archetype from `references/harness-profiles.json`.
2. Inventory existing entrypoints, docs, scripts, CI, artifact directories, trackers, reports, and ledgers.
3. Classify each harness role as mapped, partial, or absent: entrypoint, work-state, contracts, validation, runtime evidence, ledger, quality, commit discipline.
4. For absent roles required by the archetype, name the smallest artifact that would make the role discoverable.
5. Write `docs/harness-assessment.md` with current state, detected mapping, gaps, and the next three slices.
6. Link the assessment from the mapped entrypoint or README so future agents can find it.

## Validation

- Run a docs/structure check if one exists.
- If no checker exists, verify that the assessment links to concrete files or explicitly says "absent".
- Confirm every recommended next slice names a file, command, or directory to create.

## Do Not Include

- Private URLs, credentials, account names, or environment-specific hosts.
- A full platform roadmap before the first minimum slice is justified.
- Product-specific workflow details copied from a pattern source.
