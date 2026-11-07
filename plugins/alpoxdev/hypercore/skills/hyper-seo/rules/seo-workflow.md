# SEO Workflow

**Purpose**: Phase-by-phase execution rules for SEO audits.

## 1. Scope Phase

Define what to audit before scanning:

- Target URLs or file paths (single page, section, or full site)
- Focus area: technical only, on-page only, content only, or comprehensive
- Framework context: Next.js, static HTML, SPA, etc.
- Known constraints: no access to Search Console, no production URL, local-only

Output: scope summary with target list and focus areas.

## 2. Measurement Phase

Establish what can actually be measured before scoring:

- Access level: live URL, local-only files, Search Console, analytics, field Core Web Vitals, AI citation probe access, and available tools
- Evidence class for each method: exactly one of `official`, `live`, `field`, `tool`, `lab`, `synthetic`, or `heuristic`
- Comparable evaluator: target set, scoring rubric, tool/version, dates, and pass/fail checks
- Confidence impact and capability fallback: explain unavailable live, field, probe, or tool access and the strongest lower-grade method used
- Measurement methods to record in `results.json.measurement_methods`

Do not compare field-data, live, lab, tool, synthetic, or local-only results as though they were equivalent. Record unavailable checks as `unknown`, irrelevant checks as `not-applicable`, and exclude `not-applicable` checks from score denominators. A heuristic is not an official failure.

## 3. Technical SEO Phase

Scan for:

- `robots.txt` — exists, correct directives, no accidental blocks
- `sitemap.xml` — exists, valid, includes all indexable pages
- Canonical tags — present, self-referencing or correct cross-referencing
- Structured data — JSON-LD schema markup exists and validates
- HTTPS — enforced, no mixed content
- Core Web Vitals code patterns — image optimization, layout shift prevention, input responsiveness
- Mobile viewport — `<meta name="viewport">` present and correct
- HTTP status codes — no broken links, proper redirects (301 vs 302)
- Clean URL structure — descriptive, kebab-case, no query string abuse

Crawl, render, and index are separate states; record which one was observed:

- A `robots.txt` allow or disallow rule, a `noindex` or X-Robots-Tag directive, and a canonical target are different signals; none of them alone proves that a page is crawled, indexed, or served.
- Audit the raw HTML response and the rendered DOM separately and label the basis of every finding. When the runtime cannot execute JavaScript or reach a live URL, record the capability fallback and leave DOM-only checks `unknown`.
- JavaScript rendering is not itself a failure and not itself a guarantee: the finding is whether the content and metadata reach the rendered result, and a successful browser render is not evidence of indexing.
- `robots.txt` is not a general index-removal tool; use `noindex` or an X-Robots-Tag directive when the intent is removal.
- Sitemap inclusion is a discovery hint, not an index guarantee: check scope, absolute URLs, and `lastmod` accuracy.
- Filter, faceted, and paginated URL explosion, empty-result responses (soft 404), and client-side-only navigation are findings, not acceptable defaults.

Tools: `Glob`, `Grep`, `Read` for file scanning. `WebFetch` for live URL analysis if available.

## 4. Platform Policy Phase

