# Task context playbook — Jira

Use this when `task_board.type == "jira"`.

Goal: read the task identified by the resolved key and build a `TaskBrief`.

1. The board MCP server is the one named by `task_board.mcp` (e.g. `atlassian`). Its tools are
   exposed as `mcp__<task_board.mcp>__<tool>`.
2. Fetch the issue by key (e.g. `PROJ-123`) using the Atlassian MCP's get-issue tool
   (`getJiraIssue` / `jira_get_issue`, depending on the connected server).
3. Build the `TaskBrief` from the issue (best-effort — omit/empty any field that is absent):
   - `key`         ← issue key
   - `aliases`     ← `[]` (the Jira issue key is already the single canonical, globally-unique key).
   - `title`       ← summary
   - `description` ← description (rendered text)
   - `criteria[]`  ← Acceptance Criteria field if present; otherwise bullet items parsed from the
                     description; else `[]`
   - `status`      ← status name
   - `url`         ← issue browse URL
   - `links[]`     ← from `issuelinks` — one entry per linked issue as
                     `{type:<link type, e.g. blocks/relates/duplicates>, key:<issue key>, title:<summary>}`.
4. Optional: comments may add context — use only if needed.

Failure handling: if the board MCP server is not connected, the tool errors, or the issue is not
found, do NOT build a `TaskBrief` — skip the requirements dimension and note the reason in the
summary. Never abort the review.
