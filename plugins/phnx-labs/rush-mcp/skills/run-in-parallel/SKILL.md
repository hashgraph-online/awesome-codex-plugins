---
name: run-in-parallel
description: Run many Rush tasks at once, one cloud computer each, and gather the results. Use when someone has a list of independent pieces of work (issues to fix, repositories to update, files or pages to research, flaky tests to chase), or wants several approaches to one problem tried side by side.
---

# Run tasks in parallel with Rush

Each Rush session has its own computer and shares nothing with the others, so
independent work runs side by side instead of in a queue.

1. **Split the work.** Make one task per item that can be done without the
   others' results. Each task is self-contained: the goal, its inputs, and the
   same definition of done for every item ("open one pull request and do not
   merge it", "write findings.md"; leave out "do not merge" only when the
   person asked for merges). Work that touches the same files belongs in one
   task, not several racing pull requests. Show the person the list and confirm
   before starting more than five.
2. **Start them.** Call `create_session` once per item, each with its own fresh
   UUID, written yourself, as `request_id`, and the same `repo`, `project` or
   `agent` where they share one. Keep a table of item to session id. Sessions
   past the account's runs-at-once limit start `queued` and begin as others
   finish.
3. **Gather.** Call `wait_for_sessions` with all the ids (up to 20 per call),
   `until: "any"` and `timeout_seconds: 50`. Report each session as it
   settles, then call again with the ones still running.
4. **Summarize.** One row per item: its status, a one-line answer, and the pull
   request or file link. List `failed` and `needs_review` items first, with
   their reasons. To redo one, send a follow-up to that session with
   `send_session_message` rather than starting over.

**Several approaches to one problem.** Start one session per approach with the
same task and the approach named in it, then compare the results side by side:
what each changed (`get_session_changes`), whether tests pass, and the
trade-off. Let the person pick; offer `cancel_session` for the others only when
they ask.

Refusals: see `hand-off-a-task` under "When Rush refuses".
