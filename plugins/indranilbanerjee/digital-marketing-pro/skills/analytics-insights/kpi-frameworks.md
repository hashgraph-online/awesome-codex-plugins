# KPI Frameworks — Business-Model-Specific Metric Trees

## KPI Tree Methodology

A KPI tree is a hierarchical decomposition of business outcomes into measurable, actionable metrics. Every metric in the tree should trace back to a single North Star and forward to a specific team or lever.

### Hierarchy Levels

| Level | Purpose | Owner | Review Cadence |
|-------|---------|-------|----------------|
| **North Star** | Single metric representing core value delivery | CEO / Founder | Weekly |
| **Primary Metrics** | 3-5 metrics that directly drive the North Star | VP / Director | Weekly |
| **Supporting Metrics** | Channel or function-specific drivers of Primary metrics | Manager / Lead | Weekly |
| **Diagnostic Metrics** | Granular inputs investigated when Supporting metrics move | Analyst / Specialist | As needed |

### Building a KPI Tree — Step by Step

1. **Define the North Star** — What single metric, if maximized, would guarantee long-term business health?
2. **Decompose mathematically** — Break the North Star into a formula (e.g., Revenue = Customers x AOV x Frequency)
3. **Assign primary metrics** — Each variable in the formula becomes a primary metric
4. **Layer supporting metrics** — For each primary metric, identify the 2-4 inputs that drive it
5. **Add diagnostics** — For each supporting metric, list the granular signals you would check if it moved unexpectedly
6. **Assign owners** — Every metric gets one owner, never shared
7. **Set targets** — Use historical baselines + industry benchmarks + growth goals

---

## North Star Metric Selection Guide

Your North Star must satisfy all five criteria:

- [ ] **Value-aligned** — It reflects genuine value delivered to customers
- [ ] **Leading** — It predicts long-term revenue, not just measures past revenue
- [ ] **Actionable** — Teams can influence it through their daily work
- [ ] **Measurable** — It can be tracked accurately with existing infrastructure
- [ ] **Simple** — Anyone in the company can understand and recite it

| Business Model | Recommended North Star | Why |
|----------------|----------------------|-----|
| B2B SaaS | Weekly Active Users (qualified) | Predicts retention and expansion better than revenue |
| eCommerce | Revenue per Visitor (RPV) | Combines traffic quality, conversion, and AOV |
| Marketplace | Transactions completed per week | Captures both supply and demand health |
| Local Business | Repeat visit rate (monthly) | Loyalty drives sustainable local economics |
| DTC Brand | 90-day repeat purchase rate | LTV-driven models live or die on repeat behavior |
| Media / Content | Engaged time per user per week | Attention is the product; engagement predicts monetization |

---

## Full KPI Trees by Business Model

### B2B SaaS KPI Tree

**North Star:** Net Revenue Retention (NRR)

| Level | Metric | Definition | Benchmark (Median) | Benchmark (Top Quartile) |
|-------|--------|------------|--------------------|-----------------------|
| Primary | MRR | Monthly Recurring Revenue — sum of all active subscriptions | — | — |
| Primary | ARR | Annual Recurring Revenue — MRR x 12 | — | — |
| Primary | NRR | (Starting MRR + Expansion - Contraction - Churn) / Starting MRR | 100-105% | 115-130% |
| Primary | Gross Margin | (Revenue - COGS) / Revenue | 70-75% | 80-85% |
| Supporting | CAC | Total sales + marketing cost / new customers acquired | Varies by ACV | CAC Payback < 12 mo |
| Supporting | LTV | Average revenue per account x gross margin x avg lifespan | LTV:CAC > 3:1 | LTV:CAC > 5:1 |
| Supporting | Logo Churn | % of customers lost in period | 5-7% annual | < 3% annual |
| Supporting | Revenue Churn | % of MRR lost in period (excluding expansion) | 0.5-1% monthly | < 0.5% monthly |
| Supporting | Expansion Revenue | MRR gained from existing customers (upsell + cross-sell) | 20-30% of new MRR | > 40% of new MRR |
| Diagnostic | Lead Velocity Rate | Month-over-month growth in qualified leads | 10-15% | > 20% |
| Diagnostic | Sales Cycle Length | Days from first touch to closed-won | 30-90 days (SMB) | Decreasing trend |
| Diagnostic | Activation Rate | % of new users completing key onboarding milestone | 40-60% | > 70% |
| Diagnostic | NPS | Net Promoter Score | 30-40 | > 50 |
| Diagnostic | Support Ticket Volume | Tickets per 100 active accounts per month | Decreasing trend | — |

