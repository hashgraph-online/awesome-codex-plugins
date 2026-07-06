# Team Roles Framework — Permissions, Workflows & Capacity

How the Digital Marketing Pro plugin manages team roles, approval chains, cross-team workflows, regional operations, and capacity planning for agency and in-house marketing teams.

---

## Section 1: Role Definitions

| Role | Default Permissions | Channels | Approval Level | Typical Capacity |
|---|---|---|---|---|
| **agency-admin** | All permissions | All channels | Critical | 10 tasks/week (management overhead) |
| **brand-manager** | All except credential management | All channels | High | 15 tasks/week |
| **content-lead** | publish-blog, schedule-social, content-repurpose, video-script | Content channels (blog, social, video) | Medium | 20 tasks/week |
| **media-buyer** | launch-ad-campaign, budget-tracker, retargeting-strategy | Paid channels (Google, Meta, LinkedIn, TikTok, Amazon) | Medium | 15 tasks/week |
| **email-manager** | send-email-campaign, segment-audience, ab-test-plan | Email channel | Medium | 20 tasks/week |
| **social-manager** | schedule-social, review-response | Social channels (all platforms) | Medium | 25 tasks/week |
| **analytics-lead** | performance-check, anomaly-scan, data-export, exec-summary | All channels (read-only) | Medium | 15 tasks/week |
| **seo-specialist** | tech-seo-audit, local-seo-audit, keyword-research, publish-blog (SEO review) | Organic channel (search, blog) | Low | 18 tasks/week |
| **cro-specialist** | ab-test-plan, form analysis, landing page review | Website channel | Low | 15 tasks/week |
| **growth-engineer** | martech-audit, lead-import, pipeline-update | Cross-channel | Low | 12 tasks/week |

---

## Section 2: Permission Matrix

Full permissions grid. "Yes" = permitted, "---" = not permitted.

| Role | publish-blog | send-email | launch-ad | schedule-social | crm-write | approve-low | approve-medium | approve-high | approve-critical | manage-credentials | manage-team | view-portfolio | export-data |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **agency-admin** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| **brand-manager** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | --- | --- | Yes | Yes | Yes |
| **content-lead** | Yes | --- | --- | Yes | --- | Yes | Yes | --- | --- | --- | --- | --- | Yes |
| **media-buyer** | --- | --- | Yes | --- | --- | Yes | Yes | --- | --- | --- | --- | --- | Yes |
| **email-manager** | --- | Yes | --- | --- | --- | Yes | Yes | --- | --- | --- | --- | --- | Yes |
| **social-manager** | --- | --- | --- | Yes | --- | Yes | Yes | --- | --- | --- | --- | --- | Yes |
| **analytics-lead** | --- | --- | --- | --- | --- | Yes | --- | --- | --- | --- | --- | Yes | Yes |
| **seo-specialist** | Yes | --- | --- | --- | --- | Yes | --- | --- | --- | --- | --- | --- | Yes |
| **cro-specialist** | --- | --- | --- | --- | --- | Yes | --- | --- | --- | --- | --- | --- | Yes |
| **growth-engineer** | --- | --- | --- | --- | Yes | Yes | --- | --- | --- | --- | --- | --- | Yes |

---

## Section 3: Approval Chains by Risk Level

| Risk Level | Examples | Approver | Escalation |
|---|---|---|---|
| **Low** | Social post, blog comment reply, internal report | Any team member with relevant channel permission | Single approval sufficient |
| **Medium** | Blog publish, email campaign send, ad launch, social campaign | Channel lead (content-lead for blog, email-manager for email, media-buyer for ads, social-manager for social) | If no channel lead assigned, brand-manager approves |
| **High** | Budget change > 20%, new channel launch, competitor response, crisis communication draft | Brand-manager must approve | In agency context, account director (brand-manager role) approves |
| **Critical** | Budget change > 50%, legal/compliance sensitive content, public apology, brand pivot | Agency-admin must approve | For regulated industries, compliance review required before admin approval (two-step) |

**Emergency override:** Agency-admin can override any approval chain with a documented reason. All overrides are logged to the audit trail with: override reason, original approver, timestamp, and content reference.

