---
name: hyper-seo
description: "[Hyper] Use this skill when the user asks for an SEO, AEO, GEO, or LLMO audit, an optimization report, a new-site launch setup plan, or a score-improvement loop for a named target. Covers on-page, technical, content, Core Web Vitals, answer-engine, generative-engine, AI search visibility, AI crawler policy, metadata, and citation readiness, saved under `.hyper/seo/[slug]/`. Do not use it for page or product design, release gating, pure performance work with no search context, or market research with no target site."
compatibility: Works best with live web access, browser inspection, local source search, Lighthouse or Core Web Vitals data when available, and read/write access for report artifacts.
---

@rules/seo-workflow.md
@rules/validation.md

# Hyper SEO

> Audit and improve a project's search visibility across traditional search engines and AI answer engines.

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce an evidence-graded SEO/AEO/GEO/LLMO audit and a prioritized, actionable optimization report for a named target, produce a phased setup plan when a site or homepage is being planned or launched, and drive a bounded score-improvement loop when the user asks for the best achievable score. |
| Scope | Owns target classification, measurement-method selection, on-page/technical/content/Core Web Vitals/AEO/GEO/LLMO assessment, new-site setup planning, scoring, findings, recommendations, and the report workspace. Does not own implementation outside the audited target, release gating, page or product design, account actions that need the owner's credentials unless permitted, or broad market research that has no target site or content set. |
| Authority | System/harness and user instructions > the audited target's own files and live observations > official platform documentation > this skill > heuristic preference. A tool, lab, synthetic, or heuristic observation is never promoted to an official requirement. |
| Evidence | Read the target's own files, rendered pages, and live responses before scoring, and cite the command, URL, file path, or probe result behind every critical and warning finding. Record unavailable checks as `unknown` and irrelevant checks as `not-applicable`; never invent a score, a ranking, an inclusion, or a citation. |
| Tools | Use available read/search/browser tools, and render the dashboard with `bash scripts/render-dashboard.sh <artifact-dir>`. Web search, browser inspection, field Core Web Vitals, Search Console, or an AI citation probe are used only when actually available; when one is missing, state the capability limit and fall back to the strongest lower-grade method. |
| Loop | Optimize mode only: a bounded `audit -> fix or recommendation -> re-audit` cycle, default budget three iterations. Feedback = comparable re-audit evidence; metric = the 100-point score with `unknown` and `not-applicable` categories excluded; guard = no comparable-category regression and no evidence-grade promotion; stop = target reached, budget spent, plateau, guard failure, or work that needs external credentials or a business decision. |
| Output | `.hyper/seo/[slug]/` holding `results.json`, `results.js`, `dashboard.html`, `report.md`, `sources.md`, and `flow.json` for complex or optimize mode; simple and setup modes keep `report.md` and `sources.md` as the minimum. `sources.md` is a source ledger of URL, date, applicable claim, evidence class, and limitation. |
| Verification | Apply `rules/validation.md` at completion: every critical or warning finding carries evidence, scores derive from observed evidence with `unknown` and `not-applicable` handled explicitly, and optimize mode records baseline, evaluator, budget, guards, discarded iterations, stop reason, and the best comparable verified result. Package changes additionally run the focused corpus validator, the repository standard gate, and the package tests. |
| Stop condition | Stop when the requested audit or report is complete with graded evidence and no unresolved critical gap, or when optimize mode reaches its target, budget, plateau, guard, or an external dependency. Never stop by asserting a ranking, AI-feature inclusion, or citation the evidence does not support. |

</instruction_contract>

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, schema keys, JSON/YAML field names, API names, package names, proper nouns, and quoted source excerpts in their required or original language. Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens; when a localized template or reference exists (for example `*.ko.md` or `*.ko.json`), prefer it for user-facing artifacts.

</output_language>

<purpose>

