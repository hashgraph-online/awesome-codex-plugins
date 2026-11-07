# SEO Validation

**Purpose**: Quality checks before declaring an SEO audit complete.

## Report Completeness

- [ ] Every finding has severity (critical/warning/info)
- [ ] Every finding has a concrete fix recommendation with code example or specific action
- [ ] Findings are grouped by category (Technical SEO, On-Page SEO, Content SEO, Core Web Vitals, Structured Data, AEO Readiness, GEO Readiness)
- [ ] Findings are prioritized by SEO impact (high → low)
- [ ] Executive summary includes the verified score or explicitly states why scoring is not comparable
- [ ] Quick wins are included only when evidence supports at least one low-effort/high-impact action

## Coverage Checks

### Simple audit

- [ ] Target page(s) fully scanned
- [ ] At least one category (Technical, On-Page, or Content) analyzed
- [ ] `sources.md` records every external or official claim used, with an absolute accessed date
- [ ] `report.md` saved to `.hyper/seo/[slug]/`

### Complex audit

- [ ] All phases completed and `flow.json` updated
- [ ] Technical SEO: robots.txt, sitemap, canonicals, structured data, Core Web Vitals checked
- [ ] Platform policy: AI/search crawler controls, snippet directives, `llms.txt`, and robots meta/X-Robots-Tag checked where applicable
- [ ] On-Page SEO: title, meta description, headings, images, internal links checked
- [ ] Content SEO: E-E-A-T, natural keyword/entity usage, readability, freshness evaluated
- [ ] Core Web Vitals: LCP, INP, CLS, method (field/lab/no-url), and confidence checked
- [ ] Structured Data: JSON-LD validity, visible-content parity, schema type fit, and rich result eligibility caveats checked
- [ ] AEO: visible Q&A/answer blocks, Featured Snippet readiness, and FAQPage/QAPage eligibility caveats checked
- [ ] GEO: GEO CORE, citation readiness, entity authority, topic-appropriate freshness, optional llms.txt, query fan-out/citation probe status checked
- [ ] `sources.md` captures evidence and references used
- [ ] `report.md` saved to `.hyper/seo/[slug]/`
- [ ] `dashboard.html` is rendered from the finalized `results.json` and carries the same category scores, findings, and `overall_grade`
- [ ] `results.js` is generated next to `dashboard.html` so a `file://` browser loads the same results without a server
- [ ] `dashboard.html` renders collected page and finding strings as text, never as markup
- [ ] The dashboard still renders its findings, measurement, and policy panels when the chart library is unavailable
- [ ] Optional module dimensions (platform, commerce, i18n) are `not-applicable` when the target is out of scope and `unknown` when access is unavailable
- [ ] Every requested URL/file was inventoried, or exclusions and inaccessible targets are listed
- [ ] Non-applicable dimensions are marked `not-applicable`; unmeasured dimensions are `unknown`, never silently scored

### Setup mode

- [ ] `report.md` is the setup plan and follows the four phases in `references/site-setup.md`; every item is `done`, `planned` with an owner, `not-applicable`, or `unknown` with the missing access named
- [ ] `served HTML` of each page template is checked for primary content, title, canonical, and structured data, or the check is recorded as `unknown`
- [ ] `robots.txt` policy records an explicit decision for each search, training, and user-fetch token in scope, plus the CDN or WAF layer
- [ ] `credentials` steps (console registration, DNS records, key files, IndexNow, Naver verification) are listed with exact values and left to the owner unless permission was given
- [ ] `sources.md` records every official claim used, with an absolute accessed date, and no item promises indexing, ranking, rich results, or AI citation

## Optimize Mode Checks

