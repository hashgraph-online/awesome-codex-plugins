---
name: hyper-aso
description: "Use this skill when the user asks for an App Store or Google Play ASO audit, a store-listing setup plan for a new app, or a bounded keyword and conversion optimization loop for a named app. Covers metadata and keywords, screenshots, previews and icons, localization, ratings and reviews, custom pages and listing experiments, quality signals, metadata policy risk, and web-to-app links, saved under `.hyper/aso/[slug]/`. Do not use it for website search visibility, store review or compliance verdicts, paid campaign management, or market research with no named app."
compatibility: Works best with browser access to public store pages and official Apple and Google documentation, optional read access to the owner's App Store Connect or Play Console exports, and read/write access for report artifacts. Validating results.json needs jq 1.6+.
---

Open the rules as directed below. Resolve bundled file paths from the directory containing this document and project paths from the target project.

- [rules/aso-workflow.md](rules/aso-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper ASO

> Audit and improve how a named app is found and chosen inside the Apple App Store and Google Play.

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce an evidence-graded App Store Optimization audit with prioritized actions for a named app, a phased store-listing setup plan for an app that is not yet live, or a bounded optimize loop when the user asks for the best achievable listing. |
| Scope | Owns target classification (store, new or live app, locales), measurement-method selection, metadata, keyword, creative, localization, rating, conversion-tool, quality-signal, policy-risk, and web-link assessment, scoring, findings, recommendations, and the `.hyper/aso/[slug]/` workspace. Does not own editing or submitting the live listing, store review or compliance verdicts, paid campaign management, app UI or feature design, or market research with no named app. |
| Authority | System/harness and user instructions > the owner's console data and the live store page > official Apple and Google policy and documentation > this skill > vendor or heuristic advice. A vendor estimate, tool score, or practitioner claim is never promoted to an official rule. |
| Evidence | Read the live store pages, the owner's exported metadata, and console exports before scoring, and cite the URL, export file, or observation behind every critical and warning finding. Record unavailable checks as `unknown` and irrelevant ones as `not-applicable`; never invent a rank, volume, conversion rate, or download count. |
| Tools | Browser or fetch access to public store pages and official docs, local file reading for exported metadata and screenshots, and `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` to gate the results payload. Console data or a third-party ASO tool is used only when the owner provides it; when one is missing, state the limit and fall back to the strongest lower-grade method. |
| Loop | Optimize mode only: a bounded `audit -> listing change or experiment plan -> re-audit` cycle, default budget three iterations. Feedback = comparable re-audit evidence or a finished store experiment; metric = the 100-point score with `unknown` and `not-applicable` excluded; guard = no comparable-category regression, no policy-risk increase, no evidence-grade promotion; stop = target reached, budget spent, plateau, guard failure, or a step that needs the owner's console or a business decision. |
| Output | `.hyper/aso/[slug]/` holding `results.json`, `results.js`, `dashboard.html`, `report.md`, `sources.md`, and `flow.json` for complex or optimize mode; simple and setup modes keep `report.md` and `sources.md` as the minimum. |
| Verification | Apply `rules/validation.md` at completion: every critical or warning finding carries evidence, every character or asset limit cites a dated official source, scores derive from observed evidence, and optimize mode records baseline, evaluator, budget, guards, discarded iterations, stop reason, and the best comparable result. |
| Stop condition | Stop when the requested audit, plan, or report is complete with graded evidence and no unresolved critical gap, or when optimize mode reaches its target, budget, plateau, guard, or an owner-only step. Never stop by asserting a rank, feature placement, approval, or download outcome the evidence does not support. |

</instruction_contract>

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, schema keys, JSON field names, store field names (`Subtitle`, `Promotional Text`, `Short description`), proper nouns, and quoted source excerpts in their original language. Proposed listing copy is written in each target locale's own language. When a localized template exists (`*.ko.md`), prefer it for user-facing artifacts.

</output_language>

<purpose>

- Audit an app's store presence on the Apple App Store, Google Play, or both, for search (being found) and conversion (being chosen).
- Separate official limits and policy from console measurements, live observations, third-party estimates, and heuristics.
- Plan store setup for an app that is about to launch: fields, keywords, assets, locales, rating flow, links, and the first 30 days of measurement.
- Run a bounded optimize loop that keeps only changes the comparable evidence supports.
- Save the evidence, findings, and prioritized actions under `.hyper/aso/[slug]/`.

</purpose>

<routing_rule>

Use this skill when the main outcome is visibility or conversion of a named app inside an app store: an ASO audit, a store-listing setup plan, keyword or creative recommendations, or an optimize loop.

Route neighboring work by output shape:

- A website's search-engine or AI-answer visibility audit: a web search-visibility deliverable, not this skill's output, even when the site promotes an app. Web-to-app link checks (Universal Links, App Links, Smart App Banner) stay here only as part of an app-store audit.
- A submission-readiness, review-rejection, privacy-label, or policy-compliance verdict: a compliance deliverable, not this skill's output. This skill flags metadata policy risk that affects discoverability and hands the verdict off.
- Running or bidding paid campaigns (Apple Ads, Google App campaigns): campaign management, not this skill's output. This skill may read their keyword data as evidence.
- App screen or feature design: a design deliverable.
- Market or category research with no named app: source-backed research.

</routing_rule>

<activation_examples>

Positive examples:

- "Audit our iOS app's App Store listing and tell me what to fix first."
- "플레이스토어 등록정보 ASO 점검해 줘. 키워드랑 스크린샷 위주로."
- "We launch on both stores next month; give me the store listing setup plan for ko-KR and en-US."
- "Keep improving our App Store product page until the ASO score stops going up."
- "앱스토어 키워드 필드 100자 어떻게 채울지 한국어로 제안해 줘."

Negative examples:

- "Audit our website's SEO." -> a web search-visibility deliverable.
- "Why was our app rejected under guideline 4.3?" -> a review or compliance verdict.
- "Raise our Apple Ads bids on these keywords." -> campaign management.

Boundary examples:

- "Our landing page should drive installs; check it." Use this skill only for the Smart App Banner, store badge links, and app-link files as part of an app-store audit; a page SEO audit is a different deliverable.
- "Make sure our listing won't be rejected." Flag metadata policy risk found during the audit; the approval verdict itself is a compliance deliverable.
- "Research the top fitness apps' ASO." Use this skill only when the output is tied to the user's named app; otherwise it is market research.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|------|------|
| Full ASO audit of a live app | create |
| Focused review of one surface (keywords, screenshots, ratings) | create |
| Re-check after listing changes or a finished experiment | update |
| Add a store or locale to an existing audit | update |
| Store-listing plan for an app that is not yet live | setup |
| Iterative improvement toward the best achievable listing | optimize |

A request with no named app, bundle ID, package name, or store URL is not this trigger; ask for the app once.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): modes, intake, scoring, artifact contract, phase order, and the stop condition.
- Rules: [rules/aso-workflow.md](rules/aso-workflow.md) owns the phases and the optimize loop; [rules/validation.md](rules/validation.md) owns the completion gates; [rules/apple.md](rules/apple.md) and [rules/google-play.md](rules/google-play.md) own the per-store checks; [rules/listing-assets.md](rules/listing-assets.md) owns screenshot, preview, and icon checks; [rules/localization.md](rules/localization.md) owns locale, storefront, Korean-language, and ONE store checks.
- References: [references/policy-limits.md](references/policy-limits.md) (dated official limits), [references/keyword-research.md](references/keyword-research.md) (keyword method and metric caveats), [references/metrics.md](references/metrics.md) (metric dictionary), [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md) (web-to-app links and AI recommendation surfaces), [references/artifact-spec.md](references/artifact-spec.md) (workspace and `results.json` schema), [references/sources.md](references/sources.md) (the research ledger behind this package).
- Assets: the Korean and English report templates, `assets/dashboard-template.html`, `assets/runtime/check-results.jq`, and `assets/evals/`, the trigger and behavior cases.

