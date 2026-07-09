---
name: seo-drift
description: "Compare two SEO snapshots (GSC, GSC AI Performance, rank tracker, AEO probe) and surface biggest movers per metric — impressions, clicks, position, AI citations. Use when: monthly performance reviews, post-Core-Update triage, AI Mode citation tracking, or before/after content-refresh evaluation."
argument-hint: "[brand-name]"
user-invocable: true
---

# /digital-marketing-pro:seo-drift

## Purpose

Take two snapshots of SEO performance data — separated by weeks, a Core Update, a content refresh, or an algorithm change — and produce a structured drift report: top gainers, top losers, classifications (growth / decline / reshuffle / stable / new / lost), and diagnostic patterns. Works with classic GSC, the new GSC AI Performance Report, rank-tracker exports, and `aeo-audit` probe results.

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

## When to Use

- **Monthly performance review** — last month vs the month before
- **Core Update triage** — pre-update vs post-update + settling window (use 14+ days after rollout-complete)
- **AI Mode citation tracking** — quarter-over-quarter `aeo-audit` outputs to see which queries gained / lost AI Mode citations (Google AI Mode citation diff is a leading indicator for organic decline)
- **Content refresh attribution** — before vs after a planned content update to attribute lift to the refresh vs other factors
- **GSC AI Performance Report** — month-over-month deltas on the new (3 Jun 2026) combined AI Overviews + AI Mode report
- **Site migration audit** — pre-migration baseline vs post-migration settling

**Don't use** for single-point-in-time analysis (use the source skill — `seo-audit`, `aeo-audit`, `gsc-ai-performance`).

## Brand context (auto-applied)

1. Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`
2. If no brand exists: ask "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults
3. Apply `skills/context-engine/industry-profiles.md` for industry-specific noise thresholds (YMYL industries should use higher `--noise` to filter out routine Quality Rater Guidelines volatility)

## Inputs

| Input | Source | Required? |
|---|---|---|
| Baseline CSV | Older snapshot | yes |
| Current CSV | Newer snapshot | yes |
| Join keys | Auto-detected (`query`, `keyword`, `page`, `url`) or `--join-on` flag | optional |
| Noise threshold | `--noise` (default 5%) — % below which a metric is "stable" | optional |
| Top-N | `--top` (default 20) — gainers/losers per metric | optional |

**Both snapshots must come from the same source.** Mixing a GSC export with an Ahrefs export will produce nonsense — different sources count different things.

## Process (10 steps, numbered-file output)

All outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-drift/{YYYY-MM-DD}/`.

