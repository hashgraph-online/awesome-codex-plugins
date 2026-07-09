# Marketing Operations Reference

Comprehensive reference for the operational backbone of marketing automation: data hygiene, tech stack management, deliverability, compliance, reporting infrastructure, and team workflows.

---

## Data Hygiene

Clean data is the foundation of every automation program. Dirty data produces wrong scores, broken personalization, misfired triggers, and wasted budget.

### Deduplication

**Problem**: The same person exists as multiple records. Emails go to both. Scoring is split. Sales sees fragmented history.

**Deduplication rules:**
1. **Match on email address first** — Email is the most reliable unique identifier for marketing contacts.
2. **Secondary match on company + name** — For contacts with multiple email addresses (personal + work).
3. **Merge strategy**: Keep the record with the most complete data. Combine activity history. Take the higher lead score. Preserve the earliest creation date.
4. **Prevention**: Enforce email uniqueness on all forms. Use progressive profiling instead of creating new records for repeat visitors.
5. **Cadence**: Run dedup monthly for active databases, weekly during high-volume campaign periods.

### Data Normalization

**Problem**: "United States," "US," "U.S.," "usa," and "America" are all the same country but break segmentation.

| Field | Normalization Rule |
|---|---|
| Country | Map to ISO 3166-1 alpha-2 codes (US, GB, DE, etc.) |
| State/Province | Map to postal abbreviations (CA, NY, TX) |
| Phone number | E.164 format (+1XXXXXXXXXX) |
| Job title | Map to standardized categories (VP Marketing, Director of Marketing, Head of Marketing → "Marketing Leader") |
| Company name | Normalize common variations (Inc., Inc, Incorporated → "Inc.") |
| Industry | Map to a controlled list (SIC, NAICS, or custom taxonomy) |
| URL | Lowercase, strip trailing slash, normalize www vs. non-www |

**Implementation**: Build normalization as an automated workflow that triggers on record creation and field update. Do not rely on manual cleanup.

### Data Validation

**Rules to enforce at point of entry:**
- Email format validation (RFC 5322 compliant + MX record check)
- Phone number format validation (reject obviously fake: 000-000-0000, 123-456-7890)
- Required field enforcement (email is always required; name for gated content)
- Domain blocklist (competitors, disposable email providers like mailinator.com, guerrillamail.com)
- Bot detection (honeypot fields, submission timing checks, reCAPTCHA for high-value forms)

### Data Decay Management

Contact data decays at approximately 25-30% per year. People change jobs, get promoted, switch email providers, and move companies.

| Decay Signal | Detection Method | Action |
|---|---|---|
| Email hard bounce | Bounce notification from ESP | Mark invalid, suppress from sends, flag for re-enrichment |
| Job title change | Enrichment tool refresh (quarterly) | Re-score explicit fit, update segmentation |
| Company change | Enrichment tool refresh (quarterly) | Re-score all explicit criteria |
| Email soft bounce (3+ consecutive) | Bounce tracking | Investigate, attempt re-verification, suppress if unresolvable |
| No engagement in 180 days | Engagement tracking | Run re-engagement workflow, suppress if no response |
| Phone disconnected | Call disposition data from sales | Remove phone, update contact record |

### Data Enrichment

**Purpose**: Fill in missing fields without asking the prospect, using third-party data providers.

| Provider | Best For | Data Available |
|---|---|---|
| Clearbit | B2B SaaS, real-time enrichment | Company size, revenue, industry, tech stack, social profiles |
| ZoomInfo | B2B enterprise, direct dial phones | Contact info, org charts, intent data, company details |
| Apollo | B2B startup/mid-market | Email verification, company data, engagement data |
| FullContact | B2C identity resolution | Social profiles, demographics, household data |
| Datanyze | Technographics | Technology stack detection for target accounts |

**Enrichment triggers:**
- On form submission (enrich immediately to enhance lead scoring)
- On CRM record creation (enrich new contacts from sales-sourced leads)
- Quarterly batch refresh (re-enrich existing database to catch job changes, company changes)

---

## Tech Stack Management

### MAP Selection Criteria

When evaluating a marketing automation platform, score each criterion on a 1-5 scale.

