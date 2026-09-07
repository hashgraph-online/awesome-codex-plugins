# Dead-code cleanup — finite — code proven unused by tooling the repository already trusts

Unused exports, files, branches, or dependencies reported by analyzers and build tools already in
the project. Each deletion carries evidence; dynamic or uncertain references stay untouched.

Use only when the repository already has a dead-code, unused-export, dependency, compiler, or
coverage tool capable of producing findings. Supported stacks are whatever that configured tool
supports. If no such tool is configured, this shift is unsupported and must not start.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Dead-code cleanup — remove only code the project's existing tooling proves unused.**
  - Never select this entry when work mode is artifact.
  - Discovery: detect and run the repository's configured unused-code tooling, compiler checks, or
    dependency analyzer. Record its exact command and findings; dedupe against snag-log.md (ALL
    seen — fixed and rejected). Do not introduce a new analyzer without owner approval.
  - Take one coherent finding at a time. Confirm it is not reached through reflection, dynamic
    imports, registration, configuration, generated code, public exports, or external consumers.
    Remove it, run the item gate and the original analyzer, commit.
  - Park uncertain findings in snag-log.md with the analyzer evidence and the reference that could
    not be ruled out. Uncertainty is not permission to delete.
  - Never infer dead code from intuition, naming, low coverage, or a text search alone.
  - Never delete a public API, migration, plugin entry point, compatibility shim, or generated
    artifact merely because the local analyzer cannot see its consumer.
  - Never add ignore rules or weaken the analyzer to make its report clean.
  - Ends when the original analyzer reports no actionable findings, and every uncertain or
    externally consumed finding is parked with its evidence and reason.
  - Verify: the item gate is green at every commit; the existing dead-code analyzer is rerun after
    every deletion and the final repository build or package check succeeds.
```
