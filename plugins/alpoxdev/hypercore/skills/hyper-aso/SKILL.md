---
name: "hyper-aso"
description: "Use this skill when the user asks for an App Store or Google Play ASO audit, a store-listing setup plan for a new app, or a bounded keyword and conversion optimization loop for a named app. Covers metadata and keywords, screenshots, previews and icons, localization, ratings and reviews, custom pages and listing experiments, quality signals, metadata policy risk, and web-to-app links, saved under `.hyper/aso/[slug]/`. Do not use it for website search visibility, store review or compliance verdicts, paid campaign management, or market research with no named app."
compatibility: "Works best with browser/fetch access to public store pages and official Apple/Google docs, optional read access to App Store Connect or Play Console exports, and read/write access for `.hyper/aso/[slug]/` artifacts. Validating `results.json` needs jq 1.6+."
---

Open the rules below as needed. Resolve bundled paths from this skill directory and project paths from the target workspace.

- [rules/aso-workflow.md](rules/aso-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper ASO

> Audit and improve how a named app is found and chosen inside the Apple App Store and Google Play.

- **Purpose**: Produce evidence-graded App Store / Google Play ASO audits, pre-launch store-listing setup plans, or bounded keyword and conversion optimization loops for a named app.
- **Do not use when**: Auditing website SEO/GEO, issuing app-review compliance verdicts, managing paid ad bids, designing app UI, or researching markets with no named app.
- **Input**: Named app (bundle ID, package name, or store URLs), target stores/locales, optional console exports, and mode (`create`, `update`, `setup`, `optimize`).
- **Output**: `.hyper/aso/[slug]/` workspace (`report.md`, `sources.md`, plus `results.json` gated by `check-results.jq`, `results.js`, `dashboard.html`, and `flow.json` for complex/optimize).

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Deliver an evidence-graded ASO audit with prioritized listing actions, a phased pre-launch listing plan, or a bounded optimize loop for a named app. |
| Scope | Store/state/locale intake, measurement selection, metadata/keyword/creative/localization/rating/conversion-tool/quality/policy-risk/web-link assessment, scoring, copy proposals, and `.hyper/aso/[slug]/`. Never edit/submit live console listings, issue compliance verdicts, or manage paid ad campaigns. |
| Authority | System/user instructions > owner console exports and live store pages > official Apple/Google policy and docs > this skill > vendor/practitioner estimates. Never promote third-party tool estimates to official rules. |
| Evidence | Cite store URL, console export, or dated official doc on every `critical`/`warning` finding; mark missing checks `unknown` and irrelevant ones `not-applicable`; never invent ranks, search volume, conversion rates, or downloads. |
| Tools | Public store/doc fetch or browser read, local file read for exports/screenshots, and `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` payload validation. |
| Loop | `optimize` mode only: bounded `audit -> listing change or experiment plan -> re-audit` (default 3 iterations), keeping changes only when comparable categories improve without regression or policy-risk increase (`pending` while store experiments run). |
| Output | `.hyper/aso/[slug]/` with `report.md` and `sources.md` minimum, plus `results.json`, `results.js`, `dashboard.html`, and `flow.json` in complex/optimize modes. |
| Verification | [rules/validation.md](rules/validation.md) plus `check-results.jq` returning `ok` on `results.json`. |
| Stop condition | Audit/plan complete with graded evidence and zero unresolved critical gaps, or `optimize` reaches target, budget, plateau, guard, or an owner-console step. |

</instruction_contract>

<output_language>

Default all user-facing deliverables, reports, setup plans, summaries, and validation notes to Korean while preserving identifiers, CLI commands, file paths, JSON keys, store field names (`Subtitle`, `Promotional Text`, `Short description`), and target-locale listing copy (`instructions/harness-engineering/references/skill-common-rules.md`).

</output_language>

<purpose>

- Audit search discoverability and listing conversion on the Apple App Store, Google Play, or both (plus ONE store when named), separating dated official limits from console data, live pages, tool estimates, and heuristics.
- Deliver pre-launch listing setup plans or bounded optimization loops saved under `.hyper/aso/[slug]/`.

</purpose>

<routing_rule>

Use this skill when the deliverable is store discoverability or conversion for a named app: an ASO audit, store-listing setup plan, locale/keyword/creative recommendations, or an ASO optimize loop.

Do not use when:
- auditing website SEO/AEO/GEO (Universal Links / App Links / Smart App Banner belong here only inside an app-store audit)
- issuing App Store / Play compliance or rejection verdicts, managing paid Apple Ads / Google App bids, designing in-app UI, or running targetless market research

</routing_rule>

<activation_examples>

Positive:
- "Audit our iOS app's App Store listing and tell me what to fix first."
- "플레이스토어 등록정보 ASO 점검해 줘. 키워드랑 스크린샷 위주로."
- "We launch on both stores next month; give me the store listing setup plan for ko-KR and en-US."
- "앱스토어 키워드 필드 100자 어떻게 채울지 한국어로 제안해 줘."

Negative / Boundary:
- "Audit our website's SEO." -> web search-visibility deliverable.
- "Why was our app rejected under guideline 4.3?" -> compliance verdict.
- "Raise our Apple Ads bids on these keywords." -> paid campaign management.
- "Research the top fitness apps' ASO." -> use `hyper-aso` only when tied to the user's named app.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|---|---|
| Full or surface-focused ASO audit of a live app | `create` |
| Re-check after listing edits/experiments or adding a store/locale | `update` |
| Store-listing setup plan for a pre-launch app | `setup` |
| Iterative improvement toward best achievable store listing | `optimize` |

Ask once for the app identity (name, bundle ID/package name, or store URL) if omitted.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): modes, intake, 100-point weights, artifact contract, and harness workflow.
- Rules: [rules/aso-workflow.md](rules/aso-workflow.md), [rules/validation.md](rules/validation.md), [rules/apple.md](rules/apple.md), [rules/google-play.md](rules/google-play.md), [rules/listing-assets.md](rules/listing-assets.md), [rules/localization.md](rules/localization.md).
- References: [references/policy-limits.md](references/policy-limits.md), [references/keyword-research.md](references/keyword-research.md), [references/metrics.md](references/metrics.md), [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md), [references/artifact-spec.md](references/artifact-spec.md), [references/sources.md](references/sources.md).
- Assets: [assets/report.template.ko.md](assets/report.template.ko.md), `assets/report.template.md`, `assets/dashboard-template.html`, `assets/runtime/check-results.jq`, and `assets/evals/`.

