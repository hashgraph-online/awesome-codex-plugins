# Sentiment Monitoring — Setup & Reporting

> Continuous monitoring of how your brand, competitors, and industry are perceived across the internet. Early detection of sentiment shifts is the difference between proactive reputation management and crisis firefighting.

---

## Tool Recommendations & Comparison

| Tool | Best For | Price Range | Key Strengths | Limitations |
|------|----------|-------------|---------------|-------------|
| **Brandwatch** | Enterprise, deep analytics | $800-3,000+/mo | AI-powered sentiment, historical data, image recognition | Complex setup, premium pricing |
| **Mention** | SMBs, real-time alerts | $49-199/mo | Easy setup, real-time monitoring, influencer identification | Limited historical data |
| **Talkwalker** | Enterprise, visual analytics | $800-2,500+/mo | Image/video recognition, 150M sources, crisis detection | Steep learning curve |
| **Google Alerts** | Basic monitoring, free tier | Free | Zero cost, email delivery, Google index coverage | No sentiment scoring, limited sources, delays |
| **Sprout Social** | Social-first brands | $249-499/mo | Social listening + management in one, good UX | Primarily social channels |
| **Meltwater** | PR teams, media monitoring | $500-2,000+/mo | Broadcast/print/online media, PR analytics | Media-focused, less social depth |
| **Brand24** | Mid-market, value option | $79-399/mo | Good sentiment AI, discussion volume charts, alerts | Smaller source database |
| **Hootsuite Insights** | Existing Hootsuite users | Add-on pricing | Integrated with Hootsuite workflow | Dependent on Hootsuite subscription |

### Selection Framework

| If your priority is... | Choose... |
|------------------------|-----------|
| Budget-conscious basic monitoring | Google Alerts + Brand24 |
| Social media-centric brand | Sprout Social or Mention |
| Enterprise-grade analytics and AI | Brandwatch or Talkwalker |
| PR and media relations focus | Meltwater |
| All-in-one social management + listening | Sprout Social or Hootsuite Insights |

---

## Alert Configuration

### Keyword Categories to Monitor

**Category 1: Brand Terms**
| Keyword Type | Examples | Priority |
|-------------|----------|----------|
| Brand name (exact) | "{{company_name}}" | Critical |
| Brand name (misspellings) | Common typos, abbreviations | High |
| Product names | Each product/service name | High |
| Branded hashtags | #YourBrand, #YourCampaign | High |
| Domain name | yourcompany.com | Medium |
| CEO / executive names | "{{CEO name}}" | High |
| Branded slogans/taglines | "Just Do It" | Medium |

**Category 2: Competitor Terms**
| Keyword Type | Examples | Priority |
|-------------|----------|----------|
| Competitor brand names | Top 3-5 competitors by name | Medium |
| Competitor product names | Direct competing products | Medium |
| "{{brand}} vs {{competitor}}" | Comparison queries | High |
| Competitor executive names | Their CEO, CMO | Low |

**Category 3: Industry & Category**
| Keyword Type | Examples | Priority |
|-------------|----------|----------|
| Industry terms + "best" | "best CRM software" | Medium |
| Category terms + "review" | "project management tool reviews" | Medium |
| Industry trend terms | Emerging terminology in your space | Low |
| Regulatory terms | Compliance changes affecting your industry | Medium |

**Category 4: Crisis Triggers**
| Keyword Type | Examples | Priority |
|-------------|----------|----------|
| "{{brand}}" + negative terms | "{{brand}} scam", "{{brand}} lawsuit" | Critical |
| "{{brand}}" + media terms | "{{brand}} investigation", "{{brand}} report" | Critical |
| Data/security terms | "{{brand}} breach", "{{brand}} hack" | Critical |
| Employee terms | "{{brand}} layoffs", "{{brand}} toxic" | High |

---

## Sentiment Scoring Methodology

### Automated Sentiment Classification

| Score Range | Label | Definition | Example |
|-------------|-------|-----------|---------|
| 0.8 - 1.0 | Very Positive | Enthusiastic praise, strong recommendation | "Absolutely love this product, best purchase I've made!" |
| 0.5 - 0.79 | Positive | General satisfaction, mild praise | "Good product, works as expected." |
| 0.2 - 0.49 | Neutral | Factual mention, no clear sentiment | "I bought their product last week." |
| -0.2 - 0.19 | Mixed | Contains both positive and negative elements | "Great features but the support is terrible." |
| -0.5 - -0.21 | Negative | Dissatisfaction, complaint | "Disappointed with the quality, not worth the price." |
| -1.0 - -0.51 | Very Negative | Anger, outrage, intent to harm brand | "This company is a scam, DO NOT buy from them." |

### Manual Sentiment Calibration

Automated tools are typically 70-85% accurate. Improve accuracy with:

1. **Train the model:** Most tools allow you to correct misclassified mentions — do this weekly for the first month
2. **Context rules:** Create rules for sarcasm-heavy industries (e.g., gaming, fashion)
3. **Weight by reach:** A negative mention from someone with 500K followers matters more than one from 50
4. **Exclude noise:** Filter out job postings, stock tickers, unrelated name matches

---

## Reporting Templates

### Daily Alert Report (Email / Slack)