- Audit website or project SEO in a systematic way.
- Cover on-page SEO, technical SEO, content SEO, and Core Web Vitals.
- Evaluate AEO readiness for featured snippets, voice search, and direct-answer surfaces.
- Evaluate GEO readiness for citation likelihood in generative AI responses.
- Evaluate LLMO readiness for AI crawler access, freshness, and model-readable context.
- Save prioritized recommendations and evidence under `.hyper/seo/[slug]/`.
- Plan a new site or homepage launch in phases (plan, build checks, registration, first 30 days) so search engines and AI answer engines can crawl, index, and cite it.
- Update existing reports so SEO improvement history remains traceable, and when the user asks for highest score, max score, maximum score, perfect score, or continuous improvement, run an audit to fix/recommendation to re-audit loop and keep the best result.

</purpose>

<routing_rule>

Use `hyper-seo` when the main outcome is an SEO/AEO/GEO/LLMO audit, optimization report, or evidence-backed search visibility improvement plan.

Route neighboring work elsewhere:

- Page or product UI design: a design deliverable, not a search-visibility audit.
- Competitor or market research without site audit: route to the source-backed research workflow.
- Release-gate checks whose only output is a go/no-go deployment verdict rather than a search-visibility audit: not this skill's output.
- Pure performance engineering without search context: use the relevant performance or optimization workflow.
- Broad AI search trend research without a target site or content set: route to the source-backed research workflow.

</routing_rule>

<activation_examples>

Positive examples:

- "Audit this site's SEO."
- "Check metadata and structured data."
- "Review search-engine optimization status and give improvement recommendations."
- "Optimize our content so AI search engines can cite it."
- "Check whether ChatGPT or Perplexity can surface our brand."
- "Keep iterating fixes until the SEO score is as high as possible."
- "Audit, fix, and re-verify until the search optimization score is close to perfect."
- "We are launching a new homepage next month; set up SEO, GEO, and AI crawler settings before launch."

Negative examples:

- "Design this landing page." -> a page or product design deliverable, not this skill's output.
- "Research competitor market positioning." -> route to the source-backed research workflow.
- "Check the release checklist before deploying." -> a deployment gate verdict, not a search-visibility audit.

Boundary examples:

- "Optimize this page's performance."
  Use `hyper-seo` only when performance is evaluated through SEO/Core Web Vitals impact.
- "Research AI search trends."
  Use `hyper-seo` only when the output is tied to a target site, page, or content inventory.
- "Build our new homepage."
  Use `hyper-seo` only for the search-visibility setup plan or checks; building the pages is not this skill's output.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|------|------|
| Full SEO audit for a new project or site | create |
| On-page SEO review for a specific page | create |
| Add a new analysis to an existing SEO report | update |
| Focused Core Web Vitals or technical SEO analysis | create |
| Re-check after SEO improvements | update |
| Iterative improvement toward best or perfect score | optimize |
| AEO/GEO citation readiness analysis | create |
| Add AEO/GEO analysis to an existing report | update |
| Plan or launch a new site or homepage for search and AI answer engines | setup |

A request with no target site, page, or content set is not this trigger.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): modes, intake, scoring, artifact contract, phase order, and the stop condition.
- Rules: [rules/seo-workflow.md](rules/seo-workflow.md) owns the phases and the optimize loop; [rules/validation.md](rules/validation.md) owns the completion gates.
- References: [references/seo-fundamentals.md](references/seo-fundamentals.md) (E-E-A-T, Core Web Vitals, schema), [references/aeo-geo-guide.md](references/aeo-geo-guide.md) (AEO, GEO, LLMO), [references/seo-checklist.md](references/seo-checklist.md) (scan items), [references/site-setup.md](references/site-setup.md) (setup mode), [references/artifact-spec.md](references/artifact-spec.md) (workspace and `results.json` schema).
- Assets: the Korean and English report templates, the dashboard template, and `assets/evals/`, the trigger and behavior cases.
- Script: `bash scripts/render-dashboard.sh <artifact-dir>` needs Bash 3.2+ and jq; it copies the dashboard template, embeds `results.json` into `results.js`, writes `dashboard.html`, and exits non-zero naming the offending `results.json` field when the payload is structurally invalid.