</skill_architecture>

<loop_policy>

Only `optimize` mode loops (default cap: 3 iterations). Record baseline, evaluator, budget, and guards first; store experiments (`Product Page Optimization`, `Store Listing Experiments`) count only after finishing on store statistics (`pending` until then, never `kept`). Keep only non-regressing, policy-safe improvements ([rules/aso-workflow.md](rules/aso-workflow.md)).

</loop_policy>

<language_and_translation_default>

Canonical package files are English with aligned `*.ko.md` siblings; user reports default to Korean via [assets/report.template.ko.md](assets/report.template.ko.md), while proposed listing copy is written in each target locale's language.

</language_and_translation_default>

<reference_routing>

- Read [rules/aso-workflow.md](rules/aso-workflow.md) at start, [rules/apple.md](rules/apple.md) for App Store, [rules/google-play.md](rules/google-play.md) for Google Play, [rules/listing-assets.md](rules/listing-assets.md) for creatives, and [rules/localization.md](rules/localization.md) for multi-locale/Korean/ONE store.
- Read [references/policy-limits.md](references/policy-limits.md) before stating any field/asset limit, [references/keyword-research.md](references/keyword-research.md) before keyword proposals, [references/metrics.md](references/metrics.md) before console metrics, and [references/web-and-ai-surfaces.md](references/web-and-ai-surfaces.md) when web-to-app links or AI surfaces apply.
- Read [references/artifact-spec.md](references/artifact-spec.md) and [assets/report.template.ko.md](assets/report.template.ko.md) before writing `.hyper/aso/[slug]/`, [references/sources.md](references/sources.md) for claim lineage, and [rules/validation.md](rules/validation.md) before closing.