Inspect crawler and AI/search visibility controls separately by platform:
- Googlebot and standard robots directives for indexing and snippets
- Google-Extended for Google AI training/product controls where relevant
- OAI-SearchBot for ChatGPT Search inclusion, GPTBot for OpenAI training, and ChatGPT-User for user-triggered fetches; audit each separately because a rule for one does not imply a rule for another
- Claude-SearchBot (search), ClaudeBot (training), and Claude-User (user fetch); PerplexityBot (search, not training) and Perplexity-User (user fetch); and Applebot-Extended, Meta-ExternalAgent, and CCBot as training controls — each audited as its own token, because a training block does not imply a search block
- CDN or WAF bot rules as a separate layer: an edge default that blocks AI crawlers can override a robots.txt allow, so a robots.txt reading alone is not evidence of access
- The Search Console generative AI setting (include, exclude, or inherit) when Google AI features are in scope; it is a precondition for display, not a ranking signal, and an unreadable setting is `unknown`
- `nosnippet`, `data-nosnippet`, `max-snippet`, `noindex`, canonical, and X-Robots-Tag effects
- `llms.txt` only as an optional proposal/content map, not a standard or ranking/citation requirement
- Google AI features using ordinary SEO fundamentals: assess relevant indexability and snippet eligibility, without prescribing special AI schema or text files; eligibility does not guarantee inclusion
- Naver surfaces when the target set includes them: `Yeti` crawler access and Search Advisor ownership verification, Naver's own `robots.txt` response handling (4xx is allow-all, 5xx is block-all, more than five redirects is allow-all), RSS and sitemap URLs matching the ownership-verified domain, the `og:image` conditions (larger than 150x150, at least 5,000 bytes, no wider than 3:1, page-unique), and `nosourceinfo`, which suppresses only Naver's AI-generated source description for the site — not AI briefing or model training in general
- Do not transfer Google-only directives to Naver: `nosnippet`, `max-snippet`, `data-nosnippet`, `Google-Extended`, FAQPage rich results, and `llms.txt` have no documented Naver counterpart, so none of them is reported as a Naver requirement. A missing Naver document is not evidence that Naver ignores the signal
- On Naver, soft 404 responses and JavaScript-only navigation are index-exclusion risks: a content-free 200 response is collected as a normal page, and content reachable only through JavaScript can be left out of the index
- Bing surfaces when the target set includes them: treat IndexNow as change notification only — a 200 response means the URL was received and a 202 that key validation is pending, and neither one is index, ranking, or AI-citation evidence. Verify the `key file` as ownership proof (8-128 characters of `[A-Za-z0-9-]`, reachable at the host root or at the `keyLocation` path without a login), record the per-POST limit of 10,000 URLs, honor `Retry-After` and shrink the batch on a 429, account for the crawl quota each submitted URL consumes, and do not backfill existing URLs. Do not submit URLs or deploy a key file unless the user asks
- Bing sitemap processing ignores `changefreq` and `priority`; only `lastmod` in ISO 8601 is read, so neither field is reported as a Bing requirement

Policy risk review, separate from crawler controls:

- Check the target against spam and abuse policies: scaled content abuse, expired-domain reuse, site reputation abuse, doorway pages, and thin affiliate pages. See `references/seo-fundamentals.md` for the policy detail.
- Using generative AI is not by itself a policy violation; judge the outcome and the value added rather than the tool used.
- Record every policy finding with one of the defined evidence classes (`official`, `live`, `tool`, `lab`, `synthetic`, `heuristic`); do not state an unverified policy as fact.

Conditional platform modules — enter a module only when its target condition holds; when it does not, record that dimension as `not-applicable`:

- **Naver** — the audited target set includes Naver search surfaces, or the user asks for a Naver audit. Its conditional items are the Naver block in `references/seo-checklist.md`.
- **Bing/IndexNow** — the target set includes Bing surfaces, or the user asks for change notification. Its conditional items are the Bing block in `references/seo-checklist.md`.
- **Commerce/i18n** — the target has product listing, merchant feed, or multi-locale surfaces; assess these inside Technical SEO and Structured Data rather than as separate dimensions.

When a module condition holds but account, console, or live access is unavailable, record `unknown` rather than a pass.

Record policy findings with high confidence only when backed by an applicable official source or directly observed files/headers. For source-sensitive claims, add a source-ledger entry with URL, date, applicable claim, evidence class, and limitation.

## 5. On-Page SEO Phase

Scan for:

- `<title>` — present, unique where pages have distinct intent, accurate and useful for the result context; length and keyword placement are heuristic observations, not official failures
- `<meta name="description">` — present where supported and useful, accurate and compelling; character counts and keyword placement are heuristic observations, not official failures
- Heading hierarchy — meaningful, accessible structure appropriate to the page; multiple or absent `h1` elements require contextual review, not an automatic failure
- Image alt text — meaningful non-decorative images have appropriate text alternatives
- Open Graph tags — `og:title`, `og:description`, `og:image`, `og:url` when the sharing surface is in scope
- Twitter Card tags — `twitter:card`, `twitter:title`, `twitter:description` when the sharing surface is in scope
- Internal links — descriptive anchor text and contextual relevance; link density is a heuristic observation, not a requirement
- URL slug — descriptive and stable when the URL is under project control; query parameters are assessed by purpose
- Rendering basis — record whether title, description, headings, and links were read from the raw HTML response or from the rendered DOM; client-rendered values are reported with that basis.