</skill_architecture>

<loop_policy>

- Only optimize mode loops; every other mode is one pass with a completion gate.
- Record the baseline, evaluator, budget, and guards before the first change, and the stop reason when the loop ends.
- A store experiment (Product Page Optimization, Store Listing Experiments) counts as evidence only after it finishes on the store's own statistics; an iteration that waits on one is recorded `pending`, not `kept`.
- Keep an iteration only when a comparable category improves without a regression or a policy-risk increase; otherwise mark it `discarded`.
- The loop procedure is [rules/aso-workflow.md](rules/aso-workflow.md) phase 9; the fields to record are in [rules/validation.md](rules/validation.md) §Optimize Mode Checks.

</loop_policy>

<language_and_translation_default>

- Canonical package files are English and every `*.ko.md` is a structurally aligned Korean translation; deliverables follow `<output_language>`, with `assets/report.template.ko.md` as the default report template.

</language_and_translation_default>

<reference_routing>

- Read [rules/aso-workflow.md](rules/aso-workflow.md) at the start of any run; it owns the phase procedures.
- Read [rules/apple.md](rules/apple.md) when the App Store is in scope and [rules/google-play.md](rules/google-play.md) when Google Play is in scope.
- Read [rules/listing-assets.md](rules/listing-assets.md) when screenshots, previews, icons, or feature graphics are assessed.
- Read [rules/localization.md](rules/localization.md) when more than one locale or storefront is in scope, when Korean is a target language, or when ONE store is named.
- Read [references/policy-limits.md](references/policy-limits.md) before stating any character, size, count, or duration limit.
- Read [references/keyword-research.md](references/keyword-research.md) before proposing keywords or reading a popularity or difficulty number.
- Read [references/metrics.md](references/metrics.md) before reading or comparing console metrics.
- Read [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md) when web-to-app links or AI assistant recommendations are in scope.
- Read [references/artifact-spec.md](references/artifact-spec.md) before writing `.hyper/aso/[slug]/`.
- Read [references/sources.md](references/sources.md) only to trace a claim in this package back to its source.
- Read `assets/report.template.ko.md` when drafting a report, and `assets/report.template.md` only when English is required.
- Read [rules/validation.md](rules/validation.md) before declaring the run complete.