| Criterion | Weight | Questions to Ask |
|---|---|---|
| **Ease of use** | High | Can a non-technical marketer build workflows without engineering support? |
| **Email builder quality** | High | Drag-and-drop editor? Mobile-responsive templates? HTML access? |
| **Workflow/automation depth** | High | Branching logic, multiple triggers, time-based + behavioral, cross-channel? |
| **Lead scoring** | Medium-High | Custom scoring models? Decay? Multiple scoring dimensions? |
| **CRM integration** | High | Native integration with your CRM? Bi-directional sync? Real-time? |
| **Reporting and analytics** | Medium-High | Attribution? Revenue reporting? Custom dashboards? |
| **Deliverability** | High | Shared vs. dedicated IP? Authentication support? Deliverability tools? |
| **Scalability** | Medium | Contact/send limits? Performance at 100K+ contacts? API rate limits? |
| **API and integrations** | Medium | REST API? Webhook support? Pre-built integrations catalog? |
| **Compliance tools** | Medium | GDPR tools? Consent management? Suppression automation? |
| **Price** | Medium | Per-contact pricing? Feature gating by tier? Hidden costs (overages, add-ons)? |
| **Support quality** | Medium | Response time SLA? Onboarding assistance? Documentation quality? |

### Integration Patterns

**CRM Sync (Most Critical Integration)**
- Bi-directional sync between MAP and CRM (contact data, lead scores, activity, lifecycle stage)
- Sync frequency: Real-time for lead scoring and lifecycle stage changes. Batch (every 15-60 min) acceptable for enrichment data.
- Conflict resolution: Define which system is "source of truth" per field. Typically: MAP owns engagement data, CRM owns deal data.
- Field mapping: Document every mapped field, transformation rules, and sync direction.

**Common Integration Architecture:**
```
Website → MAP (form submissions, tracking)
MAP ↔ CRM (bi-directional contact/lead sync)
MAP → Ad Platforms (audience sync for retargeting)
CRM → MAP (deal stage updates, sales activity)
MAP → Analytics (campaign performance, attribution)
CDP → MAP (unified customer profiles, segmentation)
Webinar Tool → MAP (registration, attendance data)
Chat Tool → MAP (conversation data, lead creation)
Billing → MAP (subscription events, revenue data)
```

### Data Flow Mapping

Document every data flow between systems. For each flow:
1. **Source system** — Where the data originates
2. **Destination system** — Where the data goes
3. **Trigger** — What initiates the sync (real-time event, scheduled batch, manual)
4. **Data fields** — Exactly which fields are transferred
5. **Transformation** — Any field mapping, normalization, or calculation applied during sync
6. **Error handling** — What happens when a sync fails (retry, alert, queue)
7. **Owner** — Who is responsible for monitoring this integration

---

## Deliverability Management

Deliverability is the unsexy foundation that determines whether your automation actually reaches inboxes.

### Sender Authentication

| Protocol | Purpose | Implementation |
|---|---|---|
| **SPF** (Sender Policy Framework) | Declares which servers can send email on behalf of your domain | DNS TXT record listing authorized sending IPs/services |
| **DKIM** (DomainKeys Identified Mail) | Cryptographic signature proving the email was not altered in transit | DNS TXT record with public key; MAP signs outgoing emails with private key |
| **DMARC** (Domain-based Message Authentication) | Policy telling receivers what to do when SPF/DKIM fail | DNS TXT record specifying policy (none, quarantine, reject) and reporting address |

**Implementation sequence:**
1. Set up SPF for all sending sources (MAP, transactional email, CRM)
2. Configure DKIM signing in your MAP
3. Deploy DMARC with `p=none` first (monitoring only)
4. Monitor DMARC reports for 2-4 weeks to identify any unauthorized senders
5. Escalate to `p=quarantine` then `p=reject` once all legitimate senders are authenticated

### IP and Domain Warm-Up

**When warm-up is required:**
- New dedicated sending IP
- New sending domain or subdomain
- Reactivating an IP/domain that has been dormant for 30+ days
- Migrating to a new ESP/MAP

**Warm-up schedule (dedicated IP):**

| Week | Daily Send Volume | Notes |
|---|---|---|
| 1 | 500-1,000 | Send to your most engaged contacts only (opened in last 30 days) |
| 2 | 2,000-5,000 | Expand to contacts engaged in last 60 days |
| 3 | 5,000-15,000 | Expand to contacts engaged in last 90 days |
| 4 | 15,000-30,000 | Continue expanding audience |
| 5 | 30,000-50,000 | Approaching full volume |
| 6+ | Full volume | Monitor closely for first 2-3 months |

