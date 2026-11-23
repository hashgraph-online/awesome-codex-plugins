# ASO Artifact Spec

Use this reference when creating or reviewing the result workspace of an ASO run.

## Contents

- Workspace shape
- `results.json`
- Rendering
- `flow.json`
- Lifecycle rules

## Workspace Shape

```text
.hyper/aso/[slug]/
├── dashboard.html       # copied from assets/dashboard-template.html
├── results.json         # structured results
├── results.js           # file:// fallback generated from results.json
├── report.md            # report or setup plan
├── sources.md           # source ledger
└── flow.json            # complex or optimize mode
```

Create the directory at the project root, never inside the skill folder. `[slug]` is the app name in kebab-case plus the run scope when useful (`acme-budget-ios-ko`).

## `results.json`

```json
{
  "project_name": "Acme Budget",
  "date": "2026-11-22",
  "scope": "App Store ko-KR and en-US, full audit",
  "status": "complete",
  "overall_grade": "C",
  "stores": {
    "app_store": { "status": "in-scope", "locales": ["ko", "en-US"], "evidence_grade": "live", "confidence": "high", "notes": "id1234567890, iPhone storefront KR and US" },
    "google_play": { "status": "not-applicable", "notes": "no Android app" }
  },
  "categories": [
    { "name": "Metadata and keywords", "status": "measured", "score": 55, "evidence": "live page plus exported metadata", "confidence": "high" },
    { "name": "Creative assets", "status": "measured", "score": 70, "evidence": "live screenshots, iPhone and iPad", "confidence": "medium" },
    { "name": "Ratings and reviews", "status": "measured", "score": 60, "evidence": "live rating KR 4.2 (1,203) on 2026-11-22", "confidence": "medium" },
    { "name": "Localization", "status": "measured", "score": 40, "evidence": "two locales, no en-GB for KR storefront", "confidence": "high" },
    { "name": "Conversion tools", "status": "unknown", "score": null, "evidence": "no App Store Connect access", "confidence": "low" },
    { "name": "Quality signals", "status": "unknown", "score": null, "evidence": "no crash export", "confidence": "low" },
    { "name": "Policy risk", "status": "measured", "score": 80, "evidence": "guideline 2.3 scan", "confidence": "high" },
    { "name": "Web-to-app links", "status": "measured", "score": 50, "evidence": "AASA 200, no Smart App Banner", "confidence": "high" }
  ],
  "measurement_methods": {
    "store_page": { "status": "completed", "evidence_grade": "live", "confidence": "high", "notes": "KR and US storefronts, 2026-11-22" },
    "app_store_connect": { "status": "unavailable", "confidence_impact": "high", "reason": "owner did not share analytics" },
    "aso_tool": { "status": "not-run", "reason": "no vendor account" }
  },
  "keyword_set": {
    "status": "draft",
    "keywords": [
      { "term": "가계부", "store": "app_store", "locale": "ko", "placement": "name", "popularity": null, "rank": null, "source": "" },
      { "term": "budget", "store": "app_store", "locale": "en-US", "placement": "subtitle", "popularity": 61, "rank": 48, "source": "Apple Ads API 5-100, 2026-11-20" }
    ],
    "gaps": ["지출 관리", "expense tracker"]
  },
  "findings": [
    {
      "id": "M1",
      "severity": "warning",
      "store": "app_store",
      "category": "Metadata and keywords",
      "finding": "Keyword field repeats 'budget', already in the subtitle",
      "location": "en-US keyword field",
      "evidence": "exported metadata, keywords line 1",
      "evidence_grade": "official",
      "confidence": "high",
      "measurement_method": "field comparison against Apple's search rules",
      "owner_surface": "listing",
      "needs_new_version": true,
      "recommendation": "Replace 'budget' in the keyword field with 'expense,bills' (13 bytes)"
    }
  ],
  "quick_wins": [
    { "action": "Rewrite promotional text around the year-end budgeting use case", "impact": "Medium", "effort": "Low" }
  ],
  "actions": [
    { "priority": 1, "category": "Metadata and keywords", "action": "Remove repeated words across name, subtitle, keyword field", "impact": "High", "effort": "Low" }
  ]
}
```

### Field rules

- `stores` keys: `app_store`, `google_play`, `one_store`, `other`; `status`: `in-scope`, `not-applicable`, `unknown`.
- `categories[].status`: `measured` (score 0-100), `unknown` or `not-applicable` (score `null`). The default eight categories and weights are in `SKILL.md` `<scoring>`.
- `findings[].evidence_grade`: `official`, `live`, `console`, `tool`, `synthetic`, `heuristic`. `confidence`: `high`, `medium`, `low`. `store`: `app_store`, `google_play`, `both`, `other`. `evidence` is required for `critical` and `warning`.
- `findings[].needs_new_version`: `true` when the change ships only with an app version on that store.
- Finding ids: `M` metadata and keywords, `A` creative assets, `R` ratings and reviews, `L` localization, `X` conversion tools, `Q` quality signals, `P` policy risk, `W` web-to-app links.
- `keyword_set.keywords[]`: `term` required; a `popularity` value requires `source` naming the vendor or Apple, the scale, and the date.

### Optimize mode fields

- `target_score`, with its rationale.
- `score_history[]`: `iteration`, `score`, `grade`, `critical_count`, `decision` (`baseline`, `kept`, `discarded`, `reset`), `changed`, `evidence`, `evaluator_version`, `weights`. Entry 0 is the baseline.
- `best_run`: the highest-scoring kept or baseline iteration; required when `status` is `complete`.
- Pending store experiments are listed in `report.md`, not in `score_history`.

## Rendering

From the project root, with `<skill-dir>` the folder this skill is installed in and `D` the artifact directory:

```bash
D=.hyper/aso/<slug>
jq -r -f <skill-dir>/assets/runtime/check-results.jq "$D/results.json"
{ printf 'window.__ASO_RESULTS__ = '; jq -c . "$D/results.json"; printf ';\n'; } > "$D/results.js"
cp <skill-dir>/assets/dashboard-template.html "$D/dashboard.html"
```

- The first command prints `ok`, or exits 1 with one `E<TAB>message` line per violation on stderr; fix `results.json` and run it again before rendering.
- `results.js` is generated output; regenerate it after every `results.json` change.
- The dashboard reads `results.json` over HTTP and `results.js` under `file://`, refreshes every 10 seconds, renders all strings as text, and still shows its tables when the chart library cannot load.

## `flow.json`

```json
{
  "status": "running",
  "resume_at": "creative",
  "phases": [
    { "name": "scope", "status": "complete" },
    { "name": "measurement", "status": "complete" },
    { "name": "metadata", "status": "complete" },
    { "name": "creative", "status": "running" },
    { "name": "ratings_quality", "status": "pending" },
    { "name": "policy_links", "status": "pending" },
    { "name": "report", "status": "pending" }
  ]
}
```

`phases[].status` is `pending`, `running`, `complete`, or `skipped`; `resume_at` names the first phase that is not complete, and a resumed run continues there.

## Lifecycle Rules

- Update mode reads the existing workspace first and appends a dated entry to `report.md` § Changelog.
- Never delete a prior `results.json`; when the evaluator changes, record a `reset` iteration.
- `sources.md` rows are appended, never rewritten; a superseded row is marked `rejected` or `conflict` with the reason.

## Sources

> No external sources; content checked 2026-11-22.

This file specifies this package's own workspace layout, `results.json` schema, and render order. It states no external claim.
