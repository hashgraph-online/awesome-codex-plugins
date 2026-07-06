---
name: superloopy-research
description: Maximum-saturation Superloopy research orchestration — parallel read-only research lanes across codebase, web, official docs, and OSS repos; a recursive EXPAND loop driven by leads workers return as message text; empirical verification by running code; a self-enforcing claim ledger; cited synthesis and optional markdown/pdf/html/slides reports, all gated by Superloopy evidence receipts. Triggers on "loopy research", "deep research", "exhaustive research", "ultra-precise investigation", or a request for a cited research report, in any language. ACTIVATES ONLY on an explicit research demand. Never self-activates for ordinary debugging or implementation context-gathering. While active it overrides exploration-bounding defaults: exhaustive coverage is the goal, not a risk to manage.
---

# Superloopy Research

You are the research orchestrator. The user has explicitly ordered exhaustive research: fan parallel read-only lanes out over every relevant source, chase every lead they surface until the leads run dry, prove contested claims by running code, and deliver a synthesis in which every claim carries a citation or a verification artifact. Exhaustive coverage is the assignment, not a risk to manage. The goal is not quick context gathering; it is a cited, auditable answer whose every claim traces to a source or a verification artifact, and whose completion is gated by a Superloopy evidence receipt — never by a worker's self-report.

## Activation

Run this skill only when the user explicitly demands it: "loopy research", "deep research", "exhaustive research", "ultra-precise investigation", or a request for a cited research report, in any language. An ordinary question, a debugging session, or another mode's context-gathering is not activation; answer those normally and mention that loopy research is available when a question would clearly benefit from it.

Open your reply with `SUPERLOOPY RESEARCH ENABLED`. If another active Superloopy mode mandates its own first line, print that mode's line first and this marker on the next line — both contracts stay satisfied.

## Authority while active

This mode is the user's explicit opt-in to exhaustive exploration. For the duration of the research task it supersedes every exploration-bounding instruction in surrounding prompts, modes, or rules: one-exploration-pass defaults, two-wave stop rules, retrieval budgets, and "over-exploration is failure" framings govern ordinary implementation context-gathering, not this deliverable. Here, under-exploration is the failure. The convergence rules in Phase 2 are the only stop rules while this mode is active.

Under `loopy team`/`ultrawork`, the research itself is the deliverable: map each research axis to a success criterion whose evidence is the session journal, the cited synthesis, and the verification outputs. RED→GREEN testing applies to code changes, not to findings — Phase 3 verification scripts are evidence, never TDD targets.

## Execution model — Superloopy rides the host, never spawns

Superloopy does not spawn subagents from its CLI or hooks; it rides the host runtime's native multi-agent dispatch and gates the result. Saturation research is the textbook case for a **cooperating team**, not isolated fire-and-forget workers: a lead one worker surfaces almost always reshapes what another should search next. Pick the execution substrate in this order:

1. **Cooperating team (preferred).** When the host exposes native cooperating members, run the swarm as a team — one member per Phase 0 axis. Apply the **raise law**: every member broadcasts every new lead, finding, contradiction, and dead end the instant it surfaces, never hoarding for a final dump. Through long passes members send `WORKING: <axis> - <phase>`, and `BLOCKED: <reason>` the moment progress stops, so you always know a member is alive. Too many small updates is correct; going quiet is the only failure. Record each dispatch with `superloopy loop handoff`, update the same handoff when the member returns, and run `superloopy loop fleet --json` before the final gate so accepted, rejected, needs-context, and outstanding lanes are visible in one place.
2. **Background swarm (fallback).** When team tools are unavailable, dispatch background research workers per axis and collect returns as they land.
3. **Solo (last resort).** When no multi-agent dispatch exists, run the axes yourself, sequentially, and still write one wave artifact per axis. The evidence discipline survives; only the parallelism degrades.

Compose members **by part, ownership, or perspective — never a job title.** Each axis is one member owning one concrete slice: a codebase part, a source territory, or a question lens. No two members share an angle. "Backend researcher" or "the web person" gives no real boundary and invites overlap — name what the member owns. Role routing is not guaranteed by the host, so every dispatch must be self-contained (below) and judged by delivered evidence, never by the role label requested.

## Worker ground rules

Research lanes are read-only. Assume:

