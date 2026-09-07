# Build When Missing

Use this when a repository has no clear harness inventory or usable agent entrypoint. Pattern sources include full harness repositories with root docs and checks, medium harness repositories with generated reports, and thin repositories that only need an entrypoint plus validation mapping.

## Equivalent Artifacts

- Existing entrypoints, architecture docs, validation docs, trackers, ledgers, reports, or dashboards may already satisfy harness roles.
- Record the chosen artifacts under `Detected Mapping` before recommending new files.
- Use `references/harness-profiles.json` to choose a minimum role set and route each role to the owning skill.

## Minimum Files

- `AGENTS.md` or an explicitly mapped equivalent agent entrypoint.
- `docs/validation.md`, a validation section in README, or a mapped validation command surface.
- `docs/harness-assessment.md` for the first inventory if no generated report exists.
- `ARCHITECTURE.md` or a mapped architecture source only when the repository needs an explicit boundary map.

## Bootstrap Steps

1. Identify the repository archetype from `references/harness-profiles.json`.
2. Inventory existing entrypoints, docs, scripts, CI, artifact directories, trackers, reports, and ledgers.
3. Choose one canonical agent entrypoint and classify other instruction files using `entrypoint-policy.md`.
4. Classify each harness role as mapped, partial, absent, or intentionally omitted: entrypoint, work-state, ledger, contracts, validation, runtime evidence, and quality.
5. For absent roles required by the archetype, name the smallest artifact that would make the role discoverable.
6. Write `docs/harness-assessment.md` with current state, detected mapping, gaps, and no more than three next slices.
7. Link the assessment from the mapped entrypoint or README so future agents can find it.

## Validation

- Run a docs/structure check if one exists.
- If no checker exists, verify that the assessment links to concrete files or explicitly says "absent".
- Confirm every recommended next slice names a file, command, or directory to create.
- Confirm mirrors, generated copies, or pointers follow `entrypoint-policy.md`.

## Do Not Include

- Private URLs, credentials, account names, or environment-specific hosts.
- A full platform roadmap before the first minimum slice is justified.
- Multiple independent agent instruction files for the same rules.
- Product-specific workflow details copied from a pattern source.