</reference_routing>

<support_file_read_order>

1. This core, to fix the mode, the stores, the locales, and the app.
2. `rules/aso-workflow.md`, then the store rules for each store in scope.
3. `references/policy-limits.md`, `references/keyword-research.md`, and `references/metrics.md` as their phases start.
4. `rules/listing-assets.md`, `rules/localization.md`, and `references/web-and-ai-surfaces.md` when their surfaces are in scope.
5. `references/artifact-spec.md` before writing the workspace, then the report template.
6. `rules/validation.md` before completion.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|------|------|------|
| 0 | Fix app identity, stores, new-or-live, locales, mode, complexity, and proof surface | Execution brief |
| 1 | Establish measurement methods and confidence limits | `measurement_methods` |
| 2 | Collect live listing, exported metadata, console data, and official limits | Evidence log |
| 3 | Assess metadata and keywords per store and locale | Metadata findings |
| 4 | Assess creative assets and conversion tools | Creative and conversion findings |
| 5 | Assess ratings, reviews, and quality signals | Rating and quality findings |
| 6 | Assess policy risk and web-to-app links | Risk and link findings |
| 7 | Score, prioritize, and write artifacts | `.hyper/aso/[slug]/` |
| 8 | If optimize mode, apply or plan one change and re-audit | Best comparable result |
| 9 | Summarize score, wins, limits, risks, and next actions | Final report |

</workflow>

<complexity_routing>

| Complexity | Signals | Handling |
|------|------|------|
| **Simple** | One store, one locale, one surface (keywords only, screenshots only) | **Direct**: write `report.md` immediately |
| **Complex** | Both stores, several locales, full audit, competitor comparison, or optimize mode | **Tracked**: use `flow.json` for phase tracking |

Before starting, record `Complexity: [simple/complex] — [reason]`, `Mode: [create/update/setup/optimize]`, `App: [name, bundle ID or package name, store URLs]`, `Stores: [app_store/google_play/both]`, `Locales: [list]`, and `Proof surface: [store pages, exports, console data, official docs]`.

</complexity_routing>

<universal_intake>

Before scoring, classify the context:

