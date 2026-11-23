---
name: "hyper-seo"
description: "[Hyper] Use this skill when the user asks for an SEO, AEO, GEO, or LLMO audit, an optimization report, a new-site launch setup plan, or a score-improvement loop for a named target. Covers on-page, technical, content, Core Web Vitals, answer-engine, generative-engine, AI search visibility, AI crawler policy, metadata, and citation readiness, saved under `.hyper/seo/[slug]/`. Do not use it for page or product design, release gating, pure performance work with no search context, or market research with no target site."
compatibility: "Works best with live web access, browser inspection, local source search, Lighthouse or Core Web Vitals data when available, and read/write access for `.hyper/seo/[slug]/` artifacts plus Bash 3.2+ and jq."
---

Open the rules below as needed. Resolve bundled paths from this skill directory and project paths from the target workspace.

- [rules/seo-workflow.md](rules/seo-workflow.md)
- [rules/validation.md](rules/validation.md)

# Hyper SEO

> Audit and improve a project's search visibility across traditional search engines and AI answer engines.

- **Purpose**: Deliver evidence-graded SEO/AEO/GEO/LLMO audits, launch setup plans, or bounded score-optimization loops for a named site or project.
- **Do not use when**: Designing UI/pages, running deployment go/no-go release gates, tuning pure non-search performance, or researching markets with no target site.
- **Input**: Named target URL/page/repo path, optional mode (`create`, `update`, `optimize`, `setup`), and available access channels.
- **Output**: `.hyper/seo/[slug]/` workspace (`report.md`, `sources.md`, plus `results.json`, `results.js`, `dashboard.html`, and `flow.json` in complex/optimize runs).

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Produce an evidence-graded SEO/AEO/GEO/LLMO audit and prioritized action plan, a phased launch setup plan, or a bounded score-improvement loop for a named target. |
| Scope | Target classification, measurement selection, technical/platform-policy/on-page/content/CWV/schema/AEO/GEO/LLMO assessment, scoring, recommendations, and `.hyper/seo/[slug]/`. Out of scope: edits outside the target, release gating, UI design, unpermitted console actions, or targetless market research. |
| Authority | System/user instructions > target files and live observations > official platform docs > this skill > heuristics. Never promote tool/lab/synthetic/heuristic checks to official requirements. |
| Evidence | Cite command output, URL, file path, or probe result on every `critical` and `warning` finding; mark unavailable checks `unknown` and irrelevant ones `not-applicable`; never invent scores, rankings, or AI citations. |
| Tools | Available file/search/web/browser tools plus `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`; disclose missing channels and fall back to lower-grade methods honestly. |
| Loop | `optimize` mode only: bounded `audit -> fix/recommend -> re-audit` (default 3 iterations), keeping changes only when comparable categories improve with zero regression and zero evidence-grade promotion. |
| Output | `.hyper/seo/[slug]/` with `report.md` and `sources.md` minimum, plus `results.json`, `results.js`, `dashboard.html`, and `flow.json` in complex/optimize modes. |
| Verification | [rules/validation.md](rules/validation.md) plus `render-dashboard.sh` schema check on `results.json`. |
| Stop condition | Audit/plan complete with graded evidence and zero unresolved critical gaps, or `optimize` hits target, budget, plateau, guard, or external credential boundary. |

</instruction_contract>

<output_language>

Default all user-facing deliverables, reports, plans, summaries, and validation notes to Korean while preserving code identifiers, CLI commands, file paths, schema keys, API/package names, and verbatim quotes (`instructions/harness-engineering/references/skill-common-rules.md`). Prefer `*.ko.md` templates when present.

</output_language>

<purpose>

- Audit technical SEO, AI/search crawler policies, on-page SEO, content SEO, Core Web Vitals, structured data, AEO, and GEO/LLMO readiness with strict evidence grading.
- Plan phased new-site launches (plan, build checks, registration, first 30 days) or drive bounded score-optimization loops saved under `.hyper/seo/[slug]/`.

</purpose>

<routing_rule>

Use `hyper-seo` when the deliverable is an SEO/AEO/GEO/LLMO audit, optimization report, launch search-setup plan, or score-improvement loop for a named target.

