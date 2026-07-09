---
name: segment-audience
description: "Create audience segments. Use when: building or updating CRM or email platform segments for campaign targeting."
disable-model-invocation: true
argument-hint: "[segment-name or criteria]"
---

# /digital-marketing-pro:segment-audience

## Purpose

Create or update audience segments in the brand's CRM or email platform based on behavioral, demographic, or engagement criteria. Segments can be used for ad targeting, email campaigns, retargeting, or personalization. Ensures segments are well-defined, properly sized, actionable across platforms, and documented with clear criteria for reproducibility — so the team can understand exactly who is in a segment and why. Supports RFM (recency, frequency, monetary) modeling, lifecycle-based segmentation, and predictive scoring criteria for advanced audience strategies.

Use this command to build targeting audiences before campaign launches. For importing new contacts into the CRM first, use `/digital-marketing-pro:lead-import`.
For exporting segment member data to external tools, use `/digital-marketing-pro:data-export` after segment creation.

## Input Required

The user must provide (or will be prompted for):

- **Segment criteria**: The rules that define segment membership — demographics (age, location, job title, company size, industry), behaviors (pages visited, emails opened, links clicked, purchases made, events attended), engagement levels (active last 30/60/90 days, lapsed, at-risk, churned), purchase history (recency, frequency, monetary value, product category), lifecycle stage (subscriber, lead, MQL, customer), or custom field filters
- **Target platform**: Where the segment will be created — CRM (Salesforce, HubSpot, Zoho, Pipedrive), email platform (ActiveCampaign, Mailchimp), or ad platform (Meta Custom Audiences, Google Ads Customer Match, LinkedIn Matched Audiences, TikTok Custom Audiences)
- **Segment name**: A descriptive, standardized name following the brand's naming conventions — e.g., "High-Value-Customers-Last-90d" or "MQL-SaaS-Enterprise-US"
- **Segment purpose**: How this segment will be used — email campaign targeting, paid ad audience, retargeting pool, personalization cohort, suppression/exclusion list, lookalike seed audience, or cross-sell/upsell targeting
- **Dynamic vs. static**: Whether the segment should auto-update as contacts meet or leave criteria (dynamic/smart list) or remain fixed at time of creation (static/snapshot) — dynamic for ongoing campaigns, static for one-time sends or point-in-time analysis
- **Refresh frequency (if dynamic)**: How often the segment membership should be recalculated — real-time (event-triggered), daily, weekly, or on-demand before each campaign send
- **Exclusion criteria (optional)**: Contacts to explicitly exclude — unsubscribed, hard bounced, competitors, internal team members, existing customers (for acquisition campaigns), contacts in another active campaign (frequency capping), or suppression lists from partners
- **Minimum segment size (optional)**: The smallest acceptable segment size for the intended use case — ad platforms typically require 1,000+ for effective delivery, lookalike seeds perform best at 1,000-10,000, and email segments should be large enough for statistical significance in A/B testing
- **Cross-platform sync (optional)**: Whether this segment should be automatically synced to additional platforms — e.g., create in CRM and push to Meta Custom Audiences and Google Ads simultaneously
- **Segment description**: A human-readable explanation of the segment's purpose and criteria for team documentation — stored alongside the segment for future reference and knowledge transfer
- **RFM parameters (optional)**: If using recency-frequency-monetary segmentation — define the scoring thresholds for each dimension, the lookback window for transaction history, and the number of segments to create (e.g., Champions, Loyal, At Risk, Lost)
- **Lookalike expansion (optional)**: If this segment will seed a lookalike audience — specify the expansion percentage (1-10%) and target platform, so the segment can be optimized for seed quality rather than just size

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Determine available data sources**: Query connected platforms to identify what data is available for segmentation — CRM contact fields and custom properties, email engagement metrics (opens, clicks, bounces), ad platform audience data, website behavioral data (if analytics MCP connected), and purchase/transaction records. Map which criteria can be evaluated from which source and flag any criteria that cannot be supported by available data.
3. **Build segment criteria logic**: Translate the user's criteria into platform-specific filter logic — AND/OR conditions, nested groups, date ranges, relative date windows (e.g., "last 30 days" recalculated dynamically), numeric thresholds, string matching rules, and list membership checks. Validate that all referenced fields exist in the target platform's schema.
4. **Estimate segment size from available data**: Run a count query or estimate against the target platform to project segment membership. Flag if the segment is too small for its intended purpose (e.g., under 1,000 for ad targeting, under 100 for email A/B testing) or too broad (e.g., over 80% of total database — likely under-filtered and lacking targeting precision).
5. **Check overlap with existing segments**: Query existing segments on the platform to identify overlap — contacts who already belong to active segments used in current campaigns. Present overlap percentage, shared contact count, and recommend whether to exclude overlapping contacts, merge segments, or accept overlap based on the segment's purpose and campaign frequency capping rules.
6. **Apply exclusion criteria**: Layer in exclusion rules — unsubscribed contacts, hard bounces, suppression lists, competitors, internal team members, and any user-specified exclusions. Show the impact of each exclusion rule on segment size individually and cumulatively.
7. **Validate compliance for ad platform audiences**: If syncing to ad platforms, verify that contacts have appropriate consent for advertising use (not just email consent), confirm the audience matches platform-specific requirements (hashed email format for Customer Match, minimum audience size), and check for platform terms of service compliance.
8. **Create segment definition payload**: Build the platform-specific segment definition — filter criteria in the platform's API format, segment name, description, type (dynamic/static), refresh schedule, folder or tag assignment for organization, and any cross-platform sync configuration.
9. **Create approval gate**: Assess risk as medium for all segment operations. Present segment preview showing criteria summary in human-readable format, estimated member count, percentage of total database, overlap with existing segments, exclusion impact, sample member profiles (top 5 representative contacts), and the platform where the segment will be created.
10. **On approval, create segment via platform MCP**: Push the segment definition to the target platform through the appropriate MCP. For ad platform audiences, initiate the audience sync, wait for processing confirmation, and verify match rate. For CRM/email segments, confirm creation and initial member population count.
11. **Initiate cross-platform sync (if requested)**: For multi-platform segments, push the audience to additional destinations — hash emails for ad platform Customer Match uploads, format phone numbers per platform requirements, and initiate sync jobs. Monitor match rates and flag significant drops between source and destination counts.
12. **Verify segment creation and log results**: Confirm the segment was created successfully on all target platforms — verify member count matches estimate within acceptable variance, spot-check sample members against criteria, confirm the segment appears correctly in each platform's UI, and document any match rate discrepancies. Log execution to `~/.claude-marketing/brands/{slug}/logs/segment-log.json`.

