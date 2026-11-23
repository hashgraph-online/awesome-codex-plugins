# ASO Validation

**Purpose**: Quality checks before declaring an ASO run complete.

## Report Completeness

- [ ] The scope block names the app, its store identifiers and URLs, stores, locales, app state, mode, and proof surface
- [ ] Every finding has severity, store, category, evidence, evidence grade, confidence, and a specific recommendation
- [ ] Findings are grouped by the eight scoring categories and prioritized by impact
- [ ] The executive summary gives the score from measured categories or says why no comparable score exists
- [ ] Actions that need a new app version are marked as such

## Coverage Checks

### Simple run

- [ ] The requested surface was read for every store and locale in scope
- [ ] `report.md` and `sources.md` are saved under `.hyper/aso/[slug]/`

### Complex run

- [ ] Every phase in `rules/aso-workflow.md` is complete or recorded as skipped with a reason, and `flow.json` is current
- [ ] Metadata: every text field per store and locale with its counted length in the store's unit
- [ ] Creatives: icon, screenshot sets per required device class, preview or promo video, feature graphic
- [ ] Conversion tools: custom pages or listings, experiments, events or promotional content inventoried
- [ ] Ratings: rating and count per storefront with the date, prompt implementation, reply coverage
- [ ] Quality: vitals, crash, and size data read or marked `unknown`
- [ ] Policy risk and web-to-app links checked
- [ ] `results.json` passes `assets/runtime/check-results.jq`, and `results.js` and `dashboard.html` were regenerated after the last edit

### Setup mode

- [ ] `report.md` follows the seven setup phases in `rules/aso-workflow.md` §8, and every item is `done`, `planned` with an owner, `not-applicable`, or `unknown` with the missing access named
- [ ] Every proposed field fits its limit, with the counted length shown
- [ ] Console steps are prepared with exact values and left to the owner unless permission was given

## Limit And Source Checks

- [ ] Every character, byte, size, count, duration, or threshold stated in the report matches `references/policy-limits.md` or a source re-opened in this run with its checked date
- [ ] Apple keyword-field proposals are counted in UTF-8 bytes, and the byte-versus-character conflict is disclosed when the locale uses multi-byte script
- [ ] `sources.md` records URL, accessed date, applicable claim, evidence class, and limitation for every external claim, with absolute dates not later than the run date
- [ ] Vendor estimates (popularity, volume, difficulty, benchmarks) carry their vendor, scale, and date

## Evidence Discipline

- [ ] `official`, `live`, `console`, `tool`, `synthetic`, and `heuristic` evidence is labelled and never mixed without labels
- [ ] No rank, search volume, conversion rate, rating, or download count is stated without a recorded measurement
- [ ] No vendor claim is presented as an Apple or Google rule (description indexing on iOS, caption OCR, keyword density)
- [ ] Console metrics are compared only within one definition (Play's 2026 switch to click-through rate) and one window
- [ ] An experiment result is reported only in the state the store itself reports
- [ ] No recommendation uses stuffing, competitor or unrelated brand names, rank or price claims, or incentivized or gated ratings
- [ ] Missing console, tool, or live access is disclosed as a confidence limit

## Optimize Mode Checks

- [ ] `score_history[0]` is the baseline, recorded before any change
- [ ] Every iteration records score, decision (`kept`, `discarded`, `reset`), evaluator version, change, and evidence
- [ ] Iterations waiting on an unresolved store experiment are reported as pending and are not `kept`
- [ ] `best_run` points to the highest-scoring kept or baseline iteration
- [ ] Each iteration changed one field, one asset set, or one experiment plan
- [ ] The stop reason is one of target, budget, plateau, guard failure, owner-only step, or user stop
- [ ] Completion records `ship`, `iterate`, `caveated ship`, or `block` with residual risk

## Severity Guide

| Severity | Criteria | Example |
|---|---|---|
| **critical** | A policy violation, a required asset set missing, a field over its limit, or a verified block on discoverability | A rank claim in the Play title; a keyword field over 100 bytes |
| **warning** | Material loss of search coverage or conversion, supported by observed or console evidence | Words repeated across name, subtitle, and keyword field; no localized screenshots in the main locale |
| **info** | Optional improvement, low-confidence heuristic, or experiment idea | Test a benefit-led first screenshot |

## Sources

> No external sources; content checked 2026-11-22.

This file states this package's own completion gate over the artifacts it produces. Store facts it checks against are cited in `references/policy-limits.md`.
