# Defect hunt — open-ended — the review cycle, ridden to convergence

A night spent reviewing the work-target repository for defects, fixing each behind the item gate,
and re-reviewing until a full pass finds nothing new.

Supported on a repository-mode work target. Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Defect hunt — review, fix, re-review until it converges.**
  - Ending: open-ended — hours and a deadline are required; convergence may finish it earlier.
  - Never select this entry when work mode is artifact.
  - Each cycle: review for defects; dedupe every finding against snag-log.md (ALL seen — fixed and
    rejected) so a later cycle never re-reports an earlier one; fix each behind the item gate;
    append dispositions; re-review.
  - Stop at the first valid ending: a full pass finds nothing NEW (converged), or quitting time.
    Zero new findings is success — stop even with time on the clock.
  - Verify: the item gate is green at every commit; snag-log.md dispositions are current.
```
