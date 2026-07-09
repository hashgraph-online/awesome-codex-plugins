---
name: intelligence-report
description: "Generate marketing intelligence briefings from compound intelligence across agents — surfaces learnings, cross-agent patterns, confidence distribution, and playbooks. Use when reviewing accumulated marketing learnings, preparing for quarterly planning, onboarding team members, or identifying knowledge gaps."
user-invocable: true
triggers:
  - generate marketing intelligence report
  - summarize what we've learned
  - cross-agent marketing patterns
  - marketing intelligence briefing
  - compound learning report
  - review marketing playbooks
  - quarterly marketing intelligence
  - what patterns have we identified
---

# /digital-marketing-pro:intelligence-report

## Purpose

Generate a comprehensive intelligence briefing from the brand's compound intelligence system. This command surfaces the accumulated knowledge that agents have built over time — total learnings captured, confidence distribution across insights, top patterns identified across agents and channels, actionable playbooks generated from proven strategies, and intelligence base health metrics showing where the knowledge is strong and where gaps exist. The intelligence report turns raw accumulated data into strategic advantage by synthesizing cross-agent patterns that no single agent would surface alone. Use it for quarterly planning, strategy reviews, onboarding new team members to a brand's marketing intelligence, or identifying which areas need more experimentation and data collection to strengthen decision-making confidence.

## Input Required

The user must provide (or will be prompted for):

- **Focus area (optional)**: A specific channel (email, paid search, social), audience segment, campaign objective (awareness, conversion, retention), or strategic theme to deep-dive. If provided, the report prioritizes patterns, playbooks, and recommendations for that focus area while still including the full intelligence base overview. If omitted, the report covers all dimensions equally
- **Playbook request (optional)**: A specific scenario to generate an actionable playbook for — e.g., "Q2 product launch on paid social", "re-engagement campaign for churned subscribers", or "brand awareness push in new market". The intelligence system synthesizes relevant learnings into a step-by-step playbook grounded in proven patterns from this brand's data

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand positioning, channel mix, campaign history, and strategic objectives. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Get intelligence stats**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/intelligence-graph.py" --brand {slug} --action get-stats` to retrieve the intelligence base overview — total learnings captured, learnings by agent and channel, confidence score distribution (high, moderate, low), date range of intelligence, and most recent learning timestamp.
3. **Get cross-agent patterns**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/intelligence-graph.py" --brand {slug} --action get-patterns --dimension channel` (repeat with `--dimension audience` and `--dimension objective`) for key dimensions — channel performance patterns, audience response patterns, timing and seasonality patterns, creative and messaging patterns, and budget efficiency patterns. If a focus area was specified, weight pattern retrieval toward that dimension. Identify patterns that span multiple agents (e.g., a timing pattern confirmed by both the email specialist and social media manager).
4. **Generate playbooks**: If a playbook request was provided, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/intelligence-graph.py" --brand {slug} --action export-playbook --channel {channel} --min-confidence 0.6` to synthesize the highest-confidence learnings for that channel into a step-by-step actionable playbook. (There is no free-text `--scenario` filter — interpret the requested scenario to choose the `--channel`, then build the narrative around the returned learnings.) Each playbook step references the specific learnings and confidence levels that support it. If no playbook was requested, generate a summary of the top three available playbooks based on the strongest pattern clusters.
5. **Identify stale learnings**: Flag learnings that have not been revalidated within their recommended revalidation window — typically 90 days for tactical insights, 180 days for strategic patterns. Stale learnings may still be accurate but their confidence should be discounted. Prioritize revalidation recommendations by impact — stale high-impact learnings get flagged first.
6. **Calculate compound intelligence score**: Compute an overall intelligence maturity score based on total learnings volume, average confidence level, cross-agent pattern density, recency of intelligence, coverage across channels and audiences, and ratio of validated to unvalidated learnings. Score on a 0-100 scale with tier labels — Emerging (0-25), Developing (26-50), Established (51-75), Advanced (76-100).

## Output

A structured intelligence briefing containing:

- **Intelligence base health**: Total learnings captured, breakdown by agent and channel, average confidence score, confidence distribution (percentage at high, moderate, low), date range of intelligence coverage, most recent and oldest learning timestamps, and coverage gaps where channels or audiences have insufficient data
- **Top patterns by channel, audience, and objective**: The highest-confidence cross-agent patterns organized by dimension — what consistently works on each channel, which audiences respond to what approaches, and which objectives have proven playbooks versus which need more experimentation
- **Actionable playbooks**: Step-by-step playbooks for the requested scenario or the top three strongest available playbooks — each step grounded in specific learnings with confidence levels, expected outcomes based on historical patterns, and risk factors to monitor
- **Stale learnings needing revalidation**: Learnings past their revalidation window ranked by impact — with recommended revalidation methods (re-run the test, check latest analytics, update with new campaign data) and estimated effort for each
- **Compound intelligence score**: The 0-100 maturity score with tier label, breakdown by scoring component, trend versus previous assessment, and specific actions to improve the score — e.g., "Run email subject line tests to fill the email optimization gap" or "Validate Q3 social timing patterns with current data"
- **Recommendations for strengthening the intelligence base**: Prioritized list of experiments, analyses, and data collection activities that would most improve intelligence coverage, confidence, and actionability — the highest-ROI investments in marketing knowledge

## Agents Used

- **intelligence-curator** — Cross-agent pattern synthesis and identification of multi-source confirmed insights, playbook generation from proven pattern clusters with confidence-weighted step sequencing, intelligence base health assessment with coverage gap analysis, stale learning identification and revalidation prioritization, compound intelligence score calculation with component breakdown, and strategic recommendations for intelligence base improvement
