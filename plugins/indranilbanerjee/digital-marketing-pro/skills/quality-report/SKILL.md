---
name: quality-report
description: "Generate quality trends report. Use when: reviewing eval scores over time, content type performance, or regression alerts."
---

# /digital-marketing-pro:quality-report

## Purpose

Quality intelligence reporting over time. Shows eval score trends across days and weeks, identifies which content types are improving or declining, detects regression alerts where quality has dropped below established baselines, surfaces the brand's best and worst performing content, and provides actionable recommendations for improving content quality across the organization.

This command turns the evaluation data logged by /digital-marketing-pro:eval-content into strategic insight. Instead of evaluating a single piece of content, it analyzes the pattern across all evaluations to answer: Is our content quality improving or declining? Which content types are strongest? Which dimensions need the most work? Are there regressions we need to address? What specific changes will have the biggest impact on overall quality?

## Input Required

The user must provide (or will be prompted for):

- **Time period** (optional): The reporting window — `7d`, `14d`, `30d`, `60d`, `90d`, or a custom date range (`YYYY-MM-DD to YYYY-MM-DD`). Defaults to 30 days. Longer periods provide better trend visibility but may include outdated data from before process changes
- **Content type filter** (optional): Focus the report on a specific content type — `blog_post`, `email`, `ad_copy`, `social_post`, `landing_page`, `press_release`, `content_brief`, `campaign_plan`, or `all`. Defaults to all types. Useful for drilling into a specific content stream's quality trajectory
- **Dimension focus** (optional): Zoom in on a specific scoring dimension — `content_quality`, `brand_voice`, `hallucination_risk`, `claim_verification`, `output_structure`, `readability`, or `all`. Defaults to all dimensions. Useful when the team is working on improving a specific quality aspect

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand quality standards and industry context for benchmark comparison. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load any quality targets or SLA definitions. Check for agency SOPs at `~/.claude-marketing/sops/` — agency workflows may define minimum quality thresholds for client deliverables. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Pull quality trends**: Execute `scripts/quality-tracker.py --brand {slug} --action get-trends --days {period}` to retrieve time-series evaluation data — composite scores and per-dimension scores plotted over the reporting window. If a content type filter is applied, pass `--content-type {content_type}`. This returns daily and weekly aggregates, moving averages, and trend direction indicators.
3. **Pull quality summary**: Execute `scripts/quality-tracker.py --brand {slug} --action get-summary --days {period}` to retrieve aggregate statistics — total evaluations run, average composite score, grade distribution (how many A's, B's, C's, etc.), pass/fail/review breakdown, and per-dimension averages with standard deviations.
4. **Check for regressions**: Execute `scripts/quality-tracker.py --brand {slug} --action check-regression --days {period}` to detect statistically significant quality drops. The regression detector compares the most recent 7-day average against the full-period baseline and flags any dimension or content type where quality has declined by more than one standard deviation. Each regression alert includes the severity (minor, moderate, severe), the dimension or content type affected, the baseline value, the current value, and the trend direction.
5. **Pull best and worst content**: Execute `scripts/quality-tracker.py --brand {slug} --action get-best --days {period} --limit 5` and `scripts/quality-tracker.py --brand {slug} --action get-worst --days {period} --limit 5` to retrieve the highest and lowest scoring evaluations in the period. These provide concrete examples that illustrate what good and poor quality looks like for this brand.
6. **Analyze patterns**: Synthesize the trend data, summary statistics, regression alerts, and best/worst examples to identify actionable patterns:
   - Which content types consistently score highest and lowest — and what differentiates them
   - Which dimensions are the brand's strengths and weaknesses — and how that maps to common issues
   - Whether quality is trending up, stable, or declining — and what inflection points correlate with (process changes, team changes, new templates, guideline updates)
   - What the best-performing content has in common versus the worst-performing content
   - Whether there are day-of-week or volume effects (quality drops when more content is produced)
7. **Generate recommendations**: Based on the pattern analysis, produce specific, prioritized recommendations for improving quality. Each recommendation includes the issue it addresses, the expected impact (which dimension and how much), the suggested action (process change, template update, training focus, tool configuration), and a concrete example. Reference `skills/context-engine/eval-rubrics.md` for dimension-specific improvement strategies.
8. **Format as executive-ready report**: Structure the output for both quick scanning (executive summary with key metrics) and detailed review (full trend data, regression details, recommendations with rationale).

## Output

A structured quality intelligence report containing:

- **Executive summary**: 3-5 bullet overview — total evaluations in the period, average composite score with grade, quality trend direction (improving/stable/declining with percentage change), number of regression alerts, and the single most impactful recommendation
- **Overall quality metrics**: Total evaluations run, average composite score, median composite score, standard deviation, grade distribution (count and percentage for each letter grade), pass/fail/review breakdown (count and percentage), and comparison to previous period (if data exists)
- **Weekly trend chart**: Text-based visualization showing composite score by week across the reporting period — formatted as a simple ASCII chart or structured table with weekly averages, highs, lows, and evaluation counts. Includes a trend line indicator (ascending, flat, descending) and week-over-week change percentages
- **Content type leaderboard**: Ranked table of content types by average composite score — showing content type, evaluation count, average composite, grade, best dimension, worst dimension, and trend direction. Highlights which content types are improving fastest and which are declining
- **Dimension performance breakdown**: For each of the six scoring dimensions — average score, trend direction, number of failures (below threshold), most common issues, and the content types where this dimension scores lowest. If a dimension focus was requested, provide deeper analysis for that dimension including score distribution histogram and failure pattern categorization
- **Regression alerts**: Each regression with severity level (minor/moderate/severe), the affected dimension or content type, the baseline value, the current value, the decline magnitude (in points and percentage), the likely timeframe when the regression began, and potential causes based on correlation with other data points. Sorted by severity — severe regressions first
- **Best performing content**: Top 5 evaluations with content type, composite score, grade, standout dimensions, and what made this content score well — actionable patterns that can be replicated
- **Worst performing content**: Bottom 5 evaluations with content type, composite score, grade, failing dimensions, and the specific issues that dragged scores down — actionable problems to avoid
- **Quality improvement recommendations**: Prioritized list of 3-7 specific recommendations, each with:
  - The issue or pattern it addresses
  - The expected impact (which dimensions improve and by how much)
  - The specific action to take (update a template, configure a threshold, adjust a process, focus training on a dimension)
  - A concrete example or before/after illustration
  - Effort level (quick win, moderate effort, significant investment)
- **Comparison to previous period**: If enough historical data exists, side-by-side comparison of key metrics between the current period and the previous equivalent period — showing improvement or decline across composite score, pass rate, dimension averages, and regression count

## Agents Used

- **quality-assurance** — Quality data retrieval and aggregation from the evaluation log, regression detection using statistical baseline comparison, best/worst content identification with pattern extraction, grade distribution calculation, and trend computation across the reporting window
- **analytics-analyst** — Trend interpretation and pattern analysis across content types and dimensions, correlation identification between quality changes and process or team factors, recommendation generation grounded in data patterns rather than generic advice, executive summary synthesis, and comparative period analysis with statistical context
