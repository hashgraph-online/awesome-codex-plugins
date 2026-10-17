# Anomaly Diagnosis — Metric Investigation Framework

## Core Principle

When a metric moves unexpectedly, the first question is never "What happened?" — it is "Is the data correct?" Most apparent anomalies are measurement errors. After confirming data integrity, follow a structured diagnostic tree to isolate root cause before taking action.

---

## Verification Checklist — Run This First

Before investigating any anomaly, complete this checklist to rule out data and tracking issues.

### Data Integrity Checks

- [ ] **Tracking code present** — Verify the tracking pixel/tag is still firing on all relevant pages
- [ ] **Tag manager audit** — Check for recent container changes, paused tags, or version rollbacks
- [ ] **Consent management** — Confirm consent banners are functioning and not blocking tracking
- [ ] **Bot filtering** — Verify bot/spider filtering is active; check for traffic spikes from known bot IPs
- [ ] **Cross-platform reconciliation** — Compare the metric across two independent sources (e.g., GA4 vs platform data vs backend)
- [ ] **Date range alignment** — Ensure comparison periods have equal days and account for holidays or seasonal shifts
- [ ] **Currency / timezone consistency** — Confirm reports use consistent timezone and currency settings
- [ ] **Attribution window** — Check if the attribution window changed (Meta's default shifts, Google Ads attribution model change)
- [ ] **Sampling** — In GA4, check if data is sampled (yellow shield icon); switch to unsampled export if needed
- [ ] **Conversion counting** — Verify conversion counting method (one-per-click vs every conversion) hasn't changed
- [ ] **Server / site uptime** — Check for outages, slow load times, or 500 errors during the anomaly period

### Quick Validation Questions

| Question | If Yes | If No |
|----------|--------|-------|
| Does the anomaly appear in multiple data sources? | Likely real — proceed to diagnosis | Likely a tracking issue — investigate data pipeline |
| Did the anomaly start on a specific date/time? | Check for deployments, config changes, or external events on that date | Gradual drift — look for algorithmic or competitive shifts |
| Is the anomaly isolated to one segment (device, geo, channel)? | Investigate that segment specifically | Sitewide issue — check infrastructure or major external factor |
| Are other metrics moving in expected correlation? | Pattern is consistent — likely a real shift | Broken correlation suggests data error or mixed signals |

---

## Diagnostic Decision Trees

### Traffic Drop Decision Tree

```
Traffic dropped significantly
├── Is tracking working correctly?
│   ├── NO → Fix tracking. Revalidate after fix.
│   └── YES → Continue
├── Is the drop across all channels or one channel?
│   ├── ONE CHANNEL → Go to channel-specific diagnosis
│   │   ├── Organic Search dropped
│   │   │   ├── Check Google Search Console for indexing errors
│   │   │   ├── Check for manual actions or algorithmic update
│   │   │   ├── Check robots.txt and sitemap for changes
│   │   │   ├── Check for ranking losses on high-traffic keywords
│   │   │   └── Check for technical SEO regressions (page speed, crawl errors)
│   │   ├── Paid Search dropped
│   │   │   ├── Check budget pacing (did budget run out?)
│   │   │   ├── Check for paused campaigns/ad groups
│   │   │   ├── Check auction insights for new competitors
│   │   │   ├── Check quality score changes
│   │   │   └── Check for disapproved ads
│   │   ├── Paid Social dropped
│   │   │   ├── Check for ad account issues (policy violations, spending limits)
│   │   │   ├── Check for audience saturation (frequency > 3)
│   │   │   ├── Check for creative fatigue (CTR declining over time)
│   │   │   └── Check for CPM increases (auction competition)
│   │   ├── Email / SMS dropped
│   │   │   ├── Check deliverability (bounce rate, spam complaints)
│   │   │   ├── Check send volume (were fewer campaigns sent?)
│   │   │   └── Check open rate decline (subject line, send time)
│   │   └── Direct / Referral dropped
│   │       ├── Check for lost referral partnerships or broken links
│   │       └── Check for brand search volume decline (Google Trends)
│   └── ALL CHANNELS → Sitewide issue
│       ├── Check for site outage or performance degradation
│       ├── Check for domain / DNS issues
│       ├── Check for major market event or seasonal shift
│       └── Check for Google Analytics configuration change
```

### Conversion Rate Drop Decision Tree

```
Conversion rate dropped
├── Is the tracking pixel firing on the confirmation page?
│   ├── NO → Fix conversion tracking
│   └── YES → Continue
├── Did traffic source mix shift?
│   ├── YES → Lower-intent traffic is diluting CVR; segment analysis needed
│   └── NO → Continue
├── Was there a site change?
│   ├── YES → Check deployment logs
│   │   ├── Checkout flow changed → A/B test or rollback
│   │   ├── Page speed degraded → Performance fix
│   │   ├── Pricing changed → Expected CVR impact; monitor AOV
│   │   └── Design / layout changed → UX investigation
│   └── NO → Continue
├── Is the drop device-specific?
│   ├── Mobile only → Check mobile rendering, forms, payment flow
│   ├── Desktop only → Check for browser-specific issues
│   └── All devices → Continue
├── Is the drop geo-specific?
│   ├── YES → Check regional payment processing, shipping, or compliance issues
│   └── NO → Continue
└── External factors
    ├── Competitor launched promotion or undercut pricing
    ├── Seasonality or macro-economic shift
    └── Platform algorithm change affecting traffic quality
```

### Cost Spike Decision Tree

```
CPA / CPM / CPC spiked
├── Is the cost increase across all campaigns or isolated?
│   ├── ISOLATED → Investigate specific campaign
│   │   ├── Check for audience overlap / self-competition
│   │   ├── Check for bid strategy malfunction
│   │   ├── Check for quality score / relevance score drop
│   │   └── Check for creative fatigue (CTR drop → CPC increase)
│   └── ALL CAMPAIGNS → Platform-level or market-level shift
│       ├── Check for auction competition (new advertiser, Q4 seasonality)
│       ├── Check for platform policy change affecting targeting
│       ├── Check for iOS / privacy update affecting optimization
│       └── Check CPM trends in industry benchmarking tools
├── Did conversion volume also drop?
│   ├── YES → Likely a targeting or quality issue (bad traffic at higher cost)
│   └── NO → May be acceptable if ROAS still within target
└── Action framework
    ├── If ROAS still acceptable → Monitor but don't react
    ├── If ROAS degraded → Reduce spend on worst performers, reallocate
    └── If systemic → Diversify channels, improve organic/owned
```

### Revenue Decline Decision Tree

```
Revenue declined
├── Is the decline in transaction count or average order value?
│   ├── TRANSACTION COUNT → Follow Conversion Rate Drop tree
│   ├── AOV DECLINED
│   │   ├── Check for pricing changes or promotions
│   │   ├── Check product mix shift (more low-price items)
│   │   ├── Check for discount code abuse
│   │   └── Check for bundle / upsell feature breakage
│   └── BOTH → Systemic issue; investigate traffic quality + site experience
├── Is the decline in new customer revenue or returning customer revenue?
│   ├── NEW CUSTOMER → Acquisition issue; check paid channels and landing pages
│   ├── RETURNING CUSTOMER → Retention issue; check email, loyalty, product experience
│   └── BOTH → Market-level concern or major site issue
└── Revenue attribution check
    ├── Is the decline real in backend data (Shopify, Stripe, etc.)?
    ├── Or is it only in the analytics platform (attribution loss)?
    └── If discrepancy → Attribution model or tracking issue, not revenue issue
```

---

## Common Root Causes Table

| Metric | Common Root Cause | Probability | Investigation Step |
|--------|-------------------|-------------|-------------------|
| Traffic drop (all) | Tracking code removed/broken | High | Check tag manager + page source |
| Traffic drop (organic) | Google algorithm update | Medium | Check Search Console + industry chatter |
| Traffic drop (organic) | Robots.txt blocking pages | Medium | Fetch robots.txt and compare to prior version |
| Traffic drop (paid) | Budget exhausted mid-period | High | Check daily spend pacing |
| Traffic drop (paid) | Ad disapprovals | High | Check ad status in platform |
| CVR drop | Site speed regression | Medium | Check Core Web Vitals before/after |
| CVR drop | Checkout bug on specific device | High | Test checkout on all devices + browsers |
| CVR drop | Traffic mix shifted to lower-intent | Medium | Segment CVR by source |
| CPC spike | Seasonal auction pressure (Q4, Black Friday) | High | Check YoY CPC trends |
| CPC spike | Quality Score decline | Medium | Check QS trend and landing page experience |
| CPM spike | New competitor entering auction | Medium | Check auction insights / Ad Library |
| Revenue drop | Inventory / stockout on best sellers | High | Check product availability |
| Revenue drop | Promotion ended (post-promo hangover) | Medium | Compare to promotion calendar |
| ROAS decline | Attribution window change | Medium | Check platform attribution settings |
| Email open rate drop | ISP deliverability issue | Medium | Check by ISP domain in ESP |

---

## Resolution Playbooks

### Playbook: Traffic Recovery

1. Confirm the drop is real (verification checklist complete)
2. Identify the affected channel and segment
3. For paid: check budget, ad status, bid strategy, approval status
4. For organic: check GSC for crawl errors, index coverage, ranking changes
5. For email: check deliverability, send volume, list health
6. Implement fix and monitor recovery for 48-72 hours
7. If no recovery, escalate to channel specialist or platform support
8. Document root cause and update monitoring alerts

### Playbook: Conversion Rate Recovery

1. Confirm tracking integrity on conversion pages
2. Segment CVR by device, geo, source, and landing page
3. Check for site changes in the deployment log
4. Run QA on the full conversion funnel (search → PDP → cart → checkout → confirmation)
5. Test on multiple devices and browsers
6. If site change identified, revert or A/B test the change
7. If traffic quality issue, adjust targeting or bid strategy
8. Monitor CVR for 7 days post-fix to confirm recovery

### Playbook: Cost Optimization

1. Confirm cost spike is not a data lag or reporting error
2. Isolate to specific campaigns, ad sets, or keywords
3. Check for self-competition (audience overlap, keyword cannibalization)
4. Review bid strategy (is automated bidding over-indexing on expensive clicks?)
5. Reduce spend on worst-performing segments by 20-30%
6. Refresh creative if CTR has declined (creative fatigue)
7. Expand audience or keyword set to find cheaper inventory
8. Monitor for 5-7 days and reassess

---

## Alert Configuration Framework

### Recommended Alert Thresholds

| Metric | Alert Type | Threshold | Frequency | Notification |
|--------|-----------|-----------|-----------|-------------|
| Site sessions | Drop | > 20% below 7-day average | Daily | Slack + Email |
| Conversion rate | Drop | > 15% below 30-day average | Daily | Slack + Email |
| Daily revenue | Drop | > 25% below 7-day average | Daily | Slack + Email |
| CPA / CAC | Spike | > 30% above 30-day average | Daily | Slack |
| Ad spend pacing | Overspend | > 110% of daily budget | Daily | Slack |
| Ad spend pacing | Underspend | < 70% of daily budget | Daily | Slack |
| Bounce rate | Spike | > 20% above 30-day average | Daily | Email |
| Page load time (LCP) | Degradation | > 3.0 seconds | Real-time | PagerDuty |
| Email bounce rate | Spike | > 5% on any send | Per send | Slack |
| 404 error rate | Spike | > 50 unique 404s per day | Daily | Slack |

### Alert Design Principles

- [ ] Use percentage deviation from rolling average, not absolute thresholds (accounts for seasonality)
- [ ] Apply day-of-week adjustments for metrics with strong weekly patterns (e.g., B2B traffic dips on weekends)
- [ ] Set a "cool-down" period (4-6 hours) to avoid duplicate alerts for the same issue
- [ ] Require two consecutive data points before triggering (avoids one-off blips)
- [ ] Include direct links to relevant dashboards in every alert message
- [ ] Route alerts to the metric owner, not a shared channel that everyone ignores
- [ ] Review and tune thresholds monthly — if an alert fires more than 3 times/week with no action taken, the threshold is wrong

---

## Investigation Documentation Template

When completing any anomaly investigation, record findings using this format:

| Field | Detail |
|-------|--------|
| **Date detected** | |
| **Metric affected** | |
| **Magnitude** | X% change from baseline |
| **Duration** | Start date — End date (or ongoing) |
| **Root cause** | Confirmed / Hypothesized |
| **Root cause detail** | |
| **Data integrity confirmed?** | Yes / No |
| **Resolution** | |
| **Recovery confirmed?** | Yes / No — Date metric returned to baseline |
| **Prevention** | Alert or process added to prevent recurrence |
| **Documented by** | |
