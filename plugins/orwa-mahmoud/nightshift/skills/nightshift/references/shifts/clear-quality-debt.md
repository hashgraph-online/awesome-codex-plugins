# Clear quality debt — finite — the backlog your tools already know about

The finite counterpart to the hunts: the work is a list your own tooling produces, so it ends when
that list is clear. Quality uses this entry in either launch mode: Review first scans without writes
and waits for an explicit disposition; Run directly composes, arms, and works the findings without
a second pause.

```text
- [ ] **Clear quality debt — fix what the project's own tooling reports.**
  - Scan first: run the item-gate commands from `## Gates` in report mode (lint, types, tests),
    per top-level package in a monorepo. Cluster the findings by tool and directory.
  - Work one cluster per cycle: fix the root cause behind the item gate, commit, re-scan.
  - Never silence instead of fixing — no new suppressions, no relaxed config, no deleted tests. A
    finding the owner should decide on goes to parking-lot.md with a default, and work continues.
  - Dedupe against snag-log.md (ALL seen — fixed and rejected) so a rejected finding is not raised
    a second time.
  - Ends when a full scan reports nothing new, or at quitting time if hours were set.
  - Verify: the item gate is green at every commit.
```
