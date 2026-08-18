# Advanced Reporting Guide

Reference knowledge for PDF report generation, dashboard templates, multi-touch attribution, cohort analysis, budget variance reporting, incrementality measurement, and scheduled report automation. Use this when building, delivering, or automating marketing performance reports.

---

## 1. PDF Generation with Brand Theming

### WeasyPrint (HTML/CSS to PDF)

- **Method**: Write report as HTML with inline or linked CSS. Convert to PDF via `weasyprint.HTML(string=html_content).write_pdf(output_path)`
- **Brand CSS integration**:
  - Set `--brand-primary`, `--brand-secondary`, `--brand-accent` as CSS custom properties from brand profile hex values
  - `@font-face` declarations for brand fonts (embed WOFF/WOFF2 or reference system fonts)
  - Page margins: `@page { margin: 2cm; @top-center { content: "Campaign Report — Q1 2026"; font-size: 9pt; } @bottom-right { content: "Page " counter(page) " of " counter(pages); } }`
  - Logo placement: Fixed-position `<img>` in header area. Recommended: 120x40 px for header, 200x60 px for cover page
- **Limitations**: No JavaScript execution (charts must be pre-rendered as images or inline SVGs). Limited CSS Grid support — use Flexbox or table layout for complex structures

### ReportLab (Programmatic PDF)

- **Method**: Build PDF programmatically with `canvas.Canvas` or `SimpleDocTemplate` with Platypus flowables
- **Brand integration**:
  - Register brand colors: `colors.HexColor('#1a73e8')` for primary, secondary, accent
  - Register brand fonts: `pdfmetrics.registerFont(TTFont('BrandFont', 'path/to/font.ttf'))`
  - Page template with logo: `canvas.drawImage('logo.png', x, y, width, height)` in `onPage` callback
  - Headers/footers: Campaign period, confidentiality notice, page numbers via `onPage`/`onPageEnd` hooks
- **Chart embedding**: Generate charts with matplotlib, save as PNG/SVG, embed via `canvas.drawImage` or `Image` flowable

### Brand Asset Integration Checklist

| Asset | Source | Placement |
|---|---|---|
| Logo (primary) | Brand profile `logo_url` | Cover page (centered, 200x60 px), header (left-aligned, 120x40 px) |
| Brand colors | Brand profile `brand_colors` | Headings, chart colors, table headers, accent lines, CTA buttons |
| Fonts | Brand profile or system fallback | Body: 10-11pt, Headings: 14-18pt, Captions: 8-9pt |
| Header text | Dynamic per report | "Monthly Performance Report — [Brand Name] — [Date Range]" |
| Footer text | Static template | "Confidential — Prepared by [Agency/Team Name] — Page X of Y" |
| Cover page | Template | Brand logo, report title, date range, prepared for/by, version |

---

## 2. Report Structure Templates by Audience

### C-Suite Executive Summary (1-2 pages)

1. **Performance headline**: One sentence summarizing the period. "Revenue from marketing grew 23% QoQ, driven by paid search and email."
2. **KPI dashboard**: 3-5 KPIs in large-number format with trend arrows:
   - Revenue attributed to marketing: $X (+Y% vs. prior period)
   - Customer acquisition cost: $X (-Y% vs. prior period)
   - Marketing-sourced pipeline: $X
   - ROAS: X.Xx
   - Net new leads/customers: X
3. **Trend sparklines**: 12-week or 6-month trend line for each KPI. No axis labels — just direction
4. **Strategic highlights**: 2-3 bullet points on what worked, what did not, and what is changing next period
5. **Budget summary**: Planned vs. actual spend. Single row per channel. Total at bottom

### Marketing Team Report (5-10 pages)

1. **Executive summary** (1 page): Same as C-suite format above
2. **Channel performance** (2-3 pages): One section per active channel. Metrics table, trend chart, top performers, underperformers, optimizations made
3. **Campaign deep-dives** (1-2 pages): Major campaigns launched or completed. Performance vs. objectives. Key learnings
4. **A/B test results** (1 page): Tests run, winners, confidence levels, impact estimates. Tests planned for next period
5. **Content performance** (1 page): Top content by traffic, engagement, conversions. Content decay alerts. Publishing cadence vs. plan
6. **Next period plan** (1 page): Priorities, planned campaigns, budget allocation, experiments to run

