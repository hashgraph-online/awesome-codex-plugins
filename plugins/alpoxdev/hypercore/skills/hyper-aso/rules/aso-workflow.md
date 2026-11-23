# ASO Workflow

**Purpose**: Phase-by-phase execution rules for App Store and Google Play optimization runs.

## 1. Scope Phase

Fix what is audited before collecting anything:

- App identity: display name, Apple ID or bundle ID, Android package name, and the public store URLs. Confirm that every URL resolves to the same app; a same-name app from another developer is a common mix-up.
- Stores: `app_store`, `google_play`, or both. Add `one_store` only when the user names it.
- App state: `pre-launch` (setup mode), `live`, or `relaunch`.
- Locales and storefronts: the metadata locales the app ships and the storefronts the user cares about. Record the primary language per store.
- Focus: full audit, or one surface (keywords, creatives, ratings, localization).
- Competitor set: up to five named apps per store when comparison is requested; never invent a competitor list without stating how it was chosen.

Output: a scope block with these fields, written to `report.md` and, in complex mode, `flow.json` phase `scope`.

## 2. Measurement Phase

Record which channels exist before scoring:

| Channel | Evidence grade | Typical content |
|---|---|---|
| Official Apple or Google documentation and policy | `official` | Field limits, asset specs, policy text, metric definitions |
| Public store page observed in a browser | `live` | Current title, subtitle or short description, screenshots, rating, review count, category |
| Owner's App Store Connect or Play Console export | `console` | Impressions, product page views, store listing visitors, conversion or click-through rate, sources, experiments, vitals |
| Third-party ASO tool | `tool` | Keyword popularity or volume estimates, difficulty, rank history, competitor keywords |
| AI assistant probe | `synthetic` | Whether a named assistant mentions the app for a prompt set |
| Practitioner guidance or package judgment | `heuristic` | Copy quality, screenshot storytelling, keyword choice |

- A store page can differ by storefront, device, and signed-in state; record the storefront and device for every `live` reading.
- Console metrics change definition over time (see `references/metrics.md`); never compare numbers across a definition change.
- When a channel is missing, record the capability limit and the fallback in `results.json.measurement_methods`, and mark the dependent categories `unknown`.

## 3. Metadata And Keyword Phase

Per store and per locale:

- Read every searchable and visible text field with its current value and its length in the store's own unit (Apple keyword field: bytes; other fields: characters). Read the limits from `references/policy-limits.md`.
- Map which fields the store documents as search inputs (`rules/apple.md` §1, `rules/google-play.md` §1). Fields not documented as search inputs are judged for conversion, never scored as ranking inputs.
- Build or review the keyword set with `references/keyword-research.md`: relevance first, then popularity and difficulty from a named source, then placement.
- Check repetition across fields, wasted characters, brand-only titles that carry no descriptive term, and policy risk words (`rules/apple.md` §5, `rules/google-play.md` §5).
- Check the primary category (and Apple's secondary category) against the app's main function.

## 4. Creative And Conversion Phase

- Assess the icon, screenshots, previews or promo video, and feature graphic with `rules/listing-assets.md`.
- Inventory the conversion tools in use: Apple custom product pages, Product Page Optimization, In-App Events, promoted in-app purchases; Google Play custom store listings, Store Listing Experiments, promotional content, pre-registration. Record which exist, which are live, and whether their results are readable.
- For a running or finished experiment, read only the store's own result state; a variant is a winner only when the store marks it so.

## 5. Ratings, Reviews, And Quality Phase

- Read the visible average rating and rating count per store and storefront; record the date, because both move.
- Check the rating-prompt implementation against the store API limits and policy (`rules/apple.md` §4, `rules/google-play.md` §4): no gating, no incentives, no custom pre-prompt that filters unhappy users.
- Check review responses: coverage of recent critical reviews, tone, and whether replies promise things the app does not do.
- Google Play: read Android vitals when the owner provides them and compare with the bad-behavior thresholds in `references/policy-limits.md`. Apple: read crash and size data from the owner's export when available. Missing data is `unknown`.
- App size: record download and install size when observable; size growth is a conversion risk, not a ranking rule.

## 6. Policy Risk And Web Link Phase

- Policy risk: list every metadata or graphic element that conflicts with the store's metadata policy, with the policy section. This is a discoverability and rejection risk flag, not a compliance verdict.
- Web-to-app links: check the Apple App Site Association file, Android `assetlinks.json`, the Smart App Banner tag, store badge links, and custom page deep links with `references/web-and-ai-surfaces.md`. Record what was fetched and its HTTP status.
- AI assistant surfaces: when requested, run a bounded, dated prompt set (`references/web-and-ai-surfaces.md` §3) and record it as `synthetic`.

## 7. Scoring, Report, And Artifacts

- Score only measured categories with the weights in `SKILL.md` `<scoring>`; record `unknown` and `not-applicable` with `score: null`.
- Prioritize actions by expected impact, confidence, effort, and whether the action needs a new app version (Apple name, subtitle, keywords, screenshots, and icon generally ride a version; promotional text does not; Google Play listing text changes without a release) — see `references/policy-limits.md`.
- Write `results.json`, run `assets/runtime/check-results.jq`, generate `results.js`, copy the dashboard, then write `report.md` and `sources.md` (`references/artifact-spec.md`).
- Proposed copy: one block per store, locale, and field, with the counted length and the limit next to it.

## 8. Setup Mode (Pre-Launch)

Use when the app is not yet live and the output is a setup plan rather than a score. Follow these phases in order and record every item as `done`, `planned` with an owner, `not-applicable`, or `unknown` with the missing access named:

1. **Positioning and keywords**: core use cases, the target locales and storefronts, a seed keyword list with sources, and which terms go in which field.
2. **Metadata drafts**: name, subtitle or short description, keyword field, description, promotional text, What's New, category, each with counted length.
3. **Creatives**: icon, screenshot set per required device class, preview or promo video, feature graphic; the first-impression frames planned for search results.
4. **Localization**: metadata locales per storefront, with the additional-locale indexing plan (`rules/localization.md`).
5. **Ratings plan**: when the in-app rating prompt fires, the review-reply routine, and the owner who answers.
6. **Links and measurement**: AASA and `assetlinks.json`, Smart App Banner, store badge links with campaign parameters, App Analytics and Play Console access, and the baseline metrics to record in week one.
7. **First 30 days**: the first experiment (Product Page Optimization or Store Listing Experiment), the first custom page or listing, the first event or promotional content, and the review of crash and ANR data.

Console submissions, account settings, and live listing edits are prepared with exact values and left to the owner unless the user grants permission to act in the console.

## 9. Optimize Mode

Run when the user asks for the best achievable listing or repeated improvement. It is bounded.

1. **Baseline and budget first**: record the category scores, overall grade, critical-finding count, target, budget (default three iterations), and guards in `results.json.score_history[0]` with `decision: "baseline"`.
2. **Stable evaluator**: keep the same stores, locales, comparable app set, rubric version, and evidence channels. A change records `decision: "reset"`, and no delta is reported across it.
3. **One change per iteration**: one field rewrite, one screenshot-set change, or one experiment plan.
4. **Evidence that counts**: a re-audit of the same surfaces, or a store experiment that the store itself has resolved. An iteration waiting on an unresolved experiment is `pending` in `report.md` and does not enter `score_history` as `kept`.
5. **Guard and discard**: keep an iteration only when a comparable category improves, no category regresses, and policy risk does not increase; otherwise record `discarded`. `best_run` is the highest-scoring kept or baseline iteration.
6. **Stop gates**: target reached, budget spent, plateau, guard failure, an owner-only step (console access, submission, a business decision), or user stop. Record the reason.

Never fake a score and never promise a rank, featuring, or install lift.

## 10. Mode Rules

- **Create**: all phases in order for the scoped stores and locales.
- **Update**: read the existing `report.md` and `results.json` first, re-assess only changed or newly requested surfaces, append a dated changelog entry, and keep prior findings unless superseded.
- **Setup**: §8; add `results.json` and the dashboard only when the user also asks for a scored audit of drafts.
- **Optimize**: start from a create or update audit, then §9.

## Sources

> No external sources; content checked 2026-11-22.

This file states this package's own phases, evidence grades, and reporting order. Store facts it relies on are cited in `references/policy-limits.md` and the store rule files.