**Rules during warm-up:**
- Never spike volume by more than 2x day over day
- Monitor bounce rates daily (hard bounce should stay <2%)
- Watch spam complaint rates (must stay <0.1%)
- If deliverability issues appear, reduce volume and diagnose before continuing

### List Hygiene

| Action | Frequency | Criteria |
|---|---|---|
| Remove hard bounces | Real-time (automated) | Every hard bounce is immediately suppressed |
| Suppress soft bounces | After 3 consecutive | Three consecutive soft bounces = treat as hard bounce |
| Re-verify stale addresses | Quarterly | Run email verification on contacts with no engagement in 90+ days |
| Remove role-based addresses | Monthly | Suppress info@, admin@, support@, sales@ — these rarely convert |
| Suppress spam complainers | Real-time (automated) | Every spam complaint triggers immediate suppression |
| Sunset inactive contacts | Ongoing via re-engagement workflow | No engagement in 90-180 days → re-engagement → suppress if no response |

### Deliverability Monitoring

| Metric | Healthy | Warning | Critical |
|---|---|---|---|
| **Inbox placement rate** | >95% | 85-95% | <85% |
| **Hard bounce rate** | <0.5% | 0.5-2% | >2% |
| **Spam complaint rate** | <0.05% | 0.05-0.1% | >0.1% |
| **Unsubscribe rate** | <0.3% | 0.3-0.5% | >0.5% |
| **Blacklist status** | Not listed | Listed on minor lists | Listed on Spamhaus, Barracuda, or SORBS |

---

## Compliance Automation

### Consent Management

**Double opt-in workflow:**
1. User submits form → record created with `consent_status: pending`
2. Confirmation email sent immediately → "Click to confirm your subscription"
3. User clicks → `consent_status: confirmed`, `consent_date: timestamp`, `consent_source: form_name`
4. User does NOT click within 48 hours → reminder sent
5. User does NOT click within 7 days → record marked `consent_status: expired`, excluded from marketing sends

**Consent record requirements (GDPR):**
- What they consented to (specific purpose)
- When they consented (timestamp)
- How they consented (form URL, checkbox text)
- Proof of consent (form submission log, IP address)

### Preference Centers

**Minimum preference center features:**
- Email frequency options (weekly, bi-weekly, monthly)
- Topic/category preferences (product updates, educational content, promotions, events)
- Channel preferences (email, SMS, push)
- Global unsubscribe (always available, one-click)
- Email address update

**Advanced features:**
- Pause emails for a set period ("snooze for 30 days")
- Content format preferences (text vs. rich HTML)
- Language preference
- Preferred send time

### Suppression Lists

| List | Purpose | Management |
|---|---|---|
| **Global unsubscribe** | Contacts who opted out of all marketing | Automated — never manually remove |
| **Hard bounce** | Invalid email addresses | Automated — never attempt to re-send |
| **Spam complainer** | Contacts who reported spam | Automated — legally required suppression |
| **Competitor domains** | Competitor email addresses | Manual — update quarterly |
| **Do-not-contact** | Legal/compliance exclusions | Manual — managed by legal team |
| **Recently contacted** | Frequency cap enforcement | Automated — rolling window (e.g., 48-hour suppression after send) |

### GDPR/CCPA Automation

| Requirement | Automation |
|---|---|
| Right to access (GDPR Art. 15) | Automated data export from MAP + CRM on request |
| Right to erasure (GDPR Art. 17) | Automated deletion workflow across all systems when requested |
| Right to portability (GDPR Art. 20) | Automated data export in machine-readable format |
| Opt-out of sale (CCPA) | Automated suppression + propagation to downstream systems |
| Consent withdrawal | One-click unsubscribe triggers consent record update + suppression across all channels |
| Data retention limits | Automated purge of data past retention period (define per data type) |

---

## Reporting Infrastructure

### UTM Governance

**Standard UTM parameters:**

