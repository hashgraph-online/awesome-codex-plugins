---
name: content-decay-scan
description: "Scan content library for decay signals: declining traffic, falling rankings, outdated stats, dropped AI citations. Prioritizes refresh opportunities by business impact. Use when identifying content that needs refreshing, recovering lost traffic, or auditing for stale and underperforming content."
user-invocable: true
triggers:
  - scan for content decay
  - find declining content
  - content refresh audit
  - which content needs updating
  - content losing traffic
  - find stale content
  - content decay analysis
  - prioritize content refreshes
---

# /digital-marketing-pro:content-decay-scan

## Purpose

Scan the entire content library for decay signals and prioritize refreshes by business impact. Content decay is invisible revenue loss — pages that once ranked well and drove conversions silently lose traffic as competitors publish fresher content, search algorithms evolve, statistics become outdated, and AI systems stop citing stale sources. This command detects declining organic traffic, falling keyword positions, outdated content (stale dates, broken links, deprecated information), lost AI citations, and conversion rate drops. It then ranks every piece of content by business impact — traffic multiplied by conversion rate multiplied by revenue per conversion — so you refresh the content that recovers the most revenue first, not just the content that lost the most traffic.

## Input Required

The user must provide (or will be prompted for):

- **Content library data**: URLs of the content to scan — can be a full sitemap, a specific content directory (e.g., /blog/*, /resources/*), or a curated list of high-value pages. For each URL, the system will pull or needs: current monthly traffic, traffic 3 and 6 months ago for trend analysis, primary keyword rankings (current and historical positions), publish date and last updated date, conversion rate if tracked (form fills, signups, purchases), and revenue attribution if available
- **Analytics source**: Where to pull performance data — Google Analytics and Google Search Console via connected MCPs, or exported CSV data. If MCPs are connected, data is pulled automatically. If not, the user provides exported analytics covering at least the past 6 months
- **Priority metrics**: Which decay signals matter most for this scan — traffic decline (default highest weight), ranking drops, content freshness (time since last update), AI citation loss, broken links, or conversion rate decline. The user can adjust weights or accept defaults. Revenue impact is always calculated regardless of signal weights
- **Decay thresholds (optional)**: Brand-specific thresholds for what constitutes "decay" — e.g., "flag anything with 20%+ traffic decline over 3 months" or "flag content not updated in 12+ months." If not provided, standard thresholds are applied: 15% traffic decline over 3 months, 10+ position drop on primary keyword, 18+ months since last update, or 20%+ conversion rate decline
- **Exclusions (optional)**: Content to exclude from the scan — seasonal pages, archived content, redirect targets, or pages scheduled for removal. Prevents false positives and focuses the scan on content the brand intends to maintain

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply content strategy priorities, target keyword clusters, historical content performance baselines, and industry context for freshness expectations (fast-moving industries like tech need more frequent updates than evergreen niches). Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with industry defaults.
2. **Gather content performance data**: Connect to analytics MCPs (Google Analytics, Google Search Console) and pull performance data for the content library — monthly traffic for the past 6 months per URL, keyword position data for primary and secondary keywords, click-through rates from search results, and conversion data if available. For content not covered by MCPs, use any exported data the user provided. Build a performance timeline for each content piece showing the trajectory over the past 6 months.
3. **Score each content piece for decay**: Run the decay scorer with the performance data:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/creative-fatigue-predictor.py" \
       --action decay-scan \
       --data '[{"url":"/blog/post-a","traffic_now":1200,"traffic_3mo":1600,"traffic_6mo":2100,"position_now":8,"position_peak":3,"last_updated":"2024-11-01"}, ...]'
   ```
   (`creative-fatigue-predictor.py` actions: `score-health`, `predict-fatigue`, `generate-refresh-brief`, `decay-scan`, `priority-refresh`, `batch-health`. `--data` is a JSON object or array; there is no `--brand` flag on this script.) The decay scoring model evaluates multiple signals per content piece — traffic trend (3-month and 6-month decline rates, weighted by the user's priority metrics), keyword position changes (drops on primary keyword, movement direction and velocity), content freshness (months since last substantive update, presence of dated statistics or references), broken links (internal and external link health), and conversion rate trend (declining conversion even with stable traffic indicates content quality decay). Each piece receives a decay score from 0-100 where 0 is healthy and 100 is severely decayed.
4. **Calculate business impact score**: For each content piece, compute the revenue impact of its decay — current monthly traffic multiplied by conversion rate multiplied by estimated revenue per conversion. Then calculate the recoverable revenue — the difference between peak performance (from the last 12 months) and current performance, multiplied by the probability of recovery based on decay type and refresh feasibility. Content with high recoverable revenue is prioritized regardless of its raw decay score.
5. **Prioritize refreshes by impact**: Rank all decaying content by recoverable revenue impact — highest-impact decaying content first. Group into priority tiers: Critical (top 10% by revenue impact, refresh immediately), High (next 20%, refresh within 2 weeks), Medium (next 30%, schedule for refresh within 1-2 months), and Monitor (remaining, track but don't invest refresh effort yet). For each tier, estimate the total traffic and revenue recoverable if all pieces in that tier are refreshed.
6. **Generate refresh briefs for top priority items**: For the Critical and High priority content, produce specific refresh briefs — what needs updating (outdated statistics, stale examples, missing recent developments, broken links, thin sections), SEO improvements (keyword gaps versus current top-ranking competitors, missing subtopics, schema markup opportunities, internal linking gaps), and content enhancements (new sections to add, visuals to create, format improvements). Each brief is actionable enough to hand directly to a content writer.
7. **Estimate traffic recovery potential**: For each prioritized content piece, project the traffic recovery if refreshed — based on the content's historical peak performance, current competitive landscape for its target keywords, and typical recovery curves for refreshed content (a substantive refresh often recovers a majority of lost traffic within 2-4 months — the "60-80%" figure is an illustrative rule of thumb, not a measured benchmark; validate against your own refresh outcomes). Aggregate into total portfolio recovery potential.

## Output

A content decay assessment containing:

- **Content decay radar**: All scanned content scored and visualized — showing URL, title, decay score (0-100), primary decay signals (traffic decline, ranking drop, freshness, broken links, conversion drop), trend direction (improving, stable, or declining), and days since last update
- **Priority refresh list**: Content ranked by business impact — showing URL, decay score, recoverable monthly traffic, recoverable monthly revenue, priority tier (Critical/High/Medium/Monitor), and recommended refresh urgency with timeline
- **Decay signals per content piece**: For each decaying piece, the specific signals driving the decay assessment — which metrics are declining, by how much, over what period, and how they compare to the content's historical peak and to competing content on the same keywords
- **Refresh briefs for top items**: Detailed, actionable refresh recommendations for Critical and High priority content — what to update (statistics, examples, links), what to add (new sections, subtopics, visuals), what to optimize (keywords, meta tags, internal links, schema), and estimated effort level (light refresh, moderate rewrite, or major overhaul)
- **Traffic recovery estimates**: Per content piece and in aggregate — projected monthly traffic recoverable through refresh, projected monthly revenue recoverable, expected time to recovery (typically 2-4 months), and confidence level based on competitive landscape and refresh scope
- **Content health summary**: Portfolio-level view showing percentage of content that is healthy (no decay signals), decaying (active decline), and critical (severe decay requiring immediate attention) — with month-over-month trend if historical scan data is available, plus total revenue at risk from the decaying and critical segments

## Tips & caveats

- **Decay isn't always content quality** — seasonal swings, Core Updates, and SERP-feature changes all look like decay in raw GSC data. Always cross-reference with `/digital-marketing-pro:seo-drift` to separate causes.
- **Don't refresh everything that's decaying.** Some content is supposed to decay (one-time event coverage, dated news). Refresh only what has lasting search intent.
- **Refresh > delete in most cases.** A decayed page with backlinks is more valuable than a 404 + redirect. Refresh, restructure, and re-link rather than removing.
- **Refresh recovery takes 2-4 months** typically. Don't measure success at 30 days. Record the next measurement window alongside each item in the priority refresh list.
- **AI Mode citations decay differently.** A piece that's lost AI Mode citations (per `/digital-marketing-pro:gsc-ai-performance`) needs *entity consistency* refresh (re-align schema, author bios) — different fix than traditional decay.
- **Don't refresh during a Core Update window.** Wait until rollout-complete + 7-14 days settling so you can attribute the lift to the refresh, not to the algorithm reshuffle.

## Agents Used

- **content-creator** — Content refresh strategy including update prioritization, new section recommendations, example and statistic replacement sourcing, format improvement suggestions, and actionable refresh briefs that can be handed directly to writers with clear scope and direction for each content piece
- **seo-specialist** — SEO decay analysis including keyword position tracking and drop diagnosis, competitive gap analysis against current top-ranking content, technical SEO issue detection (broken links, missing schema, crawl issues), internal linking gap identification, and search intent alignment assessment to ensure refreshed content matches evolved searcher expectations
- **performance-monitor-agent** — Traffic trend analysis with multi-period decay detection (3-month and 6-month windows), conversion rate decline identification, anomaly detection to separate true decay from seasonal fluctuations or algorithm updates, recovery potential estimation based on historical refresh outcomes, and portfolio-level health scoring with trend monitoring
