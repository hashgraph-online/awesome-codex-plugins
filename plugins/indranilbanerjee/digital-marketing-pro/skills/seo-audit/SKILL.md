---
name: seo-audit
description: "Run comprehensive SEO audit. Use when: checking technical health, on-page, content quality, E-E-A-T, or link profile."
argument-hint: "[URL]"
---

# /digital-marketing-pro:seo-audit

## Purpose

Perform a comprehensive SEO audit that evaluates a website across all major ranking dimensions. Produces a prioritized action plan with estimated impact and effort for each recommendation.

### May 2026 Core Update context (read before triaging volatility)

Google rolled out a **broad core algorithm update starting 21 May 2026** with the usual ~2-week deployment window. If the audit is being run inside that window (or in the 4 weeks after) and the brand is showing ranking volatility:

- **Do not make reactive changes during the rollout.** Wait for the update to fully deploy (Google announces completion in the Search Status Dashboard) plus 7–14 days of post-deploy settling before drawing conclusions.
- **Diagnose direction before scope.** A site-wide drop vs a single-section drop vs a single-template drop have very different root causes. Use Search Console to compare pre-rollout (21 days before May 21) vs in-rollout vs post-rollout impressions and clicks segmented by page-group.
- **Core updates re-weight existing signals, they don't introduce new ones.** The audit dimensions below remain authoritative; the right response to a Core Update hit is usually to deepen E-E-A-T, improve unique value, fix thin/duplicated content, and reduce low-quality affiliate or AI-spam pages — not to chase rumoured signals.
- **Flag in the executive summary** whether ranking deltas pre-date the rollout (likely site-specific issues) or coincide with it (likely Core Update reweighting). This determines whether quick wins are appropriate or whether the brand needs a multi-quarter quality program.

## Input Required

The user must provide (or will be prompted for):

- **Website URL**: The domain or specific pages to audit
- **Target keywords**: Primary keywords the site should rank for (optional — can be researched)
- **Competitors**: 2-3 competitor URLs for benchmarking (optional)
- **Audit scope**: Full site or specific area (technical, content, local, links)
- **Known issues**: Any existing problems the user is aware of

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Technical audit**: Crawlability, indexation, Core Web Vitals, mobile usability, structured data, HTTPS, XML sitemap, robots.txt, canonical tags, redirect chains
3. **On-page audit**: Title tags, meta descriptions, heading hierarchy, keyword usage, image alt text, internal linking structure, URL structure
4. **Content audit**: Thin content, duplicate content, content gaps, freshness, E-E-A-T signals (author pages, citations, credentials, first-hand experience)
5. **Local SEO** (if applicable): Google Business Profile, NAP consistency, local schema, reviews, local link profile
6. **Link profile**: Domain authority, backlink quality, toxic links, anchor text distribution, link velocity, competitor link gap
7. Score each dimension on a 1-10 scale
8. Prioritize findings by impact (high/medium/low) and effort (quick win/medium/major project)
9. Generate the audit report with actionable recommendations

## Output

A structured SEO audit report containing:

- Executive summary with overall health score
- Technical SEO scorecard with specific issues and fixes
- On-page optimization findings per page/template
- Content quality assessment with gap analysis
- E-E-A-T evaluation and improvement recommendations
- Local SEO assessment (if applicable)
- Link profile analysis with opportunities
- Prioritized action plan sorted by impact-to-effort ratio

## Numbered output convention

All audit outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-audit/{YYYY-MM-DD}/`:

```
00-input.md                    target URL, audit scope, brand context, Core Update window flag
01-crawl-inventory.md          discovered URLs, status codes, redirect chains
02-technical-scorecard.md      Core Web Vitals, crawlability, schema validity (1-10 per dimension)
03-onpage-findings.md          per-template issues with affected URL list
04-content-quality.md          E-E-A-T, thin/duplicate, topical coverage
05-link-profile.md             own backlink health (hand off to backlink-gap for prospect work)
06-eeat-evaluation.md          author signals, expertise indicators, trust elements
07-local-seo.md                only if business profile.target_markets has local intent
08-quality-scorecard.md        the gates below — must pass for status: ready
09-prioritised-actions.md      impact × effort matrix, top 20 actions
PLAN.md                        single-page deliverable
```

Downstream skills (`seo-implement`, `seo-plan`, `content-engine`) consume `PLAN.md` and the relevant numbered file rather than re-querying.

## Quality scorecard

| Gate | What it checks |
|---|---|
| **crawl_coverage** | ≥ 90% of sitemap URLs successfully crawled (else input data is incomplete) |
| **dimension_completeness** | Scores filled for all 6 mandatory dimensions (technical, on-page, content, E-E-A-T, link, local-if-applicable) |
| **finding_actionability** | Every "high impact" finding has a named owner + effort estimate (else it's not actionable) |
| **core_update_flag_set** | If running inside a Core Update window, `00-input.md` flags it AND `PLAN.md` carries the "wait 7-14 days before reactive changes" callout |

`status: ready` requires all four gates pass.

## Chain handoffs

- **Upstream:** brand profile + (optional) prior `tech-seo-audit`, `aeo-audit` outputs
- **Downstream:**
  - `/digital-marketing-pro:seo-implement` — applies the top-N findings to CMS / dev backlog
  - `/digital-marketing-pro:seo-plan` — consumes via dispatcher pillar scoring
  - `/digital-marketing-pro:backlink-gap` — for the link-prospect side that `05-link-profile.md` only covers from the own-domain angle
  - `/digital-marketing-pro:seo-drift` — next quarter, compare two audit snapshots

## Tips & caveats

- **Run during a Core Update?** Mark it loudly in `00-input.md` and don't recommend reactive changes. The audit findings stay valid; the timing of action does not.
- **Don't audit at the URL level for sites > 10k pages.** Sample template-typically (cluster by template, audit one representative URL per template, generalise).
- **E-E-A-T scoring is judgement, not measurement.** Two senior SEOs will disagree by ~1 point per dimension on the same site. Calibrate against the brand's industry: a 7/10 author signal is excellent for SaaS but minimum-viable for a YMYL health publisher.
- **Local SEO dimension** only applies if the brand profile has `business_model: local` or `target_markets` includes specific geographies with physical service. Otherwise skip.
- **The link-profile dimension here is own-domain health** (broken links, redirect chains, anchor-text distribution on inbound links). For competitor link-gap analysis, hand off to `/digital-marketing-pro:backlink-gap` — don't try to do both in this audit.

## Agents Used

- **seo-specialist** — All audit dimensions, scoring, prioritization, and recommendations
