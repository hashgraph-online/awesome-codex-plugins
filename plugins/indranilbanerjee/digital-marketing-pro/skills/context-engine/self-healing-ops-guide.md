# Self-Healing Campaign Operations Guide — Automated Monitoring & Correction

## Overview

Self-healing operations automatically detect campaign issues and apply corrections within predefined safety guardrails. The system continuously monitors active campaigns, scores their health, identifies anomalies, and either auto-corrects low-risk issues or escalates high-risk situations for human review.

```
Monitor → Detect → Diagnose → Decide (auto-correct or escalate) → Act → Log → Learn
```

The goal is not to replace human judgment but to catch and fix mechanical failures (broken landing pages, budget overspend, deliverability drops) before they waste significant budget, while flagging strategic issues (audience shift, competitive pressure, algorithm changes) for human decision-making.

---

## Campaign Health Scoring

### Methodology

Every active campaign receives a 0–100 health score, recalculated on each monitoring cycle. Scores are weighted by campaign type because different objectives have different critical metrics.

### Awareness Campaign Weights

| Metric | Weight | Healthy (80–100) | Warning (50–79) | Critical (0–49) |
|---|---|---|---|---|
| **Reach pacing** | 30% | Within 10% of target | 10–25% off target | >25% off target |
| **CPM efficiency** | 25% | At or below target CPM | 1–1.5x target CPM | >1.5x target CPM |
| **Brand safety** | 20% | 0 violations | 1–2 minor violations | Any major violation |
| **Frequency management** | 15% | Avg frequency 2–4x/week | 5–7x/week | >7x/week (fatigue risk) |
| **Viewability** | 10% | 70%+ viewable | 50–69% viewable | <50% viewable |

### Conversion Campaign Weights

| Metric | Weight | Healthy (80–100) | Warning (50–79) | Critical (0–49) |
|---|---|---|---|---|
| **CPA / ROAS** | 35% | At or better than target | 1–1.5x target CPA | >1.5x target CPA |
| **Conversion volume pacing** | 25% | Within 15% of daily target | 15–35% off target | >35% off target |
| **Landing page health** | 20% | 200 OK, <3s load time | 200 OK, 3–5s load time | Non-200, >5s, or broken |
| **Quality score** | 10% | 7+ (Google), relevant (Meta) | 5–6 (Google), moderate | <5 (Google), low relevance |
| **Budget pacing** | 10% | 90–110% of daily target | 60–89% or 111–120% | <60% or >120% |

### Retention Campaign Weights (Email/CRM)

| Metric | Weight | Healthy (80–100) | Warning (50–79) | Critical (0–49) |
|---|---|---|---|---|
| **Open / Click rates** | 30% | Above industry avg | At industry avg | >30% below avg |
| **Unsubscribe rate** | 20% | <0.2% per send | 0.2–0.5% per send | >0.5% per send |
| **Deliverability** | 20% | >95% inbox placement | 90–95% placement | <90% placement |
| **Engagement depth** | 15% | Multiple clicks, forwards | Single click | Opens only, no clicks |
| **List health** | 15% | <2% bounce rate | 2–5% bounce rate | >5% bounce rate |

### Health Score Thresholds

| Score | Status | System Response |
|---|---|---|
| **80–100** | Healthy | Monitor only — no action needed |
| **60–79** | Warning | Increase monitoring frequency, prepare recommendations |
| **40–59** | Degraded | Auto-correct within guardrails, alert operator |
| **20–39** | Critical | Auto-pause affected elements, escalate immediately |
| **0–19** | Emergency | Full campaign pause, incident response initiated |

---

## Issue Detection Patterns

### Landing Page Monitoring

| Check | Method | Frequency | Failure Threshold |
|---|---|---|---|
| **HTTP status** | HEAD request to landing page URL | Every 15 minutes | Non-200 response |
| **Page load time** | Full page load measurement | Every 30 minutes | >5 seconds |
| **Render verification** | Check for key page elements (form, CTA, product) | Every 30 minutes | Missing critical elements |
| **SSL certificate** | Certificate validity check | Daily | Expiring within 7 days or expired |
| **Redirect chain** | Follow redirects, check final URL | Every 30 minutes | >3 redirects or redirect to error page |

