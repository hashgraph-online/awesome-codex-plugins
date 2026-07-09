---
name: crm-sync
description: "Sync data to CRM platforms. Use when: pushing contacts, deals, or campaigns to Salesforce, HubSpot, Zoho, or Pipedrive."
disable-model-invocation: true
argument-hint: "[crm-platform]"
---

# /digital-marketing-pro:crm-sync

## Purpose

Sync marketing data to and from the brand's connected CRM platform. Handles contact creation, deal updates, and campaign linking with automatic field mapping, deduplication, and compliance checks. Supports Salesforce, HubSpot, Zoho, and Pipedrive with bi-directional sync capabilities, ensuring marketing and sales teams operate from a single source of truth without manual data entry or import/export cycles. Designed for both one-time bulk syncs and recurring automated transfers, with full audit trails and rollback capabilities for enterprise-grade data governance.

Use this command instead of manual CSV imports when you need deduplication, compliance validation, or audit logging. For lead-specific imports with scoring, use `/digital-marketing-pro:lead-import` instead.

## Input Required

The user must provide (or will be prompted for):

- **Sync type**: What to sync — contacts, deals, campaigns, or a combination of multiple object types in a single operation
- **Data source**: Where the data comes from — CSV file path, JSON array, manual entry, or data from another connected MCP (e.g., Google Sheets, email platform, ad platform)
- **Target CRM platform**: Salesforce, HubSpot, Zoho, or Pipedrive — and the specific object type if applicable (e.g., Salesforce Leads vs. Contacts, HubSpot Contacts vs. Companies)
- **Sync direction**: One-way push (marketing to CRM), one-way pull (CRM to marketing), or bi-directional merge with conflict resolution preference (source wins, CRM wins, or most recent wins)
- **Field mapping overrides (optional)**: Custom mappings if default field mapping does not match the CRM's schema — e.g., "company_name" maps to "Account Name" in Salesforce, or "phone_mobile" maps to "MobilePhone"
- **Deduplication strategy**: Match on email, phone, CRM ID, or composite key — and whether to update existing records, skip duplicates, or merge fields from both sources
- **Consent and compliance requirements**: Whether GDPR consent fields, opt-in status, or data processing basis must be validated before sync — and which markets' regulations apply
- **Record filters (optional)**: Criteria to limit which records are synced — date range, segment membership, source campaign, lifecycle status, or custom field values
- **Batch size preference (optional)**: Number of records per API batch — smaller batches for safer rollback, larger batches for speed on high-volume syncs
- **Notification preferences**: Whether to alert sales reps when new contacts or deals are synced to their pipeline, and via which channel (CRM notification, email, Slack)
- **Relationship linking**: Whether to associate synced contacts with existing accounts, deals, or campaigns in the CRM — and the lookup key for matching (domain, account name, deal ID)
- **Tag or list assignment (optional)**: Tags, lists, or campaign memberships to apply to synced records for downstream segmentation and reporting attribution
- **Error handling preference**: What to do when individual records fail — skip and continue (log failures for later), halt the entire sync (rollback completed records), or quarantine failed records for manual review
- **Sync schedule (optional)**: Whether this is a one-time sync or should be saved as a recurring sync template — if recurring, specify frequency (hourly, daily, weekly) and whether to sync only records modified since the last run (incremental) or all matching records (full)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Check connected CRM status**: Run `crm-sync.py --action get-crm-status` to verify platform connection, API credentials, rate limit headroom, and available objects. If no CRM is connected, guide the user to configure their CRM MCP integration and provide platform-specific setup instructions.
3. **Validate input data**: Parse the source data and validate required fields — check email format (RFC 5322), phone number normalization (E.164), required field presence, data type consistency, and character encoding. Flag invalid records with specific error reasons and separate them from the valid set.
4. **Map fields to CRM schema**: Consult `skills/context-engine/crm-integration-guide.md` for standard field mappings per platform. Auto-map matching field names, apply user overrides, identify unmapped source fields, and flag required CRM fields with no source mapping. Present the complete field mapping table for confirmation before proceeding.
5. **Check for duplicates**: Run `crm-sync.py --action check-dedup` against the target CRM using the selected deduplication strategy. Identify exact matches, fuzzy matches (Levenshtein distance on name + domain), and genuinely new records. Present dedup results with recommended actions per record (create, update, skip, merge).
6. **Validate compliance requirements**: Check consent fields, opt-in status, and data processing basis against compliance rules for the brand's target markets. Flag records missing required consent or violating data retention policies. For GDPR markets, verify lawful basis is documented per record.
7. **Prepare CRM-ready payloads**: Transform validated, deduplicated records into platform-specific API payloads with correct field names, data types, picklist values, relationship references (e.g., linking contacts to accounts), and owner assignment based on territory or round-robin rules.
8. **Create approval gate**: Assess risk level — medium for fewer than 100 records, high for 100 or more. Present sync preview showing total record count, create/update/skip breakdown, dedup results, field mapping summary, compliance status, and any validation warnings requiring attention.
9. **On approval, execute sync via CRM MCP**: Push payloads to the target CRM through the platform MCP in batched requests. Handle rate limits with exponential backoff, retry transient failures up to 3 times, and log each record's outcome (created with ID, updated with changed fields, skipped with reason, failed with error code).
10. **Verify record counts and data integrity**: Confirm synced record counts match expected totals by querying the CRM post-sync. Spot-check 5 random records to verify field values transferred correctly. Flag any count mismatches or data discrepancies for immediate investigation.
11. **Apply relationship linking and tags**: For synced records, execute relationship associations — link contacts to accounts by domain match, associate contacts with deals by email, and apply campaign memberships. Add tags and list assignments specified by the user for downstream segmentation.
12. **Generate rollback manifest**: Create a reversible change manifest listing every record ID created or modified, with previous field values stored, enabling targeted rollback within the CRM if data quality issues surface post-sync.
13. **Log results and notify**: Record the complete sync execution — timestamp, record counts, field mapping, errors, relationship links created, and duration — to `~/.claude-marketing/brands/{slug}/logs/crm-sync-log.json`. If notification preferences were set, alert relevant sales reps about new records in their pipeline.