</reference_routing>

<support_file_read_order>

1. This `SKILL.md`, `rules/aso-workflow.md`, and store rules (`rules/apple.md`, `rules/google-play.md`).
2. `references/policy-limits.md`, `references/keyword-research.md`, `references/metrics.md`, plus `rules/listing-assets.md`, `rules/localization.md`, and `references/web-and-ai-surfaces.md` as needed.
3. `references/artifact-spec.md`, `assets/report.template.ko.md`, `assets/runtime/check-results.jq`, and `rules/validation.md`.

</support_file_read_order>

<workflow>

Resume procedure: Before Step 0, inspect `.hyper/aso/[slug]/` (`flow.json`, `results.json`, `report.md`, `sources.md`). If an interrupted run or prior `update`/`optimize` baseline exists on disk, load `flow.json` and `results.json` first and resume from the first unfinished phase without erasing baseline or `pending` experiment records.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 0 | Fix app identity (or ask once), stores, `app_state`, locales, mode, complexity, and `<universal_intake>`; init `flow.json` if complex/optimize | Execution brief recorded | Prevents auditing the wrong storefront, locale, or app state |
| 1 | Establish measurement channels and confidence limits ([references/metrics.md](references/metrics.md)) | `measurement_methods` recorded | Keeps third-party `tool` numbers separate from `console` truth |
| 2 | Collect live store pages, exported metadata, console exports, and dated limits ([references/policy-limits.md](references/policy-limits.md)) | Evidence log and `sources.md` started | Guessing character/byte limits produces rejected listing copy |
| 3 | Assess metadata/keywords, creatives/conversion tools, ratings/quality signals, policy risk, and web-to-app links per store/locale | Graded findings (`official`/`live`/`console`/`tool`/`synthetic`/`heuristic`) logged | Single-surface checks miss policy risks and conversion bottlenecks |
| 4 | Compute observed 100-point score, verify proposed copy lengths in each store's unit (chars vs bytes), write `results.json`, and run `check-results.jq` | `check-results.jq` prints `ok` and workspace files exist | Catches schema errors and field-length overflows before delivery |
| 5 | In `optimize` mode, run `<= 3` non-regressing passes (marking unfinished experiments `pending`); write final `report.md` + `sources.md` | [rules/validation.md](rules/validation.md) passes on `.hyper/aso/[slug]/` | Blocks unverified rank/install promises and policy-unsafe edits |

Step Yes/No checklist:

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Did I check `.hyper/aso/[slug]/` first and record app identity, stores, locales, mode, complexity, and `<universal_intake>` before scoring? (Yes/No) | Step 0 |
| 2 | Does every character/byte/asset limit cite [references/policy-limits.md](references/policy-limits.md) or a dated official doc, and does every proposed string fit its store unit? (Yes/No) | Step 2 |
| 3 | Does every `critical`/`warning` finding cite concrete evidence with an exact `evidence_grade` (never promoting `tool` or practitioner folklore to `official`)? (Yes/No) | Step 3 |
| 4 | Were `unknown` and `not-applicable` excluded from the score denominator, and did `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` print `ok`? (Yes/No) | Step 4 |
| 5 | Are `report.md` and `sources.md` saved with zero promised ranks/approvals/install lifts and zero live console mutations? (Yes/No) | Step 5 |

</workflow>

<complexity_routing>

| Complexity | Signals | Handling |
|---|---|---|
| **Simple** | One store, one locale, one surface (keywords only or screenshots only) | **Direct**: write `report.md` and `sources.md` |
| **Complex** | Both stores, multi-locale, full audit, competitor comparison, or `optimize` | **Tracked**: maintain `flow.json` across phases |

