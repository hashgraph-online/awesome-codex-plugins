---
name: "vibe-prospecting-hubspot"
description: "Field mapping from Vibe Prospecting prospects and businesses to HubSpot Contacts and Companies, using real field names on both sides. Use this skill whenever Vibe Prospecting prospect or business data is inserted into or updated in HubSpot, including requests like \"get prospects from Vibe and insert them into HubSpot\", and whenever the user asks how Vibe Prospecting fields map to HubSpot properties."
metadata:
  version: "1.1.0"
---

# Vibe Prospecting → HubSpot field mapping

Vibe Prospecting **prospects** map to HubSpot **Contacts**. Vibe Prospecting **businesses** map to HubSpot **Companies**.

Vibe Prospecting field names are the column names in Vibe Prospecting results. HubSpot properties are shown with their label and internal name.

**When this mapping applies.** Whenever Vibe-sourced fields are written to HubSpot (insert or update), use the destinations in these tables, even if the user did not ask about mapping. This rule only decides *where* Vibe-sourced fields go. It does not authorize a write, and it does not add records or fields beyond what the user asked for.

## Property definitions are the user's to manage

- Never create or modify HubSpot property definitions or enumeration options.
- Before writing, check that each mapped destination exists on the correct object (Contacts for prospects, Companies for businesses).
- For ordinary mapped fields, if a destination is missing or cannot accept the raw value (for example an invalid enumeration option), omit that field, report its HubSpot label and internal name, and continue with the other mapped fields. The list name below is required by default; skip it only when the user explicitly requests that exception.
- Do not silently substitute another destination, and do not transform, split, truncate or derive values to make them fit. The only scoped exception is the additional-phone extraction described below; do not apply it to other fields.

Custom destinations are marked **(custom)** and must be created by the user in HubSpot before they can receive data. They use the `VP` label prefix and `vp_` internal-name prefix. Users may change these defaults in their own skill instance.

**To change a destination:** create the property yourself in HubSpot (Settings → Properties), or pick an existing one. Then edit the row in this file: update the HubSpot label, internal name, type and the custom marker. Keep the Vibe Prospecting field name unchanged. Reinstall the updated skill.

If you edit a destination in a mapping table, use that row's edited label, internal name, and type—not the default property names mentioned elsewhere in this file.

## List name before export

By default, before each new export for a HubSpot push, suggest a list name based on the user's request and conversation, then ask the user to approve it or provide a different name. Do not offer the dataset name as a default. If the user already explicitly supplied a name for this export, that is their confirmation; do not ask again. Do not proceed with an unconfirmed or blank name, or silently reuse one from a different export.

The default destination on Contacts and Companies is **VP List Name** (`vp_list_name`, single-line text, custom). The user may explicitly choose a different existing destination for this push or explicitly ask to skip the list-name field. Honor that choice for this push without requiring a skill edit or reinstall. Do not infer permission to skip or change the destination from a missing property or general export approval. For a lasting change to the default, the user may edit this destination in the skill and reinstall it.

Unless the user explicitly asked to skip the list name, check the chosen destination's live HubSpot property definition on every target object type before export. It must exist and accept the confirmed name. If missing or incompatible, identify its label, internal name, and object type, and ask the user to create/fix it manually, choose another existing property, or explicitly request skipping the list-name field. Stop the push before export until a usable destination is verified or the user explicitly requests skipping it. Never create properties or silently substitute a destination.

When the list name is not skipped, write the confirmed name unchanged on every contact and company inserted or updated. Recheck the chosen destination before record writes; if it is no longer usable, stop until resolved or the user explicitly requests skipping it. If the user explicitly requests skipping it, omit the field and reflect that choice in the pre-write report. The name approval or skip request is not approval for export cost or HubSpot writes; retain the existing approval requirements. This is a field only: do not create a HubSpot list or add list memberships. Other fields retain ordinary mapping/reporting behavior without dedicated missing-field prompts.

## Show the field mapping before writing to HubSpot (required)