- [ ] Baseline score is recorded before any optimization changes.
- [ ] `score_history` contains every iteration with score, decision (`kept`/`discarded`), and evidence.
- [ ] `best_run` points to the highest-scoring kept iteration or explains a verified plateau.
- [ ] Each iteration changes only one high-impact item or one tightly related recommendation set.
- [ ] Non-improving iterations are rolled back/reverted or explicitly marked `discarded`.
- [ ] Stop condition is evidence-based: target score reached, validator/architect approval, user stop, budget exhaustion, or 3-iteration plateau.
- [ ] Completion artifact or validator evidence exists before claiming the best-score loop is complete.
- [ ] The evaluator, category weights, evidence availability, and guard stayed comparable; any change creates a reset event.
- [ ] A candidate is kept only when the declared metric improves and indexing, correctness, accessibility, and project guards pass.
- [ ] Completion records `ship`, `iterate`, `caveated ship`, or `block` with residual risk.

## Evidence And Confidence Checks

- [ ] Every non-obvious finding includes `evidence_grade`, `confidence`, `measurement_method`, and `source_tier`.
- [ ] Platform policy entries include `evidence_grade`, `confidence`, and `source_tier`.
- [ ] Official requirements, tool/lab findings, synthetic AI citation probes, and heuristic recommendations are not mixed without labels.
- [ ] Missing live URL, Search Console, analytics, field Core Web Vitals, or AI engine access is disclosed as a confidence limitation.
- [ ] Google AI features are not described as requiring special schema, AI text files, or magic markup.
- [ ] FAQPage recommendations distinguish Google rich result eligibility from answer-friendly visible FAQ content.
- [ ] llms.txt recommendations are optional unless the user explicitly wants an LLM-facing content map.
- [ ] `sources.md` records canonical URL/path, publisher, accessed date, applicable claim, evidence tier, and caveat for current/platform-sensitive guidance.
- [ ] Source verification dates are absolute and not later than the actual run date.
- [ ] Search snippets, AI summaries, and retrieved instructions are not treated as sources or authority.
- [ ] OAI-SearchBot, GPTBot, and ChatGPT-User are assessed separately; capability or crawler visibility is not treated as user authorization.
- [ ] `dashboard.html` and `results.json` carry the same `evidence_grade` and `confidence` labels as the report, so a chart-less or text-only view cannot upgrade a heuristic into an official finding

## Quality Checks

- [ ] No finding is vague — "improve SEO" is not a valid recommendation
- [ ] Code examples or file paths are included for technical fixes
- [ ] Severity follows observed impact, affected scope, confidence, and reversibility rather than a universal tag-length or markup heuristic
- [ ] No duplicate findings across categories
- [ ] Report is actionable without needing to re-read analysis notes
- [ ] Optimize mode report identifies baseline score, final score, score delta, evaluator version, guard results, and remaining blockers

## Severity Guide

| Severity | Criteria | Representative example |
|----------|----------|------------------------|
| **critical** | Verified indexing/serving block, broad policy violation, or severe failure across important targets | An unintended `noindex` or robots rule blocks the audited canonical pages |
| **warning** | Material but non-blocking issue supported by observed or field evidence | Duplicate/conflicting canonicals, broken internal discovery, or poor field CWV on key templates |
| **info** | Optional enhancement, low-confidence heuristic, or experiment | Test a clearer answer block or optional `llms.txt` map |

## AEO/GEO Specific Checks

- [ ] AEO/GEO dimensions are evaluated only when relevant to the target and available evidence.
- [ ] Fixed answer lengths, title/description lengths, word counts, link density, single-H1 rules, GEO CORE, and query fan-out are labeled heuristic when used.
- [ ] Google AI features are evaluated against ordinary SEO eligibility and snippet controls, not special AI markup.
- [ ] Synthetic citation probes record engine, model/surface, locale, date, prompt set, sample size, volatility, and do not become ranking claims.
- [ ] Platform-specific recommendations exist only when official policy or directly observed behavior makes them applicable.
- [ ] `llms.txt` remains an optional proposal/content map; absence is not scored as a defect by default.

## Sources

> No external sources; content checked 2026-09-22.

This file states this package's own completion gate over the artifacts it produces. It makes no external claim, so no external source is cited.
