---
name: reviewer_configure-review
description: Configure or update a repo's .review.yml context layer (subsystem cluster depth, per-prefix depth overrides, summary top-k threshold, ignore for noisy *tracked* paths, context_limits retrieval breadth per repo profile) and its task board selection (which board this repo uses — yougile/youtrack — key_pattern, url_template; never credentials) from a draft the skill generates and the user edits. Use when the user asks to set up or tune review config ("настроить .review.yml", "configure review config", "настрой контекст-слой", "tune cluster depth", "что игнорировать в ревью", "выбрать доску для репо", "set up reviewer for this repo"). Standalone baseline — needs only git, no reviewer MCP / DB required; optionally uses the reviewer MCP tool count_tasks to size context_limits.search_tasks.
---

# Configure review (.review.yml context layer)

Scan the repo's **tracked** tree (plus churn), generate a recommended `.review.yml` context layer
(cluster depth, per-prefix depth overrides, summary top-k threshold, ignore for noisy tracked
paths), show it as a draft + diff, let the user adjust, then write it — preserving every other key.
Standalone baseline: uses `git` and file editing — works on a fresh repo before the first index.
Two optional exceptions use the reviewer MCP when connected: sizing `context_limits.search_tasks`
via `count_tasks(project)`, and the finish-task done-target pick-list via
`get_board_targets(board_type, project)`; if the reviewer MCP is absent (fresh repo / older deploy)
or a tool errors, the skill **falls back to asking** the user. Everything else needs
**no reviewer MCP / Postgres / Neo4j**.

**Always answer the user in Russian** (the project language), regardless of this file's language.
Commands, code identifiers and `path:line` stay verbatim.

## Scope

Edit **only** these keys of `.review.yml`:
- `summary_cluster_depth` — global subsystem cluster depth.
- `summary_cluster_depth_overrides` — per-prefix depth (longest-prefix-match by directory segments).
- `summary_topk_threshold` — summary-prior scale threshold.
- `paths.ignore` — only for **tracked** noisy paths (eval, fixtures, generated, vendored, migrations, data).
- `context_limits` — per-repo retrieval breadth (search_codebase / search_tasks / graph limits,
  PRI-202), recommended from a **repo profile**. Written as a full documented block.
- `task_board` — which board THIS repo uses (`type: yougile|youtrack`), plus `key_pattern`, (yougile only)
  `url_template`, `project`, and the **finish-task done target**: `done_column` (yougile) or
  `status_field` + `done_state` (youtrack). **NEVER** write credentials here — board API keys live only in
  the reviewer deploy env (`YOUGILE_API_KEY` / `YOUTRACK_TOKEN` + `YOUTRACK_BASE_URL`). An empty
  `task_board:` disables the board for the repo.

Do NOT touch any other key (`categories`, `severity_threshold`, `max_comments`, `min_confidence`, …). Do NOT run a
reindex/resummarize. Do NOT walk the filesystem or try to detect untracked junk: `.venv`,
`node_modules`, `__pycache__`, `dist`, `build` are gitignored, so they never reach the git-tracked
index / graph / summaries — there is nothing to add to ignore for them.

## Inputs

Parse from $ARGUMENTS (all optional):
- `--path <path>`: repo clone path. Default: current working directory.
- `--branch <branch>`: branch whose tree to scan and whose `.review.yml` to edit. Default: the
  current git branch.

## Pipeline

1. **Preflight.** Resolve `--path` (default cwd) and `--branch`
   (`git -C <path> branch --show-current`; if empty/detached, use the current HEAD ref). Verify a git
   repo: `git -C <path> rev-parse --git-dir`. Not a repo → tell the user (in Russian) and stop. No
   database or reviewer MCP is required.

1.5. **Check .env completeness (offer `reviewer init` if needed).**
   Resolve the canonical .env path:
   ```bash
   echo "${REVIEWER_ENV_FILE:-${XDG_CONFIG_HOME:-$HOME/.config}/rag-reviewer/.env}"
   ```
   (fallback: `~/.config/rag-reviewer/.env`, then `./.env` for dev). Read and parse `KEY=VALUE` lines
   (skip comments and blank lines). If the file doesn't exist — tell the user (Russian):
   > .env не найден по пути `<path>`. Запустить `reviewer init` для первоначальной настройки?

   If the file exists, check critical groups:
   - **GitLab VCS:** `GITLAB_TOKEN` — if empty, warn.
   - **Доска задач:** `YOUGILE_API_KEY` and `YOUTRACK_TOKEN` — if both empty, warn.
   If any are missing → tell the user (Russian):
   > В .env не хватает полей: `<list>`. Запустить `reviewer init` чтобы дополнить?

   User can decline — skill continues normal pipeline. This check is **read-only** (parse
   `KEY=VALUE` lines); no reviewer MCP / Postgres / Neo4j needed. **Do NOT run** `reviewer init`
   automatically — only offer.

