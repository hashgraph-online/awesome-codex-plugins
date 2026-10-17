---
name: usage-kernel
description: Use the six Codex Usage Tracker tools for exact local usage facts, bounded exploration, allowance observations, and evidence timelines.
---

# Codex Usage Tracker

Use the tracker as a factual local data plane. The tools return exact or
explicitly graded facts; the model owns inference, explanation, and
recommendations.

Use the three-step loop **scope → batch → evidence**:

1. **Scope.** Start with the needed `usage_query` whenever the question maps
   to a curated template or a known typed request. The result carries its
   generation, grade, history coverage, and cache state. Call `usage_status`
   only when the query reports an absent or insufficiently fresh index, or
   when the user explicitly asks about operational state. A committed
   generation remains queryable while refresh is active or recommended. When
   the needed fields are unfamiliar, set `include_guidance=true` on the same
   `usage_query` call that carries the first batch; use an empty batch only for
   standalone capability discovery.
2. **Batch.** Prefer one batched `usage_query` call. Its arguments always wrap
   one or more query requests in the `requests` array. Execute a curated
   server-side template with
   `{"requests":[{"template":"<name>"}]}`; for the common thread leaderboard
   use `{"requests":[{"template":"top_threads"}]}`. Templates query the
   hydrated snapshot and report its coverage; refresh complete history only
   when the user asks. For same five ranked threads, use result 1 for
   labels, selectors, totals, shares, and token classes; use result 2 only for
   cost/credits. Do not query again unless user asks for evidence. Use
   `{"requests":[{"template":"weekly_drivers"}]}` for the latest indexed
   seven-day thread leaderboard,
   `{"requests":[{"template":"week_over_week"}]}` for that window versus the
   immediately preceding seven days, and
   `{"requests":[{"template":"latest_incremental_change"}]}` for the active
   generation's inserted calls and leading affected thread. These templates
   derive their anchors from the committed snapshot; do not discover dates or
   generation numbers first. Use
   `{"requests":[{"template":"model_effort"}]}` for model/effort mix and
   `{"requests":[{"template":"tools"}]}` for structural tool facts. Do not repeat a
   successful curated template or request guidance after it returns rows.
   Supply `parameters` only when the selected template requires them.
   Otherwise send only the typed dataset, operation, dimensions, measures,
   filters, and limits needed for the question. Do not copy or reconstruct a
   returned template body.
   Preserve the returned generation, grade, coverage, counts, and explicit
   row/byte limits. Compose filters as
   `{field, operator, value}` using only the dataset fields and operators in
   `filter_grammar`; `in` takes an array of 1–25 values. Phase queries require
   one returned scope-filter template for a thread, turn, or time window.
3. **Evidence.** Rank candidates from the facts first. Call `usage_evidence`
   only after ranking, and only with an exact returned logical selector. Use
   `live=true` for the same timeline in live mode.

Label every claim:

- **fact** — returned exact/deterministic data; for `partial`, state the
  hydration preset/cutoff and never generalize to all history;
- **estimate** — returned estimated data with coverage and provenance;
- **hypothesis** — model inference that still needs evidence;
- **unsupported** — unavailable from the returned scope and not asserted.

The optional `context` dataset is aggregate-only private local evidence. Its
`observed_bytes` and `events` measures are exact for the structurally observed
payload strings that were indexed. `estimated_tokens` is available only when
an explicit tokenizer populated it; always preserve its estimator identity and
coverage. Never describe category bytes or estimates as exact billed input
tokens, and keep `unattributed_input_tokens` unsupported when the response
reports it as `null`. If context composition is disabled, continue with the
base accounting datasets instead of starting hidden work.

Call `usage_refresh` only when freshness matters. Reuse the returned job; never
start a duplicate. Use `usage_job_status` with a bounded `wait_seconds` value
so the host waits; do not short-interval poll from the model. Use
`usage_allowance` for observed allowance facts and preserve its provenance and
limitations. Do not infer waste or productivity from token totals alone.

Never inspect raw logs as a fallback, invent missing selectors, claim narrative
findings the tools did not return, or expose prompts, reasoning, tool
arguments/output, secrets, or local paths.