Do not use when:
- designing landing/product UI
- running competitor/market/AI-trend research with no target site or content set
- issuing deployment go/no-go release verdicts or tuning non-search backend performance

</routing_rule>

<activation_examples>

Positive:
- "Audit this site's SEO and check metadata and structured data."
- "Optimize our content so AI search engines can cite it."
- "Keep iterating fixes until the SEO score is as high as possible."
- "다음 달 새 홈페이지 오픈 전에 SEO·GEO·AI 크롤러 세팅 계획을 잡아줘."

Negative / Boundary:
- "Design this landing page." -> UI design deliverable.
- "Research competitor market positioning." -> market research without site audit.
- "Optimize this page's performance." -> use `hyper-seo` only when evaluated through SEO/Core Web Vitals impact.

</activation_examples>

<trigger_conditions>

| Situation | Mode |
|---|---|
| New full-site, single-page, technical/CWV, or AEO/GEO audit | `create` |
| Re-check after fixes or append dimensions to an existing `.hyper/seo/[slug]/` report | `update` |
| Iterative improvement toward highest achievable score | `optimize` |
| Pre-launch search and AI answer-engine setup plan for a new site | `setup` |

Ask once if no target site, page, or content inventory is named.

</trigger_conditions>

<skill_architecture>

- Core (`SKILL.md`): modes, intake, scoring weights, artifact contract, and harness workflow.
- Rules: [rules/seo-workflow.md](rules/seo-workflow.md) and [rules/validation.md](rules/validation.md).
- References: [references/seo-fundamentals.md](references/seo-fundamentals.md), [references/aeo-geo-guide.md](references/aeo-geo-guide.md), [references/seo-checklist.md](references/seo-checklist.md), [references/site-setup.md](references/site-setup.md), [references/artifact-spec.md](references/artifact-spec.md).
- Script & Assets: `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`, [assets/report.template.ko.md](assets/report.template.ko.md), [assets/report.template.md](assets/report.template.md), [assets/dashboard-template.html](assets/dashboard-template.html), and `assets/evals/`.

</skill_architecture>

<loop_policy>

Only `optimize` mode loops (default cap: 3 iterations). Record baseline, evaluator, budget, and guards before editing; keep an iteration only when comparable categories improve with zero regression and zero evidence-grade promotion, marking rejected passes `discarded` ([rules/seo-workflow.md](rules/seo-workflow.md)).

</loop_policy>

<language_and_translation_default>

Canonical package files are English with aligned `*.ko.md` siblings; user deliverables default to Korean via [assets/report.template.ko.md](assets/report.template.ko.md).

</language_and_translation_default>

<reference_routing>

- Read [rules/seo-workflow.md](rules/seo-workflow.md) at run start and [rules/validation.md](rules/validation.md) before completion.
- Read [references/seo-fundamentals.md](references/seo-fundamentals.md) (E-E-A-T, CWV, schema), [references/aeo-geo-guide.md](references/aeo-geo-guide.md) (AEO/GEO/LLMO, `llms.txt`), and [references/seo-checklist.md](references/seo-checklist.md) during scanning; read [references/site-setup.md](references/site-setup.md) only in `setup` mode.
- Read [references/artifact-spec.md](references/artifact-spec.md) before writing `.hyper/seo/[slug]/`, [assets/report.template.ko.md](assets/report.template.ko.md) (or [assets/report.template.md](assets/report.template.md) when English is requested), and [assets/dashboard-template.html](assets/dashboard-template.html) when rendering the dashboard.

</reference_routing>

<support_file_read_order>

1. This `SKILL.md` and `rules/seo-workflow.md`.
2. `references/seo-fundamentals.md`, `references/aeo-geo-guide.md`, `references/seo-checklist.md` (or `references/site-setup.md` in `setup`).
3. `references/artifact-spec.md`, `assets/report.template.ko.md`, `assets/dashboard-template.html`, and `rules/validation.md`.

</support_file_read_order>

<workflow>

Resume procedure: Before Step 0, inspect `.hyper/seo/[slug]/` (`flow.json`, `results.json`, `report.md`, `sources.md`). If an interrupted run or `update`/`optimize` history exists, read `flow.json` and `results.json` from disk first and resume from the first unfinished phase rather than overwriting baseline history.