Tools: `Grep` for pattern matching (`<title>`, `<meta`, `<h1>`, `alt=`), `Read` for page content.

## 6. Content SEO Phase

Evaluate for:

- E-E-A-T signals — experience, expertise, authoritativeness, trustworthiness where relevant
- Keyword placement — natural alignment with the page's intent, not forced repetition
- Keyword and entity usage — natural placement where useful without stuffing or fixed-density targets
- Search intent fit — when live search is available, compare the page outline with the result formats on top, related searches and questions, comparison targets, and the next question searchers ask; a missing subtopic is a `heuristic` content finding, never an official failure
- Content depth — sufficient coverage for the user intent and page type; word count is a heuristic observation, not a minimum requirement
- Readability — structure and language appropriate to the intended audience and format
- Freshness — dates and updates appropriate to the topic's time sensitivity
- Uniqueness — no harmful duplicate content across pages
- AI content — when relevant, evidence of review and value-add rather than a blanket AI-content rule
- Rendering basis — when content exists only after client-side rendering, state that the evaluation used the rendered DOM and record the capability limit.

Tools: `Read` for content analysis, `WebSearch` for competitor/SERP context if needed.

## 7. AEO Phase (Answer Engine Optimization)

Evaluate readiness for AI direct answers and Featured Snippets:

- **Q&A format** — Whether concise visible answer blocks serve relevant user questions; placement and length are heuristics.
- **Featured Snippet readiness** — Whether visible structure could be eligible for definition, list, or table snippets; this is not a guarantee.
- **Voice search readiness** — Whether natural-language questions help the target audience; it is a contextual heuristic.
- **Answer extraction ease** — Whether clear structure and concise passages help readers and systems; sentence counts are heuristic.
- **FAQ/Q&A structure** — Whether visible FAQ/Q&A content is useful, while distinguishing Google FAQ rich-result eligibility from answer-friendly content.
- **Platform observations** — Do not prescribe fixed content preferences for ChatGPT, Perplexity, or Google AI Overviews. Record any platform-specific probe as dated, volatile live or synthetic evidence.
- **Entry condition** — run this phase when the target's intent is answer- or citation-relevant; otherwise record AEO readiness as `not-applicable` instead of scoring it.

Tools: `Grep` for Q&A patterns, heading structures. `Read` for content analysis. See `references/aeo-geo-guide.md` for strategy details.

## 8. GEO Phase (Generative Engine Optimization)

Evaluate readiness for possible citation in generative responses; never promise a citation:
- **GEO CORE assessment**:
  - **Context** — Does the topic include sufficient context and background?
  - **Organization** — Does the content have clear hierarchy and extractable formatting?
  - **Reliability** — Does it include verifiable statistics, citations, and expert opinions?
  - **Exclusivity** — Does it include proprietary data, original research, or a unique perspective?
- **Entity authority** — Topic cluster structure and knowledge consistency across multiple content pieces.
- **Citable statements** — Short, independently supportable statements, including statistics where relevant.
- **Content freshness** — Updated dates and source dates appropriate to the topic's time sensitivity.
- **llms.txt** — An optional proposed LLM-facing content map; its absence is not a standard, ranking, or citation failure.
- **Schema markup** — Whether JSON-LD matches visible entity information. This does not guarantee AI citation.

Tools: `Grep` for citation patterns and statistics, `Read` for content freshness, and `Glob` for `llms.txt`. If named tools or live probes are unavailable, record the capability fallback and resulting unknowns rather than simulating a result.

Optional high-confidence extensions — enter each extension only when the runtime and access allow it; otherwise record it as `unknown` and continue:
- **Query fan-out simulator** — generate a bounded, documented subquery set and map missing coverage before recommending content expansion.
- **AI citation probe** — run or prepare a stable, comparable prompt set for ChatGPT, Perplexity, Gemini, or other engines; record engine, date, sample size, prompts, cited URLs, brand mentions, evidence class, and unresolved volatility.

