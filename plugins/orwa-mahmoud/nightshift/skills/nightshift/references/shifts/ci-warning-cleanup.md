# CI warning cleanup — finite — repository-owned warnings the pipeline already prints

The warnings your CI or local gate already emits, clustered and fixed at the cause. The list is
whatever a clean run of those commands prints today, so it ends.

Use when the log is full of deprecations and warnings nobody owns, not when you want a major
upgrade night (that is the dependency-upgrade sweep) or a lint-debt dump (that is clear quality
debt).

Supported wherever the project's own CI or item-gate commands print warnings or deprecations
(compiler, test runner, bundler, linter in report mode). Skip warnings that exist only on a
host this repository does not run.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **CI warning cleanup — fix repository-owned warnings and deprecations at the cause.**
  - Never select this entry when work mode is artifact.
  - Discovery: run the project's CI-equivalent or item-gate commands in the configuration this
    repository already uses. Capture the warning/deprecation lines, dedupe against snag-log.md
    (ALL seen — fixed and rejected), and split **repository-owned** (this repo's code, scripts,
    config) from **external** (upstream libraries, the runner image, a tool this repo does not
    control).
  - Work repository-owned warnings one cluster at a time: fix the cause, run the item gate,
    commit. Re-run the same capture after each cluster.
  - External warnings stay in the receipt as unresolved — name the emitter and why it is not
    this repository's to fix. Do not silence them to make the log look clean.
  - Never add a suppression, ignore directive, or disabled check to hide a warning.
  - Never turn off a CI job or skip a gate to clear the list.
  - Never perform an unrelated major dependency upgrade; if the only fix is a major bump, park
    it for the dependency-upgrade sweep.
  - Ends when a full recapture reports no remaining repository-owned warnings, and every
    leftover external warning is recorded in snag-log.md with emitter and reason.
  - Verify: the item gate is green at every commit; the final capture lists only parked external
    warnings, each with a reason.
```