| Parameter | Convention | Example |
|---|---|---|
| `utm_source` | Platform or channel name (lowercase, no spaces) | `google`, `facebook`, `linkedin`, `email`, `direct-mail` |
| `utm_medium` | Marketing medium (lowercase) | `cpc`, `social`, `email`, `display`, `referral` |
| `utm_campaign` | Campaign name (lowercase, hyphens, include date) | `2026-q1-saas-nurture`, `2026-02-product-launch` |
| `utm_content` | Specific creative or content variant | `hero-cta-v2`, `sidebar-banner`, `email-3-casestudy` |
| `utm_term` | Keyword (paid search only) | `marketing-automation-software` |

**Governance rules:**
- Central UTM builder spreadsheet or tool — no free-form entry
- Naming convention document shared with all team members
- Automated validation on form submission and link tracking
- Monthly UTM audit to catch inconsistencies

### Attribution Setup

| Model | Best For | How It Works |
|---|---|---|
| **First touch** | Understanding top-of-funnel channel effectiveness | 100% credit to first interaction |
| **Last touch** | Understanding what directly drives conversion | 100% credit to last interaction before conversion |
| **Linear** | Equal credit across all touchpoints | Even distribution across all touches |
| **Time decay** | Long B2B cycles where recency matters | More credit to recent touchpoints, less to earlier |
| **Position-based (U-shaped)** | Balanced first + last touch emphasis | 40% first, 40% last, 20% distributed to middle |
| **Data-driven** | High-volume businesses with sufficient data | Algorithmic based on actual conversion patterns |

**For automation-specific attribution**: Track which automated sequence or workflow a contact was in when they converted. Attribute pipeline and revenue to the sequence, not just the individual email.

### Dashboard Architecture

**Executive dashboard (weekly/monthly review):**
- Marketing-sourced pipeline and revenue
- MQL and SQL volume and velocity
- CAC and LTV trends
- Top-performing channels by revenue contribution
- Automation program health summary (active workflows, conversion rates)

**Marketing ops dashboard (daily/weekly):**
- Email deliverability metrics (bounce, complaint, inbox placement)
- Automation workflow health (enrollment rates, error rates, completion rates)
- Data quality score (field completeness, duplicate rate, bounce rate)
- Integration status (sync success/failure rates)
- Lead scoring distribution and MQL flow rate

**Campaign-level dashboard (per campaign):**
- Sequence-level performance (open, click, conversion by email)
- Lead flow through stages (funnel visualization)
- A/B test results
- Revenue attributed to campaign

---

## Team Workflows

### Marketing-to-Sales Handoff

**Automated handoff workflow:**
1. Contact reaches MQL threshold → workflow triggers
2. Assign to sales rep (round-robin, territory, or account-based routing)
3. Create CRM task with SLA deadline (4 hours for B2B SaaS, 24 hours for enterprise)
4. Send notification to assigned rep with lead summary (score breakdown, activity history, content consumed)
5. If not contacted within SLA → escalation notification to sales manager
6. Sales rep dispositions the lead: Accepted (→ SQL), Recycled (→ back to nurture with reason), Disqualified (→ removed with reason)
7. Disposition data feeds back to marketing for scoring model calibration

### Campaign Briefing Process

**Campaign request template:**
1. Campaign objective and KPIs
2. Target audience (segment, persona, lifecycle stage)
3. Channels and sequence types needed
4. Content requirements (existing assets available, new content needed)
5. Timeline and launch date
6. Budget allocation
7. Compliance/legal review requirements
8. Success criteria and reporting cadence

### Content Approval Workflow

```
Draft created → Author self-review
  → Peer review (marketing team)
  → Brand/voice review (brand guardian)
  → Compliance review (if regulated industry)
  → Stakeholder approval (if applicable)
  → QA check (links, personalization tokens, rendering)
  → Schedule/publish
```

**QA checklist before automation launch:**
- [ ] All personalization tokens render correctly (test with missing data too)
- [ ] All links are correct and trackable (UTMs applied)
- [ ] Unsubscribe link present and functional
- [ ] Physical mailing address included (CAN-SPAM)
- [ ] Email renders correctly in top 5 email clients (Gmail, Outlook, Apple Mail, Yahoo, mobile)
- [ ] Subject line and preview text display correctly (no truncation)
- [ ] Sender name and reply-to are correct
- [ ] Trigger fires only for intended contacts (test with inclusion and exclusion criteria)
- [ ] Exit conditions work (test with a converting contact)
- [ ] Suppression rules prevent conflicts with other active workflows
- [ ] Wait steps use correct durations and time zone handling