**Approval timeout:** If no action is taken within 24 hours (configurable per brand), the request escalates to the next level. Critical approvals do not auto-escalate — they block until explicitly approved.

---

## Section 4: Cross-Team Workflows

Documented handoff patterns that define how work flows between roles.

### Content Pipeline

```
Brief (strategist) → Draft (content-lead) → SEO Review (seo-specialist) → Brand Review (brand-manager) → Publish (execution-coordinator) → Monitor (analytics-lead)
```

| Step | Owner | Input | Output | SLA |
|---|---|---|---|---|
| Brief | Strategist / brand-manager | Campaign goals, audience, key messages | Content brief with keywords, tone, CTA | 1 business day |
| Draft | content-lead | Content brief | Draft content (blog, social, email) | 2-3 business days |
| SEO Review | seo-specialist | Draft content | SEO-optimized draft with keyword placement, internal links, meta data | 1 business day |
| Brand Review | brand-manager | SEO-reviewed draft | Approved or revision notes | 1 business day |
| Publish | Execution coordinator | Approved content | Published content with tracking | Same day |
| Monitor | analytics-lead | Published content | Performance report at 7d, 30d, 90d | Ongoing |

### Campaign Launch

```
Strategy (strategist) → Creative (content-lead) → Audience (media-buyer) → Budget Approval (brand-manager) → Launch (execution-coordinator) → Optimize (media-buyer) → Report (analytics-lead)
```

### Lead Nurture

```
Capture (growth-engineer) → Score (automation) → Segment (email-manager) → Nurture Sequence (email-manager) → Sales Handoff (crm-manager) → Close (sales/CRM) → Report (analytics-lead)
```

### Crisis Response

```
Detect (performance-monitor) → Alert (slack notification) → Assess (brand-manager) → Pause Campaigns (media-buyer) → Draft Response (content-lead) → Approve (agency-admin) → Execute (execution-coordinator)
```

**Crisis SLA:** Detection to assessment within 1 hour. Assessment to response execution within 4 hours. All active paid campaigns paused within 30 minutes of assessment.

---

## Section 5: Regional Management

### Hierarchy

Regions are organized in a three-tier hierarchy: **Region** → **Market** → **Locale** (e.g., APAC → Japan → ja-JP).

### Per-Region Settings

| Setting | Description | Example |
|---|---|---|
| Timezone | Primary timezone for scheduling | `America/New_York`, `Asia/Tokyo` |
| Primary language | Default content language | `en-US`, `ja-JP`, `pt-BR` |
| Compliance ruleset | Applicable privacy/ad regulations | GDPR, CCPA, CASL, PDPA |
| Preferred platforms | Prioritized channels for the region | Google, Meta, LINE, WeChat |
| Currency | Reporting and budget currency | USD, EUR, JPY, BRL |
| Business hours | Standard working hours | 9:00-18:00 local |

### Platform Preferences by Region

| Region | Primary Platforms | Notes |
|---|---|---|
| **North America** | Google, Meta, LinkedIn, Twitter/X, TikTok | English primary, Spanish secondary. CAN-SPAM + CCPA/state laws. |
| **Europe** | Google, Meta, LinkedIn, Instagram | GDPR compliance mandatory. Multi-language required (minimum: English + local). |
| **APAC** | Google, LINE (Japan), WeChat/Weibo (China), KakaoTalk (Korea), Meta | Localization critical. Platform preferences vary dramatically by market. |
| **LATAM** | Google, Meta, WhatsApp, Instagram, TikTok | Portuguese (Brazil), Spanish (rest). WhatsApp is a primary marketing channel. |
| **MEA** | Google, Meta, Instagram, TikTok, Snapchat | Arabic RTL support required. Local holiday calendar critical (Ramadan, Eid). |

### Timezone-Aware Scheduling

- All scheduled content uses the brand's region timezone, not UTC
- Quiet hours for SMS/push: 9 PM - 8 AM local time (never send during quiet hours)
- South Korea nighttime marketing restriction: 9 PM - 8 AM local (legal requirement under PIPA)
- Cross-region campaigns: schedule per-region deliveries at each region's optimal time
- Use `send-time-optimizer.py --brand {slug} --region {region}` for timezone-adjusted recommendations

---

## Section 6: Capacity Planning

