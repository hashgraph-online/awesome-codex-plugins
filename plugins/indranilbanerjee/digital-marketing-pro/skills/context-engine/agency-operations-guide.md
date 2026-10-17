# Agency Operations Guide — Multi-Client Management

This reference defines standard operating procedures for agencies managing multiple client brands through the Digital Marketing Pro plugin. It covers onboarding, portfolio health tracking, SOP frameworks, reporting cadences, cross-client intelligence, credential isolation, and white-labeling rules.

---

## 1. Client Onboarding Workflow

Follow these steps sequentially when onboarding a new client. Estimated total onboarding time: 45-90 minutes depending on integration complexity.

| Step | Action | Command / Tool | Est. Time | Notes |
|---|---|---|---|---|
| 1 | **Create brand profile** | `/digital-marketing-pro:brand-setup` | 10-15 min | Walk through identity, voice, audiences, competitors, goals. Produces `profile.json` at `~/.claude-marketing/brands/{slug}/`. |
| 2 | **Create credential profile** | `/digital-marketing-pro:credential-switch` | 5-10 min | Set up platform API keys and tokens. Stored at `~/.claude-marketing/credentials/{slug}.json`. Never share credentials across brands. |
| 3 | **Connect CRM** | `/digital-marketing-pro:crm-sync` | 5-10 min | Link CRM (HubSpot, Salesforce, Pipedrive). Validate connection with a test query. Import initial contact counts. |
| 4 | **Validate MCP connections** | Manual check | 5-10 min | Test each configured MCP server (analytics, ads, email, search console). Confirm data flows. Log any failed connections for follow-up. |
| 5 | **Assign SOPs from library** | `/digital-marketing-pro:sop-library` | 5 min | Select applicable SOP templates per client's service package (content, paid media, reporting, CRM, SEO). Customize cadences. |
| 6 | **Assign team members** | `/digital-marketing-pro:team-assign` | 5 min | Map roles: account manager, strategist, content creator, media buyer, analyst. Set notification preferences. |
| 7 | **Set up reporting cadence** | Manual configuration | 5 min | Configure: weekly pulse (auto), monthly review (semi-auto), QBR (manual). Set delivery channels (Slack, email, Google Slides). |
| 8 | **Run first campaign audit** | `/digital-marketing-pro:campaign-audit` | 15-25 min | Cross-channel current-state inventory and triage (paid, organic, email, SEO, AEO, CRM, web analytics, compliance posture). Produces a healthy / quick-win / strategic-gap / 🔴 red-flag scoring per item plus an executive summary, saved to `~/Documents/DigitalMarketingPro/{brand}/audits/`. Run this BEFORE proposing anything new for the brand. |
| 9 | **Create baseline metrics snapshot** | `/digital-marketing-pro:performance-check` | 5-10 min | Pull current metrics from all connected platforms. Store as the baseline for future comparison. Record in `performance/baseline-{date}.json`. |

### Post-Onboarding Verification Checklist

- [ ] Brand profile complete (all required fields populated)
- [ ] Credentials stored and validated (no exposed secrets)
- [ ] At least 1 MCP connection active and returning data
- [ ] SOPs assigned and cadences configured
- [ ] Team roles mapped
- [ ] Baseline snapshot saved
- [ ] First campaign audit documented
- [ ] Client added to portfolio dashboard

---

## 2. Portfolio Management

### Client Health Score (0-100)

The client health score provides a single-number summary of account health. Calculate weekly for each active client.

| Dimension | Weight | Score Range | How to Calculate |
|---|---|---|---|
| **Campaign Activity** | 25% | 0-100 | Active campaigns count vs. plan (100 = all planned campaigns running). Deduct 20 points if no campaign launched in last 14 days. Deduct 10 points if pipeline has <2 upcoming campaigns. |
| **Budget Pacing** | 25% | 0-100 | Spend vs. plan (100 = within 5% of planned spend). ROAS trend: +10 if improving, -10 if declining over 30 days. CPA trend: +10 if improving, -10 if declining. Cap deductions at 0. |
| **KPI Attainment** | 25% | 0-100 | Primary KPI: score = (actual / target) x 100, capped at 100. Deduct 10 per secondary KPI below 80% of target. Trend direction: +5 if improving, -5 if declining. |
| **Content Pipeline** | 15% | 0-100 | Content calendar coverage: (scheduled pieces / planned pieces) x 100. Deduct 25 if no content scheduled for next 7 days. Deduct 10 if calendar coverage <50% for next 30 days. |
| **Engagement Health** | 10% | 0-100 | Average response time to social engagement (100 = <2h, 75 = <6h, 50 = <24h, 25 = >24h). Social engagement rate vs. 30-day rolling average: +10 if above, -10 if below. |

### Traffic Light System

| Status | Score Range | Action Required |
|---|---|---|
| **Green** | 80-100 | Healthy. Continue current strategy. Note any dimension below 70 for proactive optimization. |
| **Amber** | 60-79 | Attention needed. Identify the lowest-scoring dimension. Create an action plan within 48 hours. Schedule check-in with account manager. |
| **Red** | Below 60 | Urgent intervention. Identify root causes across all dimensions. Escalate to account director. Create recovery plan within 24 hours. Schedule emergency client check-in if external factors involved. |

