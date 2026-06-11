# Build When Missing

Use this when architecture intent exists only in conversations or conventions. Pattern sources include repositories with `ARCHITECTURE.md`, contract docs, diff/audit checkers, generated baselines, and allowlists.

## Equivalent Artifacts

- Architecture indexes, design docs, lint rules, import-boundary checks, or review policies may already satisfy the contract role.
- Record the chosen artifacts under `Detected Mapping` before creating default architecture or checker files.
- Add default files only for missing roles, not for surfaces already covered by an equivalent.

## Minimum Files

- `ARCHITECTURE.md`, `docs/architecture/index.md`, or an explicitly mapped architecture source.
- `docs/architecture/contracts.md`, a contract section, or an explicitly mapped equivalent.
- `scripts/check_repo_contracts.py` or a mapped checker command.
- Baseline or allowlist file under `docs/generated/`, `scripts/baselines/`, or `scripts/harness-baselines/`.

## Bootstrap Steps

1. Map existing architecture and contract sources.
2. Write or amend the architecture map only for missing source-of-truth coverage.
3. Choose two or three rules that can be checked mechanically before adding more.
4. Create or map a checker with diff mode for changed files and audit mode for full-repository reports.
5. Put historical violations in a baseline or allowlist with owner, reason, and repayment note.
6. Make new violations fail while historical debt remains visible.

## Validation

- Run diff mode against changed files.
- Run audit mode and confirm historical findings are reported without blocking unexpectedly.
- Verify failure messages include path, rule, reason, and suggested direction.

## Do Not Include

- Rules that cannot be checked or reviewed consistently.
- A baseline that silently hides all debt without a report.
- Product-specific ports, service names, or private deployment paths from pattern sources.
