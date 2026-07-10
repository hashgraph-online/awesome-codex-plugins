---
name: backlink-gap
description: "Find referring domains that link to your competitors but not to you, ranked by an opinionated outreach-priority score with DR / link-overlap / traffic / topical relevance. Use when: planning link-building campaigns, qualifying digital-PR prospects, or running quarterly backlink-gap audits."
argument-hint: "[brand-name]"
user-invocable: true
---

# /digital-marketing-pro:backlink-gap

## Purpose

Identify the highest-leverage backlink prospects — domains that link to multiple competitors but not to you — and rank them by an opinionated priority score that combines authority, link-overlap signal, downstream traffic, and topical relevance. Produces a numbered output bundle ready for outreach handoff.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

## When to Use

- Quarterly backlink audit — "where did our competitors grow links this quarter and we didn't?"
- Pre-launch link-building plan for a new product or content hub
- Digital PR qualification — separating "would-link-to-anyone" prospects from "high-confidence-will-link-to-our-space"
- Competitive recovery — a competitor displaced you and you want to know which links moved
- Onboarding a new client and need a "first 50 link targets" backlog

**Don't use** when you just need backlink *quantity* numbers (use the brand's connected backlink MCP directly) or when you need *anchor-text* analysis of your own profile (that's a separate audit — covered in `seo-audit`).

## Brand context (auto-applied)

1. Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`
2. If no brand exists: ask "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults
3. Apply `skills/context-engine/industry-profiles.md` for industry-specific link-quality thresholds (YMYL industries should set higher `--min-dr`)
4. Apply `skills/context-engine/compliance-rules.md` to filter out blocked publishers (e.g., PBN-style or paid-link networks the brand has explicitly banned)

## Inputs

| Input | Source | Required? |
|---|---|---|
| Our backlinks CSV | Export from connected backlink MCP (Ahrefs / Semrush / SE Ranking / Moz) for the brand's primary domain | yes |
| Competitor backlinks CSVs (2+) | Same exporter, one per competitor (2 minimum for the link-overlap signal; 3-5 is the sweet spot) | yes |
| Min DR / DA filter | CLI flag, brand-profile default, or industry standard | optional |
| Top-N count | How many prospects to surface | optional |

**One competitor is allowed** (the script warns rather than errors) but the resulting "shared signal" is noise — single-competitor gap analysis is really just "who links to them" rather than "who consistently links in our space."

## Process (10 steps, numbered-file output)

All outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/{YYYY-MM-DD}/`.

1. **`00-input.md`** — capture our domain, competitor list (with rationale: why these N?), filter parameters, run timestamp
2. **`01-data-pull.md`** — pull backlinks for `{brand}.tld` and each competitor via brand's connected backlink MCP. **Budget guard**: if the MCP exposes credit cost, sum estimated cost and ask "Continue? (y/N — default N)" before fetching when total > 200 credits.
3. **`02-ours.csv`** — our backlink export (raw)
4. **`03-comp-{competitor}.csv`** — one CSV per competitor (raw)
5. **`04-gap-run.json`** — run the script:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/backlink_gap.py" \
       --ours "${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/{date}/02-ours.csv" \
       --competitors \
         "${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/{date}/03-comp-competitor1.csv" \
         "${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/{date}/03-comp-competitor2.csv" \
       --min-dr {brand.profile.min_link_dr or 20} \
       --top 100 \
       --out "${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/{date}/04-gap-run.json"
   ```
   `--competitors` takes an explicit space-separated list of CSV paths (`nargs="+"`) — **enumerate each `03-comp-*.csv` file; the script does not expand a `*` glob**, so a quoted `03-comp-*.csv` would fail with FileNotFoundError. List one path per competitor.
6. **`05-quality-scorecard.md`** — read `quality_scorecard` from `04-gap-run.json`. If `status: needs_review`, diagnose:
   - `data_freshness: fail` → input CSV(s) older than 90 days. Re-pull data; backlink graphs decay fast.
   - `sample_size: fail` → any input < 50 unique referring domains. Either the domain is too new or the export was truncated. Re-export with no row limit.
   - `competitor_coverage: warn` → only 1 competitor. Add at least 1 more for genuine overlap signal.
   - `link_overlap_signal: fail` → fewer than 5 referring domains link to ≥2 competitors. Either competitors are poorly chosen (they don't share a content space with each other) or the data is incomplete. Re-choose competitors.
7. **`06-prospect-shortlist.md`** — top 30 prospects, formatted for outreach handoff: domain, DR, link count across competitors, suggested outreach angle (guest post, broken-link, resource-page mention)
8. **`07-broken-link-candidates.md`** — subset where one or more competitor links return 4xx (run a quick HTTP HEAD pass on competitor backlink URLs — use the brand's connected web-fetch MCP). These are "easy wins" — pitch your URL as the replacement.
9. **`08-outreach-templates.md`** — three template variants: (a) cold-pitch resource-page, (b) broken-link replacement, (c) competitor mention. Each pre-filled with brand voice from the brand profile's voice fields + `skills/context-engine/guidelines-framework.md`.
10. **`PLAN.md`** — single-page summary: stats + scorecard + top 10 prospects with outreach angle + recommended cadence (3-5 pitches/week for sustainable outreach quality).

## Output format

```
${CLAUDE_PLUGIN_DATA}/{brand}/seo/backlink-gap/2026-06-04/
├── 00-input.md
├── 01-data-pull.md
├── 02-ours.csv
├── 03-comp-{competitor1}.csv
├── 03-comp-{competitor2}.csv
├── ...
├── 04-gap-run.json
├── 05-quality-scorecard.md
├── 06-prospect-shortlist.md
├── 07-broken-link-candidates.md
├── 08-outreach-templates.md
└── PLAN.md
```

## Quality scorecard (the four gates)

| Gate | What it checks | Why it matters |
|---|---|---|
| **data_freshness** | All input CSVs have mtime within 90 days | Backlink graphs decay fast — stale data sends you chasing dead links |
| **sample_size** | Each input has ≥ 50 unique referring domains | Below this, the gap math has too little signal to rank |
| **competitor_coverage** | ≥ 2 competitor CSVs supplied | The "shared signal" is what separates real prospects from noise |
| **link_overlap_signal** | ≥ 5 referring domains link to ≥ 2 of the competitors | If no domains shared, your competitors aren't actually competing in the same content space |

`status: ready` requires all four gates pass (`competitor_coverage: warn` does not block — it's a soft signal).

## Priority score (0–1, displayed in 04-gap-run.json)

```
priority = 0.40 × DR_normalised
         + 0.25 × link_count_normalised  (how many competitors this domain links to)
         + 0.20 × traffic_normalised
         + 0.15 × topical_relevance
```

**Why link_count is weighted higher than traffic:** a domain that links to 3/3 competitors is unambiguously in your space and willing to link. A high-traffic domain that only links to 1 might just be a tier-1 publisher who happens to have covered one of you in passing.

## Chain handoffs

This skill is a producer in a longer chain:

1. `/digital-marketing-pro:competitor-analysis` — picks the right competitors
2. **`/digital-marketing-pro:backlink-gap`** — *this skill*
3. `/digital-marketing-pro:digital-pr` — consumes `06-prospect-shortlist.md` + `08-outreach-templates.md`
4. `/digital-marketing-pro:pr-pitch` — drafts individual pitches per prospect
5. `/digital-marketing-pro:performance-report` — quarterly re-runs of this skill feed the "links gained" KPI

## Tips & caveats

- **More competitors ≠ better.** Three to five focused competitors beats ten random ones. The "shared signal" gate works best when all competitors are in the same content space.
- **DR/DA from different exporters aren't comparable.** Don't mix an Ahrefs export with a Moz export — the script doesn't know to normalise across exporters. Pick one provider per audit.
- **Topical relevance is the weakest signal in most exports** because few exporters provide it well. The script defaults to 0.5 if absent, which is the right neutral. Override only if you have a curated topical-relevance score.
- **Don't outreach 100 prospects in one week.** The output is a backlog, not a queue. Sustainable cadence: 3-5 highly personalised pitches per week per outreach lead.
- **Broken-link candidates tend to have the highest hit rate** (broken-link replacement pitches typically out-reply cold pitches by a wide margin — the "30-60% vs 5-15%" figures are an illustrative rule of thumb, not measured; validate against your own outreach data) — always work the `07-broken-link-candidates.md` list first.
- **Re-run quarterly,** not monthly. Backlink data moves slowly enough that monthly runs mostly produce noise.
- **YMYL industries** (health, finance, legal) should set `--min-dr 40` to filter out low-authority publishers that could damage E-E-A-T.

## Agents used

- `seo-specialist` (primary) — interpretation of prospect quality
- `competitive-intel` — competitor-set selection rationale (Step 1)
- `pr-outreach` — outreach template drafting (Step 8)
- `brand-guardian` — banned-publisher filter at Step 6

## See also

- `/digital-marketing-pro:competitor-analysis` — pick the competitors for this audit
- `/digital-marketing-pro:digital-pr` — runs the actual outreach
- `/digital-marketing-pro:seo-drift` — re-run quarterly to track delta
- `/digital-marketing-pro:seo-audit` — broader site-level audit including own-profile health
- `scripts/backlink_gap.py` — the underlying gap engine
