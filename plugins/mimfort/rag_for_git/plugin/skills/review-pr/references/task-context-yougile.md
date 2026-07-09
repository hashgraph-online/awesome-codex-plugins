# Task context playbook — Yougile

Use this when `task_board.type == "yougile"`.

Goal: read the task identified by the resolved key and build a `TaskBrief`. Build it best-effort —
omit or empty any field you cannot resolve. A partial brief is fine; a wrong one is not.

Tools are exposed as `mcp__<task_board.mcp>__<tool>`, where `<task_board.mcp>` is the server named
in config (e.g. `yougile`). The steps below use that prefix implicitly.

## 1. Fetch the task

Call `get_task` with the resolved key. Yougile resolves three `id` forms, so the key from the PR
works directly:

- the task UUID;
- the project code `idTaskProject` — e.g. `PRI-34` (per-project counter);
- the company code `idTaskCommon` — e.g. `ID-34` (company-wide counter).

The default `key_pattern` (`[A-Z]+-\d+`) matches both code forms, so a PR may reference either.
If `get_task` errors or returns nothing, treat the task as not found (see Failure handling).

## 2. Map the response to TaskBrief

`get_task` returns identifiers, not display names, for status and subtasks — resolve them. It does
NOT return a task link:

| TaskBrief field | Source in `get_task` response   | How to fill it |
|---|---|---|
| `key`       | resolved `idTaskCommon` (`ID-N`, company-wide) | canonical — globally unique, stable |
| `aliases`   | `[idTaskProject]` (`PRI-N`, per-project)       | other codes of the same task; lets a PR referencing either code resolve to one node |
| `title`       | `title`                               | use as-is |
| `description` | `description`                         | requirements usually live here |
| `status`      | `columnId` — a UUID, NOT a name       | call `get_column` with that id → its `title`; on error omit |
| `criteria[]`  | `subtasks[]` — UUIDs, NOT titles      | optional: `get_task` each id → its `title` (see note); else `[]` |
| `url`       | `task_board.url_template` with the **project code** | the web link fragment is the project code (`…/team/<teamId>/#PRI-4`), so substitute `PRI-N` (not `ID-N`); default `null` if no template |
| `links[]`   | `subtasks[]` + `description` text              | two sources, merged and deduplicated by key: (1) for each subtask UUID, `get_task` it → `{type:"subtask", key:<its idTaskCommon>, title}` (best-effort; a failed fetch is skipped); (2) scan `description` for all matches of `task_board.key_pattern`, exclude own `key`/`aliases` and subtask keys already resolved → `{type:"related", key}` (no extra `get_task`, key alone is enough for the graph edge) |

**Canonical key note.** A PR may reference either code (`PRI-N` or `ID-N`); both resolve via
`get_task`. Always set `key` to the company-wide `idTaskCommon` and put the project `idTaskProject`
in `aliases` — `index_task` stores both as the node's `codes`, so the task is one node regardless of
which code a PR used.

**Criteria note.** Each subtask is itself a task; resolving its title costs one `get_task` call
per subtask. Do this only when `description` is thin on acceptance criteria. When criteria are
written inline in `description` (a bulleted / checklist section), leave `criteria[]` as `[]` — the
requirements prompt reads `description` anyway, so nothing is lost.

**URL note.** The Yougile API does not expose a task link directly, so `url` comes from
`task_board.url_template` (use a `{code}` placeholder for the web-facing code). The web URL fragment
uses the **project code** (`PRI-N`), e.g. `https://<host>/team/<teamId>/#PRI-4` — substitute the
`idTaskProject` value (`PRI-N`) for `{code}`, NOT the canonical `idTaskCommon`/`ID-N`.
A missing `url` only drops the hyperlink in the summary — the task is still named by `key` + `title`.

## 3. Optional discussion context

`get_task_chat` / `get_task_messages` add discussion context. Use ONLY when `description` is too
thin to judge requirements. Not required.

## Failure handling (fail-open)

If the board MCP server is not connected, any tool errors, or the task is not found, do NOT build a
`TaskBrief` — skip the requirements dimension and note the reason in the summary. A failure in a
secondary step (e.g. `get_column` for status, or a subtask fetch) must NOT abort brief-building:
keep the fields you already have and move on with a partial brief. Never abort the review.