- `stores`: `app_store`, `google_play`, or both; `one_store` only when the user names it.
- `app_state`: `pre-launch`, `live`, or `relaunch`.
- `locales`: every metadata locale and storefront in scope, with the primary language per store.
- `access_level`: public store page only, owner-exported metadata, App Store Connect analytics, Play Console statistics, third-party ASO tool data, or none.
- `allowed_action`: `audit-only`, `recommend`, `draft-copy`, or `optimize-loop`. Editing or submitting the live listing always stays with the owner.
- `evaluator`: comparable app set, rubric version, dates, stores, locales, and evidence channels.

Classify every finding and score input as exactly one of `official`, `live`, `console`, `tool`, `synthetic`, or `heuristic`. A third-party popularity or difficulty number is `tool`, never `console`; a public store page reading is `live`, never `console`.

</universal_intake>

<artifact_contract>

Create or update `.hyper/aso/[slug]/` at the project root:

```text
.hyper/aso/[slug]/
├── dashboard.html      # browser-readable dashboard (copied template)
├── results.json        # structured audit results
├── results.js          # file:// fallback, generated from results.json
├── report.md           # Markdown report or setup plan
├── sources.md          # source and evidence ledger
└── flow.json           # complex or optimize mode
```

Write `results.json` from gathered evidence first, gate it with `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` (prints `ok`, or exits 1 with one `E` line per violation), then generate `results.js` and copy the dashboard as [references/artifact-spec.md](references/artifact-spec.md) shows, then write `report.md` from [assets/report.template.ko.md](assets/report.template.ko.md) and `sources.md`. `sources.md` records, for every external or official claim, its URL, accessed date, applicable claim, evidence class, and limitation.

</artifact_contract>

<scoring>

Use a transparent 100-point score when enough evidence exists:

- Metadata and keywords: 25
- Creative assets: 20
- Ratings and reviews: 15
- Localization: 10
- Conversion tools (custom pages, experiments, events, promoted content): 10
- Quality signals (stability, size, store warnings): 10
- Policy risk: 5
- Web-to-app links: 5

Mark a category `unknown` when its evidence is missing and `not-applicable` when it does not apply (for example conversion tools before launch), and exclude both from the denominator. The score is an internal prioritization aid, not a store ranking factor. Each finding carries severity, store, category, evidence, `evidence_grade`, confidence, measurement method, a specific recommendation, and the owner surface; [references/artifact-spec.md](references/artifact-spec.md) holds the schema.

</scoring>

<required>

| Category | Required |
|---|---|
| Target | A named app with its store identifiers, and the mode, stores, locales, and proof surface recorded before scoring |
| Limits | Every character, size, count, or duration limit taken from [references/policy-limits.md](references/policy-limits.md) or re-read on the official page, with its checked date |
| Evidence | Every critical and warning finding carries a URL, export path, or observation, plus its evidence grade |
| Scoring | A total computed only from observed categories |
| Copy | Proposed listing copy that fits each field's limit as counted by the store's own unit (characters or bytes) |

</required>

<forbidden>

| Category | Forbidden |
|---|---|
| Evidence | A rank, search volume, conversion rate, or download count asserted without a recorded measurement; an `unknown` filled in to reach a total |
| Grading | A vendor estimate or practitioner rule ("the description is indexed on iOS", "caption text is OCR-indexed") presented as an official rule |
| Guarantees | Promising a rank, featuring, approval, or install lift from any change |
| Policy | Recommending keyword stuffing, competitor or unrelated brand names, rank or price claims in metadata or graphics, or incentivized or gated ratings |
| Scope | Editing or submitting the live listing, answering reviews, or acting in a console without the owner's explicit permission |

</forbidden>

<validation>

Apply [rules/validation.md](rules/validation.md) before declaring a run complete. It requires evidence on every critical and warning finding, dated official sources for every limit, copy that fits each field, scores derived from observed evidence with `unknown` and `not-applicable` excluded, a `sources.md` ledger, and, in optimize mode, the recorded baseline, evaluator, budget, guards, discarded iterations, stop reason, and best comparable result.

</validation>

## Sources

> Checked 2026-11-22. The modes, the 100-point weights, and the optimize guards are this package's design, modelled on the repository's web search-visibility audit package (user instruction, 2026-11-22). Every external fact the audit applies carries its source and checked date in [references/policy-limits.md](references/policy-limits.md) and [references/sources.md](references/sources.md); the package shape follows `instructions/skill/SKILL_AUTHORING.md`.
