# Intelligence Layer — Adaptive Marketing System

## How the Plugin Learns and Adapts

Digital Marketing Pro isn't static — it builds intelligence over time through:

### 1. Brand Context Awareness
Every marketing output is filtered through the active brand's:
- **Voice profile** (formality, energy, humor, authority on 1-10 scales)
- **Industry context** (benchmarks, compliance, channel effectiveness)
- **Business model** (funnel type, KPI framework, growth levers)
- **Goals** (primary objective shapes all recommendations)
- **Competitors** (positioning gaps inform differentiation)

### 2. Adaptive Scoring
Content scoring weights automatically adjust based on:
- **Industry**: Healthcare gets higher spam/compliance weight; tech gets higher SEO weight
- **Business model**: B2C eCommerce prioritizes CTA; B2B Services prioritizes readability
- **Goals**: Lead gen boosts CTA weight; brand awareness boosts readability weight
- **Regulated industries**: Automatic compliance weight increase

Use `adaptive-scorer.py` to compute brand-specific weights before scoring content.

### 3. Campaign Memory
Every campaign plan, performance snapshot, and marketing decision is saved to the brand's directory:
- `~/.claude-marketing/brands/{slug}/campaigns/` — Campaign plans and results
- `~/.claude-marketing/brands/{slug}/performance/` — Performance snapshots over time
- `~/.claude-marketing/brands/{slug}/insights.json` — Marketing learnings and observations

Use `campaign-tracker.py` to save and retrieve campaign data.

### 4. Cross-Session Learning
When making recommendations, always check:
1. **Past campaigns** — What worked before? What channels performed best?
2. **Saved insights** — Any learnings from previous sessions?
3. **Performance trends** — Is performance improving or declining?
4. **Voice samples** — Do we have examples of on-brand content to reference?

### 5. MCP-Enhanced Intelligence
When MCP servers are connected (Google Analytics, Search Console, ad platforms):
- Pull REAL performance data instead of relying on benchmarks
- Validate recommendations against actual metrics
- Detect anomalies in real-time data
- Build reports from live data, not templates

## Decision Framework for Agents

When any agent or module makes a recommendation:

1. **Load brand context** — Always start by checking the active brand profile
2. **Check campaign history** — Reference past campaigns for the same type of work
3. **Apply industry benchmarks** — Use industry-profiles.md data, adjusted for brand specifics
4. **Check compliance** — Auto-apply geographic + industry regulations from brand profile
5. **Adapt scoring** — Use adaptive weights rather than static defaults
6. **Save learnings** — After any significant analysis, save insights for future reference

## Data Persistence Patterns

### Saving Campaign Data
After generating a campaign plan:
```bash
python campaign-tracker.py --brand {slug} --action save-campaign --data '{"name": "...", "channels": [...], "budget": "...", "goals": [...]}'
```

### Saving Performance Snapshots
After generating a performance report:
```bash
python campaign-tracker.py --brand {slug} --action save-performance --data '{"campaign_id": "...", "metrics": {...}, "period": "..."}'
```

### Saving Marketing Insights
After any significant analysis or discovery:
```bash
python campaign-tracker.py --brand {slug} --action save-insight --data '{"type": "learning|benchmark|anomaly|recommendation", "insight": "...", "context": "..."}'
```

### Retrieving Past Data
Before making recommendations:
```bash
python campaign-tracker.py --brand {slug} --action list-campaigns
python campaign-tracker.py --brand {slug} --action get-insights --type learning --limit 10
```
