---
name: keyword-cluster
description: "Build a content cluster plan from seed keywords — pillar+spokes architecture with internal-link map, intent grouping, and quality scorecard. Use when: planning topical authority, designing a content hub, deduping cannibalising pages, or staging a programmatic content rollout."
argument-hint: "[brand-name or path/to/seeds.csv]"
user-invocable: true
---

# /digital-marketing-pro:keyword-cluster

## Purpose

Take a set of seed keywords and produce a publication-ready cluster plan: pillar pages with their spokes, intent-grouped, prioritised by an opinionated scoring formula, with an internal-link map and a four-gate quality scorecard. Output is structured for direct hand-off to `/digital-marketing-pro:content-brief` or `/digital-marketing-pro:content-engine`.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

## When to Use

- Onboarding a new content programme — turn a 20-keyword brief into a structured topical hub
- Auditing an existing content library for cannibalisation (two pages competing for the same intent)
- Designing a pillar+spokes architecture before any writing begins
- Staging programmatic SEO across hundreds of variants (use this once per topic family)
- Reorganising an existing site's internal-link graph

**Don't use** when you just need keyword *expansion* (use `/digital-marketing-pro:keyword-research`) or when you need *ranking* / SERP-feature analysis (use `/digital-marketing-pro:rank-monitor`, with `--features` for SERP features).

## Brand context (auto-applied)

1. Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`
2. If no brand exists: ask "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults
3. Apply industry-specific guidance from `skills/context-engine/industry-profiles.md`
4. Apply `skills/context-engine/compliance-rules.md` to filter out banned terminology before clustering

## Inputs

| Input | Source | Required? |
|---|---|---|
| Seed keywords (3–500) | CSV with `keyword` column (optional: `volume`, `kd`, `intent`) | yes |
| SERP results per keyword | JSON: `{keyword: [top result URLs]}` from any rank-tracker / Ahrefs / Semrush export | **strongly recommended** — without this the script falls back to lexical clustering, which is lower-confidence |
| Target country / language | From brand profile | optional override |
| Min volume / max KD filters | CLI flags | optional |
| Overlap threshold | CLI flag `--overlap` (default 0.4 for SERP mode, 0.3 for lexical) | optional |

If SERPs JSON is unavailable, you can build one quickly by running the brand's connected rank-tracker MCP (Ahrefs / SE Ranking / Semrush) for each seed and saving the top 10 URLs. Skip this step only if the seeds are too numerous to justify the API spend — but flag the lower-confidence mode in the final deliverable.

## Process (10 steps, numbered-file output)

All outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/keyword-cluster/{YYYY-MM-DD}/`.

