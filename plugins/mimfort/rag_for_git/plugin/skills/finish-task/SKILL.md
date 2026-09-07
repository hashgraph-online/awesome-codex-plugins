---
name: finish-task
description: After a task's PR is created, offer to close the task on the configured board and reindex it. Use when the user says a PR is up or asks to close or finish a task.
---

# Finish Task

Reply in Russian. The server appends the PR link idempotently, completes the selected generic
target, and adds a clickable task link to the PR body; clients never send credentials.

1. **Config.** Read `task_board` from `.review.yml`, otherwise `get_board_config()`. Use only
   `type`, `project`, `create_target`, `done_target`, and `options`. If no board is resolved,
   report a board-less no-op.
2. **Resolve key and PR.** Match `key_pattern` on the current branch, newest `briefs` file, or
   `gh pr view --json title,body`; otherwise ask. Resolve the PR URL with `gh pr view --json url -q
   .url` (or ask). Missing key or URL is a no-op.
3. **Discover.** Call `get_board_targets(board_type=<type>, project=<project>,
   provider_options=<task_board.options or {}>)`. Select `done_target` from `targets` with a done
   purpose. For each option with `required_for` containing `finish`, resolve its value from
   `choices`; if required metadata is missing, ask instead of guessing.
4. **Offer + confirm.** Show the PR link and the **resolved done target** by its label plus every
   selected option, and state that a task link will be prepended to the PR body. Ask whether to add an optional note. Write **only after explicit confirmation**;
   never write to the board silently.
5. **Write.** Call
   ```
   finish_task(key=<key>, pr_url=<url>, note=<note or null>, board_type=<type>,
               target=<done_target or null>, provider_options=<task_board.options or {}>)
   ```
   On `status == "error"`, report the reason in Russian and stop.
6. **Re-index.** Call `sync_board(board=<project or null>, board_type=<type>,
   provider_options=<task_board.options or {}>)`, then report the write and sync result. When
   `already_closed` is true, state that no duplicate PR link was added. Report the task link from
   `task_link_status`, not from `task_link_added` alone: `added` — the link was written now;
   `already_present` — it was already in the PR body, so report it as normal (an idempotent no-op,
   never as a problem); `failed` — only then relay the warning verbatim, and the board write still
   succeeded. `task_link_added` stays `true` only for `added` (older deploys may omit
   `task_link_status`: treat a missing field as `added`/`failed` by whether warnings mention the link).

All reads are fail-open; the explicitly confirmed `finish_task` call is the only write.