### Client Report (5-8 pages)

1. **Branded cover page**: Client logo, report title, date range, prepared by
2. **Executive summary** (1 page): Performance vs. agreed objectives. Traffic-light status (green/yellow/red) per objective
3. **Performance by objective** (2-3 pages): Each objective from the SOW gets a dedicated section with KPIs, charts, and commentary
4. **Competitive context** (0.5-1 page): How performance compares to industry benchmarks and competitor movements
5. **Optimizations and learnings** (1 page): What was tested, what was learned, how it informs strategy
6. **Next period plan** (1 page): Planned activities, timeline, expected outcomes
7. **Appendix**: Raw data tables, methodology notes, glossary of terms

---

## 3. Looker Studio Dashboard Templates by Business Model

### SaaS Dashboard

| Section | Metrics | Visualization |
|---|---|---|
| **Revenue** | MRR, ARR, MRR growth rate, expansion MRR, churned MRR, net new MRR | Time series line chart (12 months). Stacked bar for MRR components |
| **Acquisition** | New trials, trial-to-paid conversion rate, CAC, CAC by channel, CAC payback period | Funnel chart (visit→trial→paid). Bar chart for CAC by channel |
| **Retention** | Logo churn rate, revenue churn rate, net revenue retention (NRR), DAU/MAU ratio | Cohort heatmap (monthly cohorts, 12-month retention). Line chart for NRR trend |
| **Engagement** | Activation rate (% completing key action in first 7 days), feature adoption rates, support ticket volume | Bar chart for feature adoption. Funnel for onboarding steps |
| **Unit economics** | LTV, LTV:CAC ratio, gross margin per customer | Scorecard tiles with trend arrows. Scatter plot of LTV vs. CAC by segment |

### eCommerce Dashboard

| Section | Metrics | Visualization |
|---|---|---|
| **Revenue** | Gross revenue, net revenue, AOV, revenue per visitor, revenue by product category | Time series (daily/weekly). Treemap for category revenue share |
| **Traffic** | Sessions, users, new vs. returning, traffic by channel, traffic by device | Stacked area chart by channel. Pie chart for device split |
| **Conversion** | Overall conversion rate, add-to-cart rate, cart abandonment rate, checkout completion rate | Funnel chart (PDP view→add to cart→checkout→purchase). Line chart for CR trend |
| **Product** | Top products by revenue, top by units, top by margin, inventory turnover | Table with sparklines. Bar chart for top 10 products |
| **Paid media** | ROAS by channel, CPA, ad spend, attributed revenue, impression share | Bar chart for ROAS by channel. Waterfall for spend vs. revenue |

### B2B Lead Gen Dashboard

| Section | Metrics | Visualization |
|---|---|---|
| **Pipeline** | MQLs, SQLs, opportunities, pipeline value, closed-won value, velocity (days to close) | Funnel chart (lead→MQL→SQL→opp→closed). Time series for pipeline value |
| **Conversion rates** | Lead→MQL, MQL→SQL, SQL→Opp, Opp→Closed. By channel and by campaign | Horizontal bar chart by stage. Heatmap by channel x stage |
| **Cost efficiency** | CPL, cost per MQL, cost per SQL, cost per opportunity, CAC | Bar chart by channel. Trend line for blended CPL |
| **Content** | Downloads, form fills, webinar registrations, content-attributed pipeline | Table with attribution. Bar chart for top content by pipeline generated |
| **Channel mix** | Lead volume and quality score by channel, budget allocation vs. results | Scatter plot (volume vs. quality). Stacked bar for budget vs. pipeline |

### Agency Multi-Client Dashboard

