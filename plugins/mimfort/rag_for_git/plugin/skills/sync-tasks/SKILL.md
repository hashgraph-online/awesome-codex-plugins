---
name: sync-tasks
description: Warm the task graph and vector store by synchronizing a configured task board through the reviewer MCP server. Use when the user asks to sync or index board tasks.
---

# Sync Tasks

Reply in Russian. This is a thin, server-side trigger: the server enumerates, normalizes, and
indexes the board. Do not enumerate tasks in the client and do not send credentials.

1. Read `task_board` from `.review.yml`; if absent, call `get_board_config()`. If neither resolves
   a board, report a board-less no-op.
2. Read only generic metadata: `type`, `project`, `create_target`, `done_target`, and `options`.
   Do not infer provider-specific fields.
3. For an incomplete configuration, call
   `get_board_targets(board_type=<type>, project=<project>, provider_options=<task_board.options or {}>)`.
   Its response contains `targets` and option entries with `required_for` and `choices`. Ask the
   user to configure missing required options instead of inventing values; discovery is read-only.
4. Call:
   ```
   sync_board(board=<project or null>, board_type=<type>,
              provider_options=<task_board.options or {}>, limit=<limit or null>,
              purge_orphaned=<explicit request or false>)
   ```
5. Report the server-side summary and its `by_board` breakdown in Russian. Warnings and an error
   response are fail-open: explain the reason and leave the local repository unchanged.

`sync_board` is idempotent: rerunning is safe and inexpensive when the watermark is warm. It reads
the board; it never writes back.
