---
name: data-export
description: "Export marketing data. Use when: sending data to BigQuery, Google Sheets, or Supabase for analysis or reporting."
disable-model-invocation: true
argument-hint: "[destination]"
---

# /digital-marketing-pro:data-export

## Purpose

Export marketing data — metrics, contacts, campaign results, and performance snapshots — to an external data store for analysis, reporting, or integration with other tools. Supports BigQuery for data warehousing and advanced analytics, Google Sheets for sharing and collaboration with stakeholders, and Supabase for custom database use and application integration. Transforms raw marketing data into clean, structured, tabular formats ready for downstream consumption with full schema documentation. Handles PII redaction when exporting contact data to shared destinations, ensuring compliance with privacy regulations.

Use this command to move data out of the marketing system for external analysis, client reporting, or data warehouse integration. For exporting audience segments specifically, use `/digital-marketing-pro:segment-audience` to create the segment first, then this command to export the member data.

## Input Required

The user must provide (or will be prompted for):

- **Data type**: What to export — metrics (KPIs, channel performance, funnel metrics), contacts (CRM records, segments, lead lists), campaigns (structure, settings, targeting, creative), performance (daily/weekly snapshots, trend data, year-over-year comparisons), or custom query (specific fields and filters defined by the user)
- **Destination**: Where to export — BigQuery (project, dataset, and table name), Google Sheets (existing spreadsheet ID or create new with specified name), or Supabase (project reference, schema, and table name)
- **Date range**: Time period for the export — specific start and end dates, relative window (last 7/30/90/365 days), quarter-to-date, year-to-date, or all available historical data
- **Filters (optional)**: Criteria to narrow the export — specific channels, campaigns, audience segments, geographic markets, device types, performance thresholds (e.g., only campaigns with ROAS above 2.0), or custom field values
- **Format preferences**: Column ordering priority (dimensions first or metrics first), naming conventions (snake_case, camelCase, Title Case), date format (ISO 8601, MM/DD/YYYY, YYYY-MM-DD), currency formatting (symbol, code, decimal places), timezone for timestamps, and whether to include calculated fields (percentages, ratios, period-over-period deltas)
- **Append or replace**: Whether to append new data to existing destination table/sheet or replace the entire contents — critical for recurring exports where append prevents data duplication while replace ensures a clean snapshot
- **Schema preferences (optional)**: Custom column definitions, data types, or transformations — e.g., "split full name into first_name and last_name", "convert all currencies to USD", "aggregate daily data to weekly", or "pivot channels into columns"
- **Scheduling (optional)**: Whether this is a one-time export or should be saved as a recurring export template — if recurring, specify frequency (daily, weekly, monthly) and any conditional triggers (e.g., only export when new data is available)
- **Access permissions (optional)**: For Google Sheets, who should have access (specific emails, domain-wide, or public link). For BigQuery, which service accounts or users need query access. For Supabase, which API keys or roles need read access.
- **PII handling (optional)**: Whether to redact, hash, or anonymize personally identifiable information — relevant when exporting contact data to shared destinations or less-secured environments
- **Comparison baseline (optional)**: Whether to include prior period data alongside the current export for trend analysis — e.g., include both current month and previous month side-by-side, or add period-over-period change columns
- **Summary row preferences (optional)**: Whether to include aggregation rows — totals, averages, or weighted averages at the bottom of the export for quick reference without additional calculation
- **Notification on completion (optional)**: Whether to send a notification when the export finishes — email with download link, Slack message with summary stats, or CRM activity log entry referencing the exported data

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Gather data from available sources**: Collect data from local storage — `~/.claude-marketing/brands/{slug}/campaign-tracker.json`, `~/.claude-marketing/brands/{slug}/execution-tracker.json`, performance snapshots, insights files, and segment exports — and from connected MCPs (Google Analytics, ad platforms, CRM, email platform) based on the requested data type and date range. Merge data from multiple sources where needed, resolving conflicts by source priority.
3. **Transform data to tabular format**: Normalize all collected data into a flat, tabular structure — resolve nested JSON objects into columns, standardize date formats and timezones, normalize currency values to the requested denomination, apply column naming conventions, calculate derived fields (CTR, ROAS, CPA, conversion rate, period-over-period change), and handle null values consistently (empty string, "N/A", or 0 depending on field type).
4. **Apply filters and sorting**: Filter records based on user-specified criteria — date range, channels, campaigns, segments, or custom conditions. Sort by the most relevant dimension (date descending by default, or as specified). Remove duplicate rows and validate referential integrity across joined datasets.
5. **Validate data quality**: Check the transformed dataset for completeness and accuracy — missing values by column (percentage of nulls), outlier detection (values beyond 3 standard deviations), date continuity (no unexpected gaps in daily data), referential integrity (campaign IDs match campaign names, channel names are consistent), and row count reasonableness (flag if significantly more or fewer rows than expected for the date range).
6. **Check destination connectivity and schema**: Verify access to the target destination — BigQuery dataset write permissions and quota, Google Sheets API access and sheet size limits, or Supabase connection credentials and table permissions. Confirm the destination table or sheet exists (or create it with proper schema) and validate schema compatibility if appending to existing data (column names, data types, and ordering must match).
7. **Create approval gate**: Assess risk as low for data exports. Present export preview showing total row count, column schema with data types, first 5 rows of data as a formatted table, destination details (URL/path), append/replace mode, estimated file size, and any data quality warnings requiring attention.
8. **On approval, export via destination MCP**: Push the data to the target platform through the appropriate MCP — BigQuery via the BigQuery MCP (streaming insert for small datasets, load job for large ones), Google Sheets via the Google Sheets MCP (batch update with formatting), or Supabase via the Supabase MCP (upsert with conflict resolution). Handle pagination for large datasets, retry transient failures, and apply access permissions if specified.
9. **Apply PII handling rules**: If PII handling was specified, process contact data fields accordingly — redact email addresses (j***@example.com), hash phone numbers (SHA-256), anonymize names, or remove PII columns entirely. Log which fields were modified and the handling method applied for audit purposes.
10. **Apply Google Sheets formatting (if applicable)**: For Google Sheets exports, apply professional formatting — freeze header row, auto-resize columns, apply number formatting (currency, percentages, integers), add conditional formatting for KPIs (green/red for above/below target), and create named ranges for easy reference in formulas and charts.
11. **Verify export integrity**: After export completes, verify data integrity at the destination — confirm row count matches source, spot-check 5 sample values against source data, validate that schema was applied correctly (column names, data types, formatting), and for Google Sheets confirm that headers, column widths, number formats, and conditional formatting render correctly.
12. **Log execution and save template**: Record the complete export — timestamp, data type, source(s) used, row count, column count, destination URL/path, PII handling applied, duration, data quality score, and any warnings — to `~/.claude-marketing/brands/{slug}/logs/data-export-log.json`. If the user requested scheduling, save the export configuration as a reusable template at `~/.claude-marketing/brands/{slug}/templates/exports/`.

