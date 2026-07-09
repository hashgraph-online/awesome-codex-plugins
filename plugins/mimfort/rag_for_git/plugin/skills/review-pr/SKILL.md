---
name: reviewer_review-pr
description: Review a GitHub pull request with the RAG + code-graph pipeline (reviewer MCP server). Use when the user asks to review a PR ("review PR 123", "заревьюй PR", a PR URL). Requires ParadeDB/Neo4j running and a built base index.
---

# PR Review Pipeline

Orchestrate a full PR review using the `reviewer` MCP server tools. The deterministic
tail (policy gate, line grounding, dedup, idempotency, comment cap, publishing) is
handled by `publish_review` — your job is analysis quality, not formatting rules.

## Inputs

Parse from $ARGUMENTS: target PR as `owner/repo#N`, `owner/repo N`, or a GitHub PR URL.
`--dry-run` flag → pass `dry_run=true` to publish_review and show the report instead
of posting.

**Include resolution (applies to all steps below).** When you read any
`references/*-prompt.md` file to dispatch a subagent (steps 3, 4, and 5 —
analyze, requirements, blast-radius, verify), it may contain
`<!-- include: _common/<file>.md -->` markers. Before putting the prompt into
the subagent, replace each marker with the verbatim contents of that file
(path is relative to `plugin/skills/`). These `_common/*.md` files are the
single source of the shared findings-schema / anti-hallucination / tool-usage
blocks.

## Pipeline

1. **Prepare.** Call `prepare_review(repo, pr)`. The payload contains:
   - `pr`: `{number, title, body, base_sha, head_sha, base_ref, draft}`
   - `policy`: `{severity_threshold, min_confidence, max_comments, categories, ignore, output_language}`
   - `units`: list of `{path, patch, commentable_right, commentable_left}`
   - `task_board`: `{type, mcp, key_pattern}` or null — task board config from `.review.yml`
   - `task_keys`: `{primary, others}` or null — task keys extracted from the PR by the server
   - `skipped_paths`, `skip_drafts`, `suggestions_mode`

   If the payload has `status: "skipped"`, this is NOT an error but an expected skip
   (the PR's target branch is not in `REVIEW_BRANCHES`). Tell the user the `reason`
   value and stop: do not run analyze/publish, and do not treat it as a failure.

   If `pr.draft` is true and `skip_drafts` is true, stop and tell the user.
   Note `policy.output_language` — ALL finding messages, suggestions and the summary
   MUST be written in that language.

2. **Task context (optional).** Only if `task_board` is non-null. Resolve the task key: an
   explicit key in `$ARGUMENTS` wins; otherwise use `task_keys.primary`. If no key is available,
   skip this step and note in the summary that no task key was found.

   Task reads are scoped to this repo's project: pass `project=<task_board.project>` (from the target
   branch `.review.yml`, see step with `task_board`) to `get_task`/`get_task_context`/`search_tasks`
   (PRI-170; empty `project` = unscoped).

   Read the task **store-first** (unifies with solve-task; required for boards synced server-side
   without a board MCP, e.g. youtrack):
   - Call reviewer `get_task(key, project=<task_board.project>)` first. **Hit** (object with a `key`) → use it as the `TaskBrief`
     directly; it is already indexed by the server-side sync, so do NOT call `index_task`.
   - **Miss** (`null`) AND `task_board.mcp` is set → fall back to the board-MCP playbook for
     `task_board.type` (`references/task-context-yougile.md` or `references/task-context-jira.md`):
     call the board MCP server named by `task_board.mcp`, build a `TaskBrief`, then `index_task(TaskBrief)`.
   - **Miss** AND `task_board.mcp` is empty (e.g. youtrack — no board MCP) → treat the task as not
     found: skip the requirements dimension and note the reason in the summary.
   In all cases, if the board MCP is not connected, a tool errors, or the task is not found: skip the
   requirements dimension and note the reason — NEVER abort the review.

   The `TaskBrief` schema is `{key, aliases[], title, description, criteria[], status, url, links[]}`
   (phase 3 adds `aliases[]` and uses `links[]`; see the board playbook for how to fill them).
   On a store **hit** the brief is already indexed — do NOT re-index. Only when the brief was freshly
   built from the board MCP (the **Miss** branch) call `index_task(TaskBrief)` to persist it
   (idempotent — safe to repeat). Then gather task context to sharpen the requirements check:
   - `get_task_context(TaskBrief.key, project=<task_board.project>)` → linked tasks, their PRs, and the code those PRs touched;
   - `search_tasks("<TaskBrief.title>. <first lines of description>", project=<task_board.project>)` → semantically similar tasks.
   Keep ONLY the related/similar items that look relevant; you will pass them to the requirements
   dimension in step 4. All of this is best-effort: if `index_task`/`get_task_context`/`search_tasks`
   return a "(… unavailable)" note or error, continue — never abort the review.