| Section | Metrics | Visualization |
|---|---|---|
| **Client overview** | Client count, total MRR under management, average retainer size, client health scores | Scorecard tiles. Table with health score color coding (green/yellow/red) |
| **Performance rollup** | Aggregate KPIs across all clients: total leads generated, total revenue attributed, average ROAS | Stacked bar by client. Trend line for aggregate performance |
| **Retainer utilization** | Hours allocated vs. used per client, utilization %, at-risk clients (>90% utilized) | Bar chart per client. Threshold line at 100% |
| **Deliverable tracking** | Deliverables due, completed, overdue. By client and by team member | Gantt-style timeline. Status table with RAG indicators |
| **Client health** | NPS, response time, deliverable on-time rate, performance vs. targets | Radar chart per client. Trend line for portfolio NPS |

---

## 4. Multi-Touch Attribution Methodology

### Model Definitions

| Model | Credit Distribution | Best For | Limitations |
|---|---|---|---|
| **First-touch** | 100% to first interaction | Understanding top-of-funnel channel effectiveness | Ignores all nurturing and closing interactions |
| **Last-touch** | 100% to last interaction before conversion | Understanding bottom-of-funnel closure | Ignores all awareness and nurturing |
| **Linear** | Equal credit to every touchpoint | Simple fairness when no touchpoint is clearly more important | Treats a casual blog visit the same as a product demo |
| **Time-decay** | More credit to recent touchpoints. Typical half-life: 7 days | Sales cycles where later touches matter more | Undervalues early awareness touchpoints |
| **Position-based (U-shaped)** | 40% first touch, 40% last touch, 20% distributed across middle | Balanced view valuing both discovery and conversion | Fixed percentages may not reflect actual influence |
| **W-shaped** | 30% first touch, 30% lead creation, 30% opportunity creation, 10% middle | B2B with defined funnel stages | Requires CRM stage tracking, complex implementation |
| **Data-driven (algorithmic)** | ML model assigns credit based on statistical analysis of all conversion paths | Organizations with sufficient data volume (1,000+ conversions/month) | Black box, requires significant data volume, platform-specific |

### Attribution Data Requirements

- **Cross-channel tracking**: UTM parameters on all links (utm_source, utm_medium, utm_campaign, utm_content, utm_term). Platform pixels on all conversion pages (Meta Pixel, Google tag, LinkedIn Insight Tag). Offline conversion imports for phone calls, in-store visits, events
- **Identity resolution**: First-party cookies for cross-session tracking. Logged-in user IDs where available. CRM email matching for cross-device. Probabilistic matching as fallback (less reliable post-cookie deprecation)
- **Conversion window**: Define the maximum lookback window. Common: 30 days for eCommerce, 90 days for B2B, 7 days for impulse purchases. All touches outside the window are excluded from attribution
- **Assisted conversions**: GA4 provides assisted conversion data natively. For custom attribution, query all touchpoints within the conversion window, not just the converting session

### Attribution Report Output Format

For each channel/campaign:

| Column | Description |
|---|---|
| Channel/Campaign | Name of the marketing channel or campaign |
| First-touch conversions | Conversions attributed under first-touch model |
| Last-touch conversions | Conversions attributed under last-touch model |
| Linear conversions | Conversions attributed under linear model |
| Data-driven conversions | Conversions attributed under algorithmic model (if available) |
| Assisted conversions | Total conversions where this channel appeared in the path but was not the converting touch |
| Assist ratio | Assisted conversions / last-touch conversions. >1.0 = more of an assister; <1.0 = more of a closer |
| Revenue attributed | Revenue credited to this channel under selected model |
| ROAS | Revenue attributed / spend for this channel |

---

## 5. Cohort Analysis Frameworks

### Time-Based Cohorts

- **Acquisition cohort**: Group users by the week or month they first converted (signed up, purchased, subscribed). Track behavior over subsequent periods
- **Standard retention table**: Rows = cohort (acquisition period), Columns = period since acquisition (Week 0, Week 1, ..., Week 12). Cells = % of cohort still active/retained
- **Metric options**: Active users (logged in), retained revenue (still paying), repeat purchase rate, feature usage

### Behavioral Cohorts