### Task Weights

| Task Type | Weight (units) | Typical Duration | Frequency |
|---|---|---|---|
| Blog post | 3 | 2-4 hours | 2-4x/month |
| Social post (per platform) | 1 | 30 min | 3-7x/week |
| Email campaign | 4 | 3-5 hours | 2-4x/month |
| Ad campaign setup | 8 | 4-8 hours | 1-2x/month |
| Ad optimization cycle | 2 | 1-2 hours | 2-3x/week |
| Report (weekly pulse) | 1 | 30 min (auto-generated) | Weekly |
| Report (monthly review) | 4 | 3-4 hours | Monthly |
| QBR preparation | 10 | 8-12 hours | Quarterly |
| SEO audit | 6 | 4-6 hours | Monthly |
| CRM data import | 3 | 1-3 hours | As needed |
| Landing page review | 2 | 1-2 hours | Per campaign |
| A/B test analysis | 2 | 1-2 hours | Per test |

### Utilization Thresholds

| Utilization | Status | Action |
|---|---|---|
| < 70% | Available | Available for new work, can take on additional brands |
| 70-85% | Optimal | Sustainable pace, quality output expected |
| 85-95% | Near Capacity | Flag to brand-manager — defer non-urgent work, no new brands |
| > 95% | Overloaded | Reassign tasks immediately, escalate to agency-admin |

### Auto-Assignment

When assigning tasks, `team-manager.py --action check-capacity` recommends the best team member based on:

1. **Role match** — Does the team member's role cover the required permissions?
2. **Channel expertise** — Is this their primary or secondary channel?
3. **Current utilization** — Are they below the 85% threshold?
4. **Region alignment** — Do they cover the target market's timezone and language?
5. **Historical performance** — Have they completed similar tasks successfully before?

```bash
python team-manager.py --action check-capacity --task-type "email-campaign" --region "europe" --weight 4
```

Output: Ranked list of available team members with utilization percentages and fit scores.

---

## Section 7: Executive Reporting

### KPI Rollup Hierarchy

```
Channel Metrics → Brand Aggregate → Portfolio Summary
```

| Level | Metrics | Audience | Frequency |
|---|---|---|---|
| **Channel** | Platform-specific KPIs (CTR, CPC, open rate, impressions) | Channel leads | Weekly |
| **Brand** | Blended CAC, ROAS, pipeline contribution, engagement rate | Brand-manager | Monthly |
| **Portfolio** | Total Marketing ROI, weighted CAC, LTV:CAC ratio, market share | Agency-admin / C-suite | Quarterly |

### C-Suite Metrics

| Metric | Definition | Target Benchmark |
|---|---|---|
| Total Marketing ROI | (Revenue attributed to marketing - Marketing spend) / Marketing spend | > 3:1 for B2B SaaS, > 4:1 for eCommerce |
| Customer Acquisition Cost (CAC) | Total marketing + sales spend / New customers acquired | Industry-dependent (see industry-profiles.md) |
| Customer Lifetime Value (LTV) | Average revenue per customer x Average lifespan | LTV:CAC ratio > 3:1 |
| Market Share (estimated) | Share of voice + share of search + share of social | Trending upward quarter-over-quarter |
| Brand Health Score | Composite: NPS + brand awareness + sentiment + share of voice | > 70/100 |

### Executive Summary Format

One-page summary generated by `/digital-marketing-pro:exec-summary`:

| Section | Content | Length |
|---|---|---|
| Headline KPIs | 5 metrics with trend arrows (up/down/flat vs. prior period) | 5 lines |
| Top 3 Wins | Highest-impact positive results with specific numbers | 3 bullet points |
| Top 3 Risks | Issues requiring attention with recommended actions | 3 bullet points |
| Channel Performance | Mini-table: channel, spend, revenue, ROI, trend | 5-8 rows |
| Detailed Appendix | Full data tables, campaign-level breakdowns, methodology notes | Attached |

**Delivery:** The `/digital-marketing-pro:exec-summary` command orchestrates three agents: `agency-operations` (portfolio context), `analytics-analyst` (data and metrics), and `marketing-strategist` (insights and recommendations). Output is formatted for Google Slides or Google Sheets export via MCP.
