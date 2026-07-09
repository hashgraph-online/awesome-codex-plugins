---
name: reviewer_finish-task
description: After a task's PR is created, offer to close the task on the board — append the PR link to the task description and mark it done — so the reviewer's incremental sync re-indexes the updated task. Use when the user says the PR is up / asks to close/finish the task ("закрой задачу", "PR готов", "finish the task", "mark task done", "заверши задачу"). Server-side write via the reviewer MCP tool finish_task (works in any client). Requires the reviewer MCP server + a configured board.
---

# Finish Task

After a PR is created for a task, close that task on the board: idempotently append the
PR link to its description and mark it done. The write bumps the task's last-modified, so
the next `sync_board` re-indexes the updated task (done status + PR edge). Reply to the user
in Russian.

## Pipeline

1. **Config.** Read the `task_board` block (`type`, `project`, `done_state`, `status_field`,
   `done_column`) from the repo's `.review.yml`; if there is no block, fall back to
   `get_board_config()`. No board resolved / board MCP not needed here (write is server-side) —
   but no board type at all → **board-less no-op**: tell the user (in Russian) the task is not
   linked to a board and stop. `status_field` names the YouTrack status field (default `State`);
   `done_column` names the YouGile column to move the task into. Each is board-specific — the
   other board ignores the irrelevant key.

2. **Resolve the task key.** In order, stop at the first hit:
   - current branch: `git branch --show-current`, match the board's `key_pattern` (e.g. `PRI-\d+`);
   - the most recent brief: newest `docs/superpowers/briefs/*<KEY>*.md` (its heading carries the key);
   - the PR body/title (`gh pr view --json title,body`), match `key_pattern`;
   - else ask the user for the key. No key → **no-op** (nothing to close).

3. **Resolve the PR URL.** `gh pr view --json url -q .url` (GitHub) or `glab mr view` (GitLab).
   If none is found, ask the user for the PR URL.

4. **Offer + confirm.** Show what will be written — the PR link + the **resolved done target, named
   explicitly** (not a generic "mark done"): for yougile «перенесу задачу в колонку „<done_column>“ +
   отмечу completed» (or just «отмечу completed» when `done_column` is unset); for youtrack «выставлю
   <status_field> = <done_state>» — plus any optional note. Ask the user to **confirm** before writing,
   and whether they want to add an optional note (details under the task). **Never write to the board
   silently** — the move / mark-done happens **only after explicit confirmation**, even when the values
   are already set in `.review.yml`.

5. **Write.** Call `finish_task(key=<key>, pr_url=<url>, note=<note or null>, board_type=<type>,
   done_state=<done_state or null>, status_field=<status_field or null>,
   done_column=<done_column or null>)`. `status == "error"` → report the reason (in Russian),
   fail-open.

6. **Re-index.** Call `sync_board(board=<project or null>, board_type=<type>,
   status_field=<status_field or null>)` (incremental) so the just-closed task is re-indexed
   with its real status (its last-modified is now past the cursor). Cheap when the corpus is warm.

7. **Report.** Tell the user (in Russian) what was written (done + PR link) and the sync result. If
   `already_closed` is true, say the task was already closed (no duplicate PR link added).

## Failure handling (fail-open)

- No board configured / no task key → board-less no-op with a short Russian note; never abort.
- `finish_task` error (board unreachable, key unresolved on the board, State command failed) → report
  the reason and stop; the PR is already created, the board write is a secondary effect.
- Read-only intent everywhere except the single `finish_task` write, which is explicitly confirmed.