| Cohort Basis | Segments | Analysis Purpose |
|---|---|---|
| **First purchase category** | By product category of first order | Does first purchase predict LTV and repeat purchase behavior? |
| **Acquisition channel** | Organic, paid search, social, email, referral | Which channels produce highest-retaining customers? |
| **First feature used** | By first meaningful feature interaction | Does onboarding path predict retention? |
| **Initial order value** | $0-25, $25-50, $50-100, $100+ | Does initial spend predict lifetime value? |
| **Engagement level at signup** | High (5+ actions in first session), Medium (2-4), Low (1) | Does early engagement predict retention? |

### Retention Curve Analysis

- **Week-over-week retention**: Plot % retained at each period. Normal pattern: steep initial drop (Week 0→1), gradual decline, then flattening (stabilization)
- **Stabilization point**: The period at which retention flattens (typically Week 8-12 for SaaS, Week 4-6 for eCommerce). Users retained beyond this point are likely long-term
- **Cohort comparison**: Overlay retention curves from different cohorts. Are newer cohorts retaining better than older ones? If yes, product/onboarding improvements are working
- **Intervention impact**: Compare retention curves before and after a specific change (lifecycle email introduced, onboarding flow redesigned). Measure delta at each period

---

## 6. Budget Variance and Incrementality Reporting

### Budget Variance Report Structure

| Column | Description |
|---|---|
| Channel | Marketing channel (Google Ads, Meta Ads, Email, Content, SEO, etc.) |
| Planned spend | Budget allocated for the period |
| Actual spend | Amount spent to date |
| Variance ($) | Actual - Planned |
| Variance (%) | (Actual - Planned) / Planned x 100 |
| Pacing | On-track, Underspent (>10% below pace), Overspent (>10% above pace) |
| Planned results | Target KPI (leads, revenue, conversions) for the budget |
| Actual results | Actual KPI delivered |
| Efficiency variance | Actual CPA/ROAS vs. planned CPA/ROAS |

### Pacing Analysis

- **Daily run rate**: Actual spend / days elapsed. Compare to required run rate (remaining budget / remaining days)
- **Projection**: If current pace continues, what will total spend be? Flag if projected total exceeds budget by >5%
- **Underspend alert**: If a channel is pacing >15% under budget by mid-period, flag for investigation. Common causes: ad approval delays, low search volume, audience saturation, paused campaigns
- **Overspend alert**: If a channel is pacing >10% over budget, flag immediately. Common causes: bid strategy aggressiveness, unexpected auction competition, campaign duplication

### Incrementality Reporting

**Geo-Lift Test Design**:
1. Select treatment and control geographic regions with similar baseline metrics (population, revenue, demographics)
2. Run marketing activity in treatment regions only for 4-8 weeks
3. Measure conversion lift in treatment vs. control regions
4. Calculate incremental conversions = treatment conversions - (control conversions x scale factor)
5. Incremental ROAS = incremental revenue / marketing spend in treatment regions

**Holdout Analysis**:
1. Randomly hold out 10-20% of audience from a campaign or channel
2. Measure conversion rate in exposed group vs. holdout group
3. Incrementality = (exposed CR - holdout CR) / exposed CR
4. Example: Exposed CR = 5%, Holdout CR = 3%, Incrementality = 40% (40% of conversions were truly incremental)

**Incrementality-Adjusted ROAS**:
- Standard ROAS = total attributed revenue / spend
- Incremental ROAS = (attributed revenue x incrementality %) / spend
- Example: Standard ROAS = 5.0x, incrementality = 40%, Incremental ROAS = 2.0x. This reflects the true return on ad spend

---

## 7. Scheduled Report Automation

### Cron-Style Scheduling Configuration

| Report Type | Schedule | Delivery Time | Data Freshness |
|---|---|---|---|
| Daily pulse | Every weekday | 8:00 AM recipient timezone | Previous day (midnight cutoff) |
| Weekly summary | Every Monday | 9:00 AM recipient timezone | Previous 7 days (Mon-Sun) |
| Monthly review | 3rd business day of month | 10:00 AM recipient timezone | Previous calendar month |
| Quarterly business review | 5th business day of quarter | 10:00 AM recipient timezone | Previous quarter |
| Ad-hoc / triggered | On event (campaign end, budget threshold, anomaly detection) | Within 1 hour of trigger | Real-time or near-real-time |

### Delivery Channel Configuration

