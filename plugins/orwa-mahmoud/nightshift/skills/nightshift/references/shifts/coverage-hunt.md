# Coverage hunt — open-ended — "give it the night, wake up to tests"

A night spent adding behavior-protecting tests against the work-target repository until quitting
time.

Supported on a repository-mode work target that already has a test runner. Never select this entry in artifact mode. Do not `git init` a notes folder to make tests commitable.

```text
- [ ] **Coverage hunt — add meaningful tests until quitting time.**
  - Ending: open-ended — hours and a deadline are required.
  - Never select this entry when work mode is artifact.
  - Each cycle: find the highest-value untested behaviour, write behavior-protecting tests, run the item
    gate, commit. Coverage is a tripwire, never a target — no padding tests to move a number; any
    exclusion needs a written reason.
  - Log one line per cycle. Stop only at quitting time, then clock out orderly.
  - Verify: the item gate is green at every commit.
```