</skill_architecture>

<loop_policy>

- Only optimize mode loops; every other mode is one pass with a completion gate.
- Record the baseline, evaluator, budget, and guards before the first change, and the stop reason when the loop ends.
- Keep an iteration only when a comparable category improves without a regression and without promoting an evidence grade; otherwise revert it where possible or mark it `discarded`.
- The loop procedure is [rules/seo-workflow.md](rules/seo-workflow.md) phase 9; the fields to record are in [rules/validation.md](rules/validation.md) §Optimize Mode Checks.

</loop_policy>

<language_and_translation_default>

- Canonical package files are English and every `*.ko.md` is a structurally aligned Korean translation; deliverables follow `<output_language>`, with `assets/report.template.ko.md` as the default report template.

</language_and_translation_default>

<reference_routing>

- Read [rules/seo-workflow.md](rules/seo-workflow.md) at the start of any audit; it owns the phase procedures.
- Read [references/seo-fundamentals.md](references/seo-fundamentals.md) when judging E-E-A-T, Core Web Vitals, ranking factors, entity signals, or schema markup.
- Read [references/aeo-geo-guide.md](references/aeo-geo-guide.md) for the AEO, GEO, or LLMO dimensions, including the GEO CORE framework and `llms.txt` guidance.
- Read [references/seo-checklist.md](references/seo-checklist.md) while scanning, for the item-by-item checks.
- Read [references/site-setup.md](references/site-setup.md) only in setup mode.
- Read [references/artifact-spec.md](references/artifact-spec.md) before writing or reviewing `.hyper/seo/[slug]/`, including `flow.json`.
- Read `assets/report.template.ko.md` when drafting a report, and `assets/report.template.md` only when English is required.
- Read `assets/dashboard-template.html` only when rendering the dashboard.
- Read [rules/validation.md](rules/validation.md) before declaring the audit complete.

</reference_routing>

<support_file_read_order>

1. This core, to fix the mode, the complexity, and the target.
2. `rules/seo-workflow.md`, then `references/seo-fundamentals.md`, `references/aeo-geo-guide.md`, and `references/seo-checklist.md`.
3. `references/site-setup.md` in setup mode, then `references/artifact-spec.md` before writing the workspace.
4. `assets/report.template.ko.md` for the report, and [assets/dashboard-template.html](assets/dashboard-template.html) only when rendering.
5. `rules/validation.md` before completion.

</support_file_read_order>

<workflow>

| Phase | Task | Output |
|------|------|------|
| 0 | Determine target, mode, complexity, proof surface, and universal intake fields | Execution brief |
| 1 | Establish measurement methods and confidence limits | `measurement_methods` |
| 2 | Collect evidence from local code, pages, browser checks, and web sources | Evidence log |
| 3 | Audit technical SEO, platform policy, AEO, GEO, LLMO, Core Web Vitals, and structured data | Structured findings |
| 4 | Separate official requirements from field/tool/lab/synthetic/heuristic findings | Evidence-graded findings |
| 5 | Prioritize issues by impact, confidence, effort, and source tier | Recommendation set |
| 6 | Write artifacts and dashboard | `.hyper/seo/[slug]/` |
| 7 | If optimize mode, apply or recommend fixes and re-audit | Best verified result |
| 8 | Summarize score, wins, confidence limits, risks, and next actions | Final report |

</workflow>

<complexity_routing>

| Complexity | Signals | Handling |
|------|------|------|
| **Simple** | Single-page review, one SEO element, quick metadata audit | **Direct**: write `report.md` immediately |
| **Complex** | Full-site audit, many pages, technical SEO plus content SEO plus Core Web Vitals, competitor comparison | **Tracked**: use `flow.json` for phase tracking |