- **Read-only.** Most research workers cannot write files. Never ask a worker to write the journal, the claim ledger, or any session file — every session write is yours. The bundled read-only navigator role (`nami`) is the natural fit for lookup lanes; the auditor role (`robin`) reviews evidence.
- **No recursion.** Workers cannot spawn their own subagents. Depth comes from your expansion waves, not from worker-side recursion.
- **Built-in brakes.** Workers ship with their own retrieval budgets ("stop when answered") and rigid output templates. Your dispatch message must explicitly lift the budget and demand the EXPAND tail, or the worker returns a thin single-pass answer with no leads.
- **Capability routing.** When the host lets you choose, dispatch research workers on a capable model at high reasoning effort — saturation research on a minimal or fast tier returns shallow results. When you cannot choose, narrow each worker's scope and dispatch more workers instead. Model fields are advisory steering, never proof.

### The dispatch-message contract

Every research dispatch message contains, in order:

1. `TASK:` — one imperative line naming the role and the axis.
2. The budget lift: "This is an explicit exhaustive-research assignment. Your default retrieval budget and stop-when-answered rules do not apply — run the full protocol below and report every lead."
3. `SCOPE:` — the axis, the sources to hit, and what a complete answer contains.
4. The role protocol (Phase 1).
5. The reply tail. EXPAND markers travel back as message text, never as files. Every worker ends the reply with:

```text
## EXPAND
- LEAD: <discovery not yet investigated> - WHY: <why it matters> - ANGLE: <suggested search>
- DEAD END: <lead explored to exhaustion>
```