**SaaS Quick Ratios:**
- **Growth Efficiency:** Magic Number = Net New ARR / Sales & Marketing Spend (target > 0.75)
- **Burn Efficiency:** Burn Multiple = Net Burn / Net New ARR (target < 2x)
- **Rule of 40:** Revenue Growth % + Profit Margin % > 40

### eCommerce KPI Tree

**North Star:** Revenue per Visitor (RPV)

| Level | Metric | Definition | Benchmark | Top Quartile |
|-------|--------|------------|-----------|-------------|
| Primary | CVR | Orders / Sessions | 2-3% | > 4% |
| Primary | AOV | Revenue / Orders | Category-dependent | Increasing trend |
| Primary | Sessions | Total website visits | — | — |
| Supporting | Add-to-Cart Rate | Sessions with add-to-cart / Total sessions | 8-12% | > 15% |
| Supporting | Cart Abandonment Rate | Carts abandoned / Carts created | 65-75% | < 60% |
| Supporting | Repeat Purchase Rate | Customers with 2+ orders / Total customers (12-mo) | 25-30% | > 40% |
| Supporting | Average Units per Order | Units sold / Orders | Category-dependent | Increasing trend |
| Diagnostic | Bounce Rate | Single-page sessions / Total sessions | 35-50% | < 30% |
| Diagnostic | Site Speed (LCP) | Largest Contentful Paint | < 2.5s | < 1.5s |
| Diagnostic | Search-to-Purchase Rate | Purchases from search / Total searches | 5-10% | > 15% |
| Diagnostic | Return Rate | Items returned / Items sold | 15-30% (apparel) | < 15% |
| Diagnostic | Email Revenue Share | Revenue from email / Total revenue | 20-30% | > 35% |

### Marketplace KPI Tree

**North Star:** Gross Merchandise Volume (GMV) per Active User

| Level | Metric | Definition | Notes |
|-------|--------|------------|-------|
| Primary | GMV | Total value of transactions on platform | Supply x Demand x Take Rate awareness |
| Primary | Active Buyers (MAU) | Unique buyers transacting in 30 days | Demand-side health |
| Primary | Active Sellers | Unique sellers with at least 1 listing active | Supply-side health |
| Supporting | Liquidity Rate | % of listings that result in a transaction within 30 days | Core marketplace health signal |
| Supporting | Take Rate | Platform revenue / GMV | Balance monetization vs growth |
| Supporting | Time to First Transaction | Days from signup to first buy or sell | Activation quality |
| Diagnostic | Buyer-to-Seller Ratio | Active buyers / Active sellers | Balance indicator |
| Diagnostic | Search-to-Fill Rate | Searches resulting in a transaction | Supply-demand match |
| Diagnostic | Seller Churn | % of sellers inactive after 90 days | Supply retention |

### Local Business KPI Tree

**North Star:** Monthly Repeat Visit Rate

| Level | Metric | Definition | Benchmark |
|-------|--------|------------|-----------|
| Primary | New Customers / Month | First-time visitors or buyers | Growth signal |
| Primary | Repeat Visit Rate | Customers visiting 2+ times in 30 days | 30-40% |
| Primary | Average Transaction Value | Revenue / Transactions | Category-dependent |
| Supporting | Google Business Profile Views | Monthly views on GBP listing | Increasing trend |
| Supporting | Review Rating | Average star rating on Google/Yelp | > 4.3 stars |
| Supporting | Review Volume | New reviews per month | > 5/month |
| Supporting | Walk-in vs Appointment Ratio | Distribution of visit types | Business-specific |
| Diagnostic | Local Search Impression Share | Your impressions / Total local impressions | Increasing trend |
| Diagnostic | Direction Requests | GBP direction clicks per month | Correlates to foot traffic |
| Diagnostic | Phone Call Volume | Calls from GBP per month | — |

### DTC Brand KPI Tree

**North Star:** 90-Day Repeat Purchase Rate

