---
name: review-session
description: Review what changed in this session with RepoPilot before claiming work is done or that tests pass. Use after edits to tests, CI config, auth, or request handling, and whenever you are about to say "all tests pass".
---

# Review the session with RepoPilot

RepoPilot compares the repository with the snapshot taken when this session
started. It is deterministic and local: the same change gives the same answer.

1. Run `repopilot review --since-snapshot`.
2. Read `Decision`, then the `Definitely sensitive` and `Maybe sensitive` lists.
3. For every `integrity.*` signal — a focused, skipped, or removed test, a test
   that lost assertions, or a new suppression — either restore the check or
   state plainly in your reply why the change is intended. A green test run does
   not answer these signals: the run is what changed.
4. For security signals (auth check removed, untrusted input reaching a sink),
   confirm the guard still exists on that path or fix it.

5. Treat `behavioral.quiet-fallback-introduced` as a review candidate, not proof
   of harm. Inspect the caught operation and returned fallback, and preserve
   recovery behavior when it is intentional. This medium-confidence signal does
   not block the review gate.

Do not report the work as complete while a weakened check or a removed
safeguard is open and unexplained. Other sensitive signals, such as a changed
workflow or dependency, are context for the reviewer: mention them, but they
do not need to be undone.
