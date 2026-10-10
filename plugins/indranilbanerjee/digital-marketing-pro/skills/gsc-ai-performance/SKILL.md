---
name: gsc-ai-performance
description: "Read the GSC AI Performance report by script: AI Overviews and AI Mode impressions. \"read the new GSC AI report\""
argument-hint: "[brand-name or site URL]"
---

# /digital-marketing-pro:gsc-ai-performance

> **Script location.** If your host does not set `${CLAUDE_PLUGIN_ROOT}`, the scripts are in this plugin's `scripts/` folder, next to `skills/`.

## Purpose

Google rolled out a new **GSC AI Performance Report** on **3 June 2026** ([Search Engine Land announcement](https://searchengineland.com/google-search-console-ai-performance-reports-and-controls-to-block-your-content-in-ai-responses-479298)) covering both AI Overviews and AI Mode in a single combined surface. This skill helps you (a) baseline a brand's visibility in the new report, (b) understand the metric trade-offs, and (c) decide whether to use the new in-SC opt-out toggle.

## What is genuinely new (3 June 2026)

| Metric / surface | Status |
|---|---|
| Combined AI Overviews + AI Mode impressions | NEW — one report for both surfaces |
| Pages cited (per query group) | NEW |
| Country breakdown | NEW |
| Device breakdown | NEW |
| Date range filtering | NEW |
| **Click data** | **NOT INCLUDED** (Google explicitly excluded — important caveat for attribution) |
| Opt-out toggle in Search Console | NEW (replaces having to ship robots.txt / meta tags for AI-specific exclusion) |
| API surface | **NOT YET PUBLISHED** — UI only (last checked July 2026; re-check the Search Console API release notes before automating) |
| **Discover generative surfaces** | **NEW (June–July 2026)** — the report family now also covers generative AI features in Discover ([Google announcement](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports)) |
| Data availability | Backfilled from **18 May 2026**; access expanded broadly in July 2026, with a companion deep-dive help doc on AI controls |
| Geographic rollout | UK first, then global ([source](https://searchengineland.com/google-search-console-ai-performance-reports-and-controls-to-block-your-content-in-ai-responses-479298)) |
| **Multimodal filter** | **NEW (September 2026)** — a `multimodal` search-type filter (Lens, Circle to Search, image uploads) appears in both the Search performance report and the generative AI report. It has **no Queries dimension**, and these impressions are **newly counted** ([Google Search Central](https://developers.google.com/search/blog/2026/09/web-multimodal-in-sc)) |

**Critical interpretation guidance:** The report shows when your pages were SHOWN in AI Overviews / AI Mode, not when users clicked through to them.

Because click data is absent, all downstream attribution to AI traffic must come from your analytics, and GA4 has a blind spot for exactly this surface. Its `AI Assistant` channel **excludes** Google's AI Overviews and AI Mode; GA4 counts those visits as Organic Search (see the map below and `/digital-marketing-pro:analytics-insights`).

## Honest measurement map — what exists and what does not (checked 2026-10-04)

State these limits in every deliverable. A blank cell is not a zero; it is a metric no first-party tool publishes.

| Question | First-party answer | Source |
|---|---|---|
| How often did Google show my pages in AI Overviews / AI Mode? | **Yes:** impressions in the Search Console generative AI performance report. You can group by Pages, Countries, Dates, Devices and filter by search type (text / multimodal). The export button downloads chart + table | [Search Console help](https://support.google.com/webmasters/answer/16984139) |
| Which **queries** triggered those AI impressions? | **Does not exist.** The report has no Queries dimension | same |
| How many **clicks**, and what **CTR**, came from AI Overviews / AI Mode? | **Does not exist** in Search Console. The report shows impressions only | same; [Google Search Central blog](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports) (3 Jun 2026) |
| Can GA4 separate AI Overviews / AI Mode visits? | **No documented way.** GA4's Organic Search channel *includes* "Google's AI Overviews and AI Mode", and the AI Assistant channel *excludes* them. Google's channel page documents no dimension that splits them out of organic | [GA4 default channel group](https://support.google.com/analytics/answer/9756891) |
| Who sees the report? | Google: "As of August 31, 2026, we've rolled out these insights to all websites worldwide." If a property doesn't see it, the site may have too few AI-feature impressions or may be excluded from Search generative AI features | [Search Console help](https://support.google.com/webmasters/answer/16984139) |
| Is there an API for it? | Not documented on the help page, which describes the UI and its export button only. Keep automation on CSV exports | same |
| Copilot / Bing AI citations? | **Yes, but a different tool:** Bing Webmaster Tools AI Performance (citations, grounding queries, citation share, intents). It shows no clicks | `/digital-marketing-pro:geo-monitor` |
| ChatGPT / Claude / Perplexity citations? | **No first-party report exists.** Only synthetic probes (`/digital-marketing-pro:aeo-audit`, `/digital-marketing-pro:geo-monitor`), labeled as probes | — |

Google's [AI optimization guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) points to this report as the way to measure generative AI visibility. It also warns that "No third-party tool has access to our internal ranking or AI systems."

## When to use this skill

- Setting baseline AI visibility for a new brand (first 30-day capture of AI Overview + AI Mode impressions)
- Comparing brand AI visibility against `aeo-audit` synthetic results — the GSC report shows ACTUAL impressions vs `aeo-audit`'s probe queries
- Deciding whether to flip the in-SC AI opt-out toggle for a brand (regulated industry, brand-safety concern, or paywall/login content)
- Quarterly business review evidence — "AI search impressions grew X%" using authoritative Google data

## Brand context (auto-applied)

1. Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`
2. If no brand exists: ask "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults
3. Apply industry-specific guidance from `skills/context-engine/industry-profiles.md` (YMYL industries may want opt-out toggled ON until E-E-A-T audit is clean)
4. Reference `skills/context-engine/compliance-rules.md` for jurisdiction-specific rules (EU markets — see `skills/context-engine/eu-code-of-practice.md` for Article 50 transparency context)

## Numbered output convention

All outputs go to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/gsc-ai-performance/{YYYY-MM-DD}/`:

```
00-input.md                  brand domain, GSC access status, UK-cohort flag, date range
01-access-check.md           verification result; if no access, instructions for adding the user
02-export.csv                raw CSV export from GSC (preserved for reproducibility)
03-script-output.json        gsc-ai-performance.py parsed output (impressions, pages, countries, devices)
04-reconciliation.md         vs aeo-audit synthetic probe results — gap analysis
05-opt-out-decision.md       y/n on the in-SC opt-out toggle, with rationale
06-quality-scorecard.md      the gates below
PLAN.md                      single-page summary with tracking cadence
```

## Quality scorecard

| Gate | What it checks |
|---|---|
| **gsc_access_verified** | User has confirmed Search Console verified ownership for the brand domain |
| **export_completeness** | CSV has ≥ 1 day of data + at minimum the impressions column |
| **cohort_documented** | `00-input.md` notes whether the property sees the report. If it does not, record which documented reason applies: too few AI-feature impressions, or the site is excluded from Search generative AI features |
| **reconciliation_done** | `04-reconciliation.md` cross-references against the brand's most recent aeo-audit |

If the property still doesn't see the report after the worldwide rollout (31 Aug 2026), the gate framework still applies, but `export_completeness` will be `fail`. Record the reason; that is a finding, not a regression.

## Chain handoffs

- **Upstream:** `/digital-marketing-pro:brand-setup` for property verification
- **Downstream:**
  - `/digital-marketing-pro:aeo-geo` — optimization based on what's surfacing (or not)
  - `/digital-marketing-pro:seo-drift` — month-over-month tracking using the exported CSVs
  - `/digital-marketing-pro:analytics-insights` — GA4 AI Assistant channel attribution closes the click-side gap

## Process

1. **Access check** — confirm the user has Google Search Console verified access for the brand's domain. The report has been available to all websites worldwide since 31 Aug 2026. If it is missing, check whether the site is excluded from Search generative AI features or has too few AI-feature impressions.
2. **Locate the report** — Search Console → left nav → **Performance** → switch tab to **Search results** → look for the new **AI Overviews & AI Mode** tab (the tab title may vary slightly during rollout; Google's working name during testing was "Search Generative AI"). On rollouts pre-tab, the data may also surface under the existing Performance report with an AI Features filter.
3. **Run baseline export** — set the date range to "last 28 days" (or maximum available since rollout), export to CSV/Sheets via Search Console's export button. Capture: impressions, pages, country mix, device mix. There is **no Queries dimension** in this report (checked 2026-10-04), so do not promise a query list. Use the main Performance report's queries only as a separate, non-AI-specific view, and label it that way. Then parse and archive it with the helper script:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/gsc-ai-performance.py" \
       --brand {slug} \
       --csv "${CLAUDE_PLUGIN_DATA}/{brand}/seo/gsc-ai-performance/{date}/02-export.csv" \
       --format json \
       --archive
   ```
   Real flags only: `--brand` (required), `--csv` (path to the GSC export), `--api` (best-effort; Google has not published an AI-report API yet), `--site`, `--format text|json`, `--archive`. There is **no** `summary` subcommand — the script reads the CSV and emits the parsed metrics.
4. **Reconcile against `aeo-audit`** — synthetic queries from `/digital-marketing-pro:aeo-audit` test what AI engines *might* surface; the GSC report shows what they *actually* surfaced. Significant gaps either way are signals:
   - GSC shows much more than aeo-audit found → your test query set is too narrow; expand it
   - aeo-audit found brand in synthetic results but GSC shows few impressions → low query volume for those topics; redirect AEO effort to higher-volume topics
5. **Opt-out decision** — if any of the following apply, consider the in-SC opt-out toggle:
   - Industry has YMYL / regulatory risk and brand E-E-A-T isn't fully audited yet
   - Brand's content is paywalled or login-gated (AI surfacing of partial content can damage funnel)
   - Brand is the subject of active reputation management — surfacing in AI answers amplifies whatever sentiment AI models have absorbed
   - Editorial team wants to ship corrections via the brand's own properties first, not via AI synthesis
6. **Run optimization recommendations** — for brands NOT opting out, route to `/digital-marketing-pro:aeo-geo` for the optimization playbook (entity consistency, citation-worthy snippets, knowledge graph alignment).
7. **Set up monthly tracking** — schedule a recurring `gsc-ai-performance` baseline (CSV export → dated archive folder) so trend lines emerge over the next 6–12 months as AI search adoption grows.

## Output

A structured GSC AI performance brief containing:

- **Baseline metrics** — current-period impressions, pages, country mix, device mix
- **Trend analysis** — period-over-period change (where prior data exists)
- **Reconciliation table** — GSC actuals vs `aeo-audit` synthetic results, with gap notes
- **Opt-out recommendation** — explicit opt-in / opt-out decision with rationale grounded in industry profile and brand context
- **Optimization handoff** — list of high-impact topics where the brand is under-cited (route to `aeo-geo`)
- **Tracking cadence** — recommended monthly export schedule, archive path

## Caveats and known limitations (June 2026)

1. **No click data, no CTR, no queries.** The report shows impressions only, with Pages / Countries / Dates / Devices dimensions.
   - GA4's `AI Assistant` channel (rule: medium exactly matches `ai-assistant`) covers referrals from assistants such as ChatGPT, Gemini, Deepseek, Copilot and Grok.
   - Per Google's channel definitions (checked 2026-10-04), it **excludes Google's AI Overviews and AI Mode**, which land in **Organic Search**.
   - So **no first-party tool reports clicks from AI Overviews or AI Mode**. Say so plainly rather than inferring a number. Source: [GA4 default channel group](https://support.google.com/analytics/answer/9756891).
2. **UI only at launch.** No public API. Wait for Google to publish the AI report under the Search Console Search Analytics API (`searchanalytics.query`) before automating against it. Current automation must rely on CSV export + manual upload.
3. **Rolled out worldwide.** The report started UK-first. Google's help page now says "As of August 31, 2026, we've rolled out these insights to all websites worldwide" (checked 2026-10-04). Mark the date you first see data so subsequent month-over-month comparisons start from a real baseline.
4. **Tab placement may move during rollout.** Google often refines the UI in the first 30–60 days. If the exact tab path differs from step 2 above, look anywhere in the Performance > Search results area for "AI", "Generative", "AI Mode", or "AI Overviews" labels.
5. **September 2026 is a measurement break, not necessarily growth.** Multimodal impressions (Lens, Circle to Search, image uploads) began being counted in September 2026. Before reporting a month-over-month jump, re-run the comparison with the multimodal filter excluded — otherwise a counting change reads as a visibility gain.
6. **Don't compare AI Overviews impressions to classic SERP impressions one-for-one.** AI Overviews surface differently — an "impression" there means your page was used as a grounding source, which is a stricter bar than appearing in a 10-blue-link result.

## Agents used

- `seo-specialist` (primary) — for interpretation and recommendation framing
- `analytics-analyst` — for the GA4 reconciliation when AI Assistant channel data is available
- `brand-guardian` — for the opt-out decision when brand-safety or compliance is in play

## See also

- `/digital-marketing-pro:aeo-audit` — synthetic AI-engine probing
- `/digital-marketing-pro:aeo-geo` — optimization playbook for AI visibility
- `/digital-marketing-pro:analytics-insights` — GA4 AI Assistant channel attribution
- `skills/context-engine/eu-code-of-practice.md` — EU Article 50 transparency context for AI-cited content
- `scripts/gsc-ai-performance.py` — helper script (placeholder until Google publishes API; reads exported CSV today)