Record `Complexity`, `Mode`, `App`, `Stores`, `Locales`, and `Proof surface` before scoring.

</complexity_routing>

<universal_intake>

Classify before scoring: `stores` (`app_store`, `google_play`, both, plus `one_store` only when named), `app_state` (`pre-launch`, `live`, `relaunch`), `locales`, `access_level` (public page, exports, App Store Connect, Play Console, third-party ASO tool, none), `allowed_action` (`audit-only`, `recommend`, `draft-copy`, `optimize-loop`), and `evaluator`. Grade every input as `official`, `live`, `console`, `tool`, `synthetic`, or `heuristic`.

</universal_intake>

<artifact_contract>

```text
.hyper/aso/[slug]/
├── dashboard.html      # Browser-readable dashboard
├── results.json        # Structured audit results (validated by check-results.jq)
├── results.js          # file:// fallback generated from results.json
├── report.md           # Korean Markdown report or setup plan
├── sources.md          # Source and evidence ledger
└── flow.json           # Phase tracker for complex/optimize modes
```

Validate `results.json` with `jq -r -f <skill-dir>/assets/runtime/check-results.jq <artifact-dir>/results.json` (`ok` required) before generating `results.js`, `dashboard.html`, `report.md` ([assets/report.template.ko.md](assets/report.template.ko.md)), and `sources.md`.

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

Exclude `unknown` and `not-applicable` categories from the denominator; schema details live in [references/artifact-spec.md](references/artifact-spec.md).

</scoring>

<required>

| Category | Required |
|---|---|
| Target & Limits | Named app + store IDs, intake fields, and dated official sources ([references/policy-limits.md](references/policy-limits.md)) for every limit |
| Evidence & Scoring | Concrete URL/export/observation + `evidence_grade` on every `critical`/`warning` finding; denominator restricted to observed categories |
| Copy & Gate | Proposed copy measured in each store's own unit (characters vs bytes) and `results.json` passing `check-results.jq` |

</required>

<forbidden>

- Inventing ranks/volumes/conversion rates, promoting vendor folklore to `official` rules, promising rank/featuring/approval outcomes, recommending keyword stuffing or competitor brand names or incentivized ratings, or editing live console listings without permission.
- Bad: Presenting "iOS description text is keyword-indexed" or OCR folklore as an `official` Apple rule -> Good: Grading practitioner hypotheses as `heuristic` and relying on dated official Apple/Google docs in `references/policy-limits.md`.
- Bad: Drafting an iOS `Keyword` field over 100 characters/bytes or stuffing competitor app names -> Good: Counting exact store units per field and keeping metadata free of competitor brands, rank claims, and policy violations.
- Bad: Marking an unrun store listing experiment as `kept` in `optimize` mode -> Good: Recording unfinished PPO / Store Listing Experiments as `pending` until store console statistics finish.

</forbidden>

<validation>

- [ ] `.hyper/aso/[slug]/` state was checked on start/resume, and app identity, stores, locales, mode, and intake were recorded first.
- [ ] Every `critical` and `warning` finding carries concrete evidence and an accurate `evidence_grade`.
- [ ] Every field/asset limit cites a dated official source, and proposed listing copy fits each store's exact unit limit.
- [ ] Scores derive solely from observed categories (`25/20/15/10/10/10/5/5`), excluding `unknown` and `not-applicable`.
- [ ] `check-results.jq` printed `ok` when `results.json` was produced, and `sources.md` + `report.md` exist on disk.
- [ ] In `optimize` mode, baseline, evaluator, budget, guards, `pending`/`discarded` iterations, and stop reason are recorded.

</validation>

## Sources

> Checked 2026-11-22. Modes, 100-point weights, and optimize guards follow user instruction (2026-11-22); external store limits and claims carry dated sources in [references/policy-limits.md](references/policy-limits.md) and [references/sources.md](references/sources.md) per `instructions/skill/SKILL_AUTHORING.md`.
