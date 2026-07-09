---
name: reviewer_sync-tasks
description: Warm the task graph & vector store by indexing a board into the reviewer MCP server. Use when the user asks to sync/index tasks ("sync tasks", "index the board", "просиндексируй задачи") so search_tasks/get_task_context have a corpus. Requires the reviewer MCP server with board credentials configured server-side (YOUGILE_API_KEY or YOUTRACK_TOKEN).
---

# Sync Tasks

Index the configured task board into the reviewer task graph + vector store so
`search_tasks` and `get_task_context` are useful before many PRs have accrued.

Enumeration, normalization and indexing all happen **server-side**: the reviewer
MCP server connects to the board's REST API itself, normalizes each task into a
`TaskBrief`, and indexes it. You do **not** read the board, you do **not** pass any
task payload — you call one tool and print its summary. A sync costs O(1) LLM tokens
regardless of board size.

Always answer the user in Russian (this skill body is English to save tokens).

## Inputs

Parse from `$ARGUMENTS` (all optional):
- `--board <project>`: limit to one project by task code prefix (e.g. `PRI`). If omitted, read
  `task_board.project` from the repo `.review.yml` (deploy default via `get_board_config()` otherwise).
- `--board-type <yougile|youtrack>`: limit the sync to one board type. If omitted, read
  `task_board.type` from the repo `.review.yml`. Empty both → deploy-wide sync of every configured board.
- `--limit <N>`: index at most N tasks (a quick smoke run). Note: `--limit` also
  disables `--purge-orphaned` and watermark advance (a partial walk can't compute
  the full active-key set), so use it only for smoke runs.
- `--purge-orphaned`: after indexing, delete tasks no longer on the board from the
  store/graph. Off by default.
- `--no-keep-with-prs`: with `--purge-orphaned`, also delete tasks that have PR
  history (`:IMPLEMENTED_BY`). By default such tasks are protected.

## Pipeline

1. **Resolve `board_type` from `.review.yml`.** Run `git rev-parse --show-toplevel`
   to find the repo root. Read `<root>/.review.yml` and extract `task_board.type`
   (e.g. `"youtrack"`). Fallback chain:
   - `.review.yml` not found or has no `task_board` block → call `get_board_config()`
     and read `task_board.type` from the deploy default.
   - Still not resolved → use `board_type=null` (syncs all configured boards).
   Similarly extract `task_board.project` → `board` (or `--board` override), and
   `task_board.status_field` → `status_field` (YouTrack status field name; default `State`
   server-side when null).

2. **Call the tool once.** Map the parsed arguments to a single call:

   ```
   sync_board(
       board_type=<type from step 1 or null>,
       board=<--board or task_board.project or null>,
       status_field=<task_board.status_field or null>,
       limit=<--limit or null>,
       purge_orphaned=<True if --purge-orphaned else False>,
       keep_with_prs=<False if --no-keep-with-prs else True>,
   )
   ```
   Scoping by `board_type` + `board` keeps this repo's sync to its own board/project (PRI-170);
   an empty project syncs everything (and mixes projects on read).

   The server enumerates the board over REST (incremental via a per-board timestamp
   watermark — a repeat sync touches ~0 tasks), normalizes every task into a
   `TaskBrief`, indexes changed ones in a single Voyage batch (dedup by
   `content_hash`), auto-links PRs found in descriptions
   (`:Task-[:IMPLEMENTED_BY]->:PR`), and optionally purges orphans.

3. **Print the summary (in Russian).** The tool returns a counts dict with an optional
   `by_board` key. If `by_board` is present, report per-board first, then total:

   ```
   Синк завершён:
     youtrack / PRI: 64 задачи, изменено 2 (эмбеддинги: 0), без изменений 62
   Итого: 64 задачи, изменено 2.
   ```

   If `by_board` is absent (old server): report aggregate counts only —
   «N задач на доске, изменено M (эмбеддинги: K), без изменений U, ошибок F».
   If `purge` is present, add «Purge: D удалено, P защищено (есть PR-история)».
   Surface any `warnings`.

4. **Handle the error case.** If the tool returns `{"status": "error", "reason": ...}`,
   the board is not configured server-side. Tell the user (in Russian) to add the board
   credentials to the reviewer-mcp env file — the canonical `~/.config/rag-reviewer/.env`
   (NOT the repo `./.env`: reviewer-mcp runs with an arbitrary CWD and reads the XDG file
   first) — namely `YOUGILE_API_KEY` (for Yougile) or `YOUTRACK_TOKEN` +
   `YOUTRACK_BASE_URL` (for YouTrack), plus `TASK_BOARD_KEY_PATTERN` /
   `TASK_BOARD_URL_TEMPLATE` for normalization. Then reconnect the MCP server
   (`/mcp` reconnect or restart Claude Code — env is read at process start) and retry.

   For **Yougile**, also explain how to obtain `YOUGILE_API_KEY`:
   - **Configurator (easiest):** in Yougile press `Ctrl + ~` (or Projects → gear ⚙ next to
     the company name → «Настроить») → API settings → generate/copy the key.
   - **REST:** `POST https://yougile.com/api-v2/auth/keys` with `{login, password,
     companyId}` (get `companyId` via `Ctrl + Alt + Q`, or `POST /api-v2/auth/companies`);
     `POST /api-v2/auth/keys/get` lists existing keys.

   Do not attempt to read the board yourself, and never ask the user to paste the key into
   the chat — it belongs in the env file only.

## Notes

- The board REST credentials live only in the reviewer-mcp deploy environment
  (`YOUGILE_API_KEY` or `YOUTRACK_TOKEN`), never in this skill or the conversation.
- This skill is read-only on the board; it never writes back.
- `sync_board` is idempotent: re-running is safe and cheap (watermark + content_hash).
