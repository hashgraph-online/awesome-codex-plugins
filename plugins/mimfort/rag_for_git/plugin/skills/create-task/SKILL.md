---
name: create-task
description: Create a task on a configured board with canonical server-side structure. Use when the user asks to file or create a task on the board.
---

# Create Task

Reply in Russian. The server assembles the canonical body (Проблема / Что сделать / Критерии
приёмки / Контекст), so clients never implement board markup or send credentials.

1. **Config.** Read `task_board` from `.review.yml`; otherwise call `get_board_config()`. Read
   only `type`, `project`, `create_target`, `done_target`, and `options`. No board is a board-less
   no-op: explain it in Russian and stop.
2. **Draft.** Build `problem`, `steps`, `criteria`, and `context`. Ground `problem` with
   `search_codebase(...)` and actual `path:line` evidence. Use technical Russian: **no emoji**,
   decorative separators, or marketing tone.
3. **Discover.** Call `get_board_targets(board_type=<type>, project=<project>,
   provider_options=<task_board.options or {}>)`. Its response has `targets` and `options`:
   each option declares `required_for` and `choices`. Use `create_target` only when it is among
   create-purpose targets. If a required create option is absent, discover it or ask the user;
   never guess. Empty discovery may create without a target only when no required option is missing.
4. **Confirm.** Show the title, selected target label, selected options, and complete body. Write
   **only after explicit confirmation**; never write to the board silently.
5. **Write.** Call
   ```
   create_task(title=…, problem=…, steps=[…], criteria=[…], context=…,
               board_type=<type>, project=<project>, target=<create_target or null>,
               provider_options=<task_board.options or {}>)
   ```
   On `status == "error"`, report the reason in Russian and stop.
6. **Re-index.** Call `sync_board(board=<project or null>, board_type=<type>,
   provider_options=<task_board.options or {}>)`. Report the task key, URL, warnings, and result.

All reads stay fail-open. The confirmed `create_task` call is the only write.