| Step | Action | Done when | Why not skip |
|---|---|---|---|
| 0 | Record `Complexity`, `Mode`, `Target`, `Proof surface`, and `<universal_intake>` fields; initialize `flow.json` for complex/optimize | Execution brief and `flow.json` (`scope`) written | Prevents scoring without target context or capability bounds |
| 1 | Establish available measurement channels and confidence limits | `measurement_methods` recorded | Stops static/lab checks from masquerading as live/field data |
| 2 | Collect evidence from repo files, rendered pages, headers/robots, and official docs | Raw evidence and `sources.md` rows logged | Unbacked findings violate evidence gating |
| 3 | Audit technical SEO, crawler/platform policy, on-page, content, CWV, schema, AEO, and GEO/LLMO | Dimension findings recorded (`flow.json` updated) | Partial scans miss crawl blocks or AI bot policies |
| 4 | Grade every finding (`official`/`live`/`field`/`tool`/`lab`/`synthetic`/`heuristic`) and prioritize actions | Graded findings and denominator exclusions set | Mixing heuristics with official rules corrupts the 100-point score |
| 5 | Write `results.json`, run `scripts/render-dashboard.sh` (complex/optimize), and write `report.md` + `sources.md` | Validated artifacts exist under `.hyper/seo/[slug]/` | `render-dashboard.sh` catches malformed `results.json` fields |
| 6 | In `optimize` mode, run `<= 3` fix + re-audit passes keeping non-regressing gains; summarize score, limits, and next steps | Final `report.md` passes [rules/validation.md](rules/validation.md) | Ensures comparable re-measurement before claiming score gains |

Step Yes/No checklist:

| # | Yes/No question | On violation -> return to |
|---|---|---|
| 1 | Did I check `.hyper/seo/[slug]/` on start/resume and record `Complexity`, `Mode`, `Target`, `Proof surface`, and `<universal_intake>` before scoring? (Yes/No) | Step 0 |
| 2 | Does every `critical` and `warning` finding cite a concrete file/URL/command and carry an exact `evidence_grade` without promoting heuristics to `official`? (Yes/No) | Step 4 |
| 3 | Were `unknown` and `not-applicable` categories excluded from the denominator rather than guessed, and did `render-dashboard.sh` exit `0` when `results.json` was written? (Yes/No) | Step 5 |
| 4 | Are `sources.md` and `report.md` saved on disk with zero promised rankings/AI citations, and (in `optimize`) baseline, guards, discarded passes, and stop reason recorded? (Yes/No) | Step 6 |

</workflow>

<complexity_routing>

| Complexity | Signals | Handling |
|---|---|---|
| **Simple** | Single-page review, one SEO element, quick metadata audit | **Direct**: write `report.md` and `sources.md` |
| **Complex** | Full-site audit, multi-page technical + content + CWV, competitor comparison, or `optimize` | **Tracked**: maintain `flow.json` across phases |

Record `Complexity: [simple/complex]`, `Mode: [create/update/optimize/setup]`, `Target: [site/page/path]`, and `Proof surface: [channels]` up front.

</complexity_routing>

<universal_intake>

Classify before scoring:
- `target_type`: `live-url`, `local-static`, `nextjs`, `react-spa`, `docs-site`, `ecommerce`, `blog`, or `app-with-marketing-pages`
- `access_level`: live URL, local files only, Search Console, analytics, field CWV, or AI citation probe
- `allowed_action`: `audit-only`, `recommend`, `edit-code`, or `optimize-loop`
- `measurement_confidence` and `evaluator` (comparable targets, rubric, tools/dates)

Assign every finding one `evidence_grade`: `official`, `live`, `field`, `tool`, `lab`, `synthetic`, or `heuristic`. Mark missing checks `unknown` and irrelevant ones `not-applicable` (excluded from denominators).

</universal_intake>

<artifact_contract>

```text
.hyper/seo/[slug]/
├── dashboard.html      # Browser-readable dashboard (rendered via render-dashboard.sh)
├── results.json        # Structured audit results
├── results.js          # file:// fallback payload
├── report.md           # Korean Markdown report (assets/report.template.ko.md default)
├── sources.md          # Source ledger (URL, date, claim, evidence class, limitation)
└── flow.json           # Phase tracker for complex/optimize modes
```