### Portfolio Dashboard View

The portfolio dashboard shows all clients at a glance:

| Column | Data |
|---|---|
| Client name | Brand name + slug |
| Health score | Composite score (0-100) with traffic light indicator |
| Lowest dimension | The weakest dimension name + score |
| Monthly spend | Total ad spend across all platforms |
| ROAS | Blended return on ad spend |
| Active campaigns | Count of currently running campaigns |
| Next deliverable | Next scheduled report or campaign launch |
| Account manager | Assigned team member |

Recommended: Run portfolio scan every Monday at 8 AM. Auto-flag any client that dropped from Green to Amber or Amber to Red since last scan.

---

## 3. SOP Framework

SOPs define repeatable processes for each service category. Every SOP has: numbered steps, a responsible role, a quality checklist, approval requirements, and estimated time.

### SOP Categories

| Category | SOPs | Typical Cadence | Responsible Role |
|---|---|---|---|
| **Content Production** | Blog writing, social media content, email newsletters, video scripts, case studies, whitepapers | Per piece (varies by content calendar) | Content Creator |
| **Paid Media** | Campaign setup, weekly optimization cycles, monthly budget reviews, creative refresh, A/B test planning | Setup: per campaign. Optimization: weekly. Budget: monthly. Creative: every 2-4 weeks. | Media Buyer |
| **Reporting** | Weekly pulse, monthly performance review, QBR preparation, annual planning | Per cadence (see Section 4) | Analyst / Account Manager |
| **CRM Operations** | Lead import, pipeline hygiene, segmentation refresh, data cleanup, consent audit | Lead import: as needed. Hygiene: weekly. Segmentation: monthly. Consent audit: quarterly. | CRM Specialist |
| **SEO** | Keyword monitoring, content optimization, technical audits, link building outreach, local SEO updates | Keyword monitoring: weekly. Content optimization: monthly. Technical audit: quarterly. Link building: ongoing. | SEO Specialist |

### SOP Template Structure

Every SOP document follows this structure:

```
SOP: [Name]
Category: [Content Production | Paid Media | Reporting | CRM | SEO]
Responsible: [Role]
Cadence: [Frequency]
Estimated Time: [Duration]
Approval: [None | Team Lead | Account Manager | Account Director]

Steps:
1. [Action] — [Details]
2. [Action] — [Details]
...

Quality Checklist:
- [ ] [Check 1]
- [ ] [Check 2]
...

Escalation: [When to escalate and to whom]
```

### SOP Maintenance Rules

- Review and update SOPs quarterly or after any significant process failure.
- Document all exceptions and workarounds discovered during execution.
- Version SOPs: include `Last Updated` date and `Version` number.
- SOPs are owned by the responsible role but approved by the account manager before changes take effect.

---

## 4. Client Reporting Cadence

| Report Type | Frequency | Delivery Day/Time | Auto-Generated? | Delivery Channel | Approver | Content |
|---|---|---|---|---|---|---|
| **Weekly Pulse** | Every Monday | Monday 9:00 AM client timezone | Yes (`performance-check` + `report-generator`) | Slack + Email | None (auto-send) | Top-line KPIs, spend pacing, wins/flags, action items for the week |
| **Monthly Review** | 1st business day of month | By EOD | Semi-auto (analyst reviews, adds commentary) | Google Slides + Email | Account Manager | Full KPI report, channel breakdowns, content performance, budget reconciliation, next month plan |
| **QBR (Quarterly Business Review)** | Every 90 days | Scheduled meeting | Manual (strategist prepares) | Presentation + PDF export | Account Director | Strategic review, market trends, competitive analysis, quarterly results vs. goals, next quarter strategy, budget recommendations |
| **Annual Planning** | January (or client fiscal year start) | Scheduled workshop | Manual (team collaborates) | Strategy document + Google Slides | Agency Admin | Year-in-review, annual goal setting, budget allocation, channel strategy, content calendar framework, growth opportunities |

### Report Delivery Checklist

- [ ] Data pulled from all connected sources (no stale data older than 24h for weekly, 48h for monthly)
- [ ] All KPIs calculated with correct comparison periods
- [ ] Anomalies flagged with explanations (not just numbers)
- [ ] Action items are specific, assigned, and time-bound
- [ ] Brand voice applied (professional for client-facing, detailed for internal)
- [ ] Delivery channel confirmed (correct Slack channel, correct email addresses)
- [ ] Backup copy saved to `~/.claude-marketing/brands/{slug}/reports/`

---

## 5. Cross-Client Insights

Agencies can extract valuable patterns across their portfolio, but data isolation is paramount. Follow these rules strictly.

### Allowed Cross-Client Analysis