**Impact of broken landing pages:** A non-functional landing page wastes 100% of ad spend directed to it. This is the highest-priority detection — every other metric is irrelevant if users cannot reach the destination.

### Email Deliverability Monitoring

| Check | Threshold | Diagnosis |
|---|---|---|
| **Bounce rate spike** | >3% on single send (from baseline <1%) | List hygiene issue or blocklisting |
| **Spam folder placement** | >10% going to spam (seed test) | Authentication failure or content issue |
| **DKIM failure** | Any DKIM failure on sent emails | DNS misconfiguration or key rotation needed |
| **SPF failure** | Any SPF failure | Sending IP not in SPF record |
| **DMARC failure** | Any DMARC failure | DKIM or SPF not aligned with From domain |
| **Open rate collapse** | >40% drop from 7-day moving avg | Deliverability issue or list fatigue |

### Pacing Analysis

| Condition | Signal | Likely Cause |
|---|---|---|
| **Overspending** (>120% daily budget) | Spend accelerating beyond plan | Auction dynamics, bid too high, new competition |
| **Underspending** (<60% daily budget) | Spend velocity too low | Targeting too narrow, bid too low, ad disapprovals |
| **Front-loaded** (50%+ budget spent in first 25% of day) | Morning spike | Dayparting not set, accelerated delivery enabled |
| **Stalled** (no spend for 2+ hours during business hours) | Zero delivery | Ad disapproved, payment issue, audience exhausted |

### Engagement Anomalies

| Anomaly | Detection Rule | Possible Cause |
|---|---|---|
| **CTR drop >30%** | CTR falls below 70% of 7-day moving average | Creative fatigue, audience saturation, seasonal |
| **CPC spike >40%** | CPC exceeds 140% of 7-day moving average | Auction competition increase, quality score drop |
| **Conversion rate collapse** | CVR drops >50% from baseline | Landing page issue, tracking broken, offer changed |
| **Unusual traffic pattern** | CTR high but CVR near zero | Click fraud or bot traffic |
| **Frequency overexposure** | Avg frequency >7x/week | Audience too small for budget, no frequency cap |

---

## Auto-Correction Guardrails

### Default Safety Limits

These define what the system can do WITHOUT human approval:

| Action | Allowed Automatically | Limit |
|---|---|---|
| **Pause individual ads** | Yes | Any ad with health score <30 |
| **Pause ad sets** | Yes, if all ads within are paused | Only when all child ads qualify |
| **Reduce bid** | Yes | Up to 15% reduction per cycle |
| **Throttle daily budget** | Yes | Up to 20% reduction per cycle |
| **Pause campaign (landing page down)** | Yes | Immediate if non-200 for 2 consecutive checks |
| **Resume campaign (landing page restored)** | Yes | After 2 consecutive healthy checks, at 80% of original bid |
| **Swap to next creative variant** | No | Requires approval |
| **Increase budget** | No | Always requires approval |
| **Change targeting** | No | Always requires approval |
| **Pause entire account** | No | Always requires approval |
| **Change bidding strategy** | No | Always requires approval |

### Guardrail Configuration

Guardrails are configurable per brand at `~/.claude-marketing/brands/{slug}/guardrails.json`:

```json
{
  "auto_pause_threshold": 30,
  "max_bid_reduction_pct": 15,
  "max_budget_throttle_pct": 20,
  "landing_page_check_interval_min": 15,
  "landing_page_failure_threshold": 2,
  "resume_at_bid_pct": 80,
  "creative_swap_auto": false,
  "budget_increase_auto": false,
  "require_approval_for": ["targeting_change", "bidding_strategy_change", "account_pause", "budget_increase"]
}
```

---

## Correction Types by Risk Level

| Risk Level | Correction | When Applied | Reversibility |
|---|---|---|---|
| **Lowest** | Pause individual ad | Ad health <30, creative fatigue detected | Re-enable manually |
| **Low** | Reduce bid (up to 15%) | CPC spike, overspend pacing | Bid can be raised again |
| **Low** | Throttle daily budget (up to 20%) | Overspend pacing, CPA exceeding target | Budget can be restored |
| **Medium** | Budget shift between ad sets | One ad set outperforming another significantly | Rebalance manually |
| **Medium** | Creative swap | Creative fatigue (CTR decline >20% from peak) | Rotate back if needed |
| **High** | Pause entire campaign | Landing page down, account-level issue | Resume after investigation |
| **Highest** | Pause entire account | Payment failure, policy violation, suspected fraud | Requires full human review |