3. **Analyze (fan-out).** For each unit in `units`, dispatch a subagent (Task tool,
   run independent subagents in parallel; batch units if there are more than ~10) with:
   - the contents of `references/analyze-prompt.md` (read it once, resolve includes, include verbatim);
   - the unit's `path`, `patch`, `commentable_right` (sorted list of new-file line numbers
     available for inline), `commentable_left` (sorted list of old-file line numbers available
     for inline), and the PR `title`/`body`;
   - the repo/pr identifiers so the subagent can call the reviewer MCP tools
     (`search_code`, `get_related_symbols`, `read_file`, `get_definition`,
     `find_callers`, `get_changed_file_diff`);
   - the target output language.
   Each subagent submits findings via `submit_findings(repo, pr, findings=[...])` (schema-enforced; the server assigns ids).

4. **Dimensions (parallel with step 3).** Dispatch whole-diff subagents:
   - performance: follow the methodology of `../performance-review/SKILL.md`
     (Goal, Method, Severity sections);
   - maintainability: follow `../maintainability-review/SKILL.md`;
   - requirements (ONLY if a `TaskBrief` was built in step 2): dispatch one subagent with
     `references/requirements-prompt.md`, the diffs of all units (path + patch), the `TaskBrief`,
     plus the related/similar task context gathered in step 2 (linked tasks, their PRs, touched code,
     similar tasks) as an optional "Related context" block, the repo/pr identifiers (so it can call
     the reviewer MCP tools), and the target output language. It submits findings via
     `submit_findings` with category `requirements`.
   - blast-radius: dispatch one subagent with `references/blast-radius-prompt.md`, the diffs of
     all units (path + patch), each unit's `commentable_right`/`commentable_left` (the line numbers
     where inline comments are allowed), the PR `title`/`body`, the repo/pr identifiers, and the
     target output language. It runs two checks — changed signatures breaking callers (via
     `get_impact`) and interface expansion (a changed `Protocol`/ABC whose implementations must all
     be updated, via `get_related_symbols`/`search_code`) — and submits findings via
     `submit_findings` with category `correctness`.
   Give the performance/maintainability subagents: the diffs of all units (path + patch), the
   repo/pr identifiers so they can call the reviewer MCP tools, and the target output language.
   They must submit findings via `submit_findings` (category `performance` / `maintainability`).

5. **Verify.** Dispatch one subagent with `references/verify-prompt.md` and the
   repo/pr identifiers. It reads candidates via `get_candidate_findings(repo, pr)`
   and submits verdicts via `submit_verdicts(repo, pr, verdicts=[{id, is_real}])`.
   A finding with `is_real=false` is dropped at publish; a finding with no verdict
   is kept (recall-safe — no orchestrator action needed if verify fails).

6. **Publish.** Compose a short review summary (2-5 sentences, in
   `policy.output_language`): what the PR does, overall assessment, key risks.
   If a task was read, state whether the PR meets the task's requirements; if the task context was
   requested but unavailable (no key, board MCP not connected, task not found), say so briefly.
   Mention files that were not analyzed: failed subagents and `skipped_paths`
   from the prepare payload. Call `publish_review(repo, pr, summary, dry_run, task_key)`
   where `task_key` is the canonical `TaskBrief.key` if a task was read (else omit / null). If the
   CLI provides model/usage/cost metadata, pass them via the optional keyword arguments `model`,
   `usage`, and `total_cost` to `publish_review`. When published, this links the PR to the task in
   the graph for future reviews. Report to the user:
   posted/dry-run, inline count, and the report counters
   (dropped_by_gate/deduped/invalid/already_posted/moved_to_summary/capped/verify_rejected), run_id.

## Failure handling

- A failed analyze subagent must not abort the run: continue with the other units
  and mention the skipped file in the summary.
- A `prepare_review` payload with `status: "skipped"` is not a failure: report its
  `reason` (target branch not tracked in `REVIEW_BRANCHES`) and stop without analyze/publish.
- If `prepare_review` fails, surface its error text to the user as-is (it contains
  the remediation hint, e.g. "docker compose up -d").
- Never post comments yourself via gh/git — only through `publish_review`.