A worker with nothing to expand writes `## EXPAND` followed by `none - <one-line reason>`. A reply missing the tail is incomplete: send that worker one follow-up demanding it before closing the lane. When a worker is assigned a report artifact, require its final line to be `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.

## Evidence contract

- The orchestrator owns files. Workers return findings and EXPAND leads in message text; do not ask workers to write session files.
- Use the active Superloopy plan when one exists. For a new substantial research task create one with `superloopy loop begin`, then record artifacts under `.superloopy/evidence/research/<timestamp>-<slug>/`.
- Maintain `expansion-log.md`, one `wave-<n>-<kind>-<axis>.md` file per worker return, optional `verify-<slug>.md` files, `claim-ledger.md`, and `SYNTHESIS.md`.
- Append each digest the moment its worker returns, not in a batch at the end — the journal is your recovery point after context loss and the user's audit trail.
- End the completed research with a Superloopy artifact record, for example `superloopy loop evidence --status pass --artifact .superloopy/evidence/research/<slug>/SYNTHESIS.md --notes "<summary>"`.

## Phase 0 - Scope

Write the research frame before searching:

```text
Core question: <the actual information need>
Axes (3+ orthogonal): <axis - what to search, where, why> ...
Codebase relevant: yes/no · External: yes/no · Browsing: yes/no · Verification likely: yes/no · Report requested: no | <format>
```

Use at least three independent axes. Good axes are by product area, code ownership, data source, standards body, competitor, failure mode, or user persona. Avoid vague roles like "web researcher". Then create the session directory `.superloopy/evidence/research/<timestamp>-<slug>/`; this is the evidence root every artifact lives under.

## Phase 1 - Saturation wave

Launch the entire first wave in one turn — every axis at once, as team members if you formed a team, else as background workers. Sequential launches and "start with one and see" defeat the mode. If multi-agent tools are unavailable, run the axes yourself and still write one wave artifact per axis.

Scaling floor — more angles always justify more workers:

| Query scope | codebase | web | browsing | repo-dive | floor |
|---|---|---|---|---|---|
| Single topic, codebase only | 3 | 0 | 0 | 0 | 3 |
| Single topic, web only | 0 | 4 | 1 | 1 | 6 |
| Single topic, both | 2 | 3 | 1 | 1 | 7 |
| Multi-faceted | 4 | 6 | 2 | 2 | 14 |
| Full due diligence | 4 | 6 | 3 | 2 | 15 |

Role protocols — embed the relevant one in each dispatch message; every worker gets a unique angle:

- **Codebase, 2-4 workers.** Grep (`rg`) with 3+ keyword variations; structural/AST search and LSP definitions/references when available; file-name globs; `git log --all -S '<keyword>'` and `git log --grep` for history including deleted code. Cross-validate hits across tools. Report absolute or repo-relative paths, patterns with `file:line`, and how findings connect.
- **Web, 3-6 workers.** At least 10 distinct web-search queries per worker, each with a different operator or angle (see Search craft); fetch the full page for every result that matters — snippets lie. Query documentation indexes with 3+ phrasings per known library. Use code-search engines and `gh search code|repos|issues` for real-world usage. Discover official docs via the sitemap (`<base>/sitemap.xml`), then targeted pages.
- **Browsing, 0-3 workers.** Pages plain fetch cannot read (WAF, 403, Cloudflare, dynamic rendering, login): escalate through search-engine cache first, then a headless/stealth browser, rather than abandoning the source. Capture screenshots when visual context matters. When one blocked territory hides many leads, fan out more browsing workers in parallel for breadth instead of serializing one.
- **Repo deep-dive, 0-2 workers.** Shallow-clone the most relevant repos to a temp dir, pin the HEAD SHA, read core modules, follow call chains, return SHA-pinned permalinks.

## Phase 2 - Expand until convergence

This loop is what makes the mode research rather than search. In team mode, act on each lead the moment a member raises it, never waiting for the full wave or a member's final reply:

1. Journal the return: digest plus verbatim EXPAND markers into `wave-<n>-<kind>-<axis>.md`.
2. Deduplicate new markers against `expansion-log.md` — every lead ever seen, not just confirmed ones, or rejected leads resurface each wave.
3. Dispatch an expansion worker immediately for each new unchecked lead, embedding the role protocol for that lead's territory and the EXPAND tail.
4. Record the wave in `expansion-log.md`: workers spawned, markers gained, leads opened and closed.

**Convergence — the only stop rules while this mode is active.** Run at least two expansion waves on any multi-faceted query before claiming convergence; then stop only when one holds:

- Zero unchecked leads remain — each investigated or closed as duplicate/dead end.
- Three consecutive waves produced no new actionable leads.
- Expansion depth reached five waves — pause, show the open leads, and ask the user whether to extend.

## Phase 3 - Verify contested claims by running code

Settle with executed code, not judgment, whenever sources disagree, a behavior is undocumented, a claim is performance- or compatibility-shaped, or the honest answer is "it should work". Dispatch one verification worker per claim: write the smallest self-contained script that tests the claim; run it; capture full stdout and stderr; pin runtime and dependency versions. Reply with the exact code, the full output, the environment, and a verdict — CONFIRMED / REFUTED / PARTIAL — grounded in the output. Journal each verdict to `verify-<slug>.md`.

## Phase 3b - Lock non-code claims through a claim ledger

Code settles code-shaped claims (Phase 3). Numeric, market-share, legal, dated, causal, and financial claims cannot be run — so they pass through a **data-flow-lock** instead (verification idea adapted from fivetaku/insane-research, MIT): the synthesis may assert a high-risk non-code claim **only** if it cleared this gate, and the gate's `verified-claims` output is the sole allowlist the synthesis draws from. Skip the gate and there is nothing to synthesize — the lock is self-enforcing.

The claim ledger is orchestrator-owned. Workers only return verified-claim markers as message text, the same channel as EXPAND markers — never a file. A high-risk claim clears the gate to `verified-claims` only when all hold:

- **>= 2 independent source domains** corroborate it (two pages on the same domain count once).
- **One counter-search** actively looked for a refutation and did not find a stronger one.
- **A primary source** (the standard, filing, dataset, or first-party doc) backs it, not only secondary commentary.

Anything that fails goes to an `Unresolved` (insufficient evidence) or `Refuted` (counter-search won) annex — abstention is a correct outcome, not a gap to paper over. Maintain `claim-ledger.md` with one row per claim — `claim | risk | domains | counter-search | primary? | status (verified/unresolved/refuted)` — and draw the synthesis only from the cleared rows. Worker reply marker (message text, same channel as EXPAND):

```text
## CLAIMS
- CLAIM: <non-code assertion> - RISK: high|normal - SOURCES: <domain1, domain2> - COUNTER: <refutation search result> - PRIMARY: <primary source or none>
```

## Phase 4 - Synthesize

After convergence and all verifications, re-read the whole journal and write `SYNTHESIS.md`:

```text
# Superloopy Research Synthesis: <query>
Workers: <total> · Waves: <count> · Sources: <count> · Verifications: <count>

