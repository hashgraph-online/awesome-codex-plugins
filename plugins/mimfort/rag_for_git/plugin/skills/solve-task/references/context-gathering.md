   - **Subsystem prior (architectural map).** Use `payload.subsystems` from the Step 0
     `prepare_task_context` call — already the top-k relevant subsystems by proximity to the task
     (top-k vs all is server-side; PRI-167) for the same `branch` as `search_codebase`. An empty
     `payload.subsystems` is a normal outcome (summaries not warmed, or no cluster close enough) —
     do NOT call `get_subsystem_summaries` again for a merely empty list. Call
     `get_subsystem_summaries(repo, branch, query="<task title>. <first lines of description>")`
     directly only as a fallback: when `gaps` carries an entry with `section == "subsystems"` (a
     real failure), or when `prepare_task_context` itself is unavailable. Fail-open either way: an
     empty/absent `payload.subsystems` (no `gaps` entry) or a genuine failure (with one) both omit
     the `## Subsystems` brief section — note the gap only when one exists. The summary is only a
     prior — every `path:line` in the brief still comes from `search_codebase` snippets, never from the summary text.
   - **Project scope.** Pass `project=<task_board.project>` (from Step 1; empty = unscoped) to
     `get_task`, `get_task_context`, and `search_tasks` so only this repo's project surfaces (PRI-170).
   - **Linked tasks.** Use `payload.related.linked` from the Step 0 `prepare_task_context` call when
     you have a task key — linked tasks, their PRs, and the code those PRs touched. Call
     `get_task_context(key, project=<task_board.project>)` directly only as a fallback: when
     `payload.related.linked` is absent/empty without a matching `gaps` entry, or when
     `prepare_task_context` itself is unavailable.
   - **Similar tasks.** Use `payload.related.similar` from the same call — semantically similar
     tasks from the reviewer store. Call `search_tasks("<title>. <first lines of description>",
     project=<task_board.project>)` directly only as a fallback: when `payload.related.similar` is
     absent/empty without a matching `gaps` entry, or when `prepare_task_context` itself is
     unavailable. Use indexed fields only; if detail is missing, record that task-context gap.
   - **Related work = linked ∪ similar.** The «Related work» brief section draws from two sources —
     `get_task_context` (linked) and `search_tasks` (similar). They overlap; the Step 4 filter
     deduplicates them by key before the cap.
   - **Relevant code.** Use `payload.code` from the Step 0 `prepare_task_context` call — relevant
     existing code (files/symbols to touch or mimic). Call `search_codebase("<task description>")`
     directly only as a fallback: when `payload.code` is absent/empty without a matching `gaps`
     entry, or when `prepare_task_context` itself is unavailable.
   - **Stale summary handling.** If a returned summary has `stale: true`, keep it only as a weak prior, do not use it for structural
     claims, and prefix its `## Subsystems` line with `[stale]`. `stale: null` is unknown freshness and
     gets no marker. For `stale: true`, either omit the item or use exactly this line shape:
     `- [stale] <cluster_key> — summary content omitted; verify against code.` Do not interpolate its
     title or summary claims. Omitting a stale summary does not change the directly-informing
     `search_codebase` entries selected for `## Relevant code`: evaluate every code item solely against
     the task, independently of whether it corroborates or refutes any stale-summary claim.
   - **Lazy expansion (no user prompt).** If a tool's output ends with a cliff/rails note reporting a
     high-scoring tail beyond the cut AND the task looks broad, you MAY re-call the tool once with a
     higher ceiling (pass `top_k=<bigger>`), then merge. Do this silently — never pause to ask the user.
   - **Test exemplars (optional — when `search_codebase`/`payload.code` surfaced concrete symbols).**
     Use `payload.test_exemplars` from the Step 0 `prepare_task_context` call when present. Call
     `search_codebase("<how the task's area is tested — fixtures/mocks for the feature>", include_tests=True)`
     on the same `branch` directly only as a fallback: when `payload.test_exemplars` is
     absent/empty without a matching `gaps` entry, or when `prepare_task_context` itself is
     unavailable — a targeted *test* query (how the area is tested), not the code query with
     the flag flipped, so it surfaces the testing pattern the TDD hand-off should mimic. Snippets are
     line-numbered like the code retrieval → cite `path:line` directly. Apply the same Step 4 adaptive
     relevance filter (every directly-informing test file/symbol, no fixed cap). Fail-open: no tests
     surfaced / a `(ничего не найдено)` note / an error → omit the `## Test exemplars` brief section;
     the default code retrieval (`include_tests=False`) is unchanged.
   - **Deepen via the code graph (optional — when `search_codebase` surfaced concrete symbols).**
     `search_codebase` chunks are headed by `path#fqn (path:start-end)`; feed those `node_id`s to the
     session-less graph tools to sharpen the brief. The default `search_codebase` (code retrieval,
     `include_tests=False`) returns deduplicated, line-numbered, test-free snippets — expand only the
     few symbols central to the task (feed graph tools the code node_ids, not test-exemplar ones), and cite
     `path:line` from the line-numbered snippets directly (no re-Read needed for grounding).
     For OO/registry/dispatch tasks («add a new provider / handler») and for any
     task that smells like a roll-out («add a field to every provider»), call
     `family(node_id)` on the symbols central to the task. It answers «who else is
     like this» from two signals — inheritance and structural contract match — and
     always says which fired, so an empty answer is never mistaken for «no family
     exists». Prefer it over the undirected `related_symbols`, which mixes
     callers/tests/implements.
     A family is the unit the brief must carry: when `family` returns N members,
     the brief names all N, not the one member retrieval happened to surface. This
     is a structural signal, not a textual one — do not try to infer roll-out tasks
     from the wording of the description.
     `implementations(node_id)` remains the directed «who subclasses X» query.
     Fail-soft notes are non-fatal — continue.
     Pass the same `branch` you pass to `search_codebase`.
     Fail-open: a `(граф недоступен)` / `(нет связей)` / `(вызовов не найдено)` note is non-fatal — continue.
   - **Lazy PR diff (optional).** `get_task_context` surfaces a task and its PRs (id form
     `owner/name#N`); `search_tasks` surfaces similar task keys — fetch a key's context to see
     its PRs. If a related task passed the relevance filter AND its PR is worth inspecting for
     the implementation, parse `repo`/`number` from the PR id and call `get_pr_diff(repo, number)`
     to see what that PR changed — pull it lazily, only when the LLM judges it useful (don't
     fetch diffs for low-relevance tasks).
     Fail-open: a `(diff PR недоступен)` / `(repo не задан…)` note is non-fatal — continue.
   - **Relevance signals → Step 4 filter.** `search_tasks` `score` is an RRF rank score
     (≈0.016–0.033), not comparable across queries; `search_codebase` has no score, only order.
     Carry *rank/order* — not absolute score — into the Step 4 filter, and fetch `get_pr_diff`
     only for a related task that survives that filter (within top-3, directly informing).