After the Vibe Prospecting data is exported and before any record is created or updated in HubSpot, always show the user a field-mapping report for this specific push. Build it from a live check of the target HubSpot account, not from this file alone:

1. Check every destination in the relevant table(s) below against the account. For enumeration destinations such as Lead Status, also confirm the required option exists.
2. Check the exported data: note which Vibe fields actually have values for the rows being pushed.
3. Present one table per object type being written, with these columns:

| Vibe Prospecting field | HubSpot label | Internal name | In HubSpot? | Written in this push? |
|---|---|---|---|---|

   - **In HubSpot?**: ✅ Exists (mark standard vs custom where useful) or ❌ Missing.
   - **Written in this push?**: ✅ Yes; ➖ No data (destination exists but the field is empty for these rows, with a short reason, e.g. "emails only were requested"); or ❌ Skipped (destination missing or cannot accept the value).
   - Include every mapped field from the table, not only the ones being written, so the user sees what exists and what does not.
   - One report row per mapping-table row; never merge rows (e.g. VP Additional Phone Number 1–3 are three rows).
   - Put the list-name row first in each contact/company report table and bold its label and value so it stands out from other fields. Show the chosen destination or that the user explicitly requested skipping it. Unless explicitly skipped, stop if it cannot be written. Add rows for Lead Status on new contacts and associations being created (e.g. contact → existing company, with its ID).
4. Then ask for approval of the write as usual. The mapping report does not replace the HubSpot record-level confirmation; show both, or combine them in one message.

## Contacts: Vibe Prospecting prospect → HubSpot Contact

| Vibe Prospecting field | HubSpot label | HubSpot internal name | Type |
|---|---|---|---|
| `prospect_first_name` | First Name | `firstname` | Single-line text |
| `prospect_last_name` | Last Name | `lastname` | Single-line text |
| `contact_professional_email` | Email | `email` | Single-line text |
| `contact_mobile_phone` | Mobile Phone Number | `mobilephone` | Single-line text |
| `contact_phone_numbers` (additional number 1; see extraction below) | VP Additional Phone Number 1 **(custom)** | `vp_additional_phone_number_1` | Single-line text |
| `contact_phone_numbers` (additional number 2; see extraction below) | VP Additional Phone Number 2 **(custom)** | `vp_additional_phone_number_2` | Single-line text |
| `contact_phone_numbers` (additional number 3; see extraction below) | VP Additional Phone Number 3 **(custom)** | `vp_additional_phone_number_3` | Single-line text |
| `prospect_job_title` | Job Title | `jobtitle` | Single-line text |
| `prospect_company_name` | Company Name | `company` | Single-line text |
| `prospect_company_website` | Website URL | `website` | Single-line text |
| `prospect_city` | City | `city` | Single-line text |
| `prospect_region_name` | State/Region | `state` | Single-line text |
| `prospect_country_name` | Country/Region | `country` | Single-line text |
| `prospect_linkedin` | LinkedIn URL | `hs_linkedin_url` | Single-line text |
| `prospect_id` | VP Prospect ID **(custom)** | `vp_prospect_id` | Single-line text |
| `business_id` | VP Business ID **(custom)** | `vp_business_id` | Single-line text |
| `prospect_full_name` | VP Full Name **(custom)** | `vp_full_name` | Single-line text |
| `prospect_job_department` | VP Job Department **(custom)** | `vp_job_department` | Single-line text |
| `prospect_job_seniority_level` | VP Job Seniority Level **(custom)** | `vp_job_seniority_level` | Single-line text |
| `contact_professional_email_status` | VP Email Status **(custom)** | `vp_email_status` | Single-line text |
| `prospect_experience` | VP Experience **(custom)** | `vp_experience` | Multi-line text |
| `prospect_skills` | VP Skills **(custom)** | `vp_skills` | Multi-line text |
| `prospect_interests` | VP Interests **(custom)** | `vp_interests` | Multi-line text |

