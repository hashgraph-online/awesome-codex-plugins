---
name: lead-import
description: "Import leads into CRM. Use when: loading leads from forms, CSV, or manual entry with deduplication and scoring."
disable-model-invocation: true
argument-hint: "[source-file or URL]"
---

# /digital-marketing-pro:lead-import

## Purpose

Import leads into the brand's CRM with data validation, deduplication, lead scoring, and proper consent tracking. Supports CSV files, JSON arrays, and manual entry with automatic source attribution. Ensures every imported lead is clean, scored, deduplicated, and compliant before it reaches the sales team — eliminating the manual data hygiene work that slows down lead-to-opportunity conversion. Integrates with the marketing-automation lead scoring framework to classify leads on import, so high-value prospects are routed to sales immediately while lower-scoring leads enter nurture sequences automatically.

Use this command for leads specifically — it applies scoring, lifecycle staging, and nurture enrollment. For general CRM data syncing (contacts, deals, campaigns) without lead scoring, use `/digital-marketing-pro:crm-sync` instead.

## Input Required

The user must provide (or will be prompted for):

- **Lead data**: CSV file path, JSON array, or manual field entry — must include at minimum an email address or phone number for deduplication and identity resolution
- **Source attribution**: Where these leads originated — form name, event name, campaign identifier, landing page URL, ad platform and campaign, partner referral, webinar registration, or manual prospecting
- **Lead scoring threshold (optional)**: Minimum score for a lead to be imported as marketing-qualified (MQL) — leads below threshold are imported as raw leads with lower priority routing
- **CRM platform**: Target CRM — Salesforce, HubSpot, Zoho, or Pipedrive — and the specific object type (Lead, Contact, or platform equivalent)
- **Required fields**: Which fields are mandatory for import — email, first name, last name, company, phone, job title, or custom fields specific to the business qualification criteria
- **Consent status**: Whether leads have provided opt-in consent, the consent mechanism (single opt-in, double opt-in, legitimate interest, contractual necessity), and applicable privacy regulation (GDPR, CCPA, CASL)
- **Assignment rules (optional)**: How imported leads should be assigned — round-robin across reps, territory-based by geography, product-line based, company-size tier, or to a specific owner for manual distribution
- **Duplicate handling preference**: When a duplicate is found — update existing record with new data, skip the duplicate entirely, merge specific fields (e.g., add new source but keep existing owner), or create a secondary record linked to the original
- **Lead lifecycle stage**: Initial status to assign — new lead, marketing-qualified, sales-accepted, or a custom stage in the brand's lifecycle model
- **Tagging and list membership (optional)**: Tags, lists, or campaigns to associate with imported leads for downstream segmentation and reporting
- **Notification preferences (optional)**: Whether to notify assigned sales reps about new leads immediately, and via which channel (CRM notification, email, Slack) — with priority flagging for high-scoring MQLs
- **Nurture sequence trigger (optional)**: Whether to automatically enroll imported leads into an existing nurture sequence based on score tier, source, or lifecycle stage
- **Custom scoring overrides (optional)**: Manual score adjustments for specific lead sources — e.g., event leads get +20 bonus points, partner referrals get +15 — applied on top of the standard scoring model
- **Import frequency**: Whether this is a one-time import or a recurring source — if recurring, specify expected cadence (daily form submissions, weekly event exports, monthly partner lists) for import template creation

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Parse and validate lead data**: Read the input data source and validate every record — check email format (RFC 5322), normalize phone numbers to E.164, verify required fields are present, detect encoding issues, identify obviously fake entries (test@test.com, role-based emails like info@), and flag malformed or incomplete records with specific error reasons.
3. **Normalize and enrich fields**: Standardize company names, job titles, and geographic data. Apply consistent formatting — title case for names, lowercase for emails, standardized country and state codes. Where possible, infer missing fields from available data (e.g., company domain from email, country from phone prefix).
4. **Check for duplicates per lead**: Query the target CRM for existing records matching each lead on email, phone, or composite key. Categorize results as new (no match), exact duplicate (same email and name), fuzzy match (similar name or domain), or enrichment opportunity (existing record with missing fields this lead can fill).
5. **Score leads using lead scoring framework**: Apply the marketing-automation lead scoring model from `skills/marketing-automation/lead-scoring.md` — score based on demographic fit (job title seniority, company size, industry match), behavioral signals (source quality, content engagement, recency of interaction), and engagement potential. Classify each lead as MQL, raw lead, or nurture candidate based on the threshold.
6. **Validate consent and compliance**: Check each lead's consent status against compliance rules for the brand's target markets. Verify opt-in mechanism is documented, timestamp consent records, flag leads missing required consent fields, and ensure lawful data processing basis is recorded per applicable regulation (GDPR Article 6, CCPA, CASL).
7. **Prepare CRM-ready payloads with source attribution**: Transform validated leads into platform-specific payloads — map fields to CRM schema, attach source attribution (utm_source, utm_medium, utm_campaign), apply assignment rules, set lead status and lifecycle stage, add tags and list memberships, and include lead score as a custom field.
8. **Create approval gate**: Assess risk level — medium for fewer than 50 leads, high for 50 or more. Present import preview showing total lead count, valid vs. invalid breakdown, top 5 sample records with scores, scoring distribution (MQL/raw/nurture counts), duplicate summary, compliance status, and any validation warnings.
9. **On approval, import via CRM MCP**: Push lead payloads to the target CRM through the platform MCP in batched requests. Handle rate limits with exponential backoff, retry transient failures, apply assignment rules, trigger any CRM-side automation (welcome workflows, rep notifications), and log each lead's import outcome.
10. **Trigger notifications and nurture enrollment**: For high-scoring MQLs, send immediate notifications to assigned reps with lead details and recommended next actions. For nurture-qualified leads, enroll in the specified nurture sequence via the email platform MCP. Log all triggered automations.
11. **Verify import integrity**: Query the CRM post-import to confirm record counts match expectations. Spot-check 5 randomly selected imported leads to verify field values, scoring data, source attribution, and assignment all transferred correctly.
12. **Return import summary and log results**: Compile final results and log the complete import — timestamp, source attribution, record counts, scoring distribution, assignment breakdown, nurture enrollments, notifications sent, errors, and duration — to `~/.claude-marketing/brands/{slug}/logs/lead-import-log.json`.

