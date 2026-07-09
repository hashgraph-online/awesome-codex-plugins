# Build When Missing

Use this when a repository has tests but no clear command surface. Pattern sources include repositories with `check_repo_harness.py`, `doctor.py`, validation pipelines, JSON reports, JUnit output, and CI gates.

## Equivalent Artifacts

- Manifest scripts, Makefile targets, CI jobs, task runner commands, or existing doctor commands may already satisfy the validation role.
- Record the chosen artifacts under `Detected Mapping` before creating a default checker.
- Use `templates/validation-matrix.md` to document the mapping when no validation guide exists.

## Minimum Files

- `scripts/check_repo_harness.py`, `scripts/doctor.py`, or an explicitly mapped equivalent validation command.
- `docs/validation.md`, `docs/runbooks/validation.md`, README validation section, or a mapped validation matrix.
- CI workflow step that runs the minimum checker.
- Optional JSON/JUnit output directory under `artifacts/` for runtime or manual checks.

## Bootstrap Steps

1. Inventory existing commands from manifests, Makefiles, task runners, scripts, and CI.
2. Map existing commands to change types before creating new commands.
3. Create a change-type matrix: docs, contracts, unit/type/lint, runtime, and external-dependency checks.
4. Implement a minimum checker only if no mapped command can validate required docs, command availability, and known generated artifacts.
5. Add stdout output for humans and stable JSON/JUnit only when automation will consume it.
6. Wire the minimum checker or mapped command into CI before adding heavier runtime gates.

## Validation

- Run the minimum checker from a clean checkout or documented setup.
- Confirm docs-only changes do not require heavy runtime checks.
- Confirm runtime-sensitive changes have an escalation path beyond static checks.

## Do Not Include

- A single heavyweight command for every change type.
- Skip/fallback behavior that is not recorded.
- External dependency credentials, account names, or machine-specific setup hidden in the checker.