| Level | Metric | Definition | Benchmark | Top Quartile |
|-------|--------|------------|-----------|-------------|
| Primary | First Purchase CAC | Acquisition cost for new customer | Varies by category | < 1/3 of first order AOV |
| Primary | 90-Day Repeat Rate | % of first-time buyers who purchase again within 90 days | 15-25% | > 30% |
| Primary | LTV (12-month) | Total revenue per customer in first 12 months | 2-3x first order AOV | > 4x first order AOV |
| Supporting | Subscription Rate | % of customers on subscription | 15-25% (where applicable) | > 35% |
| Supporting | Blended ROAS | Total revenue / Total ad spend | 3-5x | > 6x |
| Supporting | Email + SMS Revenue % | Revenue from owned channels / Total revenue | 25-35% | > 40% |
| Supporting | Contribution Margin | (Revenue - COGS - Shipping - Ad Spend) / Revenue | 15-25% | > 30% |
| Diagnostic | Post-Purchase NPS | NPS collected 14 days after delivery | > 40 | > 60 |
| Diagnostic | Refund Rate | Refunds / Orders | < 8% | < 3% |
| Diagnostic | UGC Volume | Customer-created content pieces per month | Growing trend | — |

---

## Industry Benchmark Reference Table

| Metric | B2B SaaS | eCommerce | DTC | Marketplace | Source Reliability |
|--------|----------|-----------|-----|-------------|-------------------|
| CAC Payback (months) | 12-18 | 1-3 | 2-6 | 6-12 | High |
| LTV:CAC Ratio | 3:1 - 5:1 | 3:1 - 4:1 | 2.5:1 - 4:1 | 3:1+ | High |
| Gross Margin | 70-85% | 40-60% | 55-75% | 60-80% | High |
| Net Revenue Retention | 100-130% | N/A | N/A | N/A | High |
| Monthly Churn | 0.5-2% | N/A | 5-10% (sub) | 3-5% (sellers) | Medium |
| Organic Traffic Share | 40-60% | 30-50% | 20-35% | 40-60% | Medium |
| Email Open Rate | 20-25% | 15-22% | 18-25% | 15-20% | Medium |
| Paid CAC Trend | Rising 10-15% YoY | Rising 15-25% YoY | Rising 20-30% YoY | Varies | Medium |

---

## Metric Definitions Glossary

| Metric | Abbreviation | Formula | Category |
|--------|-------------|---------|----------|
| Monthly Recurring Revenue | MRR | Sum of all active monthly subscription values | Revenue |
| Annual Recurring Revenue | ARR | MRR x 12 | Revenue |
| Net Revenue Retention | NRR | (Start MRR + Expansion - Contraction - Churn) / Start MRR | Retention |
| Customer Acquisition Cost | CAC | (Sales + Marketing Spend) / New Customers | Acquisition |
| Customer Lifetime Value | LTV | ARPU x Gross Margin x (1 / Churn Rate) | Unit Economics |
| Average Order Value | AOV | Total Revenue / Total Orders | Revenue |
| Conversion Rate | CVR | Conversions / Sessions (or Visitors) | Conversion |
| Return on Ad Spend | ROAS | Revenue from Ads / Ad Spend | Efficiency |
| Cost per Acquisition | CPA | Total Campaign Cost / Conversions | Acquisition |
| Click-Through Rate | CTR | Clicks / Impressions | Engagement |
| Cost per Mille | CPM | (Ad Spend / Impressions) x 1000 | Reach |
| Gross Merchandise Volume | GMV | Total transaction value on platform | Revenue (Marketplace) |
| Revenue per Visitor | RPV | Total Revenue / Total Visitors | Efficiency |
| Contribution Margin | CM | (Revenue - Variable Costs) / Revenue | Profitability |

---

## Implementation Checklist

- [ ] North Star metric selected and validated against five criteria
- [ ] KPI tree built with all four levels populated
- [ ] Every metric has a single owner assigned
- [ ] Benchmarks established (internal baseline + industry)
- [ ] Targets set for current quarter
- [ ] Tracking infrastructure verified for every metric
- [ ] Dashboard built reflecting the tree hierarchy
- [ ] Review cadence established (weekly for Primary/Supporting, monthly for full tree)
- [ ] Alert thresholds configured for Primary and Supporting metrics
- [ ] Documentation shared with all metric owners
