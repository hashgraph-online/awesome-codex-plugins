---
name: fix-a-bug
description: Have a Rush cloud agent reproduce a bug, fix it and open a pull request with a test. Use when someone shares an error, a stack trace, a failing test or CI run, or a bug report or issue and wants it fixed in a repository.
---

# Fix a bug with Rush

1. **Gather what the agent needs.** The session cannot see this conversation or
   the person's machine, so collect: the repository, the exact error or stack
   trace, how to trigger it, what should happen instead, and any file, commit
   or CI link already suspected. Paste an issue's text rather than only its
   link. Ask one question if the repository or the symptom is missing.
2. **Start it.** Call `create_session` with the repository (or the branch the
   bug is on) as `repo`, a fresh UUID you write yourself as `request_id`, and
   a `task` like:
   "Fix this bug. <symptom, error, steps>. First reproduce it and write a test
   that fails because of it. Then fix the cause, not the symptom, and run the
   test suite. Open a pull request that explains the cause, the fix and the
   test, and do not merge it. If you cannot reproduce it, stop and report what
   you tried." Leave out "do not merge" only when the person asked for a merge.
3. **Wait** with `wait_for_sessions` (`timeout_seconds: 50`) until it settles;
   a fix takes several minutes.
4. **Report.** From `get_session`: the cause in a sentence or two, the pull
   request link (a merge request on gitlab.com), and whether the new test
   failed before the fix and passes after. `get_session_changes` with
   `include_diff` shows the change when the person wants to read it here. If it
   could not reproduce the bug, give what it tried and ask for the missing
   detail.
5. **Iterate in the same session.** Review comments or a red check go back
   with `send_session_message` ("CI fails on lint: fix it and push"), so the
   agent keeps its computer and context and updates the same pull request.

Refusals: see `hand-off-a-task` under "When Rush refuses".