In complex or `optimize` mode, `flow.json` tracks phases in order: `scope` → `measurement` → `technical` → `platform_policy` → `onpage` → `content` → `aeo` → `geo` → `report`. Render `dashboard.html` with `bash <skill-dir>/scripts/render-dashboard.sh <artifact-dir>`.

</artifact_contract>

<audit_dimensions>

Audit relevant surfaces per [rules/seo-workflow.md](rules/seo-workflow.md), [references/seo-checklist.md](references/seo-checklist.md), [references/seo-fundamentals.md](references/seo-fundamentals.md), and [references/aeo-geo-guide.md](references/aeo-geo-guide.md): technical SEO (crawl/index, canonicals, sitemaps, robots, status/redirects); platform policy (Googlebot, Google-Extended, OAI-SearchBot, GPTBot, ChatGPT-User, Claude-SearchBot, ClaudeBot, PerplexityBot, WAF rules, snippet/X-Robots-Tag, plus target-gated Naver `Yeti`/Search Advisor and Bing/IndexNow); on-page SEO; content SEO; Core Web Vitals (LCP, INP, CLS); structured data (JSON-LD parity; separate Google FAQPage rich-result eligibility from answer-friendly visible FAQ copy); AEO; and GEO/LLMO (`llms.txt`, citable statistics, entity clarity, freshness). Evaluate Google AI features through ordinary SEO fundamentals.

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

Mark incomplete categories `unknown` and irrelevant categories `not-applicable` (excluded from denominator). Schema details live in [references/artifact-spec.md](references/artifact-spec.md).

</scoring>

<required>

| Category | Required |
|---|---|
| Target & Intake | Named target plus mode, complexity, proof surface, and `<universal_intake>` recorded before scoring |
| Evidence | Command, URL, file path, or probe result + `evidence_grade` + `source_tier` on every `critical`/`warning` finding |
| Scoring | Total computed strictly from observed categories, excluding `unknown` and `not-applicable` |
| Output | Mode-appropriate `.hyper/seo/[slug]/` artifacts validated by `render-dashboard.sh` and `sources.md` ledger |

</required>

<forbidden>

- Inventing scores/rankings/citations, filling `unknown` categories with guesses, promoting heuristics or lab scores to `official` requirements, guaranteeing rankings/AI citations, or acting outside target scope.
- Bad: Guessing Core Web Vitals or live crawler status from static source files to reach a 100-point denominator -> Good: Marking unmeasured categories `unknown`, excluding `not-applicable` from the denominator, and labeling static checks `tool` or `heuristic`.
- Bad: Treating word-count or `llms.txt` heuristics as official Google ranking requirements -> Good: Grading heuristics as `heuristic` and evaluating Google AI features through ordinary SEO fundamentals.
- Bad: Claiming an `optimize` iteration improved SEO without re-auditing on comparable categories -> Good: Recording baseline, guards, re-audit delta, and `discarded` iterations in `.hyper/seo/[slug]/`.

</forbidden>

<validation>

- [ ] `.hyper/seo/[slug]/` state was checked on start/resume, and target, mode, complexity, and intake fields were recorded before scoring.
- [ ] Every `critical` and `warning` finding cites concrete evidence, `evidence_grade`, `source_tier`, owner surface, and an actionable fix.
- [ ] Category scores derive solely from observed evidence (`20/20/15/15/10/10/10` weights), with `unknown` and `not-applicable` handled explicitly.
- [ ] Google AI features use ordinary SEO fundamentals, and FAQPage guidance separates rich-result eligibility from visible answer copy.
- [ ] `sources.md` records URL, date, claim, evidence class, and limits, and `render-dashboard.sh` exited `0` for complex/optimize runs.
- [ ] In `optimize` mode, baseline, evaluator, finite budget, guards, re-audit evidence, discarded iterations, and stop reason are recorded.

</validation>

## Sources

> Checked 2026-11-09. Modes, 100-point weights, and optimize guards follow user instruction (2026-08-20) and [rules/seo-workflow.md](rules/seo-workflow.md); external platform facts carry per-claim dates in `references/*.md` per `instructions/skill/SKILL_AUTHORING.md`.