2. **Scan the tracked tree.**
   ```bash
   git -C <path> ls-tree -r --name-only <branch> | grep '\.py$'
   ```
   From the file list, count `.py` files under each directory prefix at depths 1, 2 and 3. This is
   the only file source — exactly the tracked set that gets indexed; no filesystem walk.

3. **Measure churn (fail-open).**
   ```bash
   git -C <path> log --since="6 months ago" --name-only --pretty=format: -- '*.py'
   ```
   Aggregate how many commits touched each subtree; activity = commits-touching ÷ file-count
   (size-normalized). Classify each subtree "active" vs "stable" against the median. Young repo / few
   commits → fall back to the last ~200 commits (`git -C <path> log -n 200 --name-only --pretty=format: -- '*.py'`).
   Empty or failing `git log` → skip churn, recommend from structure only, and say so to the user.

4. **Read the existing `.review.yml`** (working-tree file, or `git -C <path> show <branch>:.review.yml`).
   Parse it; KEEP every key outside the context layer (`task_board`, `categories`, …) and all
   existing comments verbatim. Keep existing `paths.ignore` entries. No file → you will create one,
   with explanatory comments in the style of this repo's `.review.yml`.

5. **Generate the recommended draft (heuristics).**
   - **`summary_cluster_depth`** (global): pick `d ∈ {1,2,3}` so clusters are a sensible size — aim
     ~3–15 files per cluster; avoid one giant cluster (too coarse) and one-file clusters (too fine).
     Default 2; tiny repos 1. From step 2's per-depth aggregates, choose `d` minimizing the share of
     too-coarse (> ~20 files) and too-fine (1 file) clusters, preferring 2 on ties.
   - **`summary_cluster_depth_overrides`**: for a subtree that is **large AND active** (size > ~20
     files and activity above median) → override `depth = d+1` (finer clusters → pointed invalidation,
     richer prior). Large-but-stable → leave at global `d`. Keys = the shortest distinguishing
     directory prefix (longest-prefix-match). Cap depth at 3.
   - **`summary_topk_threshold`**: estimate the cluster count at the chosen `d` + overrides (≈ number
     of distinct cluster keys). Above the default 20 → keep 20 (ANN top-k engages); otherwise keep
     the default. Mostly informational — show the estimated cluster count to the user.
   - **`paths.ignore`**: propose **candidates** among tracked paths that look like non-product noise
     (`eval`/`evals`, `fixtures`/`testdata`, `examples`/`samples`, `vendor`/`third_party`,
     `generated`/`gen`/`*_pb2.py`, `migrations`, large `data` modules). This is a judgment call, so
     **ask the user per candidate — never write it silently.**

