---
name: aeo-audit
description: "Audit AI search visibility. Use when: checking brand presence in ChatGPT, Perplexity, AI Overviews, Gemini."
argument-hint: "[brand-name or URL]"
---

# /digital-marketing-pro:aeo-audit

## Purpose

Evaluate the brand's visibility and accuracy across AI answer engines. Analyze how the brand is cited, described, and recommended by ChatGPT, Perplexity, **Google AI Mode** (the conversational search surface that became Google's default at I/O 2026 — ~1B MAUs as of May 2026), Google AI Overviews, Gemini, and Microsoft Copilot. Produce optimization recommendations to improve AI visibility.

**AI Mode vs AI Overviews — why both matter:** AI Overviews are the summary block at the top of a classic Google SERP and trigger on a subset of queries. AI Mode is a conversational tab (and now the default search experience for opted-in users) backed by Gemini 3.5 Flash with deeper reasoning, follow-ups, and a different citation pattern. The two surfaces select different sources for the same query in 40–60% of cases observed since May 2026. Audit both.

**Cross-reference with GSC AI Performance Report (rolled out 3 June 2026):** The Google Search Console AI Performance Report (UK rollout first, global to follow) gives you actual *impressions* in AI Overviews + AI Mode for verified properties. Synthetic probe results from this skill should be reconciled against GSC actuals — see `/digital-marketing-pro:gsc-ai-performance` for the workflow. Important caveat: the GSC report intentionally excludes click data; click-through attribution must come from GA4 (the new `AI Assistant` channel group, added 13 May 2026, captures `Medium=ai-assistant` referrals from ChatGPT/Gemini/Claude; see `/digital-marketing-pro:analytics-insights`).

**Google's official position on AI optimization** (Google AI Optimization Guide, updated 15 May 2026): no `llms.txt`, no AI-specific schema, no separate AI eligibility gate. Pages eligible for snippets in classic Search are eligible for AI Features. Don't manufacture work around fictional ranking factors — `/digital-marketing-pro:aeo-geo` documents what *does* work (entity consistency, citation-worthy snippets, knowledge graph alignment).

**Information Agents (Google AI Pro / Ultra, summer 2026 launch):** Google announced at I/O 2026 a new class of persistent agents that continuously monitor web / news / real-time data for subscribers and deliver synthesized updates with actionable capabilities. Once these go live, they become a **7th probe target** for this skill (alongside ChatGPT / Perplexity / AI Mode / AI Overviews / Gemini / Copilot). Until then, treat AI Mode as the proxy — agents are powered by the same Gemini 3.5 Flash backbone. Source: [blog.google/search-io-2026](https://blog.google/products-and-platforms/products/search/search-io-2026/).

## Input Required

The user must provide (or will be prompted for):

- **Brand name**: The brand to audit
- **Website URL**: Primary domain
- **Key queries**: 5-10 queries a potential customer might ask that should surface the brand
- **Competitors**: 2-3 competitors for comparison
- **Product/service categories**: What the brand should be known for

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Define a test query set: branded queries, category queries, comparison queries, "best of" queries, problem-solution queries
3. Analyze how the brand appears in AI responses for each query type
4. Check citation accuracy: Are facts correct? Are URLs valid? Is the description current?
5. Compare brand mention frequency and sentiment against competitors
6. Assess source authority: Which sources are AI engines pulling brand info from?
7. Evaluate structured data and knowledge panel presence
8. Identify content gaps where the brand should appear but does not
9. Generate optimization recommendations for improved AI visibility

## Output

A structured AEO audit report containing:

- AI visibility scorecard across platforms (ChatGPT, Perplexity, Google AI Mode, Google AI Overviews, Gemini, Microsoft Copilot)
- Query-by-query results showing where the brand appears, how it is described, and citation sources
- Competitor comparison matrix for AI visibility
- Citation accuracy assessment with corrections needed
- Source authority analysis — which pages/sites drive AI mentions
- Content gap list — queries where the brand is absent but should appear
- Optimization playbook: structured data, content strategy, authority building, and entity optimization

## Numbered output convention

All AEO audit outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/aeo-audit/{YYYY-MM-DD}/`:

```
00-input.md                 brand identity, target query set, competitor list, AI platforms probed
01-query-set.md             the 10-25 queries probed, with intent classification
02-probe-results.json       raw probe responses per platform per query (the data layer)
03-platform-scorecard.md    visibility scorecard per AI platform (1-10) with diff vs prior run
04-citation-accuracy.md     fact-by-fact accuracy check of AI descriptions; what to correct
05-source-authority.md      which pages/sites are driving AI mentions; topical entity map
06-content-gaps.md          queries where brand is absent but should appear
07-competitor-matrix.md     side-by-side AI presence vs competitors
08-quality-scorecard.md     the gates below
09-optimization-playbook.md  structured data, content, authority, entity work — sequenced
PLAN.md                     single-page deliverable
```

Reconcile `03-platform-scorecard.md` against `/digital-marketing-pro:gsc-ai-performance` actuals — probe results show what AI *could* surface; GSC shows what it *actually* surfaced.

## Quality scorecard

| Gate | What it checks |
|---|---|
| **query_set_size** | ≥ 10 queries probed (below this, results are anecdotal) |
| **platform_coverage** | ≥ 4 of the 6 supported platforms probed (ChatGPT, Perplexity, AI Mode, AI Overviews, Gemini, Copilot) |
| **competitor_coverage** | ≥ 2 competitors probed alongside the brand on same query set |
| **citation_accuracy_done** | Every "brand appears" result has been fact-checked (no silent ship of "AI said X — sounds right") |

`status: ready` requires all four gates pass.

## Chain handoffs

- **Upstream:** `/digital-marketing-pro:aeo-geo` for the strategy framing this audit measures against
- **Downstream:**
  - `/digital-marketing-pro:gsc-ai-performance` — reconcile synthetic probe results against GSC actuals
  - `/digital-marketing-pro:keyword-cluster` — `06-content-gaps.md` becomes seed input for clustering
  - `/digital-marketing-pro:entity-audit` — drives `05-source-authority.md` corrections in Knowledge Graph
  - `/digital-marketing-pro:seo-drift` — next quarter, compare two AEO snapshots

## Tips & caveats

- **AI Mode and AI Overviews disagree on 40-60% of the same queries** — always probe both separately, never roll them into "Google AI".
- **Don't probe more than 25 queries per session.** Beyond that, model rate limits + token cost dominate. Pick the 10-25 highest-value queries.
- **Citation accuracy is the audit's most-skipped step.** AI engines confidently hallucinate brand facts; if you don't fact-check, you're certifying wrong info. Always check at least the top-cited fact per platform.
- **Synthetic probes overstate presence.** Real users phrase queries differently than the test set. The cross-reference with the GSC AI Performance Report (3 Jun 2026, UK first) is what tells you actual impressions.
- **Score the probe results, don't average platforms.** A brand can score 9/10 on Perplexity (cites everyone) and 2/10 on ChatGPT (selective citing) — the average misleads. Report per-platform scores side by side.

## Agents Used

- **seo-specialist** — AI search analysis, entity optimization, structured data, citation strategy