Before starting, record `Complexity: [simple/complex] — [one-line reason]`, `Mode: [create/update/optimize/setup]`, `Target: [site/page/project path]`, and `Proof surface: [commands, browser checks, web sources, or local files]`.

</complexity_routing>

<universal_intake>

Before scoring any project, classify the audit context so this skill works across stacks:

- `target_type`: `live-url`, `local-static`, `nextjs`, `react-spa`, `docs-site`, `ecommerce`, `blog`, or `app-with-marketing-pages`
- `access_level`: live URL, local files only, Search Console available, analytics available, field Core Web Vitals available, or AI citation probe available
- `allowed_action`: `audit-only`, `recommend`, `edit-code`, or `optimize-loop`
- `measurement_confidence`: lower confidence when live URL, Search Console, field Core Web Vitals, or AI citation probes are unavailable
- `evaluator`: comparable target set, scoring rubric, tools/versions, dates, and evidence channels

Classify every finding and score input as exactly one of `official`, `live`, `field`, `tool`, `lab`, `synthetic`, or `heuristic`. Do not treat one class as evidence from another: a local scan is not live or field evidence, and a tool/lab result is not an official requirement.

Record unavailable checks as `unknown` and irrelevant checks as `not-applicable`; exclude `not-applicable` checks from category denominators. Do not hide missing evidence. If a recommendation is based on static files, lab data, synthetic probes, or heuristics, label it that way in `results.json`.

When live browsing, Search Console, field data, AI probes, or a named tool is unavailable, use the strongest available lower-grade method, state the capability limitation and fallback, and do not make live-performance, ranking, inclusion, or citation claims.

</universal_intake>

<artifact_contract>

Create or update `.hyper/seo/[slug]/`.

Expected files:

```text
.hyper/seo/[slug]/
├── dashboard.html      # Browser-readable dashboard
├── results.json        # Structured audit results
├── results.js          # File URL fallback for browser rendering
├── report.md           # Markdown report
├── sources.md          # Source and evidence log
└── flow.json           # Required for complex or optimize mode
```

For simple mode, `report.md` and `sources.md` are the minimum. For complex or optimize mode, all files are expected.

Follow [references/artifact-spec.md](references/artifact-spec.md) for the file schema.

For new reports, use [assets/report.template.ko.md](assets/report.template.ko.md) by default. Use [assets/report.template.md](assets/report.template.md) only when English is explicitly required.

Write `results.json` from gathered evidence first, generate `results.js` for direct local viewing, render `dashboard.html` with `bash scripts/render-dashboard.sh <artifact-dir>`, then write `report.md` and `sources.md`. `sources.md` is a source ledger: for every external or official claim, record its URL, accessed or published date, applicable claim, evidence class, and any scope/availability limitation.

For complex or optimize mode, `flow.json` tracks phases in order: `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report`.

</artifact_contract>

<audit_dimensions>

Audit these dimensions when relevant to the target: technical SEO (crawlability, indexability, canonicalization, sitemap, robots directives, response status, redirects, duplicate pages); platform policy (Googlebot, Google-Extended, OAI-SearchBot, GPTBot, ChatGPT-User, Claude-SearchBot, ClaudeBot, PerplexityBot, and the other search, training, and user-fetch tokens as separate controls, CDN or WAF bot rules, the Search Console generative AI setting, snippet controls and X-Robots-Tag, plus the target-gated Naver and Bing/IndexNow modules); on-page SEO (title, description, heading hierarchy, keyword alignment, URL readability, internal links); content SEO (intent match, depth, topical coverage, freshness, uniqueness, readability); Core Web Vitals (LCP, INP, CLS, render-blocking resources, image sizing, interaction delay); structured data (JSON-LD validity, Schema.org type fit, parity with visible content, AI trust signals); AEO (Q&A structure, direct answers, snippet readiness, voice-search phrasing); GEO/LLMO (citable claims, sourced statistics, entity authority, `llms.txt`, AI crawler access, freshness).