1. **`00-input.md`** — capture baseline date range, current date range, source (GSC / GSC AI / rank-tracker / aeo-audit), brand context
2. **`01-baseline.csv`** — copy baseline export here (so the drift run is reproducible months later)
3. **`02-current.csv`** — copy current export here
4. **`03-drift-run.json`** — run the script:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/seo_drift.py" \
       --baseline "${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-drift/{date}/01-baseline.csv" \
       --current  "${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-drift/{date}/02-current.csv" \
       --top 30 --noise 5 \
       --out "${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-drift/{date}/03-drift-run.json"
   ```
5. **`04-quality-scorecard.md`** — read `quality_scorecard` from `03-drift-run.json`. If `status: needs_review`, diagnose:
   - `date_range_distinct: warn` → script couldn't auto-validate. Manually confirm in `00-input.md` that baseline and current cover non-overlapping windows.
   - `sample_size: fail` → either input has < 50 rows. Re-export without row limits.
   - `metric_compatibility: fail` → no numeric metrics in BOTH inputs. Column-name mismatch — re-export from the same source.
   - `no_lookup_collisions: fail` → duplicate keys in one input (e.g., same query × page row twice). Re-export with deduplication or use `--join-on` to add a distinguishing column.
6. **`05-biggest-gainers.md`** — narrative on the top 10 gainers across impressions / clicks / position. For each: hypothesis on cause (new content? backlinks gained? Core Update favoured E-E-A-T? Featured Snippet rotation?). Hand off candidates to `/digital-marketing-pro:content-engine` for amplification.
7. **`05-biggest-losers.md`** — narrative on the top 10 losers. For each: triage matrix — `is_yMYL × had_recent_change × Core_Update_window` → action (refresh content / restore reverted change / wait for next algo cycle / accept and reallocate).
8. **`06-ai-mode-shift.md`** *(only if input source is GSC AI Performance Report)* — queries that LOST AI Mode impressions are a leading indicator. Cross-reference with `/digital-marketing-pro:aeo-audit` to verify citation loss in synthetic probes.
9. **`07-classification-distribution.md`** — counts table:
   - growth / decline / reshuffle / stable / new / lost
   - If >40% in decline: likely Core Update or competitor catch-up. Run `/digital-marketing-pro:seo-audit` for diagnosis.
   - If >20% reshuffle: likely intent shift (AI Mode reweighting). Run `/digital-marketing-pro:aeo-geo` to align with new intent patterns.
10. **`PLAN.md`** — single-page summary: stats + scorecard + top 5 actions ranked by impact × effort, with owner suggestions (SEO lead / content lead / dev team).

## Output format

```
${CLAUDE_PLUGIN_DATA}/{brand}/seo/seo-drift/2026-06-04/
├── 00-input.md
├── 01-baseline.csv
├── 02-current.csv
├── 03-drift-run.json
├── 04-quality-scorecard.md
├── 05-biggest-gainers.md
├── 05-biggest-losers.md
├── 06-ai-mode-shift.md       (only when input is GSC AI Performance Report)
├── 07-classification-distribution.md
└── PLAN.md
```

## Quality scorecard (the four gates)

| Gate | What it checks | Why it matters |
|---|---|---|
| **date_range_distinct** | Baseline and current cover non-overlapping windows | Overlapping windows produce false-positive deltas — same data on both sides |
| **sample_size** | Each input has ≥ 50 rows | Below this, drift is noise |
| **metric_compatibility** | ≥ 1 numeric metric exists in both inputs | If columns differ (e.g., Ahrefs vs GSC), there's nothing to compare |
| **no_lookup_collisions** | No duplicate keys within an input | Duplicates make the delta math ambiguous |

`status: ready` requires sample, metric compatibility, and no-collision gates pass (date-range-distinct is `warn` not `fail` — the script can't always autodetect dates).

## Classification rules

Each row in the report falls into one bucket:

| Classification | Trigger | Interpretation |
|---|---|---|
| **growth** | ≥ 2 metrics moved up > noise%, no metric down > 10% | Clear win — investigate for amplification |
| **decline** | ≥ 2 metrics moved down > noise%, no metric up > 10% | Clear loss — triage by YMYL × Core-Update-window |
| **reshuffle** | Significant moves in opposite directions (e.g., impressions up, position down) | AI Mode signature — content is being shown more broadly but for slightly different intents |
| **stable** | No metric moved more than noise% | No action |
| **new** | Absent in baseline, present in current | New content or new SERP coverage — track |
| **lost** | Present in baseline, absent in current | Content removed, deindexed, or fell out of tracking window |

**Position is special**: for position, *lower numbers are better*. The script automatically inverts position-delta direction for gain/loss ranking — you'll see -85.9% under position as a top gainer (page moved from position 12 to position 2).

## Chain handoffs

This skill is typically a consumer + diagnostician:

1. `/digital-marketing-pro:gsc-ai-performance` or `seo-audit` or `aeo-audit` — generates the snapshots
2. **`/digital-marketing-pro:seo-drift`** — *this skill*
3. Branch by finding:
   - **High decline** → `/digital-marketing-pro:seo-audit` for technical-side check + `/digital-marketing-pro:content-decay-scan` for content-side
   - **High reshuffle** → `/digital-marketing-pro:aeo-geo` for intent realignment
   - **High growth** → `/digital-marketing-pro:content-engine` for amplification briefs

## Tips & caveats

- **Don't run during a Core Update rollout.** Wait until Google announces "rollout complete" + 7–14 days of settling. Mid-rollout deltas are unreliable.
- **Position deltas are noisier than impression/click deltas** — pages bouncing between positions 8 and 12 produce ±30% position deltas that mean nothing. Trust impression/click moves more for diagnosis.
- **GSC's data lag is ~3 days.** When pulling "current month" data, use the date range ending 3 days ago, not yesterday.
- **The GSC AI Performance Report (3 Jun 2026) has NO click data.** drift on AI report = impressions-only drift. Don't try to compute CTR drift from it.
- **For Core Update triage, run drift twice**: pre-update vs day-after-rollout-complete (the "blast"), and pre-update vs 14-days-after (the "settled state"). The two often disagree, and the 14-day view is the one that matters.
- **Reshuffle classification is a leading indicator** — when reshuffle counts spike, intent reweighting is happening. The next quarter's drift will usually show clearer growth/decline. Don't react too fast.

## Agents used

- `analytics-analyst` (primary) — interpretation + cause hypotheses
- `seo-specialist` — for technical-cause hypotheses on losers
- `competitive-intel` — when decline correlates with a competitor's win
- `market-intelligence` — for algo-update context (was there a Core Update in the window?)

## See also

- `/digital-marketing-pro:gsc-ai-performance` — pull the GSC AI Performance Report (input source)
- `/digital-marketing-pro:seo-audit` — diagnose decline causes
- `/digital-marketing-pro:aeo-audit` — diagnose AI Mode citation loss
- `/digital-marketing-pro:content-decay-scan` — for content-side decline triage
- `/digital-marketing-pro:content-engine` — for amplifying gainers
- `scripts/seo_drift.py` — the underlying drift engine