---

## Self-Healing vs Alerting Decision Matrix

| Signal Clarity | Correction Risk | Action |
|---|---|---|
| **Clear signal** (e.g., landing page 404) + **Low-risk correction** (pause campaign) | Low | **Auto-heal** — execute and notify |
| **Clear signal** + **High-risk correction** (change targeting) | High | **Alert** — recommend correction, wait for approval |
| **Ambiguous signal** (e.g., gradual CTR decline) + **Low-risk correction** | Low | **Alert** — notify with data, suggest investigation |
| **Ambiguous signal** + **High-risk correction** | High | **Alert** — escalate with full diagnostic report |
| **Multiple simultaneous issues** | Any | **Alert** — possible systemic problem, human review required |
| **External factor suspected** (platform outage, algorithm change) | Any | **Alert** — gather evidence, do not auto-correct |

### Decision Rule

```
Auto-heal ONLY when ALL of these are true:
  1. Diagnostic signal is unambiguous (clear metric threshold breach)
  2. Correction is low-risk (pause, throttle, minor bid reduction)
  3. Correction is fully reversible
  4. Correction falls within configured guardrails
  5. No other simultaneous issues detected on the same campaign

Otherwise → Alert with recommendation and wait for approval
```

---

## Audit Trail

Every auto-correction is logged with complete context for review and reversal.

### Log Entry Structure

```json
{
  "timestamp": "2026-02-13T14:30:00Z",
  "campaign_id": "camp_abc123",
  "ad_set_id": "adset_def456",
  "ad_id": "ad_ghi789",
  "issue_detected": "landing_page_down",
  "diagnostic_evidence": {
    "http_status": 503,
    "consecutive_failures": 2,
    "last_healthy_check": "2026-02-13T14:00:00Z",
    "page_url": "https://example.com/offer"
  },
  "correction_applied": "campaign_paused",
  "expected_impact": "Zero ad spend until landing page restored",
  "reversal_instructions": "Resume campaign after landing page returns 200 for 2 consecutive checks. Set bid to 80% of pre-pause level for first 6 hours.",
  "approval_status": "auto_approved_within_guardrails",
  "health_score_before": 35,
  "health_score_after": null
}
```

Logs stored at `~/.claude-marketing/brands/{slug}/ops-log.json` and surfaced via `/digital-marketing-pro:campaign-status` and `/digital-marketing-pro:anomaly-scan` commands.

---

## Platform-Specific Health Checks

### Google Ads

| Check | Frequency | Critical Threshold | Action |
|---|---|---|---|
| Quality Score monitoring | Daily | Drop >2 points on high-spend keywords | Alert with keyword-level detail |
| Ad disapprovals | Every 30 min | Any new disapproval | Pause ad, alert with policy violation detail |
| Policy violations | Every 30 min | Any violation | Pause affected ad, escalate |
| Auction insights shift | Weekly | Impression share drop >15% | Alert with competitor analysis |
| Search term waste | Daily | >20% spend on irrelevant search terms | Alert with negative keyword recommendations |

### Meta Ads

| Check | Frequency | Critical Threshold | Action |
|---|---|---|---|
| Relevance / Quality score | Daily | Score drops to "Below Average" | Alert with creative refresh recommendation |
| Frequency vs fatigue | Daily | Frequency >5 and CTR declining | Auto-pause ad, alert for creative swap |
| Learning phase detection | After edits | Campaign re-enters learning phase | Alert — do not make further changes for 48h |
| Account spending limit | Daily | Within 10% of limit | Alert to increase limit before campaigns pause |
| Audience overlap | Weekly | >30% overlap between ad sets | Alert with consolidation recommendation |

### Email Campaigns

| Check | Frequency | Critical Threshold | Action |
|---|---|---|---|
| Deliverability score | Per send | Score <90 | Alert with authentication check |
| Bounce classification | Per send | Hard bounce >1% | Auto-suppress bounced addresses, alert |
| Engagement metrics | Per send | Open rate <50% of prior 5-send avg | Alert with subject line / list analysis |
| List decay rate | Weekly | >2% invalid addresses per month | Alert with list cleaning recommendation |
| Spam trap hits | Per send | Any spam trap hit | Alert immediately — potential blocklist risk |

