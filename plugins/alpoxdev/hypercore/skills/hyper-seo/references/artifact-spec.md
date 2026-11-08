# SEO Audit Artifact Spec

Use this reference when creating or reviewing the result workspace for an SEO audit run.

## Contents

- Workspace Shape
- `results.json`
- `results.js`
- `dashboard.html`
- `report.md`
- `flow.json`
- Lifecycle Rules

## Workspace Shape

```text
.hyper/seo/[slug]/
├── dashboard.html       # browser-openable dashboard
├── results.json         # structured audit results
├── results.js           # fallback for file:// browsers
├── report.md            # Markdown report (existing)
├── sources.md           # source log (existing)
└── flow.json            # complex path only (existing)
```

Create this directory at the repository root, not inside the skill folder.

Canonical generated assets:

- template: `skills/hyper-seo/assets/dashboard-template.html`
- renderer: `skills/hyper-seo/scripts/render-dashboard.sh`
- renderer runtime: bash 3.2+ with `jq`

## `results.json`

```json
{
  "project_name": "my-website",
  "date": "2026-03-27",
  "scope": "Full site audit",
  "status": "complete",
  "overall_grade": "C",
  "categories": [
    { "name": "Technical SEO", "status": "measured", "score": 85, "evidence": "crawl plus robots/header scan", "confidence": "high" },
    { "name": "On-Page SEO", "status": "measured", "score": 72, "evidence": "title/meta/heading sample of 40 pages", "confidence": "high" },
    { "name": "Content SEO", "status": "measured", "score": 68, "evidence": "thin-content and internal-link scan", "confidence": "medium" },
    { "name": "Core Web Vitals", "status": "measured", "score": 90, "evidence": "Lighthouse lab run, no field data", "confidence": "medium" },
    { "name": "Structured Data", "status": "measured", "score": 88, "evidence": "schema static scan plus rich results test", "confidence": "high" },
    { "name": "AEO Readiness", "status": "measured", "score": 45, "evidence": "answer-block detector over the top pages", "confidence": "medium" },
    { "name": "GEO Readiness", "status": "measured", "score": 38, "evidence": "citation and entity scan of the top pages", "confidence": "low" }
  ],
  "measurement_methods": {
    "search_console": { "status": "unavailable", "confidence_impact": "medium" },
    "pagespeed_insights": { "status": "lab-only", "tool": "Lighthouse", "confidence": "medium" },
    "rich_results_test": { "status": "not-run", "fallback_method": "schema_static_scan", "confidence": "medium" },
    "ai_citation_probe": { "status": "not-run", "reason": "no engine access" },
    "crawler_policy_scan": { "status": "completed", "method": "robots/meta/header scan", "confidence": "high" }
  },
  "platform_policy": {
    "oai_searchbot": { "status": "allowed", "purpose": "ChatGPT Search inclusion", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "gptbot": { "status": "blocked", "purpose": "OpenAI model training", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "llms_txt": { "status": "missing", "severity": "info", "evidence_grade": "heuristic", "confidence": "medium", "source_tier": "research-backed-heuristic" },
    "naver_yeti": { "status": "unknown", "purpose": "Naver Yeti crawler access to the audited pages", "evidence_grade": "official", "confidence": "medium", "source_tier": "official-doc" },
    "naver_nosourceinfo": { "status": "not-applicable", "purpose": "Naver AI-generated source description exclusion", "evidence_grade": "official", "confidence": "high", "source_tier": "official-doc" },
    "naver_feeds": { "status": "unknown", "purpose": "RSS and sitemap ownership-domain match", "evidence_grade": "official", "confidence": "medium", "source_tier": "official-doc" },
    "bing_indexnow": { "status": "unknown", "purpose": "IndexNow change notification for the audited URLs", "http_code": null, "batch_size": 0, "key_location_verified": false, "quota_source": "unknown", "evidence_grade": "official", "confidence": "low", "source_tier": "official-doc" }
  },
  "query_fanout": {
    "status": "not-run",
    "queries": [],
    "missing_topics": []
  },
  "citation_probe": {
    "status": "not-run",
    "engines": [],
    "sample_size": 0,
    "confidence": "low"
  },
  "findings": [
    {
      "id": "T1",
      "severity": "critical",
      "category": "Technical SEO",
      "finding": "robots.txt blocks /blog/ path",
      "location": "/robots.txt:3",
      "evidence_grade": "lab",
      "confidence": "high",
      "measurement_method": "static robots.txt scan",
      "source_tier": "observed-file",
      "recommendation": "Remove Disallow: /blog/ line"
    },
    {
      "id": "A1",
      "severity": "warning",
      "category": "AEO Readiness",
      "finding": "No direct answer in first paragraph",
      "location": "/blog/what-is-seo.html",
      "evidence_grade": "heuristic",
      "confidence": "medium",
      "measurement_method": "answer block detector",
      "source_tier": "research-backed-heuristic",
      "recommendation": "Add a concise visible answer block near the top of the section"
    }
  ],
  "quick_wins": [
    {
      "action": "Add meta descriptions to 12 pages missing them",
      "impact": "High",
      "effort": "Low"
    }
  ],
  "score_history": [
    {
      "iteration": 0,
      "score": 66,
      "grade": "C",
      "critical_count": 1,
      "decision": "baseline",
      "evaluator_version": "2026-03-27.1",
      "weights": [20, 20, 15, 15, 10, 10, 10],
      "evidence": "Initial audit before optimization changes"
    },
    {
      "iteration": 1,
      "score": 78,
      "grade": "B",
      "critical_count": 0,
      "decision": "kept",
      "evaluator_version": "2026-03-27.1",
      "weights": [20, 20, 15, 15, 10, 10, 10],
      "changed": "Removed robots.txt block for /blog/",
      "evidence": "Re-audit confirmed indexability restored"
    }
  ],
  "best_run": {
    "iteration": 1,
    "score": 78,
    "grade": "B",
    "reason": "Highest kept score with zero critical findings"
  },
  "validator": {
    "status": "passed",
    "summary": "Target passed or plateau condition verified"
  },
  "actions": [
    {
      "priority": 1,
      "category": "Technical SEO",
      "action": "Fix robots.txt blocking blog content",
      "impact": "High",
      "effort": "Low"
    },
    {
      "priority": 2,
      "category": "GEO Readiness",
      "action": "Add statistics and citations to top 10 pages",
      "impact": "High",
      "effort": "Medium"
    }
  ]
}
```