## Output

A structured audience segmentation report containing:

- **Segment ID and platform confirmation**: The segment's unique identifier on the target platform, creation timestamp, segment type (dynamic/static), and direct link to the segment in the platform UI
- **Member count**: Total contacts in the segment after all criteria and exclusions are applied, with comparison to initial estimate, percentage of total database, and comparison to minimum size requirements for the stated purpose
- **Criteria documentation**: Complete human-readable criteria used — each filter rule, logical operators (AND/OR), date ranges, numeric thresholds, and exclusions — formatted as a reference document for team knowledge transfer and future segment maintenance
- **Platform filter logic**: The exact filter configuration as implemented on the platform — API-level criteria for auditing, debugging, and replicating on other platforms
- **Overlap analysis**: Percentage overlap with each active segment, shared contact count per segment, and assessment of whether overlap creates audience fatigue risk, budget waste (paying to reach the same person twice), or is intentional (e.g., retargeting a subset)
- **Exclusion impact report**: How many contacts each exclusion rule removed individually, cumulative exclusion count, and the final included-to-excluded ratio with breakdown by exclusion reason
- **Sample member profiles**: 5 representative contacts from the segment showing key fields — name, email, company, engagement level, lifecycle stage, score, and which specific criteria they matched
- **Cross-platform sync status**: If synced to ad platforms — match rate per platform, audience size at each destination, processing status, estimated time to full population, and any hashing or formatting transformations applied
- **Segment size trend (for updates)**: If updating an existing segment — member count change (added, removed, net change), criteria modifications applied, and trend of segment size over the last 5 refreshes if available
- **Lookalike audience readiness**: Assessment of whether this segment is suitable as a lookalike seed — size within optimal range (1,000-10,000), engagement quality score, demographic coherence, and recommended lookalike expansion percentages per ad platform
- **Segment quality score**: Assessment of segment targeting precision — criteria specificity (narrow vs. broad), engagement level distribution within the segment, demographic coherence, and predicted response rate compared to the full database
- **Recommended next steps**: Suggested actions — sync to ad platform for lookalike creation, trigger email nurture sequence, build personalized landing page variant, create complementary exclusion segment, schedule recurring refresh for dynamic segments, or split-test segment criteria for optimization
- **Related segments**: Existing segments that could be combined with, used alongside, or explicitly excluded from this new segment — with overlap percentages and use case recommendations
- **Execution log**: Timestamped record of the segmentation process — platform API calls, response status, population duration, match rates, cross-platform sync results, and any warnings or errors encountered

## Agents Used

- **crm-manager** — Segment criteria logic, CRM data querying, deduplication, overlap analysis, platform-specific filter construction, compliance verification, cross-platform sync, and segment creation management
- **email-specialist** — Email engagement-based segmentation criteria, suppression list management, deliverability considerations, frequency capping logic, and email platform segment optimization
- **media-buyer** — Ad platform audience requirements, lookalike seed quality assessment, Customer Match formatting, and ad platform audience sync verification