### LinkedIn Ads

| Check | Frequency | Critical Threshold | Action |
|---|---|---|---|
| Bid competitiveness | Daily | Suggested bid >2x current bid | Alert with bid adjustment recommendation |
| Audience saturation | Weekly | Frequency >8 (small audience) | Alert — expand audience or reduce budget |
| Lead form completion rate | Daily | Drop >30% from baseline | Alert — check form length, fields, mobile experience |
| Content engagement rate | Daily | Engagement rate <0.3% | Alert with creative refresh recommendation |

---

## Escalation Workflow

### Tier Structure

| Tier | Trigger | System Action | Human Action Required |
|---|---|---|---|
| **Tier 1** | Single issue, within guardrails | Auto-correct, log, notify via summary | Review next ops report (no immediate action) |
| **Tier 2** | Single issue, exceeds guardrails | Alert with specific recommendation | Approve, modify, or reject recommendation |
| **Tier 3** | Multiple simultaneous issues on same campaign | Full campaign pause (auto), incident report | Review incident, diagnose root cause, approve recovery plan |
| **Tier 4** | Account-level issue (payment, policy, widespread failure) | All campaigns paused (auto), incident escalation | Full human investigation, contact platform support if needed |

### Escalation Timing

- **Tier 1:** Auto-corrected immediately. Summary in next `/digital-marketing-pro:campaign-status` report.
- **Tier 2:** Alert sent immediately. Auto-escalates to Tier 3 if no response within 4 hours.
- **Tier 3:** Alert sent immediately with "URGENT" flag. Campaigns remain paused until human responds.
- **Tier 4:** Alert sent immediately. All activity halted. No auto-resume at any tier for Tier 4 events.

---

## Recovery Patterns

### After Auto-Pause (Landing Page Down)

```
1. Campaign auto-paused at detection
2. Landing page monitoring continues at normal interval
3. Landing page returns 200 OK for 2 consecutive checks (30 min apart)
4. System auto-resumes campaign at 80% of pre-pause bid
5. Monitor for 6 hours at elevated frequency
6. If healthy for 6 hours → restore original bid
7. If issue recurs within 6 hours → re-pause and escalate to Tier 2
```

### After Budget Throttle

```
1. Daily budget reduced by up to 20%
2. Monitor spend pacing and CPA for 24 hours
3. If pacing normalizes → gradual ramp: +5% per day until original budget
4. If issue persists → maintain throttled budget, escalate for human review
5. Full budget restoration takes 4–5 days (conservative ramp)
```

### After Creative Swap (When Approved)

```
1. Fatigued creative paused, next variant activated
2. New creative enters evaluation period (24 hours minimum)
3. Monitor CTR, CPC, and CVR vs campaign average
4. If new creative performs within 80% of campaign avg → confirm and continue
5. If new creative underperforms → alert with recommendation to test additional variants
6. Old creative enters 7-day cooldown before re-eligible for rotation
```

### After Deliverability Issue (Email)

```
1. Affected send flagged, future sends to affected segment paused
2. Run authentication diagnostics (DKIM, SPF, DMARC)
3. If authentication issue found → alert with fix instructions, pause all sends
4. If list quality issue → run list cleaning, remove bounced/unengaged
5. After fix applied → send small test batch (1,000 addresses)
6. If test batch delivers >95% to inbox → resume normal sending
7. If test batch still fails → escalate to Tier 3 for ISP investigation
```

---

## Continuous Learning

The self-healing system improves over time by recording what worked:

- **False positive tracking:** When an auto-correction was unnecessary (metric dip was transient), log it and adjust thresholds
- **Correction effectiveness:** Track whether health score improved after each correction. If not, the correction type may be wrong for that issue pattern.
- **Threshold calibration:** Review thresholds quarterly. Tighten thresholds that catch real issues. Loosen thresholds that generate noise.
- **Pattern library:** Build a library of issue → diagnosis → correction patterns. New patterns are added from Tier 2/3 incidents after human resolution.

> **Key principle:** Self-healing operations exist to protect budget and maintain campaign health during the hours when no human is watching. The system should be conservative — it is always better to pause and preserve budget than to attempt a risky correction that could make things worse. When in doubt, pause and escalate.
