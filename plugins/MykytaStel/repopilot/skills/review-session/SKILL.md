---
name: review-session
description: Review what changed in this session with RepoPilot before claiming work is done or that tests pass. Use after edits to tests, exports/public APIs, CI config, auth, or request handling, and whenever you are about to say "all tests pass".
---

# Review the session with RepoPilot

RepoPilot compares the repository with the snapshot taken when this session
started. It is deterministic and local: the same change gives the same answer.

1. Run `repopilot review --since-snapshot` (or call `repopilot_review_change` via MCP).
2. Read `Decision`, `Checks this change weakened`, and the `Definitely sensitive` / `Maybe sensitive` lists.
3. For every `integrity.*` signal — a focused, skipped, or removed test, an early `exit(0)` short-circuit, a test or shared helper that lost assertions, or a new suppression — either restore the check or state plainly in your reply why the change is intended. A green test run does not answer these signals: the run is what changed.
4. For broken local API contract signals (`behavioral.removed-export-still-imported`, `behavioral.rust-public-*`), update the surviving local callers or restore the contract before finishing.
5. For security and taint signals (auth check removed, untrusted input reaching SQL, shell, or filesystem/path sinks), confirm the guard or sanitizer exists on that path or fix it.
6. To inspect one signal's provenance, impact route, and verification steps, run `repopilot review --since-snapshot --explain-signal <signal_id>` (or call `repopilot_explain_review_signal`).
7. Treat `behavioral.quiet-fallback-introduced` (empty `catch {}`, `except: pass`, `if err != nil {}`, `Err(_) => {}`) as a review candidate, not proof of harm. Inspect the caught operation and returned fallback, and preserve recovery behavior when it is intentional.

Do not report the work as complete while a weakened check, broken local caller,
or removed safeguard is open and unexplained. Other sensitive signals, such as
a changed workflow or dependency, are context for the reviewer: mention them,
but they do not need to be undone.
