---
name: hand-off-a-task
description: Hand a task to a Rush cloud agent and bring back the result. Use when someone wants work done off their machine or in the background (write tests, upgrade a dependency, research and write a report, investigate an incident), or asks what happened to a task Rush ran earlier.
---

# Hand off a task to Rush

Rush runs the task in its own cloud computer and keeps going while this
conversation moves on. Tool names may carry a client prefix
(`mcp__rush__create_session`). Never ask for a password, token or API key in
chat, and never report a result Rush did not return.

1. **Write the task.** The session knows nothing from this conversation. Put in
   `task` the goal, the files, errors, links and decisions that matter, and
   what done looks like: "open a pull request", "write the report as
   report.md", "answer in a few sentences". For code, add "do not merge" unless
   the person asked for a merge; the agent may otherwise follow merge rules of
   its own. To build on a finished session,
   pass its id as `continue_from`; its answer goes at the top of the new task.
2. **Pick where it runs.** For code, pass `repo`: a GitHub repository, branch
   (`/tree/<branch>`) or pull request URL from `list_repositories`, or a
   gitlab.com project. If the team keeps a Project for that repository
   (`list_projects`), pass `project` instead; it brings the Project's standing
   instructions and secrets. Name a saved agent with `agent` when one fits
   (`list_agents`), and the accounts the task may use in `connections`
   (`list_connections`). Leave out what the task does not need; with no
   `agent`, Claude Code does the work.
3. **Start it.** Call `create_session` once, with a fresh UUID you write
   yourself as `request_id` (no shell command needed). If the call errors and
   you retry, send the same `request_id` so only one session starts. For
   independent tasks, start one session each.
4. **Wait.** Tell the person it is running, then call `wait_for_sessions` with
   every id and `timeout_seconds: 50`, again until `settled` is true. A session
   past the runs-at-once limit starts `queued`; keep waiting. With several,
   `until: "any"` lets you report each one as it lands.
5. **Read the result.** `get_session` has the answer, branch, pull request and
   the files it made. `get_session_changes` lists the changed files
   (`include_diff` for the diff); `get_session_artifact` reads one file by
   name. Use `list_session_events` only to explain how the agent got there or
   why it failed.
6. **Continue or stop.** `send_session_message` continues in the same computer,
   with its files and conversation, for 7 days after it goes idle; follow it
   with `wait_for_sessions`. `cancel_session` stops the session and releases
   its computer, after which no follow-up is possible; ask before stopping one.

Report each session in a few lines: its status, the answer, and the pull
request or file links. `needs_review` means Rush could not confirm the result:
say so and show what the agent reported. On `failed`, give the error and the
next step; do not retry silently.

**Work started earlier.** When the person asks about Rush work without an id,
call `list_sessions` (newest first; filter by `status`), match on the first line
of each answer, then read the one they mean with `get_session`.

## When Rush refuses

A refused call's text starts with a code, and often a `Next:` step; follow it.
For these, tell the person the fix in one line:

| Code | Fix |
|---|---|
| `TOKEN_LIMIT_REACHED`, `CREDITS_EXHAUSTED`, `SPEND_CAP_REACHED`, `PAYMENT_METHOD_REQUIRED`, `COMPUTE_LIMIT_REACHED`, `WEEKLY_COMPUTE_LIMIT_REACHED` | Relay the message; it names the fix. Model accounts are at https://cloud.getrush.ai/console/settings/?section=accounts and billing at https://cloud.getrush.ai/console/settings/?section=billing |
| `RESOURCE_NOT_ACCESSIBLE` | Rush's GitHub App does not reach that repository. Add it at https://cloud.getrush.ai/console/settings/?section=connections, or run without `repo`. |
| `CONNECTION_NOT_READY` | Call `connect_account` with `type` `app` (gmail, linear, slack, …) or `mcp` (with its `url`), and `name`; for an agent made from a template, also `agent`. A gitlab.com project needs `name` `gitlab`. Give the `authorize_url` to the person to open in their own browser; never open or fetch it. It works once, for 10 minutes. Start the session again once `list_connections` shows it connected. |
