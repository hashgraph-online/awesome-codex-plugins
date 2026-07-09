---
name: reviewer_pr-walkthrough
description: Build a human-facing reading guide for a GitHub pull request (where to start, what each file changes, what it impacts) using the reviewer PR session + code graph. Use when the user asks to walk a human reviewer through a PR ("PR walkthrough", "гид по PR", "как читать этот PR", "проведи по PR"). NOT a bug review (see review-pr). Requires the reviewer MCP server + base index.
---

# PR walkthrough (reading guide for a human reviewer)

Help a human reviewer orient in a PR — not find bugs. Produce a markdown guide: where to start
(by centrality), what each file changes, and what it impacts ("careful, affects X"). Separate from
bug findings (`review-pr`).

**Always answer the user in Russian** (the project language). Tool calls, identifiers and `path:line`
stay verbatim.

## Tools

<!-- include: _common/tool-usage.md -->
Plus the PR-session tools (reviewer MCP): `prepare_review`, `get_impact`, `get_changed_file_diff`,
`find_callers`, `get_related_symbols`, `read_file`; optional `get_subsystem_summaries` (PRI-159);
optional `post_pr_walkthrough` (only on explicit user request).

## Pipeline

1. **Resolve repo & prepare the session.** Resolve `repo` (git remote). Call `prepare_review(repo, pr)`.
   If it returns `{"status": "skipped"}` (branch not in REVIEW_BRANCHES), tell the user (in Russian)
   and stop.

2. **Reading order (centrality).** Call `get_impact(repo, pr)` → changed symbols and their callers.
   Order "start here" by how much depends on each changed symbol (most central first). Graph down →
   fall back to ordering by file (fail-open).

3. **What each file changes.** For each changed file, `get_changed_file_diff(repo, pr, path)` → one
   line describing what it changes.

4. **Impact ("careful, affects X").** For the central changed symbols, `find_callers` /
   `get_related_symbols` → who depends on them. Every "affects X" must be backed by a real caller.

5. **Subsystem prior (optional).** `get_subsystem_summaries(repo, pr.base_ref, query="<PR title + changed file paths>")` → name the touched
   subsystem(s) in one line. Pass the PR's target branch `pr.base_ref` (from the `prepare_review`
   response), NOT the local git branch — subsystem summaries are indexed per target branch
   (`base:<branch>`). Empty / unavailable → skip (fail-open).

6. **Assemble the guide (Russian markdown):**
   - **Начни отсюда** — ordered list (most central first).
   - **По файлам** — one line per changed file.
   - **Осторожно, влияет на** — impacted symbols + their callers.
   - (optional) **Подсистемы** — 1–2 lines from summaries.

7. **Output.** Print the guide to the user by default. Post to the PR ONLY on explicit user request:
   confirm first, then call `post_pr_walkthrough(repo, pr, markdown)` (posts a PR review comment with
   a `<!-- ai-walkthrough -->` marker, separate from bug findings).

## Grounding (hard rule)

<!-- include: _common/anti-hallucination.md -->

Every "affects X" is backed by a real `find_callers` result. Never invent callers or impact.

## Notes

- This is a reading guide, NOT a bug review — no findings, no inline severity comments.
- Posting to the PR is outward-facing and never happens without explicit user request + confirmation.
- Works without PRI-159 summaries and degrades gracefully when the graph is unavailable.
