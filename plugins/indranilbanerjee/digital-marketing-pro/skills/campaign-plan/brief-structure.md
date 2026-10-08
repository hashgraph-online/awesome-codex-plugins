# Campaign plan — brief structure, follow-ups, and dispatch rules

Read this when you are about to write the plan document (section skeleton), offer next steps after delivering it, or fan out per-channel work in parallel. It supplements `SKILL.md`; the brand-loading and shared-reference steps there are authoritative.

## Discovery detail (ask before proceeding if missing)

- **Campaign goal** — drive signups, increase awareness, launch a product, generate leads, re-engage churned users, drive event registrations.
- **Budget** is optional. If it is not provided, generate a channel-agnostic plan and note where budget allocation would matter.
- **Additional context** (optional): key differentiators or value propositions, previous campaign performance or learnings, geographic focus or market, channel constraints or preferences, compliance requirements.
- If a brand profile exists, reuse its personas instead of asking for them again.

## The 10-section campaign brief

### 1. Campaign Overview
- Campaign name suggestion
- One-sentence campaign summary
- Primary objective with a specific, measurable goal (SMART format)
- Secondary objectives (if applicable)

### 2. Target Audience
- Primary audience segment with targeting parameters
- Secondary segment (if applicable)
- Pain points, motivations, and buying triggers
- Channel affinity — where this audience spends time
- Buying stage alignment (awareness, consideration, decision)

### 3. Key Messages
- Core campaign message (one sentence)
- 3-4 supporting messages aligned to audience pain points
- Message variations by channel (if different tones needed)
- Proof points or evidence supporting each message

### 4. Channel Strategy
Recommend channels based on audience behavior, budget, and objective. For each channel:
- Why this channel fits the audience and objective
- Content format recommendations
- Estimated effort level (low, medium, high)
- Expected performance benchmarks for the industry
- Budget allocation (if budget provided)

Channel categories to evaluate:
- **Owned**: blog, email, website, social profiles, newsletter
- **Earned**: PR, influencer partnerships, guest posts, community
- **Paid**: search ads, social ads, display, sponsored content, retail media

If analytics or advertising connectors are available, reference historical performance data to inform channel recommendations.

### 5. Content Calendar
Week-by-week (or day-by-day for short campaigns) content plan:

| Week | Content Piece | Channel | Format | Owner/Notes | Dependencies |
|------|--------------|---------|--------|-------------|--------------|

Include key milestones, launch dependencies, and approval checkpoints.

### 6. Content Assets Required
List every content asset needed:
- Asset name and type (blog, email, social, ad creative, landing page, video, etc.)
- Brief description
- Priority (must-have vs. nice-to-have)
- Production timeline

### 7. Budget Allocation (if budget provided)
- Channel-by-channel breakdown
- Production costs vs. distribution/ad spend
- Contingency recommendation (10-15%)

### 8. Success Metrics

| KPI | Target | Measurement Method | Reporting Cadence |
|-----|--------|--------------------|-------------------|

- Primary KPI with target number
- 3-5 secondary KPIs
- Attribution approach
- Reporting frequency

### 9. Risks and Mitigations
- 2-3 potential risks (timeline, audience mismatch, channel underperformance)
- Mitigation strategy for each

### 10. Next Steps
- Immediate action items to kick off
- Stakeholder approvals needed
- Key decision points

## After planning

Ask: "Would you like me to:
- Draft specific content pieces from the calendar? (`/digital-marketing-pro:content-engine`)
- Create the email sequences? (`/digital-marketing-pro:email-sequence`)
- Build the media plan with budget pacing? (`/digital-marketing-pro:media-plan`)
- Set up competitor monitoring for the campaign period? (`/digital-marketing-pro:competitor-monitor`)
- Design the landing page copy? (`/digital-marketing-pro:content-engine`)"

## Execution discipline — parallel dispatch

Campaign planning has a strict dependency order at the top (objectives → audience → channel mix) but **fans out to independent per-channel work** once the channel mix is approved. After channel selection, dispatch per-channel briefs in **one message with parallel `Task` calls** — paid ads, email, social, content, PR, partnerships each get their own subagent.

Same pattern for the measurement layer: KPI tree, attribution model, anomaly detection thresholds, and reporting cadence are independent — dispatch in parallel after the channel briefs are scoped.

The **budget allocation step must be sequential** — it consumes per-channel ROI estimates and produces a single allocation that the per-channel briefs then reference.
