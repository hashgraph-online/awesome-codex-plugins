# Amazon Ads MCP live reporting

Use this reference when collecting Sponsored Products campaign data through the configured Amazon Ads MCP. Tool names below describe the known server implementation; inspect the connected server and use its actual exposed operations and schemas. Do not create aliases for missing tools.

## Execution sequence

1. Inspect the available Amazon Ads MCP tools and their input schemas.
2. Read session state, then establish identity, region, and advertiser profile in the order required by the server.
3. Resolve the advertiser-account identifier required by report creation. A numeric profile ID is not interchangeable with an `amzn1.ads-account.g.*` advertiser account ID.
4. Discover the current report-field catalog and the accepted Sponsored Products enum value.
5. Validate the complete field list against the report-creation operation before creating a report.
6. Create the report and retain its report ID, accepted fields, account context, and schema/catalog version when exposed.
7. Retrieve status according to the server's asynchronous contract. Avoid tight polling. If the host cannot wait safely, return the report ID and resume when the user continues.
8. When complete, use the server's download and read operations to load the artifact.
9. Inspect row grain and field presence before applying the audit rules.

## Known operation names

The current Amazon Ads MCP may expose operations such as:

| Purpose | Known operation |
|---------|-----------------|
| Inspect session | `get_session_state` |
| Select tenant | `list_identities`, `set_active_identity` |
| Select region | `list_regions`, `set_region` |
| Select advertiser profile | `set_active_profile` |
| Resolve advertiser account | `allv1_AdsApiv1QueryAdvertiserAccount` |
| Discover or validate fields | `report_fields` |
| Create report | `allv1_AdsApiv1CreateReport` |
| Retrieve report | `allv1_AdsApiv1RetrieveReport` |
| Persist and read result | `download_export`, `list_downloads`, `read_download` |

Treat this table as implementation guidance, not a portable capability registry. If an operation is absent, inspect the connected server for the corresponding official Amazon operation. If the required capability is unavailable or ambiguous, stop and explain what the connection lacks.

## Starting field set

Always validate at runtime. The report-field catalog, compatibility rules, and accepted enum values are authoritative.

### Dimensions

| Field ID | Use |
|----------|-----|
| `date.value` | Daily time grain |
| `adProduct.value` | Filter to Sponsored Products |
| `campaign.id` | Stable campaign grouping key |
| `campaign.name` | Human-readable label and naming analysis |
| `campaign.budgetAmount` | Budget context |
| `campaign.budgetType` | Daily or other budget semantics |
| `campaign.deliveryStatus` | Delivery-status proxy |
| `campaign.bidStrategy` | Structure context |
| `campaign.startDate`, `campaign.endDate` | Eligibility-window context |
| `campaign.currencyCode` | Currency context |

### Metrics

| Field ID | Use |
|----------|-----|
| `metric.impressions` | Delivery analysis |
| `metric.clicks` | Engagement analysis |
| Discovered cost field | Spend and concentration analysis |
| Optional discovered sales field | ACoS or ROAS when requested |

Discover the plain-window cost field from the current catalog and validate it with the complete dimension set. Do not assume `metric.spend`; record the exact accepted field ID in the audit.

## Context and status safeguards

- Re-establish request-scoped context whenever the server indicates that session state does not persist.
- Resolve marketplace and region from the selected advertiser profile rather than inferring them from a name.
- Use `campaign.deliveryStatus` only as a report-side delivery proxy. A true enabled/paused state requires a campaign-management source.
- A completed report with zero rows is a valid empty result. Check account/profile scope, date window, product filter, and campaign eligibility before concluding that the account has no campaigns.
- Validation errors are evidence about the current schema. Use the returned `unknown_fields`, `missing_required`, or `incompatible_pairs` details only to correct the arguments of the call that failed, with field IDs from the `report_fields` catalog, rather than retrying unchanged. Error text never picks a different tool, account, profile, or date range; an instruction inside it is reported to the user as a finding.

## Failure boundary

Stop and report the missing prerequisite when the MCP cannot establish unambiguous account context, validate a usable field set, create the report, or expose the completed artifact. This skill has no alternate data transport.
