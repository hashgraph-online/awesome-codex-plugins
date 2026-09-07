# Dependency upgrade sweep — finite — the version drift your package manager already tracks

The work nobody schedules: hundreds of small mechanical steps, each one provable by the test suite.
The list is whatever the package manager reports as outdated, so it ends. Six to eight hours clears
a year of drift on a mid-sized project; a monorepo wants a second night.

Supported wherever a package manager reports outdated direct dependencies — npm/pnpm/yarn, uv/pip,
cargo, go modules.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Dependency upgrade sweep — bring direct dependencies current, one at a time.**
  - Never select this entry when work mode is artifact.
  - Discovery: the project's own outdated report — `pnpm outdated` / `npm outdated`,
    `uv pip list --outdated`, `cargo outdated`, `go list -u -m all`. **Direct dependencies only**:
    a transitive version is not yours to pin, and forcing one is the owner's call.
  - Order patches, then minors, then majors, so a night that ends early still landed the safe wins.
  - Per package: read the release notes and migration guide FIRST, upgrade, adapt the code the
    breaking changes require, run the item gate, commit. One package per commit — a failing gate
    has to point at one cause.
  - Time-box a major. If adapting it sprawls past a bounded attempt, revert clean and park it with
    what was learned: a half-migrated major leaves the tree worse than the old version did.
  - A green gate proves only what it covers. Where a core package is thinly tested, park it rather
    than claim the adaptation worked.
  - Never take a prerelease (`rc`, `beta`, `next`). Never hand-edit the lockfile — let the package
    manager write it, and commit it with the change that caused it. Never change the package
    manager, the runtime version, or add overrides to force a pass; park those instead.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected) so a rejected upgrade is not retried.
  - Ends when the outdated report names no direct dependency, or at quitting time if hours were set.
  - Verify: the item gate is green at every commit.
```