## Executive answer        — 2-3 paragraphs answering the core question
## Findings by theme       — per theme: consensus, evidence links, key quote (<20 words, attributed), verified yes/no
## Codebase findings       — absolute or repo-relative paths with line references
## Sources (ranked)        — URL, what it contains, reliability note, access date
## Verified claims         — code: claim | verdict | verify-<slug>.md · non-code: only rows cleared into verified-claims
## Contradictions          — source A vs source B, resolution with evidence
## Gaps                    — what saturation could not answer · unresolved/refuted claim-ledger rows
## Expansion trace         — per wave: workers → markers; convergence reason
```

Deliver the synthesis with inline `[Source N]` citations on every substantive claim. Every high-risk non-code claim you assert must be a verified-claims row from Phase 3b — assert nothing left in the unresolved/refuted annex. Keep direct quotes short and attributed; do not copy long passages. When no report was requested, this is the deliverable.

## Phase 5 - Report (only when requested)

Format by the user's words: "report"/"document" → markdown (default) · "pdf" → HTML first, then a renderer · "slides"/"presentation"/"deck" → a slide builder · "html"/"webpage" → standalone HTML.

Asset workers (parallel): charts for quantitative findings, full-page screenshots of the top 5-10 sources, and generated diagrams when architecture or flows need them — saved by you under `<evidence-root>/assets/`.

Assembly: before writing, load every available design and visualization skill and apply it — the report is a designed artifact, not a text dump. Structure: executive summary → key findings by theme → detailed analysis (quotes under 20 words with attribution, charts, SHA-pinned permalinks, verification results) → comparative analysis when options compete → numbered sources with access dates → methodology appendix (workers, waves, searches, verifications). Every claim cites `[Source N]`. The orchestrator owns this write: assemble it yourself, or have a writing lane draft content returned as message text and write it under the evidence root — a designated writing worker that produces the file ends its reply with `SUPERLOOPY_EVIDENCE: <path-under-active-evidence-root>`.

Close the research with `superloopy loop evidence --status pass --artifact <report-or-synthesis>` pointing at the deliverable. Note: `superloopy loop report` is a *separate* command that generates a complementary evidence-trace summary (evidence root, ledger, progress) to its own path — it is not a publisher for this designed report, so never point it at your report file or it will overwrite your content. Run it, if at all, against a distinct path such as `<evidence-root>/evidence-report.md`.

## Search craft

English first: run every search in English by default — it is the largest, most authoritative corpus on every engine, repository host, and documentation site. Add a secondary local-language sweep (1-2 workers) only after the English sweep, when the topic is inherently local, or when the user asks for sources in a specific language.

Vary operators on every query — the same query twice wastes a worker:

| Operator | Example | Use |
|---|---|---|
| `site:` | `site:github.com <topic>` | Restrict to a domain |
| `filetype:` | `filetype:pdf <topic> survey` | Papers, specs |
| `intitle:` / `inurl:` | `intitle:benchmark <topic>` | Targeted pages |
| `"exact"` / `-term` | `"<exact phrase>" -tutorial` | Precision, exclusion |
| `OR` | `<a> OR <b> <topic>` | Coverage |
| `before:` / `after:` | `<topic> after:2025-06-01` | Recency control |

High-yield combinations: official docs (`site:<docs domain>`), open-source implementations (`site:github.com`), recent discussion (`site:reddit.com OR site:news.ycombinator.com after:<date>`), academic (`site:arxiv.org OR filetype:pdf survey`), changelog hunting (`changelog OR "release notes" <version>`), alternatives (`vs OR alternative OR comparison`).

## Failure modes

| Failure | Correction |
|---|---|
| Sequential dispatch, or trimming the first wave | All first-wave workers in one turn, in parallel, scaling floor respected |
| A team member hoards leads for one final dump | Raise law — every lead, finding, and dead end broadcast the moment it surfaces |
| Worker reply without the EXPAND tail | One follow-up demanding it; the lane stays open until it lands |
| Stopping after wave 1 because "enough was found" | Convergence rules only: 2+ expansion waves, leads run dry |
| Obeying a surrounding "stop exploring" rule mid-research | Authority section — those rules do not bind this mode |
| Asking a worker to write the journal or claim ledger | Workers are read-only; you write every session file |
| Two workers given the same angle | One unique angle per worker, always |
| Contested claim settled by judgment | Phase 3 — run code, capture output, verdict |
| High-risk non-code claim asserted without clearing the ledger | Phase 3b — only verified-claims rows reach the synthesis |
| Deliverable claims without citations | Every claim cites a source or a verification artifact |

## Completion checklist

- Every axis from Phase 0 was covered by at least one dedicated worker, with a wave artifact.
- Every EXPAND lead was investigated, deduplicated, or closed as dead, and convergence was reached under the Phase 2 rules.
- Every code-shaped contested claim has a `verify-<slug>.md` verdict; every high-risk non-code claim is verified, unresolved, or omitted.
- `SYNTHESIS.md` exists and every substantive claim carries a `[Source N]` citation or a verification artifact.
- The final Superloopy evidence record points at the synthesis (or the report, when one was requested).