| Channel | Format | Payload | Notes |
|---|---|---|---|
| **Email** | PDF attachment + HTML summary in body | Subject: "[Brand] [Report Type] — [Date Range]". Body: 3-5 key metrics inline. Attachment: full PDF report | Track email open to confirm receipt |
| **Slack** | Message blocks with inline metrics + PDF link | Channel or DM. Use Block Kit for formatted metrics. Upload PDF to thread. Pin important reports | Use Slack webhooks or API for programmatic delivery |
| **Google Drive** | PDF uploaded to shared folder | Folder structure: `Reports/{Brand}/{Year}/{Report Type}/`. Filename: `{Brand}_{Report}_{DateRange}.pdf` | Share notification via Drive or separate email |
| **Google Slides** | Slide deck in shared Drive | Template deck updated with fresh data. New deck per period. Old decks archived | Best for QBRs and client presentations |

### Error Handling for Report Automation

| Error | Detection | Response |
|---|---|---|
| **Data source unavailable** | API timeout or error response during data pull | Retry 3x with exponential backoff (1min, 5min, 15min). If all fail, send partial report with "[Data unavailable]" placeholder and alert owner |
| **Data freshness issue** | Timestamp check — data is older than expected | Include warning banner: "Data as of [timestamp]. [Source] data may be delayed." Proceed with stale data rather than blocking report |
| **Rendering failure** | PDF generation throws exception | Fall back to plain-text email with key metrics. Log error for debugging. Alert owner |
| **Delivery failure** | Email bounce, Slack API error, Drive permission error | Retry delivery 2x. If persistent, alert owner via alternate channel. Log failure in execution tracker |
| **Anomaly in data** | Metric values outside expected range (>3 standard deviations) | Include anomaly callout in report. Do not suppress anomalous data. Flag for human review |

---

## 8. Data Visualization Best Practices

### Chart Type Selection Guide

| Data Relationship | Chart Type | When to Use |
|---|---|---|
| **Comparison** (items) | Horizontal bar chart | Comparing 5+ categories by a single metric (e.g., revenue by channel) |
| **Comparison** (time) | Vertical bar chart or grouped bar | Comparing values across discrete time periods (monthly revenue by channel) |
| **Trend** | Line chart | Showing change over continuous time (daily traffic, weekly revenue) |
| **Composition** | Stacked bar or 100% stacked bar | Showing parts of a whole over time (channel mix as % of total) |
| **Composition** (static) | Pie/donut chart | Parts of a whole at a single point in time. Use only with 2-5 categories |
| **Correlation** | Scatter plot | Relationship between two variables (spend vs. revenue per campaign) |
| **Distribution** | Histogram or box plot | Spread of values (deal size distribution, time-to-convert distribution) |
| **Flow/Conversion** | Funnel chart | Sequential stages with drop-off (lead→MQL→SQL→closed) |
| **Ranking** | Horizontal bar (sorted) | Top/bottom performers (top 10 keywords by traffic) |
| **Geospatial** | Choropleth map | Performance by region (revenue by state, traffic by country) |

### Accessibility and Design Standards

- **Colorblind-safe palettes**: Use palettes distinguishable by colorblind users. Avoid red-green combinations. Recommended: blue-orange, blue-yellow, or use patterns/shapes alongside color
- **Contrast ratios**: Text on colored backgrounds must meet WCAG AA (4.5:1 for normal text, 3:1 for large text)
- **Progressive disclosure**: Start with summary metrics (scorecards, KPI tiles). Then trend charts. Then detailed tables. Allow drill-down from summary to detail
- **Annotation conventions**: Mark important events on time series charts (campaign launch, algorithm update, seasonal event). Use vertical lines with labels. Keep annotations to 3-5 per chart maximum
- **Data labels**: Include direct data labels on bar charts when there are fewer than 10 bars. Avoid labels on line charts (use tooltips or legend). Always label axes with units
- **Consistent scales**: When comparing charts side by side, use the same Y-axis scale. When scales must differ, clearly indicate the difference
- **White space**: Do not overcrowd dashboards. One key insight per visual. Maximum 6-8 visualizations per dashboard page