Per-dimension criteria and the conditional platform modules live in [rules/seo-workflow.md](rules/seo-workflow.md) phases 3-8, [references/seo-checklist.md](references/seo-checklist.md), [references/seo-fundamentals.md](references/seo-fundamentals.md), and [references/aeo-geo-guide.md](references/aeo-geo-guide.md).

Two surfaces are audited only when the target set includes them: Naver (`Yeti` crawler access, Search Advisor ownership verification, RSS and sitemap ownership-domain match, `og:image` conditions, `nosourceinfo` scope) and Bing (IndexNow change notification, a receipt code that is never index or citation evidence, key-file ownership proof, the per-POST submission limit, sitemap field handling).

Treat character counts, heading counts, link density, answer length, word counts, and platform content preferences as context-dependent heuristics. Evaluate Google AI features through ordinary SEO fundamentals without prescribing special AI schema or text files.

</audit_dimensions>

<scoring>

Use a transparent 100-point score when enough evidence exists:

- Technical SEO: 20
- On-page SEO: 20
- Content SEO: 15
- Core Web Vitals: 15
- Structured data: 10
- AEO readiness: 10
- GEO/LLMO readiness: 10

If evidence is incomplete, mark affected categories as `unknown`; mark irrelevant categories as `not-applicable` and exclude them from the score denominator.

Each finding carries severity (`critical`, `warning`, `info`), confidence, `evidence_grade` (`official`, `live`, `field`, `tool`, `lab`, `synthetic`, `heuristic`), `measurement_method`, `source_tier`, the evidence itself, a specific recommendation with its expected impact, and the owner surface (code, content, infrastructure, analytics, external platform). [references/artifact-spec.md](references/artifact-spec.md) holds the allowed values and the schema.

</scoring>

<required>

| Category | Required |
|---|---|
| Target | A named target, and the mode, complexity, and proof surface recorded before scoring |
| Evidence | Every critical and warning finding carries a command, URL, file path, or probe result, plus its evidence grade and source tier |
| Scoring | A total computed only from observed categories, with `unknown` and `not-applicable` excluded rather than assumed |
| Output | The artifact set `<artifact_contract>` requires for the chosen mode |
| Limits | A missing channel named as a capability limit with its fallback, never papered over |

</required>

<forbidden>

| Category | Forbidden |
|---|---|
| Evidence | A score, ranking, inclusion, or citation asserted without a recorded measurement; an `unknown` filled in to make a total |
| Grading | A heuristic presented as an official pass/fail requirement; a tool, lab, or synthetic result promoted to an official requirement |
| Guarantees | Implying that structured data, `llms.txt`, or index and snippet eligibility guarantees rich results, ranking, AI inclusion, or a citation; promising a perfect score |
| Scope | Editing outside the audited target, or taking an account action that needs the owner's credentials without permission |
| Claims | A live-performance, ranking, or citation claim made while the channel that would prove it was unavailable |

</forbidden>

<validation>

Apply [rules/validation.md](rules/validation.md) before declaring an audit complete. It requires evidence on every critical and warning finding; recommendations specific enough for an engineer, marketer, or content owner to act on; scores derived from observed evidence with `unknown` and `not-applicable` handled explicitly rather than assumed; Google AI features described through ordinary SEO fundamentals, with FAQPage recommendations that separate Google rich-result eligibility from answer-friendly visible FAQ content; a `sources.md` source ledger carrying URL, date, applicable claim, evidence class, and limitations; and, in optimize mode, the recorded baseline, evaluator, finite budget, guards, changes and recommendations, re-audit evidence, discarded iterations, and stop reason.

The artifacts that must remain are listed in `<artifact_contract>`.

</validation>

## Sources

> Checked 2026-11-09. The mode set, the 100-point weights, and the optimize guards are this package's design (user instruction, 2026-08-20) and are restated in [rules/seo-workflow.md](rules/seo-workflow.md); every external fact the audit applies carries its own date in the reference that states it, and the package shape follows `instructions/skill/SKILL_AUTHORING.md`.