```
DAILY SENTIMENT ALERT — {{date}}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Mentions: {{count}}
Sentiment: {{positive}}% Pos / {{neutral}}% Neut / {{negative}}% Neg
Sentiment Trend: {{up/down/stable}} vs. 7-day average

⚠ ALERTS REQUIRING ACTION:
1. [{{severity}}] {{mention summary}} — Source: {{platform}} — Reach: {{number}}
2. [{{severity}}] {{mention summary}} — Source: {{platform}} — Reach: {{number}}

📈 NOTABLE POSITIVE:
1. {{positive mention summary}} — Source: {{platform}} — Reach: {{number}}

Full dashboard: {{link}}
```

### Weekly Digest Report

| Section | Content |
|---------|---------|
| Executive Summary | 2-3 sentence overview of the week's sentiment landscape |
| Volume Metrics | Total mentions, week-over-week change, channel breakdown |
| Sentiment Breakdown | Positive/neutral/negative split with trend arrows |
| Top Positive Mentions | Top 5 by reach, with links |
| Top Negative Mentions | Top 5 by reach, with links and response status |
| Competitor Comparison | Side-by-side sentiment vs. top 3 competitors |
| Emerging Topics | New themes or topics gaining traction |
| Action Items | Recommended responses, content opportunities, escalations |

### Monthly Report

| Section | Content |
|---------|---------|
| 30-Day Trend Analysis | Sentiment trendline chart, volume chart |
| Channel Performance | Sentiment by channel (social, news, reviews, forums) |
| Competitive Benchmarking | Share of voice, sentiment comparison, key competitor moves |
| Theme Analysis | Top 10 themes/topics driving mentions, sentiment per theme |
| Influencer Activity | Key influencers mentioning brand (positive and negative) |
| Campaign Impact | Sentiment lift/dip correlated with marketing campaigns |
| Crisis Log | Any incidents, severity, response time, resolution |
| Recommendations | Strategic recommendations for next month |

---

## Competitive Benchmarking

### Share of Voice Dashboard

| Metric | Your Brand | Competitor A | Competitor B | Competitor C |
|--------|-----------|-------------|-------------|-------------|
| Total Mentions | | | | |
| Share of Voice % | | | | |
| Avg. Sentiment Score | | | | |
| Positive Mention % | | | | |
| Negative Mention % | | | | |
| Top Channel | | | | |
| Trending Topics | | | | |

### Competitive Sentiment Tracking Process
1. Set up identical monitoring queries for each competitor
2. Normalize volume by brand size (mentions per $1M revenue or per 1K customers)
3. Track sentiment weekly in a shared dashboard
4. Flag significant competitor sentiment shifts (product launch, crisis, campaign)
5. Report quarterly competitive sentiment trends to leadership

---

## Trend Detection & Early Warning System

### Early Warning Indicators

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Mention volume spike | >200% of daily average | Investigate source immediately |
| Negative sentiment spike | >150% of daily negative average | Alert community manager, prepare holding statement |
| New negative hashtag | Any new hashtag with >50 uses in 24hrs | Classify severity, brief crisis team |
| Media pickup | Brand mentioned in 3+ news outlets same day | Alert PR team |
| Executive mention spike | >300% of normal for named individual | Alert executive and PR team |
| Competitor attack | Competitor brand mentions yours negatively | Assess and prepare counter-narrative |

### Trend Analysis Cadence

| Timeframe | What to Analyze | Who Reviews |
|-----------|----------------|-------------|
| Real-time | Crisis triggers, volume spikes | Community Manager (automated alerts) |
| Daily | Sentiment shifts, top mentions | Community Manager |
| Weekly | Theme emergence, competitor moves | Marketing Manager |
| Monthly | Long-term trends, campaign correlations | VP Marketing |
| Quarterly | Strategic shifts, market perception changes | CMO / Leadership |

---

## Escalation Rules

| Condition | Escalation Level | Timeline | Action |
|-----------|-----------------|----------|--------|
| Single negative mention, low reach (<1K) | Level 0 — No escalation | Handle within 24 hrs | CM responds per template |
| Negative mention, high reach (>10K) | Level 1 — Manager | Handle within 4 hrs | Manager reviews response before publishing |
| Multiple negative mentions, trending topic | Level 2 — Crisis Team | Handle within 2 hrs | Activate Tier 2 crisis protocol |
| Media coverage, legal implications | Level 3 — Executive | Handle within 1 hr | Activate Tier 3 crisis protocol (see `crisis-communication.md`) |
| Positive viral mention (>100K reach) | Level 1 — Opportunity | Handle within 2 hrs | Amplify, engage, leverage for UGC |

---

## Setup Checklist

- [ ] Select and subscribe to monitoring tool(s) based on selection framework above
- [ ] Configure all keyword categories (brand, competitor, industry, crisis triggers)
- [ ] Set up alert routing (email, Slack, SMS) by priority level
- [ ] Calibrate sentiment model with 50+ manually classified mentions
- [ ] Create reporting templates in your BI tool or monitoring platform
- [ ] Assign daily monitoring responsibility to specific team member
- [ ] Configure escalation rules with notification routing
- [ ] Set up competitive tracking for top 3-5 competitors
- [ ] Schedule weekly digest and monthly report delivery
- [ ] Conduct first baseline measurement (current sentiment scores and volume)

---

> **You cannot manage what you do not measure.** Sentiment monitoring is not optional — it is the nervous system of your reputation management practice. Set it up once, maintain it continuously, and act on what it tells you.