5b. **Task board selection (ask before writing).** Read the existing `task_board` block (keep it
   verbatim if present). Ask the user which board this repo uses:
   - `yougile` → write `{type: yougile, mcp: yougile, key_pattern: '[A-Z]+-\d+', url_template: <ask>}`.
   - `youtrack` → write `{type: youtrack, key_pattern: '[A-Z]+-\d+'}` (NO `url_template` — youtrack derives
     the link from its base URL; NO `mcp` — youtrack is read server-side via sync, not board-MCP).
   - off / none → write an empty `task_board:` (disables the board for this repo).
   - leave unchanged → skip.

   **Then ask which PROJECT this repo uses** (e.g. PRI-170) and write it to `task_board.project` — the task
   **code prefix** (e.g. `PRI`, `TES`), the part before the dash in task codes. Warn the user (in Russian):
   если `project` пуст — и синк, и выдача/граф затянут **все проекты** аккаунта/инстанса вперемешку
   (напр. чужой `TES-1` всплывёт в связях задачи `PRI`); один аккаунт с несколькими проектами без
   `project` смешивает их. Пустой `task_board.project` = текущее глобальное поведение.

   **Then ask the finish-task done target** (closing a task after its PR — skill `/reviewer_finish-task`
   moves the finished task into the board's "done" cell). First **discover candidates server-side**: call
   the reviewer MCP tool `get_board_targets(board_type=<type>, project=<project>)` (read-only; creds live in
   the reviewer env — nothing to configure on the client, and **no yougile/youtrack board-MCP is needed**).
   Show the result as a **pick-list**; if the tool is absent (older deploy), returns an empty list, or
   errors, **fall back to asking** the user for the value. Write only the key(s) matching the board type;
   comment out the other board's keys with a one-line note (mirror the root `.review.yml`). All are optional
   and fail-soft — a wrong/absent column or value only warns, the PR link is still written:
   - **yougile** → `done_column`: the exact column **title** finish-task moves the finished task into (plus
     `completed:true`). `get_board_targets` returns `columns: [{title, board_title, …}]` — present them as a
     pick-list and disambiguate same-named columns by `board_title`; the user picks the done column by title.
     Empty / tool absent → ask for the title. Not set → finish-task only flips `completed:true` without
     moving the card.
   - **youtrack** → `status_field` (name of the custom field the board is built on — default `State`; it
     **also** governs status reading on sync, so set it when the board runs on a custom field like `Stage`)
     and `done_state` (target value of that field — default `Fixed`). `get_board_targets` returns
     `status_fields: [{field, values: […]}]` — let the user pick the field, then a value from that field's
     `values` as `done_state`. Empty / tool absent → ask for both. YouTrack-only; a yougile board ignores them.

   **Never write credentials.** Remind the user (in Russian): ключи доски (`YOUTRACK_TOKEN`/
   `YOUTRACK_BASE_URL` для youtrack, `YOUGILE_API_KEY` для yougile) задаются в env деплоя reviewer-mcp,
   не в `.review.yml`. Грабли youtrack: `YOUTRACK_BASE_URL` обязан оканчиваться на `/api`. Changing the
   board has no effect until those env keys are set and the board is synced (`/reviewer_sync-tasks`).

5c. **`context_limits` — retrieval breadth via a repo profile (PRI-202).** Classify the repo into
   one **profile** from the step-2 structure scan and map it to a full, documented `context_limits`
   block. Write **all** knobs (even when equal to code defaults) — the block is self-documenting,
   matching this repo's own `.review.yml`.

   **Profile from git signals** (no churn — churn drives cluster depth, not retrieval breadth):
   - `N` = number of tracked `.py` files (from step 2).
   - `pkgs` = number of large top-level packages (large ≈ > 50 `.py`; a monorepo signal — several
     independent roots like `services/*`, `packages/*`).

   | Profile | Condition | Meaning |
   |---|---|---|
   | tiny-util | `N < 80` and one package | narrow context, save Voyage |
   | standard (default) | `80 ≤ N ≤ 800` | == code default constants |
   | large / monorepo | `N > 800` OR `pkgs ≥ 3` large | wider rail so broad tasks aren't clipped |

   **Preset bundles** (search_codebase + graph):
   ```
                       floor ceiling ratio abs_floor pool  ann   | hops callers_topk
   tiny-util             3     8     0.60   0.35     20   0.65   |  1        20
   standard (=default)   4    15     0.50   0.30     30   0.65   |  1        25
   large / monorepo      4    25     0.45   0.30     40   0.60   |  1        30
   ```
   Strong signal (scale-driven): `ceiling`, `candidate_pool`, `callers_topk`. Weak signal
   (score-shape): `ratio` / `abs_floor` / `ann_distance_max` — near default, nudged directionally;
   annotate them in the yml «directional, weak — tune after watching the cliff notes».
   `graph.hops` stays 1 in every profile (2 explodes cost).

   **`search_tasks.{floor,ceiling}` from board size** (orthogonal to the repo profile):
   | Board | Condition | floor / ceiling |
   |---|---|---|
   | small | < 150 tasks | 3 / 8 |
   | medium | 150–800 | 3 / 10 |
   | large | 800+ | 4 / 14 |

   Get the count **best-effort**: call `count_tasks(project)` (reviewer MCP; `project` from step 5b).
   Success and `count > 0` → bucket silently. reviewer MCP absent / tool missing (older deploy) /
   `count == 0` (corpus never synced) → **fall back** to asking the user (small / medium / large).
   Never block on it.

   Emit the full block with explanatory comments (mirror the root `.review.yml`). Merge like every
   other key (step 7) — never clobber.

6. **Present draft + diff.** Show the proposed context layer and a unified diff against the current
   `.review.yml` (or "new file"). Briefly justify each recommendation in Russian (why this depth; why
   an override on this subtree — cite its size/churn; why each ignore candidate). Take the user's
   edits in free dialogue and revise the draft.

7. **Write `.review.yml`.** Write the result by **merging** — preserve every other key and the
   explanatory comments. **Never clobber** keys outside the context layer. Idempotent: re-running on
   an already-configured repo yields a minimal diff.

8. **Suggest rebuild commands (do NOT run them).**
   - `paths.ignore` changed → suggest `/reviewer_sync-codebase --path <path> --ref <branch>`
     (re-index vectors + graph).
   - `summary_cluster_depth` / `*_overrides` / `summary_topk_threshold` changed → suggest
     `/reviewer_summarize-subsystems` (changing depth changes every `cluster_key` → a full summary
     rebuild; old-depth summaries orphan and are pruned on a full pass).
   - `context_limits` changed → **no rebuild needed.** It is read live server-side
     (`_resolve_context_limits`) at review / solve-task time; the effect applies on the next run from
     the branch the `.review.yml` is committed to. Do NOT suggest a reindex/resummarize for it.
   - Remind the user (in Russian): changes take effect only after a rebuild, and only from the branch
     the `.review.yml` is committed to (policy is read from the target/index branch).

## Notes

- **Never clobber** keys outside the context layer — edit by merge.
- **Tracked files only** — `git ls-tree`, the exact set that gets indexed. No filesystem walk.
- **Fail-open on churn** — no history / `git log` failure → structure-only recommendations, noted.
- **No index side effects** — the skill only edits the file and suggests commands.
