---
name: sync-tasks
description: Warm the task graph and vector store by synchronizing a configured task board through the reviewer MCP server. Use when the user asks to sync or index board tasks.
---

# Sync Tasks

Reply in Russian. This is a thin, server-side trigger: the server enumerates, normalizes, and
indexes the board. Do not enumerate tasks in the client and do not send credentials.

1. Resolve the repository path with `git rev-parse --show-toplevel`, then run
   `git -C <path> remote get-url origin`. For HTTPS and SSH URLs, remove the scheme, userinfo, and
   host; for scp-style remotes, remove everything through the host's first colon. Preserve every
   path segment after the host or scp colon, remove the leading slash, strip a trailing `.git`, then
   lowercase and validate the result as the canonical lowercase repository id (`owner/name` or
   `group/.../name`). Examples:

   - `https://gitlab.example.com/group/sub/repo.git` → `group/sub/repo`
   - `ssh://git@gitlab.example.com/group/sub/repo.git` → `group/sub/repo`
   - `git@gitlab.example.com:group/sub/repo.git` → `group/sub/repo`

   If origin is missing or ambiguous, ask for the complete namespace/repo id; do not guess from the
   directory name.
2. Resolve branch independently. Pass a non-null branch only when the user explicitly supplied or
   selected one and it is in the tracked branches list (`REVIEW_BRANCHES`). With no explicit tracked
   selection, pass `branch=null` so the server uses its primary tracked branch. Never infer the
   branch from the current worktree branch or blindly pass an untracked feature branch.
3. Call only repo mode with operation flags. The server owns effective board-policy resolution; do
   not reconstruct policy in the client:

   ```text
   sync_board(repo=<canonical owner/name or group/.../name>,
              branch=<explicit tracked branch or null>,
              limit=<limit or null>,
              purge_orphaned=<explicit request or false>,
              keep_with_prs=<explicit request or true>,
              force_renormalize=<explicit request or false>)
   ```
4. If the result is a configuration or policy error, explain it in Russian and stop. Do not retry
   through unfiltered explicit mode: that could enumerate or purge the wrong task corpus.
5. Report the server-side summary in Russian, including `eligible`, `filtered_by_age`,
   `filtered_archived`, `age_unknown`, `archive_unknown`, `filter_applied`, `filter_fingerprint`,
   `filter_source`, `by_board`, `purge`, and `warnings`. Explain warnings and leave the local
   repository unchanged.

`sync_board` is idempotent: rerunning is safe and inexpensive when the watermark is warm. It reads
the board; it never writes back.