## 9. Score Optimization Phase (Optimize Mode Only)

Run this phase when the user asks for the highest score, max score, perfect score, or repeated improvement. It is a bounded process, not an infinite loop.

1. **Baseline and budget first** — before changing files or recommendations, record the current category average, `overall_grade`, critical-finding count, target score, finite iteration budget (default three), and regression guards in `results.json.score_history[0]`.
2. **Stable evaluator** — keep the same comparable target set, scoring categories, evidence classes, tools/versions, and pass/fail checks for all iterations. If the evaluator changes, record a reset event and do not compare the new score with old runs.
3. **One change per iteration** — choose one high-impact change or one tightly related recommendation set. Avoid bundling unrelated technical, content, and AEO/GEO changes in the same iteration.
4. **Comparable re-audit** — update category scores, findings, quick wins, evidence class, capability limits, and unknown/not-applicable states. Append an iteration record with `iteration`, `changed`, `score`, `critical_count`, `decision`, and `evidence`.
5. **Guard and discard** — keep an iteration only when comparable evidence improves without a regression guard. Otherwise rollback/revert code changes where possible or mark the iteration `discarded`; preserve `best_run`.
6. **Stop gates** — stop at the target, finite budget, plateau, guard failure, no safe local fix, required external credential/business decision, or user stop. Record the stop reason.
7. **Completion artifact** — finish with `results.json.status: "complete"`, populated `score_history`, populated `best_run`, and evidence explaining why the final result is the best comparable verified run.

Do not fake a perfect score or promise ranking, AI-feature inclusion, or citation. Report unknowns and capability limits.

## 10. Report Phase

Compile findings into `report.md`:

1. Executive summary with overall SEO health score (A/B/C/D/F)
2. Findings grouped by category (Technical SEO, On-Page SEO, Content SEO, Core Web Vitals, Structured Data, AEO Readiness, GEO Readiness)
3. Each finding has: severity (critical/warning/info), description, location, fix recommendation
4. Prioritized action items sorted by impact
5. Quick wins section for low-effort/high-impact fixes

Write evidence and raw data to `sources.md` as a source ledger. For each official or external source-sensitive claim, record URL, accessed or published date, applicable claim, evidence class, and scope or availability limitation.

## Optimize Mode Rules

- Use `optimize` when the user explicitly requests the highest score, max score, perfect score, repeated iteration, or an infinite-loop-style improvement request.
- Start from `create` or `update` audit output, then enter the Score Optimization Phase.
- Preserve the best-scoring report and dashboard even when later experiments are discarded.
- If implementation edits are allowed, verify each kept code-changing iteration with relevant project checks before treating it as `best_run`.

## Mode Rules

### Create mode

- Full analysis from scratch
- All phases run sequentially
- Template-based report generation

### Update mode

- Read existing `report.md` first
- Only re-analyze changed or newly requested areas
- Append dated changelog entry to report
- Preserve prior findings unless superseded

### Setup mode

- Use for a site or homepage that is being planned, built, or rebuilt, when the requested output is a setup plan or launch checklist rather than a score.
- Follow `references/site-setup.md` phases in order: plan before build, build checks before launch, launch-day registration, first 30 days.
- Write `report.md` as the setup plan and `sources.md` as the ledger; add `results.json` and the dashboard only when the user also asks for a scored audit of an existing build.
- Record every item as `done`, `planned` with an owner, `not-applicable`, or `unknown` with the missing access named.
- Prepare console registration, DNS records, key files, and submissions with exact values, but leave them to the site owner unless the user gives permission to act with their credentials.

## Research Rule

- If the audit needs live SERP data, competitor analysis, or current ranking info, run web searches with specific queries.
- If the user already provided sufficient context, do not force unnecessary external research.
- Record all external queries and sources in `sources.md`.

## Sources

> No external sources; content checked 2026-11-03.

This file states this package's own execution phases, evidence grading, and reporting order. It makes no external claim, so no external source is cited.