**Lead Status.** For contacts newly created from Vibe Prospecting data, set Lead Status (`hs_lead_status`) to the option labelled **New**, internal value `NEW`. Never change Lead Status on existing contacts. If `hs_lead_status` in the target account has no option labelled New, skip it and report; do not create or substitute an option.

### Additional phone extraction

Keep **`contact_mobile_phone` → `mobilephone` unchanged**. Extra numbers come from the separate **`contact_phone_numbers`** export column, not from splitting `contact_mobile_phone`.

In the VP CSV export, `contact_phone_numbers` is a **JSON-encoded array of phone-number strings**, not an array of objects. Read the CSV with a proper CSV parser first, then JSON-decode the cell once; CSV quote escaping is not part of the JSON value. If the data reader already decoded the cell, use the array of strings directly. Walk its string items in array order. Do not split on commas, inspect object values, stringify other types, or extract numbers from arbitrary text. An empty cell is ordinary no data. A malformed JSON cell, non-array value (including a single plain-text phone number), or non-string array item leaves the additional-phone fields unmapped for that row rather than guessing a format.

For comparison only, trim surrounding whitespace and remove spaces, parentheses, hyphens, and dots from each number; preserve a leading `+` and any explicit country code. Exclude every value with the same comparison key as `contact_mobile_phone`, skip blank values, and deduplicate the remaining values by that key in first-occurrence order. The primary can occur anywhere in the array or be absent: do not drop the first item by position or require the primary to be present. Do not infer a country code, convert `00` prefixes, or drop extensions to force equality. Write each retained value exactly as supplied, not its comparison key.

Map the first three retained values to VP Additional Phone Number 1, 2, and 3 respectively. The limit is three **additional** numbers, beyond the primary. Omit unused destinations without clearing existing values; ignore excess values. A missing destination keeps its assigned slot: do not shift its number into another property. Phone fields use the same pre-write mapping report and skip/no-data handling as ordinary fields—no extra prompts, missing-phone warnings, or overflow counts.

The array may not be included in a particular export. If `contact_phone_numbers` is absent or empty, handle it as ordinary unavailable source data and preserve the primary mapping. Never invent extra numbers or fetch a different data source just to fill these fields.

## Companies: Vibe Prospecting business → HubSpot Company

| Vibe Prospecting field | HubSpot label | HubSpot internal name | Type |
|---|---|---|---|
| `business_name` | Company name | `name` | Single-line text |
| `business_domain` | Company Domain Name | `domain` | Single-line text |
| `business_website` | Website URL | `website` | Single-line text |
| `business_city_name` | City | `city` | Single-line text |
| `business_region` | State/Region | `state` | Single-line text |
| `business_country_name` | Country/Region | `country` | Single-line text |
| `business_business_description` | Description | `description` | Multi-line text |
| `prospect_company_linkedin` | LinkedIn Company Page | `linkedin_company_page` | Single-line text |
| `business_logo` | Logo URL | `hs_logo_url` | Text (string) |
| `business_number_of_employees_range` | Employee range | `hs_employee_range` | Text (string) |
| `business_yearly_revenue_range` | Revenue range | `hs_revenue_range` | Text (string) |
| `business_id` | VP Business ID **(custom)** | `vp_business_id` | Single-line text |
| `business_naics` | VP NAICS Code **(custom)** | `vp_naics_code` | Single-line text |
| `business_naics_description` | VP NAICS Description **(custom)** | `vp_naics_description` | Single-line text |
| `business_sic_code` | VP SIC Code **(custom)** | `vp_sic_code` | Single-line text |
| `business_sic_code_description` | VP SIC Code Description **(custom)** | `vp_sic_code_description` | Single-line text |
| `business_business_intent_topics` | VP Intent Topics **(custom)** | `vp_intent_topics` | Multi-line text |

Employee and revenue ranges go only to the range properties above, as the raw range text. Never write them to the numeric `numberofemployees` or `annualrevenue` properties.

`row_num` and `created_at` are export metadata and are not mapped.