## Output

A structured lead import report containing:

- **Import results summary**: Total leads processed with breakdown — created, duplicates skipped, duplicates updated/merged, validation errors, and compliance rejections with percentages and counts
- **Lead score distribution**: Breakdown of imported leads by score tier — MQL count and percentage, raw lead count, nurture candidates, average score, median score, and highest-scoring leads highlighted
- **Source attribution record**: Campaign, medium, source, and content attribution applied to all imported leads — formatted for downstream ROI reporting and marketing-sourced pipeline tracking
- **Validation error report**: Leads that failed validation listed with specific field-level errors — malformed email, missing required field, suspected fake entry, phone format issue, or data type mismatch with suggested corrections
- **Deduplication summary**: Duplicate leads found with match type (exact/fuzzy), match fields, confidence score, and action taken (updated, skipped, merged, or flagged for manual review) for each pair
- **Compliance audit trail**: Consent status for every imported lead — opt-in mechanism, consent timestamp, applicable regulation, lawful basis, and any leads flagged for missing or insufficient consent with remediation steps
- **Assignment summary**: How leads were distributed across sales reps — by owner, territory, product line, or score tier — with counts per assignee and any unassigned leads requiring manual routing
- **Nurture enrollment summary**: Leads enrolled in nurture sequences — sequence name, enrollment count, expected first touchpoint date, and leads excluded from nurture (already in active sequences or opted out)
- **Notification delivery report**: Notifications sent to sales reps — rep name, lead count assigned, delivery channel, delivery status, and any failed notifications with retry recommendations
- **Execution log**: Timestamped record of the import process — batch sizes, API responses, retry attempts, rate limit pauses, processing duration, and CRM confirmation IDs for created records
- **Data quality baseline**: Field completeness rates across the imported batch — percentage of leads with company, phone, job title, and other optional fields populated, establishing a quality baseline for this source
- **Source quality comparison**: If prior imports from this source exist, compare current batch quality against historical averages — validation error rate trend, scoring distribution shift, duplicate rate trend, and field completeness changes over time
- **CRM automation triggers**: Any CRM-side workflows triggered by the import — welcome email sends, task creation for reps, lead routing rule execution, and workflow enrollment confirmations
- **Follow-up recommendations**: Suggested next steps — trigger additional nurture sequences, alert sales reps to hot MQLs, schedule data quality review in 30 days, configure recurring import for this source, or refine lead scoring thresholds based on import results

## Agents Used

- **crm-manager** — Lead validation, deduplication, field mapping, CRM schema resolution, lead scoring application, consent verification, assignment rule execution, lifecycle stage setting, nurture enrollment, and import management
- **email-specialist** — Nurture sequence enrollment, email deliverability validation (checking imported emails against known bounce and spam trap lists), and engagement-based scoring input