## Output

A structured CRM sync report containing:

- **Sync summary**: Total records processed with breakdown — created, updated, skipped (duplicates), and failed counts with percentages and comparison to expected totals
- **Deduplication report**: Duplicate records found with match type (exact/fuzzy), match fields used, confidence score, and action taken (updated, skipped, or merged) for each duplicate pair
- **Field mapping table**: Complete source-to-CRM field mapping used, including auto-mapped fields, user overrides, unmapped source fields, and any default values applied to required CRM fields
- **Compliance audit**: Records flagged for missing consent, opt-in gaps, or data processing basis issues — with remediation recommendations per record and applicable regulation referenced
- **Validation error report**: Invalid records listed with specific field-level errors — malformed email, missing required field, data type mismatch, or encoding issue — and suggested corrections
- **Execution log**: Timestamped record of every API call — batch number, records per batch, response status, retry attempts, rate limit pauses, and processing duration per batch
- **Rollback reference**: Record IDs created or modified during this sync with previous field values, enabling targeted rollback if issues are discovered post-sync
- **Data integrity verification**: Post-sync spot-check results — 5 randomly sampled records compared source vs. CRM to confirm field accuracy across all mapped fields
- **Relationship linking summary**: Contacts linked to accounts, deals associated with campaigns, and any relationship links that failed due to missing target records — with manual resolution steps
- **Performance metrics**: Sync throughput (records per second), total API calls consumed, rate limit utilization percentage, and estimated time for future syncs of similar size
- **Tag and list assignment confirmation**: Tags applied, lists assigned, and campaign memberships created — with counts per tag/list and any assignment failures noted
- **Conflict resolution log (bi-directional only)**: For bi-directional syncs, each field-level conflict encountered — source value, CRM value, resolution applied (source wins, CRM wins, most recent wins), and any conflicts requiring manual review
- **Next sync recommendations**: Suggested follow-up actions — re-sync failed records, schedule recurring syncs, clean up unmapped fields, update field mapping defaults, or configure automated bi-directional sync

## Agents Used

- **crm-manager** — Field mapping, deduplication logic, data validation, CRM schema resolution, compliance checking, payload preparation, owner assignment, relationship linking, and sync execution management
- **execution-coordinator** — Approval workflow, risk assessment, batched execution orchestration, rate limit handling, retry logic, rollback manifest generation, notification delivery, and execution logging