1. **`00-input.md`** — capture seeds, source, filters, brand context, run timestamp
2. **`01-seed-expansion.md`** — if seeds < 20, expand via brand's keyword-research MCP (Ahrefs `getRelatedKeywords`, etc.) to ~50–200; otherwise skip. Document expansion source.
3. **`02-filtered.csv`** — apply min-volume / max-KD / banned-word filters. Save the filtered set as CSV (this is what the script consumes).
4. **`03-serps.json`** — fetch top-10 SERP URLs per keyword via the connected rank-tracker (skip if SERPs already provided). **Budget guard**: if estimated cost > 500 credits, surface the cost and ask "Continue? (y/N — default N)" before fetching.
5. **`04-cluster-run.json`** — run the script:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/keyword_cluster.py" \
       --keywords "${CLAUDE_PLUGIN_DATA}/{brand}/seo/keyword-cluster/{date}/02-filtered.csv" \
       --serps "${CLAUDE_PLUGIN_DATA}/{brand}/seo/keyword-cluster/{date}/03-serps.json" \
       --overlap 0.4 \
       --min-volume {profile.min_volume or 0} \
       --max-kd {profile.max_kd or 100} \
       --out "${CLAUDE_PLUGIN_DATA}/{brand}/seo/keyword-cluster/{date}/04-cluster-run.json"
   ```
6. **`05-quality-scorecard.md`** — read the `quality_scorecard` block from `04-cluster-run.json`. If `status: needs_review`, diagnose:
   - `cannibalisation: fail` → two clusters share pillar+intent. Merge them or reassign the lower-priority cluster's pillar.
   - `orphan: fail` → a multi-keyword cluster has 0 spokes. Re-tokenise its members or lower `--overlap`.
   - `coverage: fail` → < 80% of seeds clustered. Lower `--overlap` to 0.3 or expand seeds.
   - `anchor_diversity: fail` → pillar names too similar. Rewrite cluster names with synonym variation.
   - `fragmentation_warning: true` (pillar-only > 50%) → overlap threshold too strict. Try `--overlap 0.3` first.
7. **`06-pillar-pages.md`** — for each cluster with `priority_score >= 0.5`, draft a one-paragraph pillar page brief (intent, audience, length target, key questions to answer). These feed `/digital-marketing-pro:content-brief`.
8. **`07-internal-link-map.md`** — table view of `internal_link_targets` from the script output. Per cluster: which other clusters to link out to + suggested anchor text. This is the file your dev team or CMS template should consume.
9. **`08-build-order.md`** — sorted by `priority_score` descending. Recommended build cadence: top 10% in Q1, next 30% in Q2, remainder backlog.
10. **`PLAN.md`** — single-page summary: stats + scorecard + top 5 priority clusters + handoff to next skill in chain.

## Output format

```
${CLAUDE_PLUGIN_DATA}/{brand}/seo/keyword-cluster/2026-06-04/
├── 00-input.md
├── 01-seed-expansion.md      (only if seeds expanded)
├── 02-filtered.csv
├── 03-serps.json             (if SERP mode)
├── 04-cluster-run.json       (raw script output)
├── 05-quality-scorecard.md
├── 06-pillar-pages.md
├── 07-internal-link-map.md
├── 08-build-order.md
└── PLAN.md                   (the deliverable)
```

`PLAN.md` is what you hand to the brand / client / next skill. Everything else is auditable intermediate state.

## Quality scorecard (the four gates)

Every run produces a scorecard from `scripts/keyword_cluster.py`. **All four must pass** for `status: ready`:

| Gate | What it checks | Why it matters |
|---|---|---|
| **cannibalisation** | No two clusters share the same `(pillar, primary_intent)` pair | Prevents you from writing two pages competing for the same SERP |
| **orphan** | Every multi-keyword cluster has ≥1 spoke (pillar-only clusters are exempt and tagged) | Catches clustering bugs where a cluster head has no supporting topics |
| **coverage** | ≥ 80% of input seeds are assigned to at least one cluster | Catches "junk" seeds and overly strict thresholds |
| **anchor_diversity** | Each multi-keyword cluster has ≥ 2 anchor-text variants suggested | Stops anchor-text over-optimisation across the internal-link graph |

A `fragmentation_warning: true` (pillar-only > 50%) is a **soft** signal — the run is valid but you should consider lowering `--overlap` and re-running.

## Chain handoffs

This skill is a producer in the chain:

1. `/digital-marketing-pro:keyword-research` — generate seeds
2. **`/digital-marketing-pro:keyword-cluster`** — *this skill*
3. `/digital-marketing-pro:content-brief` — consumes `PLAN.md` + `06-pillar-pages.md` to brief each pillar
4. `/digital-marketing-pro:content-engine` (or `contentforge:create-content`) — drafts the content
5. `/digital-marketing-pro:seo-implement` — applies the internal-link map to the CMS

## Tips & caveats

- **SERP mode is strictly better than lexical mode.** Lexical clustering can't see that "shopify seo" and "ecommerce platform seo" target overlapping SERPs while "shopify themes" doesn't.
- **Overlap threshold defaults are conservative.** If you get `fragmentation_warning: true`, lower to 0.3 first. If you get `cannibalisation: fail` with too few clusters, raise to 0.5.
- **The priority score isn't a ranking** — it's a starting build order. A cluster with `priority_score: 0.3` may still be your highest-conversion opportunity if it maps to a high-margin product line. Use the brand profile's `business_goals` to override mechanically.
- **Don't run this on raw GSC query exports** without filtering first. GSC dumps thousands of long-tail variants of the same query — they'll all cluster together and produce a single mega-cluster.
- **Pillar-only clusters are valid** — they represent distinct intents that simply lack spoke candidates in your seed set. Add seeds via Step 2 expansion if you want spokes.
- **The internal-link map is suggestions, not commands.** Final anchor text should be reviewed for brand voice (apply the brand profile's voice fields + `skills/context-engine/guidelines-framework.md`).

## Agents used

- `seo-specialist` (primary) — interpretation + final pillar-page recommendations
- `competitive-intel` — for SERP-overlap reasoning when results look surprising
- `brand-guardian` — anchor-text review against banned-term lists

## See also

- `/digital-marketing-pro:keyword-research` — generates seeds (use first)
- `/digital-marketing-pro:content-brief` — consumes the cluster plan (use next)
- `/digital-marketing-pro:seo-implement` — applies internal-link map to CMS
- `/digital-marketing-pro:seo-drift` — re-run quarterly to detect cluster drift
- `scripts/keyword_cluster.py` — the underlying clustering engine
