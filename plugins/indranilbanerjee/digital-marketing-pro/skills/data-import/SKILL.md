---
name: data-import
description: "Import data from external sources. Use when: loading CRM contacts, email lists, or campaign data from CSV, JSON, or Sheets."
disable-model-invocation: true
argument-hint: "[source-file or URL]"
---

# /digital-marketing-pro:data-import

## Purpose

Universal data import tool for bringing structured data into any connected platform. Import from CSV, JSON, or Google Sheets into CRM systems, email subscriber lists, audience segments, competitor trackers, campaign managers, or custom data stores. Handles the full import pipeline — field mapping with auto-suggestion, data validation, deduplication against existing records, consent and compliance verification for contact data, batched execution through platform MCPs, and detailed result reporting with rollback guidance if needed.

## Input Required

The user must provide (or will be prompted for):

- **Data source**: File path to a local CSV or JSON file, or a Google Sheets URL — the raw data to import. For CSV, specify delimiter if non-standard. For Google Sheets, specify the sheet name and range if not the full first sheet. The file must be accessible from the current environment
- **Destination platform**: Where the data should land — CRM (HubSpot, Salesforce), email platform (Mailchimp, ActiveCampaign, SendGrid), audience manager, competitor tracker, or custom destination. Must have the corresponding MCP server connected and configured in `.mcp.json`
- **Field mapping**: How source columns map to destination fields — provide explicit mappings (e.g., "Company Name" -> "company", "Work Email" -> "email"), or request auto-mapping where the system suggests mappings based on column name similarity. Unmapped columns are flagged for review, and unmapped required destination fields block the import until resolved
- **Import options (optional)**: Deduplication strategy (`skip` duplicates, `update` existing records, or `create-new` regardless — default is `skip`), consent verification level (`strict` requires explicit opt-in field, `standard` checks for unsubscribe flags, `none` for non-contact data), batch size for API writes (default 100), and dry-run mode to validate without executing

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply compliance rules for target markets (`skills/context-engine/compliance-rules.md`) — especially GDPR, CAN-SPAM, and CCPA requirements for contact data imports. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Read and parse source data**: Load the data from the specified source — parse CSV with header detection and delimiter handling, parse JSON with schema inference, or fetch from Google Sheets via the Google Sheets MCP. Validate basic format integrity — consistent column count across rows, parseable data types, no completely empty rows or columns. Report source statistics: total records, columns detected, data types inferred.
3. **Field mapping wizard**: Auto-suggest mappings based on column name similarity to destination field names (fuzzy matching on common patterns like "email", "first_name", "phone", "company"). Present the suggested mapping for user confirmation. Flag any unmapped source columns (data that will be ignored) and any unmapped required destination fields (blockers that must be resolved before import). Allow the user to adjust, add, or remove mappings.
4. **Validate data quality**: Run validation checks on every record — email format validation (RFC 5322), phone number format detection, required fields present and non-empty, data type conformance (dates, numbers, strings), field length limits per destination platform. Detect duplicates within the import file itself. If CRM is connected, check for duplicates against existing records using email or phone as match keys. For email and SMS imports, verify consent fields — check for explicit opt-in timestamps, unsubscribe flags, and compliance with the brand's market regulations.
5. **Create approval gate**: Present a comprehensive import summary for user confirmation — total records in source, records passing validation, records failing validation (with categorized reasons), duplicate records detected (within file and against existing data), consent verification status for contact imports, destination platform and target object type, field mapping summary, and deduplication strategy that will be applied. Block execution until the user explicitly approves.
6. **Execute import via destination MCP**: On approval, write records to the destination platform in batches through the appropriate MCP — CRM contacts via CRM MCP (HubSpot or Salesforce), email subscriber lists via email MCP (Mailchimp, ActiveCampaign, or SendGrid), competitor baseline data via `competitor-tracker.py`, or audience segments via the audience manager. Track success, failure, and skip status per record. Implement retry logic for transient API failures (rate limits, timeouts) with exponential backoff.
7. **Report results**: Generate a detailed import results report — records successfully imported with destination IDs, records that failed with specific error reasons per record, records skipped due to deduplication or validation, consent verification summary, total API calls made, and processing time. If failures exceed 10% of total records, flag for review and provide rollback guidance.

## Output

A structured import results report containing:

- **Import summary**: Total records processed, successfully imported, failed, skipped (duplicates), and skipped (validation failures) — with percentage breakdown and processing time
- **Field mapping used**: Final mapping applied between source columns and destination fields, including any auto-mapped fields and user overrides, for audit trail and reuse on future imports
- **Validation report**: Categorized list of data quality issues found — invalid emails, missing required fields, format mismatches, field length violations — with affected record counts and sample values for each issue type
- **Consent verification status**: For contact data imports — count of records with verified opt-in, records missing consent, records with unsubscribe flags, and compliance assessment against the brand's target market regulations (GDPR, CAN-SPAM, CCPA)
- **Destination confirmation**: Platform name, object type, batch count, API response summary, and destination record IDs for successfully imported records where available
- **Error details for failed records**: Per-record failure reasons grouped by error type — API validation errors, rate limit failures after retry exhaustion, permission errors, and data format rejections from the destination platform
- **Rollback instructions**: If the import needs to be reversed — record IDs to delete, API endpoints to use, and batch deletion guidance for the destination platform

## Agents Used

- **execution-coordinator** — Import pipeline orchestration from source parsing through MCP execution, approval workflow with comprehensive pre-import summary and risk assessment, batched MCP data writing with retry logic and error handling, execution logging with per-record status tracking, and rollback guidance generation for failed or problematic imports
- **crm-manager** — CRM-specific field mapping intelligence with platform schema awareness (HubSpot properties, Salesforce fields), deduplication logic using email and phone match keys against existing CRM records, contact data quality scoring, and consent field verification against compliance requirements for the brand's target markets