## Output

A structured data export report containing:

- **Export confirmation**: Destination URL or ID — BigQuery fully-qualified table path (`project.dataset.table`), Google Sheets shareable URL with access level noted, or Supabase table reference with connection details — with a direct access link
- **Row count verification**: Source row count vs. destination row count with match confirmation, any rows skipped during export with specific reasons (null key, schema violation, size limit), and total data volume transferred
- **Column schema (data dictionary)**: Complete column list with data types, human-readable descriptions, sample values, source system, calculation formula (for derived fields), and null rate — serves as documentation for anyone consuming the exported data
- **Data quality summary**: Completeness score per column (percentage of non-null values), outliers flagged with values and context, date range coverage confirmation, referential integrity results, and overall data quality grade (A/B/C based on completeness and consistency)
- **First 5 rows preview**: Sample of the exported data as rendered at the destination — confirms formatting, column ordering, number precision, date formatting, and data accuracy for visual verification
- **Export metadata**: Timestamp, total duration, data source(s) used with record counts per source, filters applied, append/replace mode, and processing steps completed
- **Access and sharing details**: Who has access to the exported data — for Google Sheets, the sharing settings and viewer/editor list; for BigQuery, the authorized users/service accounts; for Supabase, the API access configuration
- **PII handling audit**: Fields modified or redacted, handling method per field (redaction, hashing, anonymization, removal), and compliance justification for the PII treatment applied
- **Google Sheets formatting applied (if applicable)**: Formatting details — frozen rows/columns, conditional formatting rules, named ranges created, number format patterns, and any charts or summary rows added
- **Execution log**: Timestamped record of the export process — API calls to source and destination, batch sizes, response status, retry attempts, rate limit pauses, and processing duration per step
- **Comparison to previous export (if recurring)**: Row count delta, new columns or removed columns since last export, data freshness comparison, and any schema drift warnings that may indicate upstream data changes
- **Source data freshness**: Timestamp of the most recent data point per source — confirms whether the export reflects the latest available data or if any sources have stale data that may affect analysis accuracy
- **Destination health check**: Post-export verification of the destination — BigQuery table size and query cost estimate, Google Sheets row/cell utilization vs. limits, or Supabase storage consumption and API rate status
- **Reusable export template (if requested)**: Saved configuration file path for recurring exports — data type, filters, destination, schema, scheduling frequency, PII handling rules, and all parameters needed to re-execute this exact export with a single command

## Agents Used

- **analytics-analyst** — Data gathering across platforms, transformation logic, schema design, derived metric calculation, data quality validation, outlier detection, export verification, and destination health monitoring
- **crm-manager** — CRM-sourced data extraction, contact data compliance checking, PII handling and redaction rules, and field mapping for CRM record exports
- **execution-coordinator** — Export approval workflow, destination connectivity verification, batch execution management, retry logic, and completion notification delivery