### Evidence and confidence fields

Every non-obvious finding should include:

- `evidence_grade`: `official`, `live`, `field`, `tool`, `lab`, `synthetic`, or `heuristic`.
- `confidence`: `high`, `medium`, or `low`.
- `measurement_method`: the scan, tool, probe, or source used to produce the finding.
- `source_tier`: `official-doc`, `observed-file`, `live-observation`, `field-data`, `tool-output`, `lab-result`, `synthetic-probe`, or `research-backed-heuristic`.

Use high confidence for official docs, direct file/header observations, or field data. Use lower confidence for local-only static scans, lab-only performance, synthetic AI prompt probes, and heuristic AEO/GEO advice.

### Measurement and platform fields

- `measurement_methods` records which evidence channels were available and how they affected confidence.
- `platform_policy` records search/AI crawler and snippet controls by platform or bot. Separate `OAI-SearchBot` search inclusion from `GPTBot` training policy. Conditional platform entries are target-gated: use `not-applicable` when the target is out of scope and `unknown` when the target applies but console, account, or live access is unavailable. When the target set includes Naver surfaces, record `naver_yeti`, `naver_nosourceinfo`, and `naver_feeds`. When it includes Bing surfaces, record `bing_indexnow` with the observed response code, the batch size, whether the key file was verified, and a quota source of `engine` or `unknown`; a receipt code is never recorded as index evidence and no quota number is estimated.
- `query_fanout` records generated subqueries and missing topical coverage.
- `citation_probe` records AI engine, prompt set, cited URLs, brand mentions, sample size, date, and confidence when run. If not run, store `status: "not-run"` and the reason.

### Optimize mode fields

When `mode` is `optimize` or the user asked for highest/max/perfect score, add these fields to `results.json`:

- `target_score` — optional user-defined or evaluator-defined goal; record its rationale and do not default to an arbitrary “perfect” threshold.
- `score_history[]` — ordered iteration log. Each item includes `iteration`, `score`, `grade`, `critical_count`, `decision`, `changed`, `evidence`, `evaluator_version`, `weights`, and `guard`.
- `best_run` — the highest-scoring kept iteration. Required before completion.
- `validator` — artifact-gated completion evidence, such as `{ "status": "passed" }` or an architect review verdict.
- `plateau` — optional object with `consecutive_iterations` and `reason` when completion is due to no further score gains.

Rules:

1. `score_history[0]` is always the baseline before changes.
2. Later scores are comparable only when the evaluator stayed stable. If scoring changes, record a reset event.
3. `best_run` must not point to a discarded iteration.
4. If code changes were made, validator evidence should include the relevant test/build/lint command output summary.
5. A higher rubric score is not sufficient when an indexing, correctness, accessibility, policy, or project guard regresses.
6. `unknown` and `not-applicable` categories never become numeric zeroes.
7. Every `score_history[]` entry records `evaluator_version` and `weights` (the category weights in canonical order). Scores are comparable only inside one evaluator version and weight set.
8. When `evaluator_version`, `weights`, or the category set changes, the first iteration under the new definition carries `decision: "reset"`. Do not report a score delta across a reset.
9. `best_run` must be the highest-scoring `kept` iteration, not merely a kept one.

### Status values