| Analysis Type | How to Apply | Example Output |
|---|---|---|
| **Pattern detection** | Aggregate anonymized metrics across 5+ clients in the same industry. Report findings as general patterns. | "Email subject lines with numbers achieve 15% higher open rates across 8 B2B SaaS clients." |
| **Anonymized benchmarking** | Compare a single client's metrics against the anonymized portfolio average for their industry/segment. Never reveal which clients form the benchmark. | "Your CPC of $2.40 is 20% below the portfolio average of $3.00 for B2B SaaS." |
| **Shared learnings** | Opt-in only. Each client must explicitly consent to their anonymized data being included in agency benchmarks. Document consent. | Agency benchmark report (opt-in clients only): "Q4 average email open rate: 24.3% (n=12 clients)." |
| **Resource optimization** | Analyze team workload distribution across accounts. Identify underutilized or overloaded team members. | "Content Creator A is at 120% capacity this week. Content Creator B has 30% availability." |

### Prohibited Cross-Client Actions

- Never expose one client's brand name, data, strategy, or performance to another client.
- Never use one client's proprietary content, creative assets, or audience data for another client.
- Never share raw data across brand boundaries, even anonymized, without explicit opt-in.
- Never reference specific client results in proposals to prospects without written permission.
- Never allow MCP connections from one brand to query another brand's data sources.

---

## 6. Credential Isolation

### Security Model

| Component | Implementation | Details |
|---|---|---|
| **Storage location** | `~/.claude-marketing/credentials/{slug}.json` | Each brand has its own credential file. File permissions should be user-read-only (chmod 600 on Unix). |
| **Active profile tracking** | `~/.claude-marketing/credentials/_active-profile.json` | Contains the slug of the currently active credential profile. Only one profile can be active at a time. |
| **Profile switching** | `/digital-marketing-pro:credential-switch` or `setup.py --switch-credentials` | Switches the active credential profile. All subsequent MCP and API calls use the new profile's keys. |
| **Env var loading** | Credentials loaded as environment variables at session start | Each profile maps to env vars: e.g., `SENDGRID_API_KEY`, `GOOGLE_ADS_CUSTOMER_ID`. |
| **Cross-brand isolation** | Hard boundary | Credentials NEVER cross brand boundaries. A request for Brand A's data must use Brand A's credentials. Attempting to use Brand B's credentials for Brand A's operations is a system-level error. |

### Audit Trail

Every credential operation is logged:

| Event | Logged Data |
|---|---|
| Profile created | Timestamp, slug, platforms configured (no secrets logged) |
| Profile switched | Timestamp, from_slug, to_slug, user/session ID |
| Profile updated | Timestamp, slug, fields changed (no secrets logged) |
| Profile deleted | Timestamp, slug, confirmation status |
| Validation check | Timestamp, slug, result (pass/fail per platform, no secrets exposed) |

### Best Practices

- Use client-prefixed env var names when managing multiple profiles in the same environment: `ACME_SENDGRID_API_KEY`, `BETA_SENDGRID_API_KEY`.
- After every credential change, run `/digital-marketing-pro:validate-profile --brand {brand}` — it probes every connector referenced by the profile and reports pass / fail / error-class without ever printing credential values. Add `--connectors slack,hubspot` to probe only the rotated subset.
- Rotate API keys quarterly. Log rotation dates in the credential profile metadata.
- Never store credentials in the plugin directory, brand profile JSON, or any file under version control.
- If a credential is suspected compromised: immediately rotate the key on the platform, update the profile, re-validate, and log the incident.

---

## 7. White-Labeling

### Report Voice Rules

| Context | Voice Guidelines | Do | Don't |
|---|---|---|---|
| **Client-facing reports** | Agency voice: professional, third-person, no brand personality bleeding through | "Campaign performance exceeded targets by 12% this month." | "We crushed it this month!" or any casual/brand-personality language |
| **Internal reports** | Team voice: can reference multiple clients, use shorthand, be direct | "Acme's Q4 ROAS is trending down. Need to review creative." | Share internally without marking as confidential |
| **Executive summaries** | Portfolio-level: aggregate metrics, strategic recommendations | "Portfolio ad spend efficiency improved 8% QoQ across 15 accounts." | Include individual client names or data unless the summary is for that specific client |
| **Client dashboards** | Single-client view: all data scoped to that client only | Show that client's KPIs, campaigns, and trends | Show any cross-client data, benchmarks from identifiable sources, or other client names |

### Branding Rules for Deliverables

| Element | Rule |
|---|---|
| **Logo** | Use the agency's logo on all client-facing reports. Never use the Digital Marketing Pro plugin branding. |
| **Color scheme** | Use the agency's brand colors for report templates. Client brand colors may be used for content examples within the report. |
| **Footer** | Include agency name, contact info, and confidentiality notice. Example: "Confidential. Prepared by [Agency Name] for [Client Name]." |
| **Authorship** | Reports are attributed to the agency, not to individual AI tools or plugins. |
| **Data sources** | Reference data sources generically: "Analytics data," "Ad platform data." Do not reference specific MCP server names or plugin internals. |

### Dashboard Isolation Rules

- Each client dashboard is scoped exclusively to that client's brand slug.
- Dashboard URL or access tokens must not grant access to other clients' data.
- Portfolio-level dashboards are internal only and must require agency-admin authentication.
- Filters on portfolio dashboards must default to aggregate view; drilling into a specific client requires explicit selection.
- Never display two different clients' data on the same screen in a client-facing context.