---

## Platform Comparison Matrix

| Capability | HubSpot | ActiveCampaign | Klaviyo | Mailchimp | Marketo | Pardot |
|---|---|---|---|---|---|---|
| **Best for** | B2B SMB to mid-market | SMB, agencies | eCommerce (Shopify focus) | Small business, beginners | B2B enterprise | B2B (Salesforce shops) |
| **Pricing model** | Per contact tier | Per contact tier | Per profile tier | Per contact + feature tier | Per contact (custom) | Per contact (custom) |
| **Starting price** | ~$800/mo (Pro) | ~$49/mo | ~$20/mo | ~$13/mo | ~$1,000+/mo | ~$1,250/mo |
| **CRM included** | Yes (HubSpot CRM, free) | Basic CRM included | No (integrates with others) | No | No (integrates with CRMs) | No (Salesforce required) |
| **Email builder** | Excellent (drag & drop) | Good | Excellent (eCommerce templates) | Good (basic) | Good | Adequate |
| **Workflow complexity** | High (visual builder) | High (visual builder) | Medium-High (flow builder) | Low-Medium | Very High | Medium-High |
| **Lead scoring** | Yes (custom properties) | Yes (contact scoring) | Predictive analytics | Basic (tags-based) | Advanced (multi-model) | Yes (Salesforce-integrated) |
| **SMS** | Yes (add-on) | Yes (built-in) | Yes (built-in) | Yes (add-on) | Via integration | Via integration |
| **eCommerce integration** | Good (Shopify, WooCommerce) | Good | Excellent (Shopify native) | Basic | Via integration | Via integration |
| **Salesforce integration** | Good (bi-directional) | Good | Basic | Basic | Good | Native (same company) |
| **Reporting** | Strong (built-in attribution) | Good | Strong (revenue attribution) | Basic | Advanced (custom reports) | Good (Salesforce reports) |
| **API quality** | Excellent | Good | Excellent | Adequate | Excellent | Good |
| **Learning curve** | Medium | Low-Medium | Low (eCommerce) | Low | High | Medium-High |
| **Scalability** | Good to 100K+ | Good to 50K+ | Excellent for eCommerce | Limited at scale | Enterprise-grade | Enterprise-grade |

### Strengths and Weaknesses Summary

**HubSpot**: All-in-one platform with excellent UX. Weakness: Gets expensive at scale; some advanced features require Enterprise tier.

**ActiveCampaign**: Best value for automation depth at SMB price. Weakness: CRM is basic; reporting is adequate but not best-in-class.

**Klaviyo**: Dominant for eCommerce with deep Shopify integration and predictive analytics. Weakness: Not built for B2B; limited CRM capabilities.

**Mailchimp**: Easiest to start with, lowest barrier to entry. Weakness: Automation is shallow; outgrown quickly by serious marketers.

**Marketo**: Most powerful automation for enterprise B2B. Weakness: Steep learning curve; expensive; requires dedicated admin.

**Pardot (Marketing Cloud Account Engagement)**: Best choice if already committed to Salesforce ecosystem. Weakness: UI is dated; innovation pace is slow; pricing is high for what you get.

### Vendor Evaluation Framework

**Must-Haves (Deal-Breakers if Missing):**
- Native integration with your CRM
- Visual workflow builder with branching logic
- Lead scoring (custom criteria, not just engagement points)
- Email builder with mobile-responsive templates
- GDPR/CCPA compliance tools (consent management, data deletion)
- API access for custom integrations
- Deliverability tools (authentication support, dedicated IP option)

**Nice-to-Haves (Differentiate Finalists):**
- Built-in SMS and push notification channels
- Predictive analytics and AI recommendations
- Revenue attribution reporting
- A/B testing within workflows (not just email subject lines)
- Dynamic content blocks based on contact properties
- Account-based marketing features
- Customer data platform (CDP) capabilities

**Deal-Breakers (Eliminate Immediately):**
- No API or webhook support
- Contact-list-based pricing with no way to manage costs at scale
- No GDPR compliance tools (no consent tracking, no deletion workflow)
- Shared IP only with no dedicated IP option
- No workflow branching (linear sequences only)
- Vendor lock-in (no data export capability)