- `running` — audit in progress
- `idle` — waiting
- `complete` — audit complete

### Default category list

Seven default categories. Each category records `status: "measured" | "unknown" | "not-applicable"`, `score: 0..100 | null`, evidence, and confidence. The numeric rubric is an internal prioritization aid, not a Google or AI-platform ranking score.

1. Technical SEO
2. On-Page SEO
3. Content SEO
4. Core Web Vitals
5. Structured Data
6. AEO Readiness
7. GEO Readiness

### Finding ID rules

- `T1`, `T2`... — Technical SEO
- `O1`, `O2`... — On-Page SEO
- `C1`, `C2`... — Content SEO
- `W1`, `W2`... — Core Web Vitals
- `S1`, `S2`... — Structured Data
- `A1`, `A2`... — AEO Readiness
- `G1`, `G2`... — GEO Readiness

### Severity values

- `critical` — blocks indexing or severely harms ranking
- `warning` — degrades ranking or UX
- `info` — improvement opportunity

## `results.js`

Fallback for browsers where `fetch` does not work when opened via `file://`:

```javascript
window.__SEO_RESULTS__ = { /* same content as results.json */ };
```

`render-dashboard.sh` writes this file from the same parsed `results.json` payload as `dashboard.html`, so it is generated output rather than a hand-maintained file. Re-run the renderer after `results.json` changes; hand edits are overwritten.

## `dashboard.html`

Copy it from `skills/hyper-seo/assets/dashboard-template.html`.

Required behavior:

- Auto-refresh every 10 seconds
- Read `results.json` (fall back to `results.js` for `file://`)
- Radar chart for seven category scores
- Severity distribution donut chart
- Category score bars
- Findings table with severity color coding
- Quick Wins table
- Prioritized Actions table
- Overall Grade display (A/B/C/D/F)

## `report.md`

Generate it from the existing `assets/report.template.md`. It is a Markdown rendering of the data in `results.json`.

## `flow.json`

Complex and optimize runs record phase state here. Minimal contract:

```json
{
  "status": "running",
  "resume_at": "onpage",
  "phases": [
    { "name": "scope", "status": "complete" },
    { "name": "measurement", "status": "complete" },
    { "name": "technical", "status": "complete" },
    { "name": "platform_policy", "status": "complete" },
    { "name": "onpage", "status": "running" },
    { "name": "content", "status": "pending" },
    { "name": "aeo", "status": "pending" },
    { "name": "geo", "status": "pending" },
    { "name": "report", "status": "pending" }
  ]
}
```

| Field | Contract |
|-------|----------|
| `phases[].name` | canonical phase name, in the phase order below |
| `phases[].status` | `pending`, `running`, `complete`, or `skipped` |
| `resume_at` | `name` of the first phase whose `status` is not `complete`; a resumed run reads `flow.json` first and continues there |

Canonical phase order: `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report`. Keep this list identical to the phase order in `SKILL.md`.

## Lifecycle Rules

1. Create `.hyper/seo/[slug]/` when the audit starts.
2. Set `status` in `results.json` to `running`.
3. Add findings to `results.json` as each phase completes.
4. After all phases finish, set `status` to `complete` and calculate `overall_grade`.
4-1. In Optimize mode, populate `score_history`, `best_run`, and `validator`, then record the evidence for the highest score or plateau.
5. Run `bash scripts/render-dashboard.sh <artifact-dir>` to generate `dashboard.html` and `results.js`.
6. Write `report.md` and `sources.md` as well.
7. Open `dashboard.html` in a browser if the runtime is safe.

### Grade Calculation

The weighted formula is the only aggregation. Category scores come from the seven default categories in canonical order, and the weights come from the `<scoring>` block in `SKILL.md`.

```text
overall_score = Σ(category_score × category_weight) / Σ(category_weight)
```

| Rule | Contract |
|------|----------|
| Aggregation | `overall_score = Σ(score × weight) / Σ(weight)` over the included categories |
| Included categories | only `status: "measured"` categories count; `unknown` and `not-applicable` categories leave both the numerator and the denominator |
| Weights | the `<scoring>` weights in `SKILL.md`, applied in canonical category order |
| Recorded | included categories, weights, evaluator version, and evidence availability |
| Definition change | when the category set, weights, or evaluator version changes, start a new baseline and record a reset instead of reporting a delta |

Apply the thresholds below to the weighted score.

| Average | Grade |
|---------|-------|
| >= 90 | A |
| >= 75 | B |
| >= 60 | C |
| >= 40 | D |
| < 40 | F |

### Render Order

```bash
bash skills/hyper-seo/scripts/render-dashboard.sh .hyper/seo/my-site
open .hyper/seo/my-site/dashboard.html
```

## Sources

> No external sources; content checked 2026-09-22.

This file specifies this package's own workspace layout, `results.json` schema, dashboard lifecycle, and render order. It states no external claim, so no external source is cited.
